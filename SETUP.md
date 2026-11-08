# FabulA: setting up a new Claude client

A short guide for a player who wants to play FabulA from their own Claude. It takes about five minutes.

## What you need

- A Claude account (web, desktop or Android) that can add a custom connector. If your plan or your organization does not offer custom connectors, the connector settings will not show the option to add one.
- The **server address** and the **connector key**. Ask the host of the server for the key: it is a shared password for everyone allowed to play, not your personal key.

The server address is:

```
https://fabula-rpg.vercel.app/mcp
```

The full connector URL adds the connector key at the end:

```
https://fabula-rpg.vercel.app/mcp?key=<CONNECTOR_KEY>
```

Replace `<CONNECTOR_KEY>` with the key the host gave you. Treat the whole URL as a password: do not post it in public places.

## Step 1: add the custom connector

1. Open Claude and go to **Settings**, then **Connectors**.
2. Choose **Add custom connector**.
3. Name: `FabulA`.
4. Remote MCP server URL: paste the full connector URL from above, including `?key=...`.
5. Save (**Add**). If Claude asks for authentication, leave it empty: the key in the URL is the only credential needed.
6. Open a new chat and make sure the **FabulA** connector is switched on for it (the tools or connectors menu in the chat box).

## Step 2 (recommended): make a Project for your game

Playing from a Claude **Project** keeps everything in one place and lets Claude remember your secret player key between chats.

1. Create a new Project called, for example, `FabulA`.
2. In the Project instructions write:

   > This project is for playing FabulA through the FabulA connector. At the start of every chat call `start_here`. Keep my player key (it starts with `pk_`) in these instructions or in memory and use it on every call, but never show it to anyone else. Reply in my language.

## Step 3: the first request

In a new chat inside the Project, send something like this (change the name and language):

> Use the FabulA connector. I'm new here. Explain briefly how the game works, register me as "Alex" (I want to play in English), and then show me the adventures I can play.

What happens:

1. Claude calls `start_here` and explains the game.
2. Claude calls `register_player`. The server returns your **player key** (`pk_...`) **once**. Claude shows it to you: copy it somewhere safe and add it to the Project instructions (ask Claude to do it, or edit them yourself). If you lose it, ask the host to reset it; your characters stay yours.
3. Claude lists the adventures. Pick one.

## Step 4: start a game

Tell Claude, for example:

> Start a solo game of "<adventure title>" in English. Ask me for the settings.

Claude asks for the game settings: lethality (low, moderate or high), how often the world advances (the tick), the hour a tick closes (default 03:00 Spanish time), whether players may fight each other, whether others can join (private or open), and whether the game draws pictures of key scenes. Playing alone is fully supported. You get a **game id**; share it with friends if you want them to join.

Then Claude helps you create or pick a **character**. Read the sheet, say yes to confirm, and you are in the story. From then on just write what your character does: "I search the study", "I follow the man in the grey coat". At the start of every session ask "What happened?" to collect any results that arrived while you were away.

## Joining a friend's game

Register as above, then say: "Join the game `g_xxxxxxxx`" with the game id your friend gave you, and create your character.

## If something goes wrong

- **Claude does not see FabulA tools:** check that the connector is switched on in the chat, and that the URL ends in `/mcp?key=...` with the right key.
- **The connector shows an error or a 403:** the key in the URL is wrong or was changed. Ask the host for the current one.
- **Claude says it needs a player key:** paste your `pk_...` key into the chat, or add it to the Project instructions.
- **The Master (Gemini) is busy:** the server retries on its own; if it still cannot answer, Claude tells you. Nothing is lost: try again in a few minutes.
- Say "Show me the rules" or "What can I do?" at any time.

More about how the game works: [README.md](README.md) and the player guide in [gm/setup_guide.md](gm/setup_guide.md).
