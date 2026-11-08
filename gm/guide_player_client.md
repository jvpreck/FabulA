---
id: guide_player_client
title: Player client guide, how to use FabulA
---
# How to use FabulA (for you, the player's Claude or other assistant)

## The model of the engine

- **The server** stores everything and decides everything. **The AI Master** (a separate model on the server) resolves the game. **You** talk to the player and call the tools.
- You never run the game yourself, and you never keep the truth: the server does. Your chat is a window onto it.
- Everything is identified by ids returned by the tools: `adventure_id`, `game_id`, `character_id`, `task_id`, `image_id`. Copy them exactly.

## Tools, in the order a player normally meets them

| Step | Tool | Notes |
|---|---|---|
| 0 | `start_here`, `get_guide` | No key needed |
| 1 | `register_player` | Once per human. Returns `player_key` only once |
| 2 | `list_adventures`, `list_games` | See what can be played and which games are open |
| 3 | `create_game` or `join_game` | `create_game` returns a work package |
| 4 | `generate_character` | Routes: `generate`, `provided` (the player's own sheet) return a work package; `pregen` and `from_npc` act at once |
| 5 | `submit_package` | Sends back the finished package |
| 6 | `submit_action` with `kind: "character_confirm"` | The player approves their character |
| 7 | `get_results`, `submit_action` | The play loop |
| any | `get_character`, `save_story_summary`, `list_images`, `get_image`, `get_rules` | Support |

## The work-package loop

1. A tool such as `create_game`, `generate_character` or `generate_adventure` returns `{package: {task_id, instructions, context, submission: {schema}}}`.
2. Read `package.instructions` and follow every step in order, in the chat, with the player. Ask questions in one batch and offer defaults.
3. Build the answer in exactly the shape of `package.submission.schema`.
4. Call `submit_package(player_key, task_id, package=<your answer>)`.
5. If the reply has `accepted: false`, fix exactly the listed `problems` and submit again with the same `task_id` (five attempts, then the task expires). If `accepted: true`, continue with what the reply says.

## The play loop

1. Start every session with `get_results` (all games, or one `game_id`). Narrate what is new.
2. Ask the player what the character does. Send it with `submit_action` (`kind: "action"`, free text). Small things that only involve the character resolve at once and come back in the reply. Bigger things wait for the turn, and the results arrive with a later `get_results`.
   Give every new `submit_action` its own `request_id` (any fresh unique string, up to 64 characters). If a call times out or fails and you did not see the answer, send it again with the **same** `request_id`: the server runs it once and returns the first answer. Never reuse a `request_id` for a different request.
3. Speech to another character in the same place: `kind: "say"`. Messages to other players: `kind: "message"`. Standing orders for when the player is away: `kind: "standing_orders"`.
4. Keep the three artifacts described in the `narrator` guide up to date.

## Common mistakes

- Calling a tool that needs `player_key` without one. Ask the player, or register them if new. Never invent a key.
- Registering a second time because the key was lost from the chat. Ask the player for the key. Only the host can reset one.
- Making up facts, rolls, clues or outcomes. Narrate only what the server returns.
- Showing GM-only text from a package to the player.
- Submitting a package with extra fields, or a different shape from `submission.schema`. Extra fields are dropped.
- Skipping `character_confirm`. A character cannot play until the player confirms it.
- Forgetting that time runs in turns: not every action gets an answer at once.

## Languages

Talk to the player in their language. Package fields that say "in English" (picture descriptions, image style, portrait descriptions) must be in English whatever the player's language.
