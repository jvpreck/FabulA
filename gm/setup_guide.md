# FabulA: Player Setup Guide
## For a new player, and for the player's Claude who explains it

> **CLIENT-FACING FILE.** The `get_setup_guide` tool returns it to a player who is new. It contains no secrets and is independent of any ruleset or adventure. When you (Claude) relay it, translate it into the player's language, keep it friendly and short, and show the section the player asked for rather than the whole file. A section is selected by its key in brackets.

---

## [start] How to start playing

This is a play-by-message role-playing game. A hidden AI Game Master (the "Master") runs the world on a server. You play one character, and your Claude tells the story of what your character sees and does. You do not need to be online at the same time as other players.

**Before you start: connect Claude to the server (once per Claude account).** Ask the host of the server for the **connector key** (a shared password for everyone allowed to play; it is not your personal player key). The connector address is `https://fabula-rpg.vercel.app/mcp?key=<CONNECTOR_KEY>`, with the key in place of `<CONNECTOR_KEY>`. Treat the whole address as a password.

1. In Claude open **Settings**, then **Connectors**, and choose **Add custom connector**.
2. Name it `FabulA`, paste the address as the remote MCP server URL, and save. If Claude asks for authentication, leave it empty: the key in the address is the only credential needed.
3. Open a new chat and make sure the FabulA connector is switched on for it. A Claude **Project** is recommended: put in its instructions "This project is for playing FabulA through the FabulA connector. At the start of every chat call `start_here`. Keep my player key (it starts with `pk_`) here or in memory and use it on every call, but never show it to anyone else. Reply in my language." That is how Claude remembers your key between chats.
4. Send a first message such as: "Use the FabulA connector. I'm new here. Explain briefly how the game works, register me as 'Alex' (I want to play in English), and show me the adventures I can play." Then follow the steps below.

If Claude does not see the tools, check that the connector is on in the chat and that the address ends in `/mcp?key=...` with the right key. A 403 error means the key is wrong or was changed: ask the host for the current one.

1. **Register once.** Ask Claude to register you. The server gives you a **player key** (it starts with `pk_`). It is your secret identity on the server. See "Your player key" below.
2. **Pick a game.** Either create a new one from an adventure, or join one that already exists (see "How to choose a game").
3. **Make a character.** You cannot play without one (see "Your character").
4. **Confirm the character.** Claude shows you the finished sheet. When you approve it, you are in the story.
5. **Play.** Tell Claude what your character does. Small things happen at once. Bigger things wait for the next turn, when the Master resolves everyone's actions together.

At any time you can say "what can I do?" and Claude will remind you of your options.

**Your player key.** It works like a password. Keep it private: do not paste it in public places or share it with other players. Anyone who has it can act as you. Claude must keep it for you in this chat or project (for example in the project instructions or its memory) and send it with every request, but never show it to anyone else. If you lose it, or think someone else has it, ask the host of the server to reset it. A reset gives you a new key and your characters stay yours.

## [choose] How to choose a game

- **See what can be played.** Ask for the adventure list. Each adventure has a title, era, ruleset, how many players it supports and a short premise. Secrets are never listed.
- **Start your own game.** Pick an adventure (or ask Claude to write a new one from your idea), then Claude asks you for the settings: language, how deadly it is (lethality), how often the world advances (the turn), the stance on players fighting each other (PvP), and who can join (**private**: only people who get the game id, or **open**: it is listed for other registered players while it has free seats), and whether the game draws **pictures** of key scenes (see "Other things worth knowing"). You get a **game id**. Share it with friends so they can join. Playing alone is fully supported.
- **Join a game.** Ask for the list of games. It shows your games and the open ones that have free seats. You can also join any game if someone gives you its game id.
- **Several games.** You can be in more than one game, with one character in each. Tell Claude which one you mean if it is not obvious.

## [character] Your character

Every player needs a character in each game. There are four ways to get one:

1. **Generate** one with Claude. Claude builds it with you, step by step, following the game's rules, and then sends it to the server.
2. **Pick a pregenerated** character if the adventure offers some. It is ready at once.
3. **Provide your own sheet.** Paste a character you already have. Claude converts it and the Master checks that it follows the rules. If something does not fit, you are told exactly what to change.
4. **Take over an NPC** (only as a replacement after your character dies, and only if the Master has marked one as available).

After the server accepts the character, Claude shows it. Say yes to confirm it. If you want changes, say so before you confirm. The server stores the sheet, your current stats, your inventory, your relationships and what your character knows. It is the truth if your chat is ever lost.

## [commands] What you can ask for

You write in plain language. Claude turns it into the right request. Useful things to say:

| You want to | Say something like |
|---|---|
| Do something | "I search the study." "I follow the man in the grey coat." |
| Talk to a character in the same place | "I say to Sam: ..." (add "whisper" for a private word) |
| Contact someone far away | "I phone / write to ..." (this is a message, not speech) |
| Ask the Master a question | "What do I know about ...?" (a free query) |
| Answer a choice the story puts to you | "I choose the second door." |
| Leave instructions for when you are away | "While I am away: stay safe, never go to the cellar." (standing orders) |
| Pause | "Pause." The fiction stops at once for you. "Resume" when you are back. |
| Catch up | "What happened?" (collects results you have not received yet) |
| Check your character | "Show my character." "What do I know?" "What are my plans?" |
| Read the rules | "Show me the rules." |
| Keep a record | Claude keeps three summaries (character, knowledge and plans, story so far) and stores the story on the server. |
| Replace a dead character | "I want a new character." |

