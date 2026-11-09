"""MCP tools. Players use these, identified by their secret player key (see register_player).
There are no administrator tools here: resolve_turn and the host commands live behind /internal/* (see app.py and admin.py)."""
import functools
import json

from mcp.server.fastmcp import Image

from .engine import AIMasterBusy, Engine, EngineError, GeminiTrouble
from .db import Conflict
from .files import AdventureSourceError


def _next_step(msg):
    m = msg.lower()
    if "player key" in m:
        return ("If the player has a key, ask them for it and use it. If they are new, call start_here, then register_player. "
                "Never invent a key and never register a second time without asking the player.")
    if "no character" in m or "character" in m and "confirm" in m:
        return "The player needs a confirmed character in this game: call get_guide('create-character')."
    if "unknown guide" in m or "unknown topic" in m:
        return "Call get_guide with no name to list the guides."
    return "If you are unsure how to use the engine, call start_here, or get_guide('player-client-guide')."


def _safe(fn):
    @functools.wraps(fn)
    def wrapper(*a, **kw):
        try:
            return fn(*a, **kw)
        except GeminiTrouble as e:
            return {"error": str(e), "gemini_unavailable": True, "retry_in_minutes": 5,
                    "next_step": "Tell the player plainly that there are problems with Gemini (the AI Master's model), that nothing was lost "
                                 "or changed, and to try the same thing again in a few minutes. Do not retry in a loop and do not invent a result."}
        except AIMasterBusy as e:
            return {"error": str(e), "ai_master_busy": True, "retry_in_minutes": 2,
                    "next_step": "Tell the player plainly that the AI Master has used its request quota for now, that nothing was lost or changed, and to try "
                                 "the same thing again in a couple of minutes. An action can still be sent: it is saved for the turn close. Do not retry in a loop."}
        except EngineError as e:
            return {"error": str(e), "next_step": _next_step(str(e))}
        except AdventureSourceError as e:
            return {"error": f"The supplied adventures cannot be read right now ({e}). Try again later."}
        except Conflict:
            return {"error": "The game changed while your request was processed. Please try again."}
    return wrapper


