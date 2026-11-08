# gm/ : the AI Master's files

These files are adventure- and ruleset-independent. The server builds the AI Master's system prompt from them plus one ruleset and one adventure.

| File | For | Purpose |
|---|---|---|
| `protocol.md` | AI Master | How to behave: secrecy, voice, lifecycle, interaction classes (client, query, say, autonomous, queued, message), turn resolution, arbitration, lethality and replacement, persistence, adventure generation |
| `oracles.md` | AI Master | Random tables and generators |
| `state_and_messages.md` | AI Master and server | The Supabase data model, the envelope, the JSON response |
| `player_client_brief.md` | Player's Claude | How to narrate, the three artifacts, which tools to call |
| `setup_guide.md` | CLIENT-FACING. The guide for a new player (how to start, choose a game, make a character, the commands, turns and collaboration, autonomous actions, death, other mechanics). Returned by `get_setup_guide`. |
| `mcp_instructions.md` | Player's Claude | The short text the server sends when a client connects (MCP `instructions`): call `start_here` first |
| `start_here.md` | Player's Claude | Returned by `start_here`: orientation, the table of what to call for what, the always-apply rules |
| `guide_player_client.md`, `guide_create_character.md`, `guide_create_game.md`, `guide_generate_adventure.md` | Player's Claude | Returned by `get_guide` (`player-client-guide`, `create-character`, `create-game`, `generate-adventure`). `setup_guide.md` is `players-guide`, `player_client_brief.md` is `narrator` and `mcp_instructions.md` is `mcp-guide` |
| `ruleset_contract.md` | Player's Claude and server | The ruleset file contract: front matter, required sections, rules for the text. The server validates imported rulesets against it |
| `guide_import_ruleset.md` | Player's Claude | Returned by `get_guide` (`import-ruleset`) |
| `client_tasks.md` | Player's Claude | Step-by-step work packages: generate a character, generate an adventure, create a game. The server serves them to the client, which does the work locally and sends the result back with `submit_package` |

Prompt assembly order: protocol, oracles, state contract, the ruleset (`../rulesets/`), then the adventure (read from the private repository `jvpreck/rpg_adventures`, never from this one). The client brief and the client tasks are not sent to Gemini. The server sends `mcp_instructions.md` as MCP `instructions` when a client connects, the other client files through `start_here` and `get_guide`, and the tasks as work packages.

Rulesets and adventures have YAML front matter (`id`, `title`, and so on) so the server can list them. See `../README.md`.

## Sections: what each request is told

The documents the AI Master reads (`protocol.md`, `oracles.md`, `state_and_messages.md`, and the rulesets) are sent in sections chosen by the kind of request, so a request does not carry instructions it cannot use (TLR-03-010, TLR-05-007). A heading may be followed on the next line by a tag comment:

```
## 5.2 `resolve_turn` mode (the turn closes)
<!-- for: turn -->
```

- `for: turn, play, setup` keeps the section only for those request profiles. `turn` is the turn close. `setup` is creating a game, joining, setup answers and the character routes (`game_created`, `join`, `setup_answers`, `character_submission`, `character_confirm`). `play` is every other request.
- `needs: illustrations, generated` keeps it only when pictures are on and the server can draw them (`illustrations`), or when the adventure is not a supplied one (`generated`).
- The tag applies to the heading and everything under it, sub-sections included, up to the next heading of the same or a higher level. A section with no tag is always sent. The tag line itself is never sent.
- When you add or move a tag, run the live scenarios (`FABULA_LIVE_SCENARIOS=1`, see `../README.md`): an instruction left out by mistake shows up as a worse answer, not as an error. `PROMPT_SLIM=off` sends everything again at once.
