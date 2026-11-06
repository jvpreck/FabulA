"""Applies the GM's response to a Workspace. Everything is validated in memory before anything is saved."""
import copy
import uuid

from .db import state_key, definition_key


class ApplyError(Exception):
    pass


# Paths the GM may never write (the server owns them).
FORBIDDEN_TOP = {
    "character": {"inbox", "client_sync", "events", "decisions", "player_id", "game_id"},
    "game": {"events", "decisions", "messages", "ticks", "id", "adventure_id", "ruleset_id"},
}
GM_ENTITIES = {"game", "character", "npc_state", "location_state", "npc", "location"}
OPS = {"upsert", "merge", "adjust", "append", "remove"}


def new_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _walk(doc, path, create=False):
    parts = path.split(".")
    cur = doc
    for p in parts[:-1]:
        cur = _step(cur, p, create)
    return cur, parts[-1]


def _step(cur, p, create):
    if isinstance(cur, list):
        try:
            return cur[int(p)]
        except (ValueError, IndexError):
            raise ApplyError(f"bad list index {p}")
    if not isinstance(cur, dict):
        raise ApplyError(f"path crosses a non-object at {p}")
    if p not in cur or cur[p] is None:
        if not create:
            raise ApplyError(f"path segment {p} does not exist")
        cur[p] = {}
    return cur[p]


def _get_leaf(container, key):
    if isinstance(container, list):
        return container[int(key)]
    return container.get(key)


def _set_leaf(container, key, value):
    if isinstance(container, list):
        container[int(key)] = value
    else:
        container[key] = value


def deep_merge(dst, patch):
    for k, v in patch.items():
        if v is None:
            dst.pop(k, None)
        elif isinstance(v, dict) and isinstance(dst.get(k), dict):
            deep_merge(dst[k], v)
        else:
            dst[k] = copy.deepcopy(v)
    return dst


def character_defaults(game_id, player_id, adventure_id, ruleset_id, character_id, name=None, language="en"):
    return {
        "id": character_id, "game_id": game_id, "player_id": player_id,
        "adventure_id": adventure_id, "ruleset_id": ruleset_id, "name": name, "origin": "generated",
        "status": "draft", "is_alive": True, "death": None, "replaces_character_id": None,
        "replaced_by_character_id": None, "from_npc_id": None,
        "participation": {"role": "player", "status": "active", "joined_tick": 0, "missed_ticks": 0, "last_submitted_tick": None},
        "language": language,
        "settings": {"safety": {"fears": [], "pvp_optout": False, "stop_signal": "pause"},
                     "standing_orders": {"hold": "Stay safe, rest, take no risks.", "risk_tolerance": "low",
                                         "perception_check": {"mode": "auto", "anchor": None, "spend": None},
                                         "default_spends": [], "never_do": [], "reply_to_messages": True}},
        "validation": None, "sheet": {"groups": {}, "derived": {}, "unrated": []}, "conditions": [],
        "ruleset_state": {}, "location": None, "inventory": [], "means": {}, "relationships": [],
        "run_notes": {"known_gaps": [], "promises": [], "debts": [], "scars": [], "goals_progress": "", "other": {}},
        "knowledge": {"facts": [], "clues": [], "documents": [], "threads": [], "spend_offers": [], "journal": "", "met": []},
        "decisions": [], "events": [], "inbox": [],
        "tick_state": {"tick": 0, "blocks_used": [], "queued_action_ids": [], "autonomous_action_ids": []},
        "client_sync": {"version": 1, "story_summary": "", "story_summary_tick": 0, "updated_at": None},
        "gm_only": {},
    }