def register(mcp, engine: Engine):
    @mcp.tool()
    @_safe
    def register_player(display_name: str = "", language: str = "en") -> dict:
        """First step for a new player. Creates the player and returns their secret player_key, shown only once. Keep it (in this chat or
        project) and pass it as player_key on every other call. Never show it to anyone else, and never print it in shared places."""
        return engine.register_player(display_name, language)

    @mcp.tool()
    @_safe
    def start_here() -> dict:
        """CALL THIS FIRST, before any other tool, in every new conversation. Needs no key. Returns what this engine is, what you are
        supposed to do, which tool to call for what the player wants, and the list of guides (get_guide)."""
        return engine.start_here()

    @mcp.tool()
    @_safe
    def get_guide(name: str = "", topic: str = "") -> dict:
        """Read a guide. Needs no key. name is one of: player-client-guide (how to use the engine and its tools), players-guide (how to play, for
        the player; topic can be start, choose, character, commands, turns, autonomous, death or mechanics), create-character,
        create-game, generate-adventure, narrator (how to narrate and what to remember), mcp-guide (the short connection instructions), import-ruleset (convert a game system from a document). With no name it lists the guides."""
        return engine.guide(name, topic)

    @mcp.tool()
    @_safe
    def get_setup_guide(topic: str = "") -> dict:
        """The guide for a new player (same as get_guide with name players-guide). Needs no key. topic is empty for the whole guide, or one of:
        start, choose, character, commands, turns, autonomous, death, mechanics. Relay it in the player's language and show only what was asked."""
        return engine.setup_guide(topic)

    @mcp.tool()
    @_safe
    def list_games(player_key: str) -> dict:
        """The player's games, and the open games that have free seats and can be joined with join_game."""
        return engine.list_games(engine.authenticate(player_key))

    @mcp.tool()
    @_safe
    def list_adventures(player_key: str) -> dict:
        """List the adventures and rulesets available. Adventures can be supplied files or ones you generated."""
        return engine.list_adventures(engine.authenticate(player_key))

    @mcp.tool()
    @_safe
    def generate_adventure(player_key: str, ruleset_id: str = "", seed_text: str = "", document_text: str = "",
                           generation: str = "", language: str = "en", seed_id: str = "") -> dict:
        """Start generating a new adventure from a published seed (seed_id, from list_seeds), from a short seed of the player's own
        (seed_text: premise, theme, era, place) or from a document. Returns a work package: follow its instructions step by step in the chat,
        then send the result with submit_package. generation is 'emergent' (a secret seed, the rest is created in play) or 'full' (a complete
        secret plan); leave it empty to use the seed's suggestion, otherwise 'emergent'. ruleset_id may be empty with a seed_id."""
        return engine.generate_adventure(engine.authenticate(player_key), ruleset_id, seed_text, document_text, generation, language, seed_id)

    @mcp.tool()
    @_safe
    def list_seeds(player_key: str) -> dict:
        """List the published adventure seeds a player can choose from to generate a full adventure. Each has a title, format, suggested
        number of players, era and a one-line summary without spoilers. Show only those fields to the player."""
        return engine.list_seeds(engine.authenticate(player_key))

    @mcp.tool()
    @_safe
    def list_takeovers(player_key: str, game_id: str) -> dict:
        """List the NPCs a player of a running game may take over as their character (a late joiner, or a player whose character died): unclaimed
        pregenerated characters and other NPCs the party has met, never the adventure's main characters. Show only name, role and trait. To take one,
        call generate_character with route 'from_npc' and its npc_id."""
        return engine.list_takeovers(engine.authenticate(player_key), game_id)

    @mcp.tool()
    @_safe
    def import_ruleset(player_key: str, document_text: str, ruleset_id: str = "", language: str = "en") -> dict:
        """Convert a game system from a document the player provides (pasted text of the rules) into a ruleset for this engine. Returns a
        work package: follow its steps in the chat, then send the result with submit_package. The new ruleset is stored as pending and
        can be used only after the host approves it. Call get_guide with name import-ruleset first."""
        return engine.import_ruleset(engine.authenticate(player_key), document_text, ruleset_id, language)

    @mcp.tool()
    @_safe
    def create_game(player_key: str, adventure_id: str, title: str = "", language: str = "", display_name: str = "",
                    lethality: str = "", turn_interval_hours: int = 0, turn_span: str = "", pvp: str = "", visibility: str = "",
                    turn_close_hour: int = -2, turn_timezone: str = "") -> dict:
        """Start a new game run from an adventure. Returns a work package that collects the settings (lethality low, moderate or high; the default is high,
        turn interval, the hour of the day a turn closes, pvp, language, visibility private or open) with the player; then send the result with submit_package.
        turn_close_hour is 0 to 23 (hour of the day in turn_timezone, default Europe/Madrid, at which a turn of whole days closes; the default is 3, in the middle of
        the night) or -1 for no fixed hour. Optional arguments prefill defaults."""
        s = {k: v for k, v in {"lethality": lethality, "turn_interval_hours": turn_interval_hours or None,
                               "turn_span": turn_span, "pvp": pvp, "visibility": visibility,
                               "turn_timezone": turn_timezone}.items() if v}
        if turn_close_hour != -2:
            s["turn_close_hour"] = turn_close_hour
        return engine.create_game(engine.authenticate(player_key), adventure_id, title or None, language or None, s, display_name or None)

    @mcp.tool()
    @_safe
    def join_game(player_key: str, game_id: str, display_name: str = "", language: str = "") -> dict:
        """Join an existing game by its id."""
        return engine.join_game(engine.authenticate(player_key), game_id, display_name or None, language or None)

    @mcp.tool()
    @_safe
    def generate_character(player_key: str, game_id: str, route: str = "generate", concept: str = "", pregen_id: str = "",
                           sheet_text: str = "", sheet_json: dict | None = None, npc_id: str = "",
                           replaces_character_id: str = "", changes: str = "") -> dict:
        """Create a character for a game. route 'generate' (build a new one) and 'provided' (convert and check a sheet the player pastes)
        return a work package to follow in the chat, then send the result with submit_package. route 'pregen' (pick a pregenerated one)
        and 'from_npc' (replacement only, from an available NPC) act at once. After a character dies, pass replaces_character_id
        to continue in the same game."""
        return engine.generate_character(engine.authenticate(player_key), game_id, route, concept, pregen_id or None, sheet_text, sheet_json,
                                         npc_id or None, replaces_character_id or None, changes)

    @mcp.tool()
    @_safe
    def submit_package(player_key: str, task_id: str, package: dict) -> dict:
        """Send back the finished work package for generate_adventure, create_game, generate_character or import_ruleset. If accepted is false, fix the
        listed problems and submit again with the same task_id."""
        return engine.submit_package(engine.authenticate(player_key), task_id, package)

    @mcp.tool()
    @_safe
    def submit_action(player_key: str, game_id: str, kind: str, text: str = "", character_id: str = "",
                      payload: dict | None = None, request_id: str = "") -> dict:
        """Send anything the character does or the player decides. kind is one of: action (what the character wants to do, free text),
        say (speak to a character in the same place; payload {to, whisper}), setup_answers (payload {answers}),
        character_submission, character_confirm (payload {approved}), standing_orders (payload {standing_orders, safety}),
        thread_note (payload {type, text}), message (payload {to, channel, text}), decision (payload {prompt_id, choice}),
        free_query, pause, resume (payload {choice}). Minor actions that affect only your character are resolved at once;
        the rest wait for the turn. Returns the results now available to you.
        request_id: a fresh unique id (for example a short random string) for each new request, sent again unchanged if you must retry after
        a timeout or an error you did not see the answer to. The same request_id is processed once; the retry returns the first answer."""
        return engine.submit_action(engine.authenticate(player_key), game_id, kind, text, character_id or None, payload, request_id)

    @mcp.tool()
    @_safe
    def get_results(player_key: str, game_id: str = "") -> dict:
        """Collect results you have not received yet: turn results, what other characters did in front of yours, messages and speech.
        Call it at the start of every session and whenever the player asks what happened."""
        return engine.get_results(engine.authenticate(player_key), game_id or None)

    @mcp.tool()
    @_safe
    def get_character(player_key: str, game_id: str, character_id: str = "") -> dict:
        """Fetch the character's current state, knowledge, settings and saved story summary from the server (the truth)."""
        return engine.get_character(engine.authenticate(player_key), game_id, character_id or None)

    @mcp.tool()
    @_safe
    def list_images(player_key: str, game_id: str) -> dict:
        """The pictures of the story that the player's characters could see in this game: image_id, turn and caption."""
        return engine.list_images(engine.authenticate(player_key), game_id)

    @mcp.tool()
    @_safe
    def get_image(player_key: str, game_id: str, image_id: str, inline: bool = False):
        """One picture of the story. By default returns a fresh short-lived link to give the player (it expires after a few minutes; call
        again for a new one). Always present pictures to the player as this link, written [Illustration: caption](url). Pass inline=true only
        when the player explicitly asks to see the picture itself in the chat. Never post a link anywhere shared."""
        pid = engine.authenticate(player_key)
        if not inline:
            return engine.get_image(pid, game_id, image_id)
        info, data = engine.get_image_data(pid, game_id, image_id)
        if data is None:
            return info
        return [json.dumps(info, ensure_ascii=False), Image(data=data, format="jpeg")]

    @mcp.tool()
    @_safe
    def set_game_options(player_key: str, game_id: str, illustrations: str = "") -> dict:
        """For the host of a game only: turn illustrations 'on' or 'off' for the game."""
        return engine.set_game_options(engine.authenticate(player_key), game_id, illustrations)

    @mcp.tool()
    @_safe
    def get_rules(ruleset_id: str) -> dict:
        """Read the text of an available ruleset (ids are in list_adventures under rulesets)."""
        return engine.get_rules(ruleset_id)

    @mcp.tool()
    @_safe
    def save_story_summary(player_key: str, game_id: str, character_id: str, text: str, turn: int = -1) -> dict:
        """Store the story summary you keep for the character, so it survives if the chat is compacted."""
        return engine.save_story_summary(engine.authenticate(player_key), game_id, character_id, text, None if turn < 0 else turn)
