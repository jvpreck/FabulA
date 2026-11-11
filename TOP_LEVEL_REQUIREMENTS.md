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
- **TLR-01-009** Level 2: the engine answers from the database without calling the AI Master and without using its quota (inventory, who is in the character's location, time left in the turn, messages, public status of others, speech between characters).
- **TLR-01-010-Pending** Level 3: the AI Master resolves immediately any request that affects only the requesting character and touches nothing shared with other players (other characters, shared NPC or location state, contested objects).
- **TLR-01-011-Pending** Level 4: a request that involves other players or shared state waits for the turn close and is resolved together with the others.
- **TLR-01-013** There is no game setup phase. A game is created by one action (the host's settings, including how many players are expected) and each player creates a character with one action. A character whose check passes is confirmed by the server, and the game starts by itself when every player who joined, and as many as the host expects, have a confirmed character. The AI Master is called once to check the character and once to give the openings when the game starts.
- **TLR-01-012** A player who has played enough for the turn can send the command "ready to pass turn". The engine records that status for the player's character. After it, the player can no longer send actions to the engine for that turn (they can only use what the client answers alone, level 1). When every active player has sent it, the engine may close the turn before the formal time.
- **TLR-01-014-Pending** An action never closes the turn by itself. If the Blocks of the turn are used up, the engine either resolves the action in the Block that is open or refuses it plainly and tells the player what they can do. The turn closes only at its time, when every active player is ready, or by an explicit rule of the adventure.
- **TLR-01-015-Pending** The time a turn closes is recomputed when each turn opens (its configured length from its opening, the first turn up to the next closing hour). The closing time shown to the client is the one the scheduler uses.
- **TLR-01-016-Pending** Every answer reports the level at which it was actually answered. A turn close is level 4, bookkeeping handled by the engine is level 2, and no answer lacks a level.
- **TLR-01-017-Pending** A player can speak to the NPCs present in the scene. The answer comes at once (level 3), and the list of who is present includes the NPCs the character can talk to.

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
- **TLR-03-009** If the AI Master is unavailable or over its limits, a level 3 request is queued as level 4 instead of failing.
- **TLR-03-010** The context sent to the AI Master is limited to what the request type needs. A level 3 request does not carry the instructions, entities or history that only a turn close needs.
- **TLR-03-011-Pending** The static parts of the AI Master's instructions are reused across requests and games, so repeated input is billed and processed at the lowest cost the provider offers.
- **TLR-03-012** The state snapshot for a request includes only the NPCs, locations and history relevant to the requesting character or the scene. A turn close includes everything involved in the turn.
- **TLR-03-013-Pending** Older events and messages are condensed into a rolling digest, so the context size stays bounded however long the game runs.
- **TLR-03-014** The request sent to the AI Master is serialized compactly, and the number of server-rolled dice is proportional to what the request can need.
- **TLR-03-015-Pending** The AI Master's answers must follow a declared structure that the provider enforces, so a malformed answer is rare. Retries are counted and reported.
- **TLR-03-016** Changes to the AI Master's instructions are checked against a set of recorded scenarios before release. The checks cover valid structure, secrecy (nothing hidden reaches a player) and rules fidelity.
- **TLR-03-017-Pending** The fixed instructions sent with each request are limited to what that kind of request needs. An ordinary request of one character carries far less than the turn close (a target of at most 20,000 tokens, against about 56,000 now), so more requests fit in the provider's per-minute token limit and each is answered faster.
- **TLR-03-018-Pending** The AI Master's thinking effort follows the request: the lowest level for questions and simple requests, a higher one for actions that need judgment and for the turn close. The effect on answer time and quality is measured before a level is made the default.
- **TLR-03-019-Pending** An AI Master answer that is malformed but whose meaning is clear (a missing key, a number sent as text, a character named by id instead of name) is repaired by the server. Only an answer that cannot be understood is rejected. Repairs and rejections are counted per request kind (see 08-006).
- **TLR-03-020-Pending** When an action cannot be resolved after the retries, the player does not receive a bare error. The action is queued for the turn close as in 03-009 and the answer says so. The same request id returns the same outcome when sent again, without running the AI Master again.
- **TLR-03-021-Pending** Requests that need no judgment (pause, resume, standing orders, thread notes, ready, a decision on a prompt) are handled by the engine without the AI Master and work while it is unavailable.
- **TLR-03-022-Pending** When every strong model fails, the turn close falls back to the light models (see 03-005) and retries on a schedule. The client is told when the next retry is, and a turn queued by an outage is resolved as soon as any model answers, not only at its deadline.
- **TLR-03-023-Pending** Every answer carries the time spent in the engine, in the AI Master and in pictures, so clients and the host can see where time goes.

## 04. Characters
- **TLR-04-001** A player can generate a character, choose a pregenerated one, supply their own for validation, or take over an NPC.
- **TLR-04-002** The player chooses a pregenerated character. The server never chooses for them, rejects a character already taken, and lists the ones still available.
- **TLR-04-003** A character's whole state lives in one record: sheet (maximum and current), inventory, relationships, knowledge, plans, standing orders, decisions, events and inbox.
- **TLR-04-004** A player can have several characters, in different games.
- **TLR-04-005-Pending** A character's name is always present in what the client receives, a portrait is captioned with it, and the default standing orders are neutral (not "take no risks"). The player is asked about them when the character is created.

## 05. Content
- **TLR-05-001** Rulesets are markdown files with front matter. Adding one needs no code change. Players can import a ruleset from a document of their own, subject to host approval.
- **TLR-05-002** Adventures are kept in a private repository, so players cannot read their secrets. Adventures can be provided, generated from a seed or document, or generated by the AI Master as the game unfolds.
- **TLR-05-003** The engine supports at least the Fear Itself and Trail of Cthulhu rulesets (GUMSHOE).
- **TLR-05-004** Text written by clients (adventures, rulesets, characters) is treated as data and cannot change the AI Master's protocol.
- **TLR-05-005-Pending** Every NPC, and every player character, has a short description that identifies them without giving their real name or hinting at their identity. It may include appearance, role, manner, and any title or alias by which people commonly know them ("the sheriff", "Doc", "the mayor"). Well-known figures are therefore recognised at first sight through their description. It is part of the adventure or character definition and contains no secrets.
- **TLR-05-006-Pending** The short descriptions of any two NPCs or characters who can be in the same scene must be clearly distinguishable by appearance, role or manner. Two nurses, for example, must differ visibly. This is checked when the adventure or character is validated, and a description that is too similar to another is sent back for correction.
- **TLR-05-007** Repository documents for the AI Master are sectioned by purpose, so each request type can load only its section.

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
- **TLR-06-011-Pending** The state summary the client receives is current after every result, not only at the turn close: current day and Block, Blocks left, location, the journal and notebook entries, the people the character has met, the status of every thread and the spend offers that can be claimed.
- **TLR-06-012-Pending** A result already delivered to the player is never replaced or contradicted by a later one. A turn close may add to what was delivered (rolls, scenes), never change it.
- **TLR-06-013-Pending** Everything the player is told (events, news, calls, decisions credited to the character) is backed by a fact in the game state. The turn close does not invent events the adventure or the AI Master did not record, and the character is never credited with actions they did not take.
- **TLR-06-014-Pending** A change to standing orders or settings is stored, or rejected with the reason. A success message is only given for a change that is stored.
- **TLR-06-015-Pending** An NPC keeps a consistent role, place and relationships. A change of any of them is recorded as an event.

## 07. Client experience
- **TLR-07-001** Creative work (character, game settings, adventure) is done as work packages in the player's own client. The server validates the result and returns the problems to fix.
- **TLR-07-002** After each result the client shows the narration, notebook, status, available illustrations and next possible actions.
- **TLR-07-003** Illustrations are optional per game and consistent in style. Each is visible only to the characters who could see it, delivered as short-lived links.
- **TLR-07-004** The client tells the player when a request was queued, and that the answer arrives at the turn close.
- **TLR-07-005-Pending** Before answering a time-sensitive question locally, the client refreshes its synced data from the engine.
- **TLR-07-006-Pending** Fixed guidance for the client (narration rules, tool help) is sent once per session or when it changes, not with every result.
- **TLR-07-007-Pending** A result carries only the changes since the client's last sync, unless the client asks for a full resync.
- **TLR-07-008-Pending** Results state how long the narration should be, so clients do not produce more text than the game needs.
- **TLR-07-010** The verbosity of the client's narration is a setting of each player in each game (so different players of the same game may use different levels, and the same player may use another level in another game): `medium` by default, `low` or `high`. The player can change it at any time, and the server delivers it with each result so the client narrates to that level.
- **TLR-07-011** Everything about the game world is narrated, not listed: when a player asks about an NPC, a place or an object, the client answers in the voice of the story (from the facts it holds) and does not hand over the data plainly. Everything about the game mechanics (rolls, pools, abilities, rules, time left; a Difficulty is never shown) is stated plainly outside the narration blocks.
- **TLR-07-009** If the AI Master is busy or over its limits, the player is told clearly what was queued and when to expect the answer. Nothing is lost.
- **TLR-07-012-Pending** Large texts (the ruleset, the guides) are served in sections with an index, so every client can read them within its limits.
- **TLR-07-013-Pending** Illustrations are produced without delaying any answer. Actions, standing orders and turn closes do not wait for them, and the client collects them later.
- **TLR-07-014-Pending** An error tells the player what happened to the action (not applied, queued, or applied), whether to retry now or later, and what else they can do. It never points only at the guides.
- **TLR-07-015-Pending** A prompt the engine offers can always be answered. A prompt for something already closed is not offered.
- **TLR-07-016-Pending** The facts of the opening (background, time, place, appearance) are enough for the narration length the player chose, for pregenerated characters too.

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
- **TLR-08-013-Pending** Each level has a latency target set by the host (proposed defaults: level 2 under 1 second in the engine, level 3 median under 30 seconds, level 4 under 90 seconds). Latency is measured per level and request kind and reported with 08-006, and the host status view (08-012) shows when a target is missed.
- **TLR-08-014-Pending** The rate of AI Master answers that were repaired, retried, rejected or queued is recorded per request kind and shown in the host status view.

## 09. Gameplay and pacing
Source: the first full test game, g_d228070f, analysed in `FabulA_testgames/ANALYSIS.md` (2026-11-11).
- **TLR-09-001-Pending** An adventure may declare its finale: the beats that resolve it and, if it has one, its deadline (a time limit or a trigger). The declaration says when the players have won or lost the adventure. It never says when the game stops.
- **TLR-09-002-Pending** A crisis or finale scene is played beat by beat. While a scene is flagged as a crisis, Blocks and the turn clock are suspended, each action gets its own resolution at level 3, and the turn does not close until the crisis is resolved or the player is ready.
- **TLR-09-003-Pending** The engine never ends a game by itself. Winning the adventure, losing it (a missed deadline, a failed finale) or the death of a character changes the story and the players are told the outcome plainly, but they can keep sending actions and turns, and the world goes on with the consequences. A game ends only when every player has quit it (09-010), or when all the remaining players agree to end it. As long as one player wants to continue, the game continues. The engine records whether, when and how the adventure was won or lost.
- **TLR-09-004-Pending** The outcome depends on what the characters did: the items, allies, information and rolls, and whether the key people were reached. Won, lost and partial outcomes are all possible, and a loss is a state of the world the game continues from, not an ending.
- **TLR-09-005-Pending** A deadline is fair. The player is told what it is, and what is still open a turn before the point of no return, and it moves when the player lost actions to engine faults. When it passes, the players are told plainly which objective they lost and what the world is like now, and play continues.
- **TLR-09-006-Pending** Every lead the player is given (a contact, a clue, a thread) has at least one consequence or stays open while the game goes on. When the players end the game, the epilogue closes or explains the leads that are still open.
- **TLR-09-007-Pending** Mechanics matter. Investigative clues and spends are visible and can be claimed, risky actions are rolled and reported, and the pressure on Health and Stability (fear, shocks) that the scenes call for appears, so a character who took risks ends the game changed.
- **TLR-09-008-Pending** An adventure states its expected length in turns and in Blocks per turn, the number of Blocks per turn can be set for the game, and the engine tells the client whether the game is on track.
- **TLR-09-009-Pending** NPCs react to what the character did. Their attitude, knowledge and place are updated after the character's actions and used in later scenes. Events that happen offscreen (a death, a transfer) are tied to earlier actions or marked as scheduled by the adventure.
- **TLR-09-010-Pending** A player can quit a game at any time, not only at the end. Their character then becomes an NPC run by the AI Master, and the other players see it as one; it keeps its state and knowledge, and it can be taken over later like any other NPC (TLR-01-006). Quitting does not end the game for the others.
