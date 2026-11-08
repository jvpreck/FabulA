"""Storage. One generic Store over Supabase (JSONB `data` + version) and an in-memory twin for tests."""
import copy
from datetime import datetime, timezone

from . import config


class Conflict(Exception):
    """A record changed between read and write."""


class MemoryStore:
    def __init__(self):
        self.t = {k: {} for k in config.TABLES}

    def get(self, kind, id_):
        row = self.t[kind].get(id_)
        return (copy.deepcopy(row["data"]), row["version"]) if row else (None, 0)

    def put(self, kind, id_, data, version, index=None):
        row = self.t[kind].get(id_)
        cur = row["version"] if row else 0
        if cur != version:
            raise Conflict(f"{kind}:{id_} version {cur} != {version}")
        self.t[kind][id_] = {"data": copy.deepcopy(data), "version": cur + 1, "index": dict(index or {})}
        return cur + 1

    def delete(self, kind, id_):
        self.t[kind].pop(id_, None)

    def find(self, kind, **flt):
        out = []
        for id_, row in self.t[kind].items():
            if all(row["index"].get(k) == v for k, v in flt.items()):
                out.append((copy.deepcopy(row["data"]), row["version"]))
        return out

    def due_games(self, now_iso):
        res = []
        for id_, row in self.t["game"].items():
            ix = row["index"]
            if ix.get("phase") == "active" and ix.get("turn_closes") and ix["turn_closes"] <= now_iso:
                res.append(id_)
        return res


class SupabaseStore:
    def __init__(self, client):
        self.c = client

    def _tbl(self, kind):
        return self.c.table(config.TABLES[kind])

    def get(self, kind, id_):
        r = self._tbl(kind).select("data,version").eq("id", id_).limit(1).execute().data
        return (r[0]["data"], r[0]["version"]) if r else (None, 0)

    def put(self, kind, id_, data, version, index=None):
        now = datetime.now(timezone.utc).isoformat()
        payload = {"data": data, "version": version + 1, "updated_at": now, **(index or {})}
        if version == 0:
            try:
                self._tbl(kind).insert({"id": id_, **payload}).execute()
            except Exception as e:  # duplicate key means someone else created it
                raise Conflict(str(e))
            return 1
        r = self._tbl(kind).update(payload).eq("id", id_).eq("version", version).execute().data
        if not r:
            raise Conflict(f"{kind}:{id_} changed")
        return version + 1

    def delete(self, kind, id_):
        self._tbl(kind).delete().eq("id", id_).execute()

    def find(self, kind, **flt):
        q = self._tbl(kind).select("data,version")
        for k, v in flt.items():
            q = q.eq(k, v)
        return [(r["data"], r["version"]) for r in q.execute().data]

    def due_games(self, now_iso):
        r = (self._tbl("game").select("id").eq("phase", "active").lte("turn_closes", now_iso).execute().data)
        return [x["id"] for x in r]


def index_for(kind, doc):
    """Index columns for a record, so that the store can query without opening the JSON."""
    if kind == "game":
        return {"phase": doc.get("phase"), "turn_closes": (doc.get("clock") or {}).get("turn_closes")}
    if kind == "character":
        return {"game_id": doc["game_id"], "player_id": doc["player_id"], "is_alive": bool(doc.get("is_alive", True))}
    if kind in ("npc_state", "location_state"):
        return {"game_id": doc["game_id"]}
    if kind == "submit_action":
        return {"game_id": doc["game_id"], "turn": doc["turn"]}
    if kind in ("npc", "location"):
        sc = doc.get("scope") or {}
        return {"adventure_id": sc.get("adventure_id"), "game_id": sc.get("game_id")}
    if kind == "adventure":
        return {"owner_player_id": doc.get("owner_player_id")}
    if kind == "task":
        return {"player_id": doc["player_id"], "status": doc.get("status")}
    if kind == "image":
        return {"game_id": doc["game_id"], "status": doc.get("status")}
    if kind == "ruleset":
        return {"status": doc.get("status")}
    if kind == "key":
        return {"player_id": doc.get("player_id")}
    return {}


def definition_key(scope_id, entity_id):
    return f"{scope_id}:{entity_id}"


def doc_key(kind, doc):
    if kind in ("npc_state",):
        return state_key(kind, doc["game_id"], doc["npc_id"])
    if kind == "location_state":
        return state_key(kind, doc["game_id"], doc["location_id"])
    if kind in ("npc", "location"):
        sc = doc.get("scope") or {}
        return definition_key(sc.get("adventure_id") or sc.get("game_id"), doc["id"])
    return doc["id"]


def state_key(kind, game_id, entity_id):
    """Run-state records are keyed by game and entity."""
    if kind in ("npc_state", "location_state"):
        return f"{game_id}:{entity_id}"
    return entity_id


class Workspace:
    """Loads records lazily, tracks changes, writes them back together.
    All validation happens in memory first, so a rejected response leaves storage untouched."""

    def __init__(self, store):
        self.store = store
        self.docs = {}
        self.versions = {}
        self.dirty = set()

    def get(self, kind, id_, create=None):
        key = (kind, id_)
        if key not in self.docs:
            doc, ver = self.store.get(kind, id_)
            if doc is None and create is not None:
                doc, ver = copy.deepcopy(create), 0
                self.dirty.add(key)
            self.docs[key] = doc
            self.versions[key] = ver
        return self.docs[key]

    def put(self, kind, id_, doc):
        key = (kind, id_)
        if key not in self.versions:
            self.versions[key] = self.store.get(kind, id_)[1]
        self.docs[key] = doc
        self.dirty.add(key)

    def snapshot(self):
        return copy.deepcopy((self.docs, self.versions, self.dirty))

    def restore(self, snap):
        self.docs, self.versions, self.dirty = copy.deepcopy(snap)

    def touch(self, kind, id_):
        if (kind, id_) in self.docs and self.docs[(kind, id_)] is not None:
            self.dirty.add((kind, id_))

    def find(self, kind, **flt):
        """Store rows plus anything created or changed in this workspace."""
        out, seen = [], set()
        for doc, ver in self.store.find(kind, **flt):
            key = (kind, doc_key(kind, doc))
            if key not in self.docs:
                self.docs[key], self.versions[key] = doc, ver
            seen.add(key)
            if self.docs[key] is not None:
                out.append(self.docs[key])
        for key, doc in list(self.docs.items()):
            if key[0] == kind and key not in seen and doc is not None:
                ix = index_for(kind, doc)
                if all(ix.get(k) == v for k, v in flt.items()):
                    out.append(doc)
        return out

    def load_game_characters(self, game_id):
        return self.find("character", game_id=game_id)

    def commit(self):
        for key in sorted(self.dirty):
            kind, id_ = key
            doc = self.docs[key]
            if doc is None:
                continue
            ver = self.versions[key]
            self.versions[key] = self.store.put(kind, id_, doc, ver, index_for(kind, doc))
        self.dirty.clear()
