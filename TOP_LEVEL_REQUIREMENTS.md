# FabulA: Top Level Requirements

Requirements state what the engine must do, not how. Each has an ID so other documents and tests can cite it.

## How to read the IDs
- Format: `TLR-xx-yyy`. `xx` is the chapter number (01 Game model, 02 Players and access, and so on, in document order). `yyy` is a sequence number that starts at 001 in each chapter.
- A requirement that is not implemented yet carries the suffix `-Pending`: `TLR-xx-yyy-Pending`. Pending and implemented requirements share the same sequence in their chapter.
- When a requirement is implemented, only the `-Pending` suffix is dropped. The rest of the ID never changes.
- IDs are never reused. A requirement that is withdrawn is struck through and keeps its ID.

## 01. Game model
- **TLR-01-001** The engine runs asynchronous tabletop RPG games with an AI Master, for 1 to N players, solo included.
- **TLR-01-002** Players act whenever they like. They never have to be online at the same time.
- **TLR-01-003** The world advances in turns. When a turn closes, the AI Master resolves all queued actions together and arbitrates conflicts.
- **TLR-01-004** The turn length is set at game setup (default 24 hours). The closing hour and time zone are also configurable (default 03:00, Spain time). Solo games may close the turn as soon as the player has acted.
- **TLR-01-005** Minor actions that affect only one character resolve immediately. Characters in the same place can talk instantly, without waiting for a turn.
- **TLR-01-006** Lethality (low, moderate or high) is set per game. A player whose character dies can continue with a new character, a pregenerated one or an available NPC.
- **TLR-01-007-Pending** Every player request is answered at one of four levels: (1) local in the client, (2) by the engine from the database, (3) by the AI Master immediately, (4) by the AI Master at the turn close.
- **TLR-01-008-Pending** Level 1: the client answers from its synced data, without contacting the engine and using no AI Master quota, when the answer is already known (for example who an NPC was, or where the character first met someone). It may describe atmosphere but must not add facts that change the game world. Anything that would add such a fact goes to a higher level.
- **TLR-01-009-Pending** Level 2: the engine answers from the database without calling the AI Master and without using its quota (inventory, who is in the character's location, time left in the turn, messages, public status of others, speech between characters).
- **TLR-01-010-Pending** Level 3: the AI Master resolves immediately any request that affects only the requesting character and touches nothing shared with other players (other characters, shared NPC or location state, contested objects).
- **TLR-01-011-Pending** Level 4: a request that involves other players or shared state waits for the turn close and is resolved together with the others.

## 02. Players and access
- **TLR-02-001** Each player uses their own AI client (Claude, ChatGPT, Grok or others) through an MCP custom connector. The engine needs no other front end.
- **TLR-02-002** A player proves who they are with a secret key. It is shown once, stored only as a hash, and is never revealed to other players.
- **TLR-02-003** A shared connector key controls access to the server.
- **TLR-02-004** Host administration is not reachable through the player tools. It needs a separate secret.
- **TLR-02-005** A new player can go from nothing to a first game with a step-by-step guide (`gm/setup_guide.md`).
- **TLR-02-006-Pending** Secrets are never carried in places that get logged or stored by intermediaries (URLs, query strings).
- **TLR-02-007-Pending** Player registration and failed key attempts are rate-limited, per source.
- **TLR-02-008-Pending** The engine supports a stronger sign-in than a shared key (such as OAuth) without changing the player tools.

## 03. AI Master
- **TLR-03-001** The AI Master (Gemini) is stateless. Each request carries everything the AI Master needs to answer that request, and nothing the request does not need.
- **TLR-03-002** The AI Master decides the outcomes and keeps the secrets. The server owns the fields it controls (clock, turn state, event logs) and drops attempts to write them.
- **TLR-03-003** The AI Master never narrates. The player's client narrates from the facts it receives.
- **TLR-03-004** Dice are rolled by the server, never by the AI Master or the client.
- **TLR-03-005** The engine uses a strong model for closing turns and a light model for everything else, within the provider's free-tier limits. When the strong model is rate-limited the turn is deferred. When its quota is exhausted or it fails the turn falls back to the light model, and the turn record shows this.
- **TLR-03-006** An invalid AI response is rejected as a whole and retried, and no partial result is stored.
- **TLR-03-007-Pending** The client declares the structured request (type and targets) and the level it expects. The server decides the level by fixed rules over the request and the game data, and the final level may be higher or lower than the client expected.
- **TLR-03-008-Pending** The AI Master may change the level of a request in either direction when its content requires judgment. The player is told the reason.
- **TLR-03-009-Pending** If the AI Master is unavailable or over its limits, a level 3 request is queued as level 4 instead of failing.
- **TLR-03-010-Pending** The context sent to the AI Master is limited to what the request type needs. A level 3 request does not carry the instructions, entities or history that only a turn close needs.
- **TLR-03-011-Pending** The static parts of the AI Master's instructions are reused across requests and games, so repeated input is billed and processed at the lowest cost the provider offers.
- **TLR-03-012-Pending** The state snapshot for a request includes only the NPCs, locations and history relevant to the requesting character or the scene. A turn close includes everything involved in the turn.
- **TLR-03-013-Pending** Older events and messages are condensed into a rolling digest, so the context size stays bounded however long the game runs.
- **TLR-03-014-Pending** The request sent to the AI Master is serialized compactly, and the number of server-rolled dice is proportional to what the request can need.
- **TLR-03-015** The AI Master's answers must follow a declared structure that the provider enforces, so a malformed answer is rare. Retries are counted and reported.
- **TLR-03-016** Changes to the AI Master's instructions are checked against a set of recorded scenarios before release. The checks cover valid structure, secrecy (nothing hidden reaches a player) and rules fidelity.

## 04. Characters
- **TLR-04-001** A player can generate a character, choose a pregenerated one, supply their own for validation, or take over an NPC.
- **TLR-04-002** The player chooses a pregenerated character. The server never chooses for them, rejects a character already taken, and lists the ones still available.
- **TLR-04-003** A character's whole state lives in one record: sheet (maximum and current), inventory, relationships, knowledge, plans, standing orders, decisions, events and inbox.
- **TLR-04-004** A player can have several characters, in different games.

## 05. Content
- **TLR-05-001** Rulesets are markdown files with front matter. Adding one needs no code change. Players can import a ruleset from a document of their own, subject to host approval.
- **TLR-05-002** Adventures are kept in a private repository, so players cannot read their secrets. Adventures can be provided, generated from a seed or document, or generated by the AI Master as the game unfolds.
- **TLR-05-003** The engine supports at least the Fear Itself and Trail of Cthulhu rulesets (GUMSHOE).
- **TLR-05-004** Text written by clients (adventures, rulesets, characters) is treated as data and cannot change the AI Master's protocol.
- **TLR-05-005-Pending** Every NPC, and every player character, has a short description that identifies them without giving their real name or hinting at their identity. It may include appearance, role, manner, and any title or alias by which people commonly know them ("the sheriff", "Doc", "the mayor"). Well-known figures are therefore recognised at first sight through their description. It is part of the adventure or character definition and contains no secrets.
- **TLR-05-006-Pending** The short descriptions of any two NPCs or characters who can be in the same scene must be clearly distinguishable by appearance, role or manner. Two nurses, for example, must differ visibly. This is checked when the adventure or character is validated, and a description that is too similar to another is sent back for correction.
- **TLR-05-007-Pending** Repository documents for the AI Master are sectioned by purpose, so each request type can load only its section.

## 06. State and information integrity
- **TLR-06-001** All game, character, NPC and location state is persisted in the database, which is the single source of truth.
- **TLR-06-002** A player only receives information their characters could know. Secrets of the AI Master and other players stay hidden.
- **TLR-06-003** Every request the client makes returns a player-safe state summary, so the client can always resync.
- **TLR-06-004** A failed or interrupted request never leaves the game in an inconsistent state. A turn cannot be advanced outside its resolution.
- **TLR-06-005-Pending** A character knows another character or an NPC by real name only after learning it: by being introduced or speaking with them, by investigation (a document, a clue, an overheard name), or by being told. Until then, everything that character's player receives, including the narration facts, refers to that person by their short description. This applies equally to NPCs and to other players' characters.
- **TLR-06-006-Pending** Which names a character knows is stored per character, not per player. A name learned by one character is not known by another, including another character of the same player.
- **TLR-06-007-Pending** The AI Master refers to people by id. The server decides, for each receiving character, whether to show the real name or the short description, and it never sends a name the character does not know yet. This does not depend on the Master or the client remembering the rule.
- **TLR-06-008-Pending** When a character learns a name, the change is recorded as an event in that character's knowledge, and the name can be used from the next result onward.
- **TLR-06-009** Saving the result of a request or a turn is atomic: all the records change together or none do, even if the server stops partway through.
- **TLR-06-010** The same request submitted twice (a client retry, a double click) has the effect of one request.

## 07. Client experience
- **TLR-07-001** Creative work (character, game settings, adventure) is done as work packages in the player's own client. The server validates the result and returns the problems to fix.
- **TLR-07-002** After each result the client shows the narration, notebook, status, available illustrations and next possible actions.
- **TLR-07-003** Illustrations are optional per game and consistent in style. Each is visible only to the characters who could see it, delivered as short-lived links.
- **TLR-07-004-Pending** The client tells the player when a request was queued, and that the answer arrives at the turn close.
- **TLR-07-005-Pending** Before answering a time-sensitive question locally, the client refreshes its synced data from the engine.
- **TLR-07-006-Pending** Fixed guidance for the client (narration rules, tool help) is sent once per session or when it changes, not with every result.
- **TLR-07-007-Pending** A result carries only the changes since the client's last sync, unless the client asks for a full resync.
- **TLR-07-008-Pending** Results state how long the narration should be, so clients do not produce more text than the game needs.
- **TLR-07-009-Pending** If the AI Master is busy or over its limits, the player is told clearly what was queued and when to expect the answer. Nothing is lost.

## 08. Operation and cost
- **TLR-08-001** The engine runs on free or low-cost tiers (Vercel, Supabase, Gemini, Cloudflare), with guards against exceeding their limits.
- **TLR-08-002** An external scheduler resolves due turns automatically, at least every 5 minutes.
- **TLR-08-003** The host can manage games, players, adventures and usage through admin commands, never through the player tools.
- **TLR-08-004** Requests stay within the serverless time limit. Slow AI calls fail with a clear message instead of leaving the player waiting.
- **TLR-08-005-Pending** The engine records the level at which each request was answered, so usage and costs per level can be monitored.
- **TLR-08-006** For every AI Master call the engine records the request type, level, tokens in (separating reused from new), tokens out, latency and retries, so cost can be reported per level, per game and per request type.
- **TLR-08-007-Pending** The request quota counters are exact when several server instances run at once, and a counter fault never lets the quota be exceeded unnoticed.
- **TLR-08-008-Pending** The size of a game's persisted state is bounded. Old events and turns move to an archive, and the time to answer a request does not grow with the game's age.
- **TLR-08-009-Pending** The number of database reads per request is bounded and independent of the number of players and entities in the game.
- **TLR-08-010-Pending** The scheduler calls the engine only when a turn is due or work is waiting, without lengthening the maximum delay in 08-002.
- **TLR-08-011-Pending** Configured model names are checked against the provider at startup, and an unavailable model is reported to the host before a turn needs it.
- **TLR-08-012-Pending** The host has a single status view: usage against limits per level, deferred or degraded turns, queued requests, failed images and recent errors.
