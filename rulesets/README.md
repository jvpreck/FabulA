# rulesets/

The game systems the engine can run. Each ruleset is **one markdown file** with YAML front matter. It is the single source of truth for the
**mechanics**, the **character creation and validation rules**, the **numbers and tables** and the **sheet layout** of one system. It
knows nothing about any adventure. An adventure names a ruleset by its `id`, and the server sends that ruleset to the AI Master with every
request, after the engine's protocol, oracles and state contract.

This folder is in the public engine repository. Rules are not secret (adventures are: they live in the private `rpg_adventures` repository).

## Contents

| File | Ruleset | Dice | Players |
|---|---|---|---|
| `fear_itself.md` | *Fear Itself* (GUMSHOE) horror: grounded by default, with an optional supernatural module (psychic powers, creatures), and house modules for perception drift, the antagonist ladder, belief states and time blocks | d6 | 1 to 5 |
| `trail_of_cthulhu.md` | *Trail of Cthulhu* (GUMSHOE) Lovecraftian investigative horror in the 1930s, Purist or Pulp: Stability and Sanity, Drives, Pillars of Sanity, Mythos magic rules (the adventure supplies creatures, tomes and spells) | d6 | 1 to 5 |

## File format

```yaml
---
id: my_system                      # unique, lowercase letters, digits, underscores (3 to 40). Same as the file name. Never change it once games use it
title: "Display title"
system: "Name of the game system"
version: 1
players: { min: 1, max: 5 }
dice: d6
language: en
summary: "One or two sentences shown to players. No spoilers."
modules: [hazard_stages]           # optional switchable rules defined in the body
tone_presets: [slow_dread]         # optional tones the adventure can pick
---
```

The body must cover, with `##` headings that contain these words: **core concept**, **characters** (with the validation checklist as a
numbered table and the outcomes `pass`, `pass_with_adjustments`, `fail`), **abilities**, **core mechanics** (tests, damage, the dead
condition, lethality), **solo and party play** (including conflicting actions), **NPC statistics** and **sheet layout**
(`sheet.groups`, `sheet.derived`, `sheet.unrated`, `ruleset_state`). The full contract, with the rules for the text, is
[`gm/ruleset_contract.md`](../gm/ruleset_contract.md). Use `fear_itself.md` as the model.

## How the engine uses it

- The server lists the `*.md` files in this folder. A file is a ruleset only if its front matter has an `id`. `README.md` is ignored.
- Imported rulesets that the host has approved (see below) are listed next to the files. An id is unique across both.
- Players see `title`, `summary` and the text through `list_adventures` and `get_rules`.
- Adventures name their ruleset in their front matter (`ruleset: my_system`). Games keep pointing at it by `id`.

## Adding a ruleset

**From a file (the host).** Write the file following the contract, check that the front matter parses, commit it to `main` here, and
Vercel redeploys. Check it with the same checks the server uses on imports:
`python -c "from server import tasks, files; m,b = files.split_front_matter(open('rulesets/my_system.md').read()); print(tasks.ruleset_checks(m, b))"`.
No problems should be listed.

**From a document (any player).** The player gives their Claude the rules and the `import_ruleset` tool. Claude follows a work package
(`gm/client_tasks.md`, task `import_ruleset`), converts the document into this format in its own words, and sends it back with
`submit_package`. The server validates the structure and stores it as **pending** in the `gm_rulesets` table. Nothing can use it until
the host approves it:

1. `review_ruleset` (admin command, run with curl): shows the fields, headings, checklist rows and any suspicious wording. Read the full text
   in the Supabase table `gm_rulesets` (a ruleset goes into the AI Master's prompt, so read it before approving).
2. `approve_ruleset`, `reject_ruleset` or `delete_ruleset` (the three are also in the `admin` GitHub workflow). `list_rulesets` lists
   them all.

The host can also turn an approved imported ruleset into a file: copy `meta` and `body` from the table into a new file here, then delete
the database copy.

## Changing or retiring one

- Do not change an `id`. Think before changing the rules of a ruleset that games are playing: sheets already built stay as they are.
- Retire a file by deleting it once no adventure or game uses it. Retire an imported one with `delete_ruleset`.

## Copyright

Write rulesets of published games in your own words. Do not copy passages, tables or art. Leave out setting lore, licensed creature stat
blocks and example adventures. The player who imports a system must confirm they may use the source document.