Claude can answer some things without asking the server: your stats, inventory and what you know, a reminder of the story, a rules question, and more detail about a scene already told. It asks the server for anything new.

## [turns] Time, turns and playing together

- The game runs in **turns**. A turn is a period of real time, by default **24 hours** (the host or the adventure may choose another). Each turn covers a slice of game time, usually a day, split into Blocks (Morning, Afternoon, Evening, Night).
- During a turn, everyone sends actions whenever they like. When the turn closes, the Master resolves **all** the players' actions together, settles any conflicts between them, and sends each player their own results. Then the next turn opens.
- **You never have to wait idly.** Many things resolve at once (see the next section). Only what truly involves other people, or something big, waits for the turn.
- **Playing together.** Players are separate people at separate times. Your character knows only what they have seen or been told in the story. Other players' characters can be in the same place: you will see what they do in front of you, you can talk to them directly, and what you do may be seen by them. Secrets between characters stay secret unless the story shares them.
- **Playing alone.** When you are the only player, the turn closes as soon as you have used the time you intend to use, so the game moves at your own pace.
- **If you are away.** If you do not send anything in a turn, your character follows your standing orders, or holds back and stays safe. After a few missed turns you are marked away and the character keeps following your standing orders. You can come back at any time and carry on.
- **Late joiners.** A new player can join a running game. They can create a character, pick a pregenerated one that is still free, or **take over an NPC** the party has met (never a main character of the adventure). Pregenerated characters nobody chose stay in the story as NPC companions and can be claimed later this way. The Master finds a natural way to bring them into the story.

## [autonomous] What you can do without waiting

The Master resolves a minor action **at once** when it affects only your character, nobody else in the same place is involved, it does not change what another character is waiting on, it triggers nothing irreversible, and your character still has time (a Block) left in this turn. Typical examples: searching a room, studying a document, walking inside the same place, talking to an NPC, resting, preparing, crafting.

- Each such action uses up part of your character's time in the turn. You can do several, one after another, until the Blocks of the turn are used. After that, further actions wait for the next turn.
- If an action grows into something that touches others (it makes noise, wakes someone, draws the enemy), the Master stops it there, tells you, and the rest waits for the turn.
- An immediate result is final. It cannot be reopened at the turn.
- **Speech between characters in the same place is instant** and costs no time. A conversation is possible one line at a time if the other player is online.
- Claude can also answer things locally (your stats, inventory, plans, a reminder of the story, a rules question) with no waiting at all.

## [death] If your character dies

How deadly the game is is chosen when it is created, and you can always see it:

| Lethality | What it means |
|---|---|
| **Low** | Your character cannot die unless **you** choose it at a decision point. Lethal outcomes become severe losses instead (injury, capture, ruin, a scar). |
| **Moderate** | Your character can die only after a clear warning was given and you had a chance to withdraw or you walked past a decision point on purpose. Players who are away are never exposed to lethal risk. |
| **High** | Your character can die after a clear warning, with the dice and the story deciding. Players who are away still hold in safety. |

In every level the danger is shown to you in the story before it can kill, and a death is never silently reversed.

When a character dies you stay **in the same game**. The server offers a replacement: a newly generated character, a pregenerated one that is still free, an NPC the Master has marked as available, or leaving the game. A new character is a new person: it does not inherit the dead character's knowledge, items or relationships. (A character taken from an NPC starts with what the NPC knew and had.) The new character arrives in the story within a turn or two. The dead character's belongings stay in the world.

## [mechanics] Other things worth knowing

- **The server is the truth.** If the chat is compacted or you switch device, Claude rebuilds everything from the server. Keep your player key.
- **Secrets.** The Master keeps the adventure's secrets. Claude only turns the Master's facts into narration and never invents events. If a rule or a secret is unknown, you are told "nothing you have seen tells you that yet".
- **Safety.** There are no lines or veils: all content is possible, because every player is an adult. You can name your character's **fears**. You can say **pause** at any moment. After intense scenes the game checks in out of character.
- **PvP.** The game's stance is `none`, `soft` (default: characters may oppose each other, but nothing lethal or permanent happens between players) or `full`. Each player can also opt out in their safety settings.
- **Standing orders.** Short rules for what your character does when you are away (how much risk to take, what never to do, how to reply to messages). They are always obeyed in your absence.
- **Messages.** Letters, calls and other messages between characters are delivered by the story: they can take time and can be intercepted.
- **Dice.** The server provides the dice, not Claude and not you. Rolls are shown as one plain line, and difficulties are never shown.
- **Language.** You play in your language. A game has a language and each player's results follow their own.
- **Setting up a game.** A new game has a setup period (3 days by default) in which players join and make characters. The story starts when the characters are confirmed.
- **Pictures.** A game has illustrations on by default (the host of the game can turn them off, and they exist only if the server has them set up). When it is on, the Master occasionally asks for a picture of an important scene. Only the characters who were there, and their players, can see it. Claude tells you when one is ready and gives you a link that opens in your browser. The link stops working after a few minutes, but you can ask for any past picture again at any time and get a new link. Each game has one fixed art style chosen when it is created, and every character and important NPC gets a portrait with their name, drawn once and used as a reference so they look the same in the scene pictures. Pictures can still be imperfect in fine details.
- **Hosts and administrators.** Only the host of the server can delete games, adventures or players, or reset a key. Ask the host if you need one.
- **Fairness between you and the story.** Claude and the Master never decide for your character. You choose what your character does.
