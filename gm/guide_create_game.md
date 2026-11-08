---
id: guide_create_game
title: Create a game
---
# Create a game

Use this when the player wants to start a new game from an adventure. A game is one run of an adventure with its own clock, world and characters.

## Before you call

1. Have the player's `player_key` (register them first if they are new).
2. Have an `adventure_id`: from `list_adventures`, or one the player just generated.

## The call

`create_game(player_key, adventure_id, title, language, display_name, ...)`. Optional arguments prefill defaults. It returns a **work package** that collects the settings with the player. Follow its steps. In short, you will settle with the player:

- **Lethality:** low, moderate or high (the default is high; the package explains what each means).
- **Turn:** how often the world advances (default 24 hours) and its span (a day of four Blocks, or one Block).
- **PvP:** none, soft or full.
- **Visibility:** `private` (only people who get the game id) or `open` (listed for other registered players while there are free seats).
- **Language** and the player's display name.
- **Illustrations** (only offered when the server has them): `on` (the default) or `off`. When `on`, you also write the game's **image style**: one English paragraph (40 to 700 characters) fixing the look of every picture in the game: medium and technique, era and year, place, ambience, light, palette. Build it from the adventure's player-safe part. **It can never be changed afterwards**, so show it to the player and let them adjust it before you submit. Never name real artists, brands or known characters, and ask for no readable text.

## After

`submit_package` with the answers. When accepted you get a `game_id`. Tell the player, and share the id if they want friends to join. The next step is the character: `get_guide("create-character")`. Playing alone is fully supported.
