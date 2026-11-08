---
id: guide_create_character
title: Create a character
---
# Create a character

A character is needed to play. Each player has one character per game. Use this guide after the game exists (`create_game`) or after the player joined one (`join_game`).

## Routes

| Route | What it is | Result |
|---|---|---|
| `generate` | Build a new character with the player | Work package |
| `provided` | The player pastes their own sheet, you convert it to this ruleset and the server checks it | Work package |
| `pregen` | Pick a pregenerated character. Show the player the adventure's pregenerated characters (`pregenerated` in `list_adventures`), let them choose, and give `pregen_id`. The server refuses one that another player holds and lists the ones still available; offer those and call again. Never choose for the player | Acts at once |
| `from_npc` | Take over an NPC the party has met or an unclaimed pregenerated character who is in the story as an NPC (give `npc_id`; call `list_takeovers` first). For a late joiner or a replacement. Main characters of the adventure are never available | Acts at once |

To continue in the same game after a death, pass `replaces_character_id`.

## The call

`generate_character(player_key, game_id, route, concept, pregen_id, sheet_text, sheet_json, npc_id, replaces_character_id, changes)`. Use the fields that fit the route. A work package arrives for `generate` and `provided`: follow its steps. In short:

1. Ask the player, in one batch: the concept or occupation, their character's drive and personal goal, their character's fears if they want to name any, and, for a replacement, whether they want a link to the story.
2. Build the sheet from the ruleset text in the package, within its budgets. Never raise a rating to be generous and never invent rules.
3. Fill the whole record, including a `portrait` (`appearance` and `signature_action`, in English) when the game has illustrations. Use only what the player gave; if they gave nothing, propose a look that fits the concept and era and let them adjust it.
4. Self-check against the ruleset's checklist, show the player a short summary and make the changes they ask for.
5. `submit_package`. If rejected, fix the listed problems and submit again.

## Confirm

When the server accepts the sheet, show the validation summary and ask the player to confirm the character: `submit_action(player_key, game_id, kind="character_confirm", payload={"approved": true})`. Only then is the character in play. The server's reply says what happens next (other players, the start of the first tick, or an immediate scene if playing alone).