class Applier:
    def __init__(self, ws, game_id, mode, now_iso, allow_definitions_for_adventure=None):
        self.ws = ws
        self.game_id = game_id
        self.mode = mode
        self.now = now_iso
        self.adv_scope = allow_definitions_for_adventure
        self.touched = set()
        self.ignored = []  # writes to server-owned fields that were dropped instead of rejected
        self.before_alive = {}

    # -- entity access -------------------------------------------------
    def _doc(self, entity, id_, must_exist=True):
        if entity == "game":
            d = self.ws.get("game", id_)
            kind, key = "game", id_
        elif entity in ("npc_state", "location_state"):
            key = state_key(entity, self.game_id, id_)
            d = self.ws.get(entity, key)
            kind = entity
        else:
            d = self.ws.get(entity, id_)
            kind, key = entity, id_
        if d is None and must_exist:
            raise ApplyError(f"{entity} {id_} does not exist")
        return d, kind, key

    def _check_scope(self, entity, id_):
        if entity == "game" and id_ != self.game_id:
            raise ApplyError("an operation targets another game")
        if entity == "character":
            c = self.ws.get("character", id_)
            if c is not None and c["game_id"] != self.game_id:
                raise ApplyError("an operation targets a character of another game")

    # -- operations ----------------------------------------------------
    def apply_ops(self, ops):
        for i, op in enumerate(ops or []):
            try:
                self._one(op)
            except ApplyError as e:
                raise ApplyError(f"state_changes[{i}] {op.get('op')} {op.get('entity')} {op.get('id')}: {e}")
            except (KeyError, TypeError, ValueError) as e:
                raise ApplyError(f"state_changes[{i}] malformed: {e!r}")

    def _one(self, op):
        kind = op.get("op")
        entity = op.get("entity")
        id_ = op.get("id")
        if kind not in OPS:
            raise ApplyError(f"unknown op {kind}")
        if entity not in GM_ENTITIES:
            raise ApplyError(f"entity {entity} is not writable by the GM")
        if not id_:
            raise ApplyError("missing id")
        self._check_scope(entity, id_)
        if entity in ("npc", "location"):
            return self._definition(op, entity, id_)
        if kind == "upsert":
            return self._upsert(op, entity, id_)
        doc, k, key = self._doc(entity, id_)
        top_forbidden = FORBIDDEN_TOP.get(entity, set())
        if kind == "merge":
            patch = op["patch"]
            bad = set(patch) & top_forbidden
            if bad:  # the server writes these itself (events, decisions, inbox...): drop them, keep the rest
                self.ignored.append(f"{entity} {id_}: fields {sorted(bad)}")
                patch = {k: v for k, v in patch.items() if k not in bad}
            if entity == "game" and "inbox" in (patch.get("setup") or {}):
                self.ignored.append(f"{entity} {id_}: setup.inbox")
                patch = {**patch, "setup": {k: v for k, v in patch["setup"].items() if k != "inbox"}}
            deep_merge(doc, patch)
        else:
            path = op["path"]
            if path.split(".")[0] in top_forbidden or (entity == "game" and path.startswith("setup.inbox")):
                self.ignored.append(f"{entity} {id_}: path {path}")  # server-owned: the response fields already carry it
                return
            if kind == "adjust":
                cont, last = _walk(doc, path)
                cur = _get_leaf(cont, last)
                if isinstance(cur, bool) or not isinstance(cur, (int, float)):
                    raise ApplyError(f"{path} is not a number")
                delta = op["delta"]
                if isinstance(delta, bool) or not isinstance(delta, (int, float)):
                    raise ApplyError("delta must be a number")
                _set_leaf(cont, last, cur + delta)
            elif kind == "append":
                cont, last = _walk(doc, path, create=True)
                arr = _get_leaf(cont, last)
                if arr is None:
                    arr = []
                    _set_leaf(cont, last, arr)
                if not isinstance(arr, list):
                    raise ApplyError(f"{path} is not a list")
                arr.append(copy.deepcopy(op["doc"]))
            elif kind == "remove":
                cont, last = _walk(doc, path)
                arr = _get_leaf(cont, last)
                if not isinstance(arr, list):
                    raise ApplyError(f"{path} is not a list")
                n = len(arr)
                arr[:] = [x for x in arr if not (isinstance(x, dict) and x.get("id") == op["item_id"])]
                if len(arr) == n:
                    raise ApplyError(f"no item {op['item_id']} in {path}")
        self._mark(entity, k, key, id_)

    def _mark(self, entity, kind, key, id_):
        self.ws.touch(kind, key)
        if entity == "character":
            self.touched.add(id_)

    def _upsert(self, op, entity, id_):
        doc = copy.deepcopy(op["doc"])
        if not isinstance(doc, dict):
            raise ApplyError("doc must be an object")
        if entity == "game":
            raise ApplyError("the game record cannot be replaced")
        if entity == "character":
            existing = self.ws.get("character", id_)
            if existing is None:
                raise ApplyError("characters are created by the server; use merge")
            for k in FORBIDDEN_TOP["character"]:
                doc.pop(k, None)
            for k in FORBIDDEN_TOP["character"]:
                if k in existing:
                    doc[k] = existing[k]
            self.ws.put("character", id_, doc)
            self.touched.add(id_)
            return
        if entity == "npc_state":
            doc["npc_id"] = id_
        else:
            doc["location_id"] = id_
        doc["game_id"] = self.game_id
        key = state_key(entity, self.game_id, id_)
        self.ws.put(entity, key, doc)

    def _definition(self, op, entity, id_):
        if op["op"] != "upsert":
            raise ApplyError("fixed npc and location definitions can only be created, never edited")
        scope_id = self.adv_scope or self.game_id
        key = definition_key(scope_id, id_)
        if self.ws.get(entity, key) is not None:
            raise ApplyError(f"fixed {entity} {id_} already exists and cannot change")
        doc = copy.deepcopy(op["doc"])
        doc["id"] = id_
        sc = doc.get("scope") or {}
        if self.adv_scope:
            doc["scope"] = {"adventure_id": self.adv_scope, "game_id": None}
        else:
            doc["scope"] = {"adventure_id": None, "game_id": self.game_id}
        if sc and not self.adv_scope and sc.get("game_id") not in (None, self.game_id):
            raise ApplyError("definition scoped to another game")
        self.ws.put(entity, key, doc)

    # -- records the server writes for the GM ---------------------------
    def snapshot_alive(self, characters):
        self.before_alive = {c["id"]: c.get("is_alive", True) for c in characters}

    def apply_events(self, game, events, characters_by_id):
        for ev in events or []:
            ev = copy.deepcopy(ev)
            ev.setdefault("id", new_id("ev"))
            ev.setdefault("visibility", "gm")
            ev.setdefault("participants", [])
            ev.setdefault("witnesses", [])
            cs = ev.pop("character_summaries", {}) or {}
            game["events"].append(ev)
            for cid in set(ev["participants"]) | set(ev["witnesses"]) | set(cs):
                c = characters_by_id.get(cid)
                text = cs.get(cid)
                if not c or not text:
                    continue
                c["events"].append({"id": ev["id"], "tick": ev.get("tick"), "day": ev.get("day"), "block": ev.get("block"),
                                    "location_id": ev.get("location_id"), "summary": text})
                self._touch_char(c)

    def apply_decisions(self, game, decisions, characters_by_id):
        for d in decisions or []:
            d = copy.deepcopy(d)
            d.setdefault("id", new_id("d"))
            d.setdefault("status", "active")
            game["decisions"].append(d)
            c = characters_by_id.get(d.get("character_id"))
            if c:
                safe = {k: v for k, v in d.items() if k != "gm_impact"}
                c["decisions"].append(safe)
                self._touch_char(c)

    def apply_messages(self, game, messages, characters_by_id, tick):
        for m in messages or []:
            m = copy.deepcopy(m)
            m.setdefault("id", new_id("m"))
            m.setdefault("sent_tick", tick)
            m.setdefault("status", "pending")
            game["messages"].append(m)
            if m.get("status") == "delivered" and m.get("to") in characters_by_id:
                c = characters_by_id[m["to"]]
                self.add_inbox(game, c, "message", {
                    "kind": "message", "language": c.get("language"),
                    "facts": [{"block": None, "kind": "dialogue",
                               "text": f"A message from {self._name(m.get('from'), characters_by_id)} by {m.get('channel')}: \"{m.get('text')}\""}],
                    "prompts": [], "narration_hints": {"mood": "", "pace": "", "senses": [], "do_not": []}}, tick)

    @staticmethod
    def _name(id_, chars):
        c = chars.get(id_)
        return c["name"] if c and c.get("name") else str(id_)

    def _touch_char(self, c):
        self.ws.touch("character", c["id"])
        self.touched.add(c["id"])

    def add_inbox(self, game, character, kind, result, tick):
        item = {"id": new_id("r"), "tick": tick, "kind": kind, "delivered": False,
                "created_at": self.now, "result": result}
        character["inbox"].append(item)
        hints = result.get("narration_hints") if isinstance(result, dict) else None
        if character.get("opening_due") and isinstance(hints, dict) and hints.get("opening") is True:
            character["opening_due"] = False
        self._touch_char(character)
        return item

    def add_setup_inbox(self, game, player_id, result, tick):
        item = {"id": new_id("r"), "tick": tick, "kind": "system", "delivered": False,
                "created_at": self.now, "result": result}
        game.setdefault("setup", {"answers": {}, "inbox": {}}).setdefault("inbox", {}).setdefault(player_id, []).append(item)
        self.ws.touch("game", game["id"])

    def apply_results(self, game, results, characters_by_id, tick, store_in_tick=False):
        players = {c["player_id"] for c in characters_by_id.values()} | {r.get("player_id") for r in game.get("roster", [])}
        entry = next((t for t in game.get("ticks", []) if t["n"] == tick), None)
        for key, items in (results or {}).items():
            if isinstance(items, dict):
                items = [items]
            for it in items:
                it = copy.deepcopy(it)
                kind = it.get("kind", "own")
                if key in characters_by_id:
                    self.add_inbox(game, characters_by_id[key], kind, it, tick)
                    if store_in_tick and entry is not None:
                        entry.setdefault("results", {}).setdefault(key, []).append(it)
                elif key in players:
                    self.add_setup_inbox(game, key, it, tick)
                else:
                    raise ApplyError(f"result addressed to unknown recipient {key}")

    def apply_shared_digest(self, game, digest, characters, tick):
        if not digest:
            return
        entry = next((t for t in game.get("ticks", []) if t["n"] == tick), None)
        if entry is not None:
            entry.setdefault("shared_digest", []).extend(digest)
        for c in characters:
            if c.get("is_alive", True) and c.get("status") in ("active", "sidelined"):
                self.add_inbox(game, c, "system", {
                    "kind": "system", "language": c.get("language"),
                    "facts": [{"block": None, "kind": "world", "text": d.get("text", "")} for d in digest],
                    "prompts": [], "narration_hints": {"mood": "", "pace": "", "senses": [], "do_not": []}}, tick)

    def check_lethality(self, game, characters, decisions):
        lethality = (game.get("settings") or {}).get("lethality", "high")
        for c in characters:
            if self.before_alive.get(c["id"], True) and not c.get("is_alive", True):
                if not c.get("death"):
                    raise ApplyError(f"character {c['id']} died without a death record")
                if lethality == "low":
                    chose = any(d.get("character_id") == c["id"] and "chosen_death" in (d.get("tags") or []) for d in decisions or [])
                    if not chose:
                        raise ApplyError("lethality is low: a character can only die by the player's choice at a gate (decision tagged chosen_death)")
                c["status"] = "dead"
                self._touch_char(c)

    def bump_versions(self, characters_by_id):
        for cid in self.touched:
            c = characters_by_id.get(cid)
            if c:
                c["client_sync"]["version"] = c["client_sync"].get("version", 0) + 1
