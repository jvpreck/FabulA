---
id: trail_of_cthulhu
title: Trail of Cthulhu (GUMSHOE) cosmic horror, Purist or Pulp
system: GUMSHOE
version: 1
players: { min: 1, max: 5 }
dice: d6
modules: [purist, pulp, sources_of_stability, mythos_magic, big_reveal]
tone_presets: [purist_cosmic, pulp_action, noir_investigation]
language: en
summary: Lovecraftian investigative horror in the 1930s. Investigative abilities always find clues; general abilities are rolled with a d6. Two mental scores, Stability (short term) and Sanity (long term), measure how close the Investigators are to breaking and to seeing the truth.
---

# Trail of Cthulhu (GUMSHOE) Rules Reference for AI-Run Cosmic Horror
## Lovecraftian investigation in the 1930s, Purist or Pulp, solo or party

> A paraphrased rules reference for a GM (human or AI) running **investigative cosmic horror**. It is the single source of truth for this ruleset's rule numbers, mechanics, tables and sheet layout. Behavior is governed by the protocol; random tables by the oracles; the world, cast, secrets and any pregenerated characters by the adventure; data shapes by the state contract. This ruleset is selected by id (`trail_of_cthulhu`) and works with any adventure that names it.
>
> **Precedence:** facts about the world and its secrets come from the adventure. How to behave and what to show comes from the protocol. Rule numbers and house rules come from this file. The shape of JSON data comes from the state contract. If two sources seem to disagree, follow that order and never mention the conflict to the players.
>
> **What this file leaves out on purpose.** Setting history, the catalogue of gods and monsters with their statistics, the list of grimoires, equipment price lists, sample campaigns and example adventures of the published book are not included. An adventure supplies the creatures, books and spells it needs, with their numbers, using the rules of §5 and §7. Rules marked **[House]** adapt the game to AI-run, asynchronous and small-group play and override the published rules where they differ. If you own the published book, you may use its tables for anything this file does not give.
>
> **Two idioms, one rule set.** Rules tagged **[Purist]** suit bleak, philosophical, cosmic horror in which learning the truth dooms the seeker. Rules tagged **[Pulp]** suit desperate physical struggle in which Investigators survive more often. Untagged rules apply to both. The adventure picks the idiom in its header (`mode: purist` or `mode: pulp`, default Purist) and may borrow single rules from the other.
>
> **Asynchronous play.** Players act at different times and the AI Master resolves their actions, some at once and the rest together at each turn. The [House] rules in §2, §4.2, §4.9, §5.8, §6 and §7 adapt the live-table rules to that.

---

## 1. Core concept

- *Trail of Cthulhu* is a GUMSHOE game of Lovecraftian investigation. The characters (**Investigators**) look into a mystery with a horrifying truth behind it. The tension is not whether they find the clue but what it means and what they will do about it.
- **Investigative abilities** find clues and are **never rolled**. **General abilities** get things done and are rolled with a **d6**; they can fail. Gathering clues is automatic so that one bad roll never stalls the story; confrontations are where the dice matter.
- Each scene holds information. Every scene points to another one. The solution usually leads to a confrontation with something monstrous, and often to a price.
- **Two mental scores.** **Stability** is short-term resistance to shock and falls quickly during an adventure. **Sanity** is the long-term ability to keep believing the comforting lies of the human world; it erodes slowly and in the Purist idiom never returns.
- **Truth rule.** The Mythos is real in this game. What the adventure says is true is true. The AI Master never invents Mythos facts that contradict it, and never lets a rational explanation erase a real horror once the adventure has established it.
- **Principles the AI Master never breaks.** (1) An essential clue is never lost to a die roll or to a missing ability. (2) Difficulties are chosen before the roll and the dice are never fudged. (3) Warnings precede lethal danger.
- **Tone presets [House]** (the adventure picks one; default Purist cosmic):
  - **Purist cosmic:** dread of what the universe is. Slow reveals, few fights, firearms discouraged, Sanity loss is permanent.
  - **Pulp action:** dread of what hunts you. Fights are common and winnable, heroic gestures are rewarded, Sanity may return after victories.
  - **Noir investigation:** dread of people and corruption with the Mythos behind it. Informants, bribes, bad weather, local power.
- **Formats [House]:** one-shot (one story), miniseries (a fixed arc over several stories) or campaign (§9).

---

## 2. Characters

- **Characters:** 1 (solo) to 5. Each player controls one Investigator. GM-run allies never roll or decide for a player character.

### 2.1 Building an Investigator
<!-- for: setup, check -->

1. **Occupation** (§2.2). The Investigator may still work it, or have left it to hunt the Mythos full time (poorer and more isolated). In a one-shot the job usually is not quit yet.
2. **Drive** (§2.3). Exactly one.
3. **Build points** (§2.1a): Investigative and General.
4. **Pillars of Sanity** and, if the module is on, **Sources of Stability** (§2.5).
5. **Contacts** (§2.6), name, background, equipment and means in the style of the era.

### 2.1a Build points
<!-- for: setup, check -->

| Characters at the start | Investigative points each |
|---|---|
| 1 (solo) [House] | 26 |
| 2 | 24 |
| 3 | 18 |
| 4 or 5 | 16 |

- The party size is the number of characters when the game starts and stays fixed, even if players join or leave later.
- **General abilities: 65 build points** [Purist and Pulp]. A **doomed specialists** variant (adventure's choice): 60 General points and Investigative points 16 (2 characters), 12 (3) or 10 (4 or 5); solo characters keep 26. A **pulpier** variant: 75 General points and the standard Investigative points.
- **Free ratings:** Sanity 4, Stability 1, Health 1, and Credit Rating at the lower edge of the Occupation's band. A character may trade free Credit Rating points one for one into Investigative build points for a down-and-out concept.
- **Cost.** One rating point costs one build point. An **Occupational** ability (marked with an asterisk) costs half: two rating points per build point, so assign an even number of points (a leftover half point is lost). Fleeing, Credit Rating, Cthulhu Mythos, Health, Sanity and Stability can never be Occupational (except Credit Rating for Dilettantes).
- **Fleeing discount.** Fleeing points above twice the final Athletics rating cost half (with Athletics 0, all Fleeing). Decide Athletics first. Example: Athletics 2 and Fleeing 8 cost 4 build points for the first 4 Fleeing points and 2 for the next 4. The AI Master may refuse the discount to a character who is plainly a fighter.
- **Credit Rating** costs 1 per point up to the top of the Occupation's band and 2 per point above it (Dilettantes have no top). The adventure may cap it at the top of the band.
- **Cthulhu Mythos** cannot be bought at creation (it is never Occupational) unless the adventure says the characters already know something.
- **Balance rule.** The second-highest General ability (not counting Fleeing, and counting Occupational General abilities only at their purchased value) must be at least half the highest.
- **Caps.** [Purist] Health and Stability at most 12; Sanity at most 10, and never above 10 minus Cthulhu Mythos. [Pulp] 12 is still recommended for tension.
- **Saving points.** Unspent build points may be kept for later in a campaign. In a one-shot they are lost.
- **Trading points [optional].** At creation one Investigative build point may be traded for 3 General build points, at most 3 Investigative for 9 General. State it in the validation block; the checklist totals are then counted after the swap.
- **Quick pick [House].** For Investigative abilities buy many low ratings (even 1 is real expertise; rarely above 3 or 4) and cover what the story is likely to need. For General abilities concentrate: Health and Stability 8 to 12, plus the ability that defines the concept.
- **Building a party.** Cover as many abilities as possible and give each Investigator a role in which to shine. Allow at most one combat expert and one occult or Mythos expert, each weakened somehow (a retiree, a washout, an untrustworthy mentor) [House].

### 2.2 Occupations
<!-- for: setup, check -->

Each Occupation lists its Occupational abilities (half price), a Credit Rating band and a special benefit. The adventure may ban Occupations or allow only some. Only **Military** is closed to women even in a realistic game; sexism of the era may appear as color and may make a character underestimated, never as a ban.

| Occupation | Occupational abilities | Credit Rating | Special benefit |
|---|---|---|---|
| **Alienist** | Biology, Languages (German, Latin), Library Use, Medicine, Pharmacy, Psychoanalysis, Assess Honesty, two other Interpersonal | 3 to 4 | Medicine or an Interpersonal ability opens mental records and sanitarium wards; with Medicine 2+ (licensed) also medical records and hospital wards. Psychological Triage at Difficulty 3; steadying an erratic character costs 1 Psychoanalysis point instead of 2; may buy Hypnosis. Assess Honesty works as forensic psychology (profile a perpetrator from a scene). |
| **Antiquarian** | Architecture, Art History, Bargain, History, Languages, Law, Library Use, one more Investigative ability | 2 to 5 | Once per adventure the character may have a relevant item "back at the shop" (a book, a dagger, a mask), recalled with a matching ability. The AI Master may refuse anything that would be abusive. |
| **Archaeologist** | Archaeology, Athletics, Evidence Collection, First Aid, History, Languages, Library Use, Riding, two other Investigative | 4 to 5 | Archaeology or an Interpersonal ability opens museum storage; with Archaeology 2+ and Credit Rating 3+, university closed stacks. |
| **Artist** | Architecture, Art, Art History, Craft, Disguise, Flattery, Photography, Assess Honesty, two more Academic or Interpersonal | 1 to 4 | Meaningful downtime refreshes 1 pool point in an ability tied to the art, up to 4 times per story. |
| **Author** | Art, History, Languages, Library Use, Oral History, Assess Honesty, three others | 1 to 3 | Downtime reading refreshes 1 Academic pool point, up to 4 times per story. |
| **Clergy** | History, Languages (Latin, Greek, Aramaic or Hebrew), Library Use, Psychoanalysis, Assess Honesty, Reassurance, Theology, one other Interpersonal | 2 to 5 | Church records open to Theology or Reassurance. Once per story, talking with a co-religionist refreshes any Interpersonal pool. Triage at Difficulty 3. Psychoanalysis is not Occupational. |
| **Criminal** | Bargain, Intimidation, Locksmith, Scuffling, Sense Trouble, Shadowing, Stealth, Streetwise, one other Interpersonal or Technical | 0 to 4 | With pools in Conceal, Filch or Shadowing the player may spend points after rolling, 2 points per +1, only when undistracted and unobserved and never in a contest. |
| **Dilettante** | Credit Rating, Flattery, Riding, any five abilities | 3 and up | The Credit Rating pool calls on personal connections in any field. |
| **Doctor** | Accounting, Biology, First Aid, Forensics, Languages (Latin), Medicine, Pharmacy, Assess Honesty, Reassurance | 4 to 6 | Medical records and hospital wards open. First Aid heals 3 Health per point (2 on self); stabilizing costs 1 point instead of 2. |
| **Hobo** | Athletics, Bargain, Filch, Outdoorsman, Sense Trouble, Stealth, Streetwise | 0 (no points allowed) | Reads hobo signs and a strange town; Streetwise reaches hobo contacts. |
| **Journalist** | Cop Talk, Disguise, Evidence Collection, Languages, Oral History, Photography, Assess Honesty, Reassurance, Shadowing, one other Interpersonal | 2 to 4 | Reassurance opens newspaper morgues; fellow journalists share off-the-record rumors. |
| **Military** | Athletics, Firearms, Intimidation, Outdoorsman, Scuffling, Weapons; plus a branch package (Army: Conceal, Driving, Stealth; Corpsman: First Aid, Medicine, Reassurance; Engineers: Driving, Explosives, Mechanical Repair; Navy: Astronomy, Mechanical Repair, Piloting; Officer: Bureaucracy, Riding or Piloting, Reassurance) | 2 to 5 officers, 2 to 4 enlisted | 2 Reassurance points steady a panicking character while the user's own Stability is above 0. Any Interpersonal ability opens one's own nation's military facilities. A combat veteran's combat Difficulties and opponents' Hit Thresholds do not rise by 1 from Hurt or shaken until Stability or Health is below -5, but Stability is capped at 10. |
| **Nurse** | Biology, First Aid, Medicine, Pharmacy, Assess Honesty, Reassurance | 2 to 4 | Same medical access and First Aid bonuses as a Doctor. |
| **Parapsychologist** | Anthropology, Electrical Repair, Library Use, Mechanical Repair, Occult, Photography, Assess Honesty, Sense Trouble | 2 to 3 | May buy Hypnosis. |
| **Pilot** | Astronomy, Driving, Electrical Repair, Mechanical Repair, Piloting, Sense Trouble | 2 to 3 | Owns or regularly uses an airplane, as the Credit Rating allows. |
| **Police Detective** | Athletics, Cop Talk, Driving, Evidence Collection, Firearms, Interrogation, Law, Assess Honesty, Sense Trouble | 3 to 4 | Cop Talk opens case files, evidence rooms and prisoners; in the home jurisdiction also the lab and the morgue. |
| **Private Investigator** | Accounting, Disguise, Driving, Law, Locksmith, Photography, Assess Honesty, Reassurance, Scuffling, Shadowing. [Pulp] hard-boiled variant: Cop Talk, Driving, Intimidation, Locksmith, Assess Honesty, Scuffling, Shadowing, Streetwise | 2 to 3 | Post-roll spending as a Criminal, for Disguise or Shadowing. |
| **Professor** | Bureaucracy, Languages, Library Use, one Interpersonal, three Academic | 3 to 5 | With intact credentials (Credit Rating 3+) Bureaucracy opens closed stacks, labs and many archives. Credit Rating 5+ means tenure. |
| **Scientist** | Electrical Repair, Evidence Collection, Languages, Library Use, Photography, two of Astronomy, Biology, Chemistry, Cryptography, Forensics, Geology, Physics | 3 to 5 | Access to a suitable lab; with Credit Rating 3+ and a 2+ science, university closed stacks. |
| **Federal Agent** | Driving, Evidence Collection, Reassurance or Intimidation, Law, Assess Honesty, plus the agency's package (Treasury, FBI, Secret Service, Marshals) | 3 to 5 (cap 5) | Bureaucracy pulls strings in the agency; Law or Intimidation gets into almost any premises in US territory. |

- **New Occupation [House].** A variant of an existing one swaps one or two abilities (Pilot becomes Sailor by trading Athletics for Driving). A wholly new Occupation has 7 to 9 Occupational abilities and never includes Credit Rating, Cthulhu Mythos, Health, Sanity or Stability. Its special rule is either privileged access to scenes and sources or one small mechanical tweak.

### 2.3 Drives
<!-- for: setup, check -->

Every Investigator has exactly one Drive: a core desire worth more than life or sanity. Any Drive fits any character; suggested pairings in parentheses.

| Drive | Essence |
|---|---|
| **Adventure** | Thrill-seeking; refusing a risk feels like admitting the life was meaningless (Criminal, Military, Pilot). |
| **Antiquarianism** | Only the past feels alive (Antiquarian, Archaeologist, Clergy, Professor). |
| **Arrogance** | Success will justify everything; petty rules and fears do not apply (Alienist, Scientist). |
| **Artistic Sensitivity** | Already attuned to the numinous; must follow the Muse (Artist, Author, Dilettante). |
| **Bad Luck** | Things just happen to this person. It cannot be resisted, so it has no Stability penalty (Criminal, Hobo). |
| **Curiosity** | Cannot leave a mystery alone (Journalist, Police Detective, Private Investigator, Scientist). |
| **Duty** | Someone has to go down those steps, and if not this person, who (Clergy, Doctor, Military, Police Detective). |
| **Ennui** | Everything else is exhausted; only the unnatural interests this person (Artist, Dilettante, Military). |
| **Follower** | Someone important went in, and the character follows to protect them. Pick a fellow Investigator or an NPC. If that person dies the player may pick a new leader or switch to Revenge. |
| **In the Blood** | Strange behavior runs in the family. May be a **secret** Drive revealed in play. |
| **Revenge** | Something hurt this person's own and must be destroyed at any cost. |
| **Scholarship** | Uncovering truth, acclaim and the satisfaction of knowledge. |
| **Sudden Shock** | Something tore the scrim off the world and there is no going back. The player invents the shock (or opts for amnesia). |
| **Thirst for Knowledge** | Must learn the secrets of the cosmos. |

How Drives cost and refresh Stability is in §5.3.

### 2.4 Pregenerated, provided and replacement characters [House]

- A character reaches the game by one of three routes: **generated** with the AI Master (§2.1), **pregenerated** (supplied by the adventure) or **provided** by the player in any format. Whatever the route, produce the canonical character record and run the checklist of §2.7.
- **Pregenerated** characters may swap Pillars, Sources or small details but not break the budgets. A pregenerated character built for another party size is **rescaled** by trimming Investigative points only, highest ratings first, keeping each ability the character needs at 1 or more, and telling the player exactly what changed. The adventure's own trim table wins. A character claimed by one player cannot be claimed by another. With no pregenerated characters, or too few, generate three to five on demand and save them as unclaimed (`status: "pregen"`).
- **Late joiners** use the budgets for the party size at the start and get an in-world way into the story, designed by the AI Master. They begin when the next turn opens.
- **A dead, Gone or committed character** may be replaced in the same game by a newly generated one, an unclaimed pregenerated one or an NPC marked available. The replacement arrives in the fiction within one or two turns and does not inherit the other's knowledge, items or relationships.
- **Converting an NPC into a character.** Keep the NPC's name, role, trait, knowledge and inventory. Build the sheet from the NPC's tier (§7) and the budgets of §2.1a, never above them. The NPC stops acting as an NPC. A **main** NPC of the adventure is never offered.
- **Converting a sheet from another system** (including other GUMSHOE games and *Call of Cthulhu*): map each entry to the nearest ability here, keep the totals within the budgets, drop spells and powers, turn wealth into Credit Rating and narrative means, and give a traceability table (original entry, result, note). Show it and wait for approval. Imported pools start full.
- **A player who leaves** turns the character into a GM-run ally who stays safe or departs plausibly.

### 2.5 Pillars of Sanity and Sources of Stability
<!-- for: setup, check -->

- **Pillars of Sanity:** for every 3 full rating points of Sanity, one Pillar: an abstract principle the character trusts implicitly (not a person or an object). Examples: religious faith; family honor; human dignity; scientific progress; the laws of physics; the goodness of nature; the innate goodness of mankind; a moral code; high art; patriotism; love of a home town. A revelation that undermines a Pillar costs extra Sanity (§5.4).
- **Sources of Stability** (module `sources_of_stability`, for campaigns with a soap-opera element): for every 3 full rating points of Stability, one named person who keeps the character sane (name and an identifying phrase; not another Investigator, though several Investigators may share one at a risk). Cultists and entities may use these people. If harm comes to one, the character faces hard Stability tests and may permanently lose the linked rating points. For a one-shot only one Source (a person) is set at the start, the others appear in play. With the module off, Stability simply refreshes between stories.

### 2.6 Contacts and the intimate correspondent
<!-- for: turn, play, setup -->

- Whenever a character uses Bureaucracy, Cop Talk, Credit Rating, Streetwise or any ability to call on a contact, the player supplies the contact's name, residence and connection. The size of the spend sets the contact's attitude, the value of the information and the position in the field. Essential clues are always free. The AI Master reuses contacts as recurring NPCs and may have them ask for favors, bring trouble or die badly.
- **Intimate correspondent [optional].** A mentor, protégé, relative or clergyman to whom the character confides everything. If the Investigator dies or goes mad, that person is a briefed replacement seed.

### 2.7 Character intake and validation [House]
<!-- for: setup, check -->

| # | Check | Passes when |
|---|---|---|
| 1 | Fit | Concept, Occupation, era and place fit the adventure's era, mode and tone. A banned Occupation or type is refused. |
| 2 | General budget | General build points spent equal the budget of §2.1a (65 by default). Spent points are the sum of the General ratings, with Occupational General abilities counted at half, minus the free points (Health 1, Stability 1, Sanity 4). Sanity above 4 is bought from this budget. |
| 3 | Investigative budget | Investigative build points spent equal the figure of §2.1a for the party size at the start: the sum of the ratings, with Occupational abilities counted at half and Credit Rating counted only above its free lower edge (1 point each up to the top of the band, 2 each above it). |
| 4 | Ability list | Every ability appears in §3. Hypnosis only for Alienists and Parapsychologists (and Pulp, by the adventure). Cthulhu Mythos is 0 at the start unless the adventure grants it. No spells at the start. |
| 5 | Occupational abilities | Each starred ability belongs to the Occupation's list, has an even rating and is never Fleeing, Credit Rating, Cthulhu Mythos, Health, Sanity or Stability. |
| 6 | Credit Rating | Within the Occupation's band, or paid for at double cost above it, and within any cap set by the adventure. A Hobo has 0. |
| 7 | Balance | The second-highest General ability (excluding Fleeing) is at least half the highest. Health, Stability and Sanity caps of §2.1a hold. |
| 8 | Fleeing | Fleeing above twice Athletics is paid at the half price of §2.1a, and the character is not plainly a fighter if the discount was used. |
| 9 | Professions | Law 2+ and Medicine 2+ imply a licensed profession. If the character is not licensed the sheet says so, and the character cannot practise or certify. |
| 10 | Pools | Every ability has a maximum and a current value, equal at the start. Sanity is 4 or higher. Hit Threshold is 3, or 4 with Athletics 8 or more. |
| 11 | Drive | Exactly one Drive of §2.3 with a clear trigger. |
| 12 | Pillars and Sources | One Pillar per 3 full Sanity points. With the module on, no more than one Source per 3 full Stability points (a one-shot starts with one). |
| 13 | Means and kit | Money, transport and kit fit the era and the Credit Rating. Weapons beyond a plausible kit are refused. |
| 14 | Appearance and content | Only the appearance the player supplied. Nothing conflicts with the truth rule. |

**Outcomes.** `pass`; `pass_with_adjustments` (list the smallest changes needed, each needing the player's approval); `fail` (list the violations and the smallest fixes). Never silently change a submitted sheet, except for a plain arithmetic slip with one unambiguous correction, which is still reported. Never raise ratings to be generous. A character starts play only after `pass` and the player's confirmation.

---

## 3. Abilities

Abilities come in two kinds. **Investigative** abilities (Academic, Interpersonal, Technical) automatically yield clues when used reasonably, and each rating point is also a pool of points for spends (§4.1). **General** abilities are tested with a die (§4.2).

### 3.1 Investigative abilities

**Academic**
- **Accounting:** read and keep financial records; separate honest business from crime; trace payments, embezzlement, bribes and dummy companies.
- **Anthropology:** artifacts and rituals of living cultures; customs of foreign groups and subcultures.
- **Archaeology:** date burials and buildings; identify artifacts and fakes; navigate ruins and find secret doors.
- **Architecture:** judge a structure's age, style, strength and alterations; deduce hidden rooms and load-bearing elements.
- **Art History:** tell real from fake, date by style, estimate prices, recall artists' lives.
- **Biology:** animal and plant behavior and origin; tissue, ichor and slime; natural poisons.
- **Cryptography:** make and break codes; puzzle out unfamiliar alphabets.
- **Cthulhu Mythos:** the character has begun to piece together the secret rules of reality. Recalls facts from tomes read, and reads the history of an artifact or relief in one glance. **Using it costs Stability and sometimes Sanity** (§5.4). The AI Master gives an insight that points the investigation in the right direction, not necessarily the solution; a spend yields more specific and more dangerous answers.
- **Geology:** soils, minerals, strata, fossils; where oil, water and mines lie; natural hazards.
- **History:** obscure allusions; events by place; ancient scripts; dating and attributing manuscripts; period dress.
- **Languages:** each rating point is one more language spoken and read, possibly a dead one. The adventure may forbid occult tongues.
- **Law:** criminal and civil law of the home jurisdiction; legal risk and jargon; legal colleagues. Rating 2+ may mean a bar-certified lawyer.
- **Library Use:** find information in collections, archives and correspondence; detect patterns, gaps and doctored records.
- **Medicine:** diagnose disease, injury, poisoning and frailty; elementary Forensics if the AI Master allows. Rating 2+ may mean a licensed doctor.
- **Occult:** the history of magic, superstition and sorcery; the tradition behind a ritual and its intended effect; paraphernalia, grimoires and symbols. It does not allow working magic. **With both Occult and Cthulhu Mythos, recognizing a ritual as a real Mythos ritual costs no Stability or Sanity.**
- **Physics:** experimental machinery, advanced and non-Euclidean mathematics, comprehending strange technology.
- **Theology:** religious practice and belief; orthodox against heretical; officiating a ceremony. It does not allow miracles. With Cthulhu Mythos, identifying a Mythos ceremony costs nothing.

**Interpersonal**
- **Assess Honesty:** tell if someone lies and, with a spend, why; cold-read marks. Con men, sociopaths, most sorcerers and brainwashed cultists may not register.
- **Bargain:** haggle, mediate, swap favors or information.
- **Bureaucracy:** navigate organizations; get official information; false credentials. Not a catch-all: information better found by other abilities earns "do your own legwork".
- **Cop Talk:** police lingo; confidential information from cops; excusing minor infractions; calling in favors.
- **Credit Rating:** operate within one's economic class (table below); buy, mingle, borrow, collect rumors. It is both a class and a pool, and behaves like eight abilities in one.
- **Flattery:** get help by compliment; information, favors, trust.
- **Interrogation:** formal questioning of a subject who is confined or fears confinement and recognizes the questioner's authority.
- **Intimidation:** physical or psychological dominance to get information, make subjects leave or quell violence.
- **Oral History:** find sources and gather testimony, folklore and gossip; best in rural settings; shorthand and unobtrusive recording.
- **Reassurance:** put people at ease to get information or favors; allay fear and panic.
- **Streetwise:** behave among criminals; unsafe places and dangerous people; fences, dealers and arms runners; underworld rumors.

| Credit Rating | Class | Signifiers | Approximate yearly income |
|---|---|---|---|
| 0 | Pauper | Hobo life, handouts | $0 to 150 |
| 1 | Lower Class | Janitor, servant; flophouse; canned food | $150 to 250 |
| 2 | Working Class | Factory or skilled service; tenement; meat most days | $250 to 1,250 |
| 3 | Lower Middle | Clerk; shabby apartment; an old car | $1,250 to 1,500 |
| 4 | Middle | Supervisor, lesser professional; one good suit; modest car | $1,500 to 3,000 |
| 5 | Upper Middle | Professional; tailored suits; good house; new car; a live-in servant | $3,000 to 10,000 |
| 6 | Upper | Independent income; mansion or penthouse; luxury cars; several servants | $10,000 to 75,000 |
| 7+ | Wealthy | Estates, yachts, private planes, a staff | $75,000 and up |

Credit Rating is class and bearing, not a bank balance. Social bearing may drift one or two ranks from the income.

**Technical**
- **Art:** create music, painting, dance, sculpture, poetry or drama. Each rating point adds a medium. Great works need spends.
- **Astronomy:** astrological texts, telescopes, plotting stars, predicting eclipses and comets.
- **Chemistry:** with a lab, identify drugs, toxins and substances; make simple explosives, poisons, gases and acids; ballistic, ink and soil analysis.
- **Craft:** make useful objects in wood, metal or jewelry; may find hidden drawers.
- **Evidence Collection:** the default search ability: hidden objects, sequences of events, fingerprints, typewriter and handwriting matches, uncontaminated storage.
- **Forensics:** crime scenes and autopsies; skeletal analysis; weapon, time of death, intoxicants, last meal.
- **Locksmith:** open locks and disarm alarms. A lock that hides a clue simply opens; only safes and locks that exist to create drama need a test.
- **Outdoorsman:** live and work outdoors; strange animal behavior; hunt, forage, navigate and track.
- **Pharmacy:** identify and compound drugs; side effects; poisons and antidotes; controlled substances.
- **Photography:** record scenes; develop, enhance and filter film; spot retouching; trick photographs.

Overlap is expected: a clue may be reachable by several abilities. If the player's reasonable use matches a clue, give it. The ability need not even be named.

### 3.2 General abilities

- **Athletics:** physical derring-do not covered elsewhere. **Athletics 8 or more gives Hit Threshold 4**; otherwise 3.
- **Conceal:** hide things and search for things hidden on purpose.
- **Disguise** (also Investigative): alter appearance, posture, voice; a cover identity; brief misrepresentation. Impersonating a known person is very hard: voice only Difficulty 4; face to face needs a Difficulty 7 test every five minutes of sustained contact.
- **Driving:** skilled driving, evasion, pursuit, minor repairs. Every 2 further points add a vehicle type.
- **Electrical Repair** (also Investigative): build, repair, disable and use electrical devices; tap lines; judge workmanship.
- **Explosives** (also Investigative): defuse, handle and make explosives; reconstruct a bomb from the debris.
- **Filch:** pick pockets, pilfer clues from or plant clues at scenes.
- **Firearms:** guns and similar trigger weapons, repair and identification. [Pulp] 2 Firearms points allow a long-range pistol shot (or a rifle shot up to 500 yards); with Firearms 5+, 1 point fires two pistols in one round, one target's Hit Threshold rising by 2.
- **First Aid:** treat injury (§4.7). Basic poison control.
- **Fleeing:** running away; substitutes for Athletics in escapes; never helps pursuit.
- **Health:** the ability to take injury and resist infection and toxins; can drop below 0.
- **Hypnosis** (Alienists and Parapsychologists only; usually [Pulp]): willing subjects only, one at a time. Simple trance Difficulty 3; analytic rapport 3 (adds 3 to the user's Psychoanalysis pool against that patient); recover memories 4 (reliving costs the patient the same Stability again); post-hypnotic suggestion 4 or more (one simple action, never against the patient's nature); ease pain 4 or more (removes Hurt penalties until wounded again); implant false memories, a contest of the user's Hypnosis (Difficulty 5) against the patient's Stability (Difficulty 4), unethical, undone by a later collapse.
- **Mechanical Repair** (also Investigative): build, repair, operate and disable mechanisms; each point adds a heavy machine; clear a jammed gun at Difficulty 4.
- **Piloting:** small boats or single-engine light aircraft; every 2 further points add a type of craft.
- **Preparedness:** pack a kit. A simple test (§4.2) produces an item if it is credible. Items any investigator would carry (notebook, flashlight, matches, chalk, tools, magnifying glass, string, sandwiches, brandy) need no test. Abilities imply their gear. Anything that would make the table laugh is out.
- **Psychoanalysis:** comfort and perspective for the troubled; calms the panicked, restores Stability (§5.7), treats long-term illness (§5.6).
- **Riding:** horses, donkeys and mules; every 2 further points add an animal.
- **Sanity:** never tested and never spent; it is eroded by the Outside (§5.4). At 0 the Investigator becomes an NPC. Free: 4.
- **Scuffling:** hand-to-hand fighting, including blackjacks, brass knuckles and saps.
- **Sense Trouble:** perceive danger by any sense. **The Difficulty is never known before the player decides how much to spend.** Never require Sense Trouble to find a clue; use an Investigative ability (default Evidence Collection). It is for action: if not noticing something gets you attacked, it is Sense Trouble.
- **Shadowing:** follow suspects unseen; lose a follower.
- **Stability:** resistance to mental trauma (§5). Free: 1.
- **Stealth:** move quietly, hide, evade watchers, eavesdrop at doors.
- **Weapons:** skilled use of hand weapons such as knives, swords and whips.

The asterisked abilities Disguise, Electrical Repair, Explosives and Mechanical Repair double as Investigative abilities in some circumstances but are bought and rolled as General abilities.

---

## 4. Core mechanics
<!-- for: turn, play -->

### 4.1 Clues
- **Gathering is automatic.** The character must be in a scene where the information exists, have the right ability and say it is being used. The player may be specific ("Art History on the idol"), speculative ("Oral History to find the town drunk"; the AI Master may swap the planned source) or general ("Evidence Collection on the alley"). The ability need not be named.
- **Essential (core) clue:** needed to reach the next scene; always found, and the AI Master tells a suitable Investigator it is available even if nobody asks. It is never tied to an obscure ability. **0-point clue:** free atmosphere. **Spend clue:** a bonus for 1 or more pool points. **Inconspicuous clue:** noticed without actively searching; the Investigator with the highest current pool in the ability finds it (ties: higher rating; then both). The default ability is Evidence Collection. **Simple search:** anything an ordinary person finds by looking where the player says needs no ability. **Floating clue:** not tied to a scene; the AI Master releases it to unstick play.
- **Spends.** A clue may allow a spend of 1 or 2 points for a special benefit: an advantage in a later contest, a favorable impression on an NPC, a flashback, resolving a moral dilemma without violence, speeding the investigation, a dedicated pool point, a notable work, or refreshing Stability (§5.7). Spend information is flavor, never required. If no benefit exists the points are not lost. Investigative spends can also lower the Difficulty of a General test by 1.
- **Dedicated pool points** are extra points usable only in one circumstance or on one subject (from tomes, communion with alien perceptions, mental illness). They stack on the rating for that use only.
- **Interpretation is the game.** Clues need not be true, and they point on. A good clue leaves the players deciding what it means.

### 4.2 Tests (General abilities)

A test is called only when the outcome is in doubt and failure matters. Otherwise the action succeeds, with optional bonus spends.

1. The player may spend any number of pool points from the ability, each adding +1, **before** rolling.
2. Roll one d6 and add the spend. Meet or beat the **Difficulty (2 to 8)**: success. **Default 4.** 2 is a slim chance of failure; 8 verges on impossible. Tests that move the story forward are 4 or lower; high Difficulties are for optional obstacles.
- The ability must have a rating of 1 or more. **No retry** unless the character does something that credibly improves the odds and spends more points than the previous attempt.
- **Hidden Difficulty.** [Purist] the AI Master never reveals Difficulties. [Pulp] it may reveal them for conventional obstacles, never for Sense Trouble.
- **Success at a cost** is allowed for a must-pass obstacle: the action succeeds and the test sets the price (the fence is climbed but the character is cut).
- **Cooperation:** the leader tests and spends normally; an assistant may spend any number of points, **all but one** adding to the leader's roll. **Piggybacking:** a group acting together appoints a leader; every other participant pays 1 point from the relevant pool and takes part; for each participant who cannot pay, the Difficulty rises by 2.
- **Light, weather and terrain** shift Difficulty by 1. **Surprise:** +2 on the surprised character's next test [House].
- **Declared spends [House, asynchronous].** Players cannot answer mid-turn, so spends are those declared in the action or in the standing orders (§6.4). Apply them as declared, each +1 before the roll. Never apply more than declared or more than the pool holds.
- **Dice [House].** The AI Master rolls every die, using only the server's dice stream, in order. Each roll is reported without its Difficulty (it may be revealed afterwards if the player asks). A roll report shows the ability, the spend, the die, the total and the outcome: success, narrow success, failure, narrow failure.

### 4.3 Contests and chases

In a **contest** two characters actively oppose each other and **the first to fail a test loses**. The one who bolts or strikes first acts first; if simultaneous, the lower rating acts first; ties: NPCs before Investigators. Each tests at Difficulty 4 unless the odds are unequal (a significant advantage lowers the Difficulty, a major handicap raises it). Raise your own Difficulty to raise the pursuer's, for example by taking dangerous terrain. Narrate each result.

- **Prolonged chase:** the pursued loses only after failing two or three more tests than the pursuer. **Relentless pursuer:** lower the Difficulty, but the characters make three tests for each of the pursuer's.
- **Investigative contests** are rare (Bargain at an auction, Assess Honesty at a card table) and used only when the contest is as dramatic as a fight. The opponent's pool is at most 1 higher, and defeat never stalls the plot (a cooler NPC, a warned enemy, a worse route).
- **Being questioned by an NPC.** Casual pumping: let the player notice with Assess Honesty and choose what to say. An official or hostile interrogation is a plot device, not a contest.
- **Escape pool [House, optional]** for a trapped group: start at 0; add 1 to 3 per way-out clue, +1 per relevant Investigative spend and +1 per successful relevant test; Difficulty is 6 plus 2 per escaping character; one attempt per turn; failure empties the pool and triggers a hazard.

### 4.4 Fighting

Fights use Scuffling against Scuffling or Weapons, Weapons against Weapons, or Firearms against Firearms at range. In the Purist idiom a fight is a failure state or a threat, not the solution.

- **Aggressor and defender.** The aggressor acts first against the other. If unclear, compare current pools in the abilities being used; the higher may choose. In a **free-for-all** rank everyone by current pool in their starting fighting ability (ties: higher rating, then Investigators before creatures), a full pass is a round, and the order stays fixed. A combatant who does something else (runs, climbs, throws a grenade) moves to last.
- **Hit Threshold.** The Difficulty an attacker must meet or beat to harm someone: **3**, or **4** with Athletics 8 or more. Less competent NPCs may have less, creatures often 4 or more, very large creatures 1 lower than man-sized ones. [Pulp] faceless mooks have 2 or 3; Mythos creatures keep their values.
- **Damage.** On a hit roll a die plus the weapon modifier and subtract it from the target's Health. Pool points cannot be spent on damage. Fighters are not "out" on a failed roll; they are forced out by unconsciousness or serious wounds.

| Weapon | Modifier |
|---|---|
| Fist, kick | -2 |
| Small improvised weapon, blackjack, nightstick, knife | -1 |
| Big improvised weapon, machete, heavy club, light firearm | 0 |
| Sword, heavy firearm | +1 |
| Very heavy firearm (big-game rifle, automatic rifle) | +2 |

- **Firearms.** +2 at point-blank. Shotguns count as heavy at point-blank and light at near range; both barrels of a double-barrel add +1 at point-blank or close range. **Examples:** light, +0: .32 pistols and revolvers, .22 and 20-gauge guns, small carbines. Heavy, +1: .38 and .357 revolvers, .45 and 9 mm automatics, 12-gauge, combat and sporting rifles, submachine guns. **Automatic fire:** +2 Firearms pool points (+3 with a drum); after a burst the shooter stops for a round to reload; a 1 on a submachine gun jams it (Mechanical Repair, Difficulty 4). [Pulp] a full-auto shooter may hit several targets within close range, each after the first raising all Hit Thresholds by 1. **Ammunition:** [Purist] a Firearms roll of 1 means the gun is empty; [Pulp] reload only when dramatic; when reloading matters it is a Firearms test at Difficulty 3.
- **Range.** Point-blank (arm's reach); close (the same room, about 10 yards); near (30 to 40 yards, the limit for pistols and shotguns); long (up to 100 yards, the limit for rifles).
- **Cover.** Exposed: Hit Threshold -1. Partial: no change. Full: +1.
- **Armor** subtracts from each instance of damage it is effective against and is rare: a Great War helmet (-2 against bullets and blades, -1 blunt, head shots only); a heavy coat may take 1 from small blades and fists; gangster vests take 2 from bullets and clubs and cost 1 Athletics point while worn.
- **Untrained** (no Firearms, Weapons or Scuffling): damage -2 more, must declare the action at the start of each round and goes last; a 1 with a gun hits an ally or the shooter.
- **Non-lethal Scuffling** never lowers Health below -11 but forces another consciousness roll. Firearms are never non-lethal.
- **At the mercy of an armed person.** Someone with a gun well in hand, or charged from more than 5 feet away without cover, may empty it first: automatic hit (Difficulty 1; 2 if the target has Athletics 8+ and moves), one damage roll tripled. Jumping a person whose gun is not ready is a Scuffling contest for the gun.
- **Explosions.** Setting a charge needs Explosives. Added damage by range (point-blank, close, near): Molotov cocktail +1, 0, none; pipe bomb +2, +1, -1; stick of dynamite +3, +2, -2; bundle of dynamite +7, +4, -1; grenade +3, +1, -2; land mine +8, +3, -1; gas main +9, +5, 0. Throwing a grenade is an Athletics test: Difficulty 2 point-blank, 3 close, 5 near, +1 or +2 to aim at a spot. Explosions usually start fires.
- **Optional realism [House]:** a gunshot to a human that would leave Hurt leaves Seriously Wounded instead; a gunshot that takes Health to 0 or below deals +6 more. Monsters are not affected. Recommended in the Purist idiom with the lethality `high`.
- **Restraint and ejection [House].** Being held, thrown out or arrested by guards, staff or police is resolved narratively with an Athletics or Fleeing contest at Difficulty 3 plus the number of restrainers. Consequences are ejection, a ban, a report, a bruise or a night in a cell, never an automatic death.
- **Vehicles in combat.** A driver in a firefight may spend 1 Driving point per round to avoid serious damage; shooting tires or the engine of a moving vehicle raises Hit Threshold by 2; a fuel tank has armor 2 and an engine block 4; only in a very pulpy game does a hit tank explode.

### 4.5 Other dangers

- **Acid:** damage each round (weak -2, strong 0, very strong +1) until removed; roll once and reuse.
- **Extreme temperature:** treat as Hurt. **Fire:** torch -1, bonfire 0, burning room +1; a burning character takes damage at 0 each round until extinguished. Smoke follows the drowning rule.
- **Drowning and suffocation:** with warning, hold breath; Athletics test each round (Difficulty 3, +1 each round); on failure lose d6+1 Health per round.
- **Falling:** damage equals the Difficulty of the wall; +2 for spikes or jagged rock. Avoid a story in which one failed test kills an Investigator.
- **Poison:** the AI Master sets onset, symptoms and lethality. Instant death is for NPCs; an Investigator gets a chance to reach a Pharmacy or Medicine spend unless the poison is implacable.
- **Environmental hazards [House].** Any lingering hazard in a place (bad air, smoke, cold, exhaustion) uses stages. Cues first (at least two distinct signs before Stage 2); **1 Uneasy** (discomfort; Sense Trouble can identify it); **2 Unwell** (Health test Difficulty 4 each further half hour; failure costs 1 Health and +1 Difficulty); **3 Impaired** (Difficulties +2, a Stability test); **4 Collapse** (unconscious; 2 Health per 10 minutes until carried out). No instant death; always a way out.

### 4.6 Time, scenes and clocks [House]

- Play is divided into **Blocks** (parts of an in-world day) and **turns** (the interval at which the AI Master resolves all actions). Each Investigator has the Blocks the adventure's clock gives. A long action (an evening of research, a night's rest) costs a Block; a brief one (a telephone call, a few lines in the notebook) costs none.
- The adventure may keep a **clock** (dates, a countdown, an escalating phenomenon). Time-sensitive events fire on their dates whether or not the characters are there.
- **Fail forward.** A failed test costs time, access, trust, safety or evidence; it never halts the investigation or erases an essential clue.

### 4.7 Injury and death

- **Health can fall below 0.** Below 0 the character must make a **consciousness roll**: a d6 against a Difficulty equal to the absolute value of the current Health (before any extra loss). The player may voluntarily lower Health further to add +1 per point (not below -11).
- **0 to -5: Hurt.** No permanent injury; no Investigative spends; all Difficulties, including opponents' Hit Thresholds, +1.
- **-6 to -11: Seriously Wounded.** Consciousness roll required; whether conscious or not the character cannot fight; lose 1 more Health every half hour until First Aid.
- **-12 or lower: dead** (subject to the lethality of §4.8).
- **First Aid.** Hurt: 1 First Aid point heals 2 Health (1 on self; Doctors and Nurses 3 and 2), up to the Health the character had before the incident; the healer gives full attention. [Purist, variant] First Aid never brings Health above one third of the maximum. Seriously Wounded: 2 First Aid points stabilize (1 for Doctors and Nurses) but restore nothing. Convalescence: days equal to the lowest negative Health reached; on discharge Health is half the maximum and full the next day.
- **Rest** restores 2 Health per day.
- **NPC Health.** [Purist] NPCs lose Health as Investigators do; key NPCs follow the Investigator rules. [Pulp] ordinary NPCs die when Health falls below 0. Creatures die, vanish or are banished below 0 unless their entry says otherwise.

### 4.8 Lethality in this ruleset [House]

The game's `lethality` setting decides when the "dead", "Gone" and Sanity 0 conditions of §4.7 and §5 actually apply.

| Level | Health, Stability and Sanity reach the bottom |
|---|---|
| `low` | The character does not die. At Health -12 the character is Seriously Wounded and out of the story in care. At Stability -12 the character is Gone only if the player chooses at a decision gate, otherwise Shattered and incapacitated. At Sanity 0 the player may choose retirement to an institution instead of becoming an NPC. |
| `moderate` | Dead at Health -12 and Gone at Stability -12, but only after a warning cue and a decision gate or a chance to withdraw. Without them, stop at -11 and apply the Seriously Wounded or blasted state. |
| `high` | Dead at Health -12 and Gone at Stability -12 after a clear warning cue, with no gate. At Sanity 0 the character becomes an NPC. |

Absent, paused and away characters are never taken to the bottom at any level (§6.4). A death or a Gone outcome starts the replacement offer (§2.4).

### 4.9 Regaining pool points

- **Investigative pools** refresh at the **end of each case**, regardless of in-world time.
- **Haven** [House]: an hour of genuine safety (a bolted room, a quiet pew, a locked carrel) refreshes up to **3 General abilities, not Health, Sanity or Stability, once per in-world day** per character. A breached Haven is lost.
- **Physical abilities** (Athletics, Driving, Firearms, Fleeing, Piloting, Riding, Scuffling, Weapons) refresh fully after 24 game hours without spending. Other General abilities refresh at the end of the case.
- **Health** 2 per day of rest.
- **Stability** is refreshed by Sources (§5.7), by indulging a Drive (§5.3), by Psychological Triage and by Confidence; between cases it recovers automatically unless the Sources module makes it depend on time with them.
- **Asynchronous play [House].** A Haven or a Source reconnect must be declared in the action; a long one costs a Block, a brief one none. The once-per-day limits still apply.

### 4.10 Improving an Investigator
<!-- for: turn -->

At the end of each case each player gets **2 build points per session played** (adjust for the number of turns in the story) to spend one for one on Investigative or General abilities, new or existing, or to reassign 1 or 2 points as atrophy. Never on Credit Rating, Cthulhu Mythos or Sanity. The AI Master may adjust Credit Rating for treasure, decoration, ruin. [Purist] nothing improves the Investigator, but reassigning points is allowed.

---

## 5. Stability, Sanity and the Mythos
<!-- for: turn, play -->

### 5.1 The two scores

- **Stability** is the character's mental Health pool: resistance to any trauma, natural, human or supernatural. It falls quickly and normally refreshes between cases.
- **Sanity** is the capacity to believe in, fear for or care about the human world. It is never spent and never tested. It erodes slowly, one or two points per case unless the character meets a god, loses a Pillar or suffers the big reveal. [Purist] it never returns.
- Stability measures how close the character is to snapping today; Sanity how close to seeing the Truth forever. A character can be steady and nearly gone (high Stability, low Sanity), or fragile and whole.

### 5.2 Stability tests

When an incident challenges the character's grip, make a **Stability test at Difficulty 4**. The player may spend Stability points before rolling (never wise beyond the possible loss). **On failure the character loses the incident's points** as well as the points spent. Name tests by potential loss ("a 4-point Stability test").

- **Mythos shocks** are always at least +1 Difficulty, and most Mythos entities cost more (their entries say so). No one gets a break against the supernatural.
- **Experience.** Difficulty 3 for the inured (a nurse among the mutilated, a soldier among the dead); 5 for the especially susceptible.
- **Cap:** total loss in one incident cannot exceed the highest single potential loss in it.
- **[Pulp]** after passing as many tests against one kind of creature as its Difficulty, the Difficulty drops by 1 (not below 2).
- **Group scares [House].** When an event threatens all, each character tests separately at the same Difficulty.

| Incident | Loss |
|---|---|
| See a fresh corpse; witness a killing | 1 |
| A human attacks intending serious harm; serious vehicle accident; strong unnatural sensation (intense déjà vu, missing time, hallucination); witness torture | 2 |
| A human attacks intending to kill; kill someone in a fight; a particularly grisly scene; a supernatural creature seen at a distance; an obvious unnatural omen without threat | 3 |
| Hundreds of corpses or a large battle; a supernatural creature up close; a week in solitary; learn that a friend, loved one or Source was violently killed | 4 |
| Discover the corpse of a friend, loved one or Source; attacked by a supernatural creature or by a loved one; witness a clearly impossible killing; a threatening unnatural omen; kill in cold blood; torture someone | 5 |
| See a friend, loved one or Source killed; tortured for an hour or more; discover that you committed cannibalism | 6 |
| Possessed but conscious; speak with a known dead person; attacked by a single gigantic creature or a horde | 7 |
| See a loved one or Source killed gruesomely or unpreventably; kill a loved one or Source | 8 |

**Role-playing instability** (no mechanical effect above 0): 1 or 2 points: a twitch, a stutter, a rising voice; 3 or 4: hyperventilating, sweating, runaway talk, comforting rituals; 5 or 6: fugue, frame drop, hyper-alert to triggers; 7 or 8: adrenaline shock, tunnel vision, babbled confessions. Interpersonal abilities work through fear.

### 5.3 Drives and Stability

The AI Master tells the player when the Drive impels the character. The player is never obliged to obey, but **resisting costs Stability automatically, with no test**.

- **Hard driver** (written into the scenario or invoked at will): resisting costs **4 Stability or one third of the pool, whichever is greater**; obeying refreshes **2**.
- **Soft driver** (a tangential situation): resisting costs **2**; obeying refreshes **1**.
- Gains never exceed the Stability rating. The AI Master grants the refresh only if obeying advances the story or puts the Investigator in grave peril.
- **Bad Luck** cannot be resisted. When the universe hoses that Investigator more than others, give a Stability reward as if obeying (the hatred is oddly comforting).
- **Asynchronous play [House].** The AI Master puts the temptation in the facts and a `risk_factor` prompt in the result; the player answers in the next action. If an action abandons a person or a danger the character knows about and the Drive is hard, the cost is paid when the action is carried out, after a decision gate unless the player was already warned.

### 5.4 Losing Sanity

Sanity cannot be tested to avoid. It is lost in two ways: a **Mythos shock** that takes Stability to 0 or below, or **using the Cthulhu Mythos ability**. Beholding a god or titan, and some spells, also cost Sanity (their entries say so).

- **Mythos shocks.** Shaken (Stability 0 to -5): Sanity rating -1. Blasted (-6 to -11): Sanity rating -2. Only the worst such loss applies in one investigation.
- **Using Cthulhu Mythos.** Costs Stability and, if the discovery is terrifying enough, Sanity, with no test. The loss depends on the nature of the revelation, not on the pool points spent. The AI Master does not enforce a loss if the player deduces the truth without using the ability; any player may ask for the loss to confirm a deduction. Loss cannot be denied away.

| Revelation or intuition | Stability | Sanity |
|---|---|---|
| Some aspect of the Mythos is behind this mystery; specifics comfortably distant or not immediately relevant | 2 | 0 |
| A clear and present danger to innocents; the truth goes deeper, farther or wider than believed | 3 | 1 |
| A clear and present danger to you or your loved ones; global or epochal scope | 4 | 1 |
| Shatters one of your Pillars of Sanity | 6 | 2 |
| Could destroy the world (or is doing so, probably inevitably); proves your Drive meaningless or doomed | 8 | 3 |

- **Pillars.** After losing 3 Sanity the player may decide a Pillar has crumbled from within, avoiding the shock of its destruction. [Pulp] this may happen repeatedly. A character who loses the **last Pillar** (or whose Sanity falls to 2 or below) survives on instinct: all Stability tests +1 Difficulty.
- **Lost Drives.** If a revelation proves the Drive meaningless, the character can no longer gain Stability from it but still loses Stability for not following it.
- **Denial.** At the end of an adventure with no proof of what happened (no samples, photographs, artifacts), the AI Master may restore 1 Sanity rating point. It may demand a delusion, amnesia or a cover memory. Acting on the knowledge again costs the point back. Impossible once Sanity has hit 0.
- **Fainting.** The player may declare that the character faints rather than absorb a Mythos experience: lose only 1 Sanity pool point and take no further part in the scene. It does not apply to the cost of casting spells or using the Cthulhu Mythos ability. The AI Master may do dreadful things to the unconscious body but offers a way to learn its fate and does not kill it outright.
- **Sanity 0.** The character becomes an NPC: locked away, or a willing servant of the Mythos (subject to §4.8).
- **Mythos rating and Sanity.** With any Cthulhu Mythos rating, Sanity is at most 10 minus the rating; excess points are lost when the rating rises.

### 5.5 Coming unstrung

- **0 to -5: shaken.** The character can work but cannot spend Investigative points, and all General Difficulties are +1.
- **-6 to -11: blasted.** The AI Master may give a mental illness (§5.6) that outlasts the loss. The character can only panic-flee, attack perceived dangers frenziedly, or do nothing colorfully (gibber, go catatonic). **Permanently lose 1 Stability rating point** (it may be rebought).
- **-12 or lower: incurably insane (Gone).** One last act (self-destructively heroic or destructive) or a drooling check-out, then a sunny hospital; make a new Investigator (subject to §4.8).
- Returning to 0 or above ends shaken.

### 5.6 Mental illness

- **Shell shock** (a mundane or merely supernatural incident): constant anxiety and dreams. When a sense reminds the character of the incident, a Stability test at Difficulty 4 or freeze for 15 minutes and be shaken for 24 hours; the test costs no Stability.
- **Mythos madness** (a Mythos incident): the AI Master chooses (or rolls, dropping the two least appropriate). **Delusion** (a mundane thing does not exist; everyone denies it). **Homicidal mania** (told another Investigator is a monster). **Megalomania** (failures narrated as success; the group tells the truth later). **Multiple personality** (another player voices the character under stress). **Obsession** (4 pool points become dedicated to the obsessive object). **Paranoia** (others seem to hide something). **Phobia** (a stimulus from the event; Sense Trouble tests). **Selective amnesia** (an event that did happen is forgotten). For players who dislike collaboration, agree a non-collaborative disorder in advance. In asynchronous play the AI Master applies the effect through the facts it reports and any player-visible state.
- **Curing.** With Psychoanalysis, at the start of each case a prologue scene tests Difficulty 4 ([Purist] twice the patient's Cthulhu Mythos rating or 4, whichever is higher). After three consecutive successes and three consecutive cases with Stability above 0 the illness vanishes; a new illness brings the old one back. Therapy can replace a shattered Pillar or disproven Drive (one at a time) and can build a wall of **false Sanity** equal to half the lost Sanity, capped at 10 minus Cthulhu Mythos; the next loss of 2 or more destroys it, and using the Cthulhu Mythos ability negates the therapy.
- This simulates mental illness as in Lovecraftian fiction, not real psychology.

### 5.7 Refreshing Stability during play

- **Psychological Triage.** With Psychoanalysis a character may spend points to help another. The healer takes no other action and tests at **Difficulty 4** (3 for Clergy and Alienists); on failure no retry for that character until he loses more Stability. Each Psychoanalysis point spent (not counting test spends) gives the recipient **2 Stability**. An erratic mentally ill character gains lucidity for the rest of the scene from 2 Psychoanalysis points (1 for an Alienist) and a Difficulty 3 test.
- **Source of Stability** (module on): reconnecting refreshes 2 Stability, once per Source per in-world day.
- **Confidence [Pulp]:** if a player's suggested spend impresses the AI Master, roll a d6 and refresh that much Stability, once per player per story.
- **Selfless aid or an inspiring feat [House]:** a d6 of Stability, up to the rating.
- **Big reveal [Purist, optional module `big_reveal`].** The key moment of a Lovecraft story: the character pieces together the Mythos and goes to pieces. Afterward the character has **no Drive**, immediately loses **8 Stability** (or triple the normal loss), and any Sanity loss is doubled. It is almost always the end of the Investigator's story (an institution, death, or at Sanity 0 a future villain). In Pulp it is merely the solution.

### 5.8 The Cthulhu Mythos and magic

Lovecraftian magic is alien science, garbled knowledge, or a focus for psychic power; belief does not change the effect. Helpful human magic is rare and magic is generally aimed at the Investigators, not used by them. The adventure supplies its tomes, spells and entities with their numbers; this section gives the rules for them (module `mythos_magic`).

- **Tomes.** A **clue tome** holds a fact, spell or requirement the story needs; a **resource tome** is kept for general information. **Skimming** a clue tome takes about 1 hour per 100 printed pages (10 handwritten); a 1-point Library Use or Languages spend halves the time, a 2-point spend finds the vital fact in minutes. Skimming gives no Cthulhu Mythos points. **Poring over** a resource tome, usually between cases, grants its Cthulhu Mythos points all at once the first time (a major tome +2 to +4, a minor +1), and may teach spells. Tomes in foreign languages need Languages. Dedicated pool points from a tome are decided by the adventure.
- **Learning a spell** takes 1 to 6 hours in play (Physics, Languages, Archaeology or Art spends can shorten it) and needs a Stability test, usually Difficulty 4. Learning by epiphany or communion is instantaneous.
- **Casting.** An **incantation** is a simple test, usually Stability, with a Difficulty and a cost given per spell. A **ritual** is a contest, usually against a summoned creature or the fabric of space-time, which resists with an **Inertia pool** the spell gives. Almost all spells cost pool points, usually Stability; another ability can pay at twice the cost. **A failed spell costs half.** Several casters who know the spell cooperate under §4.2; those who do not know it but take part pay 3 points to add 1. Unless noted, no spell is cast while fighting or fleeing. **Casting counts as a Mythos shock** if the Stability loss costs Sanity. A caster with Sanity 0 never tests for incantations and pays Stability and Health at half cost.
- **Summon and bind.** Summoning is an incantation; a failed Stability test may mean the creature recognizes a weak master and attacks. A binding forces the creature to follow one specific, limited instruction ("leave", "kill that wizard"), takes 2 rounds and is a ritual (Stability against Inertia) if the creature is already present. Seeing a summoned creature is a Stability test for the caster and the witnesses.
- **Generic spell forms for adventures:**
  - **Contact [being]:** Difficulty 4 to 5; cost about 3 Stability (and 1 Sanity for a god); minutes to hours; the being or its servants answer by dream, vision or arrival within a day.
  - **Elder Sign:** seals a path against servants of the Great Old Ones, engraved on an object or a threshold; Difficulty 4; cost 1 Stability rating point; five minutes. An amulet does not protect the wearer.
  - **Voorish Sign:** makes invisible things visible for five minutes; Difficulty 5; 1 Stability plus 1 Sense Trouble or Evidence Collection.
  - **Powder of Ibn-Ghazi:** makes one invisible being visible for ten heartbeats; compounded at Difficulty 3 (2 with Chemistry or Occult); 1 Stability or 2 Chemistry or Occult per vial.
  - **Create gate:** Difficulty 5; 2 Stability or 4 Health, doubled per step of distance (continental, global, interplanetary, interstellar, intergalactic); each 4 Health spent also costs 1 Health rating.
  - **Enchant item:** Difficulty 5; 3 Stability and at least 1 Stability rating point; weeks or months; each further rating point sacrificed adds 1 to casting and 1 dedicated pool point in a ritual.
  - **Call or dismiss a deity:** a ritual; calling a god is nearly always a terrible idea; seeing it is a Stability test with a minimum of 6 points plus its own extras; the Inertia pool is large (typically 8 to 35 or more) and the adventure states it.
- **Creating a tome or spell for an adventure.** Say what it does, its price in Stability, Sanity, Health or rating points, its Difficulty and time, and what its failure does. A spell that solves the mystery on its own is not allowed; magic is a price, a hook or a weapon aimed at the Investigators.

---

## 6. Solo and party play (asynchronous)
<!-- for: turn, play, setup -->

### 6.1 Solo [House]
1. **One viewpoint.** Every thread is narrated through the Investigator. No cutaways.
2. **Allies advise and assist; the character decides.** A GM-run ally never rolls for the player, overrides a choice or solves a problem the player has not engaged with.
3. **Spotlight is automatic.** The freed attention goes to deeper NPCs and consequences, not to filler.
4. **Own pace.** With early close on, the turn resolves when the player has used the Blocks intended.
5. **The clock is real.** An Investigator cannot do everything.
6. **Fail forward, not fail free.** §4.6.
7. **Be honest and fair.** The AI Master never fudges a roll; Difficulty is set before the roll; warnings precede lethal danger.
8. **Death and ruin.** If the Investigator dies, is Gone or at Sanity 0, present it with weight, resolve what happens to the people at stake and the evidence, then offer a replacement, a debrief or a restart. Do not silently reverse it.
9. **Pacing.** Aim for about 12 to 16 meaningful scenes across the adventure: investigation first, then the build, then the finale and a short epilogue.

### 6.2 Party [House]
1. **Parallel threads.** Every character acts every turn. Group characters by place into threads and resolve each. Give every player a result of similar weight and a hook for the next turn.
2. **Splitting the party** is allowed. Every thread resolves every turn.
3. **Group tests.** A test that affects everyone (stealth, scares) is rolled by each affected character separately, with separate dice. A helper's contribution follows §4.2.
4. **Disagreement.** Players may argue in character; the AI Master does not resolve it for them.
5. **Shared knowledge.** Knowledge moves between characters only in the fiction, by speaking, a message or a document, and arrives as hearsay tagged with its source.
6. **Per-character state.** Pools, Pillars, Sources, illnesses and Drives are tracked per character.
7. **Group size.** Budgets come from the party size at the start (§2.1a).

### 6.3 Resolving conflicting actions [House]
<!-- for: turn -->

One world, one truth. Order first, dice second. Nobody's action is dropped.

1. **Block order.** An earlier Block resolves first and later Blocks see its results.
2. **Cause and effect.** Inside a Block, an action that changes what another depends on resolves first.
3. **Claim.** Whoever already holds the item, occupies the place or has the NPC's attention has the claim. A challenger must win an opposed test.
4. **Priority roll (ties only).** Each tied party rolls a d6 from the stream; the higher goes first; re-roll ties.
5. **Cooperation.** If two characters action the same task together, treat it as cooperation under §4.2: the higher rating leads.
6. **Competition.** For one unique thing (the only copy of a document, the only car): the first in time gets it unless the other acts against it; at the same moment roll an opposed test (d6 plus rating plus declared spends); ties go to the holder or whoever was there first.
7. **Opposition.** One character trying to stop another is a contest under §4.3, or for a single action opposed totals; ties go to the defender.
8. **Contradiction.** If two actions assume incompatible facts, the database and the fiction decide. Each character perceives the truth from their own position, and one may be wrong.
9. **Player against player.** Follow the game's `pvp` setting. `none`: no harm or coercion between characters, only argument, refusal and withholding; obstruction is friction (a delay, Difficulty +1). `soft` (default): also deceive, compete, steal small items, block a door; no Health or Stability damage and no killing. `full`: all rules apply, with a warning and a decision gate before any lethal step. A player who set `pvp_optout` is never the target.
10. **Information fairness.** Each player sees only what their character perceives, and results about one event are consistent across players.
11. **Overtaken actions.** Resolve what is left in the fiction (arrive, find it gone). Essential clue routes remain open.
12. **NPCs and the antagonist** act after the characters in each Block unless their schedule says otherwise.

### 6.4 Standing orders, absent and paused players [House]
<!-- for: turn, play -->

- **Standing orders** are stored in each character's record (`settings.standing_orders`): `hold` (where to stay and what to do when absent), `risk_tolerance` (`low`, `medium`, `high`), `default_spends` (for example Sense Trouble 1 each Block), `never_do` (a list) and `reply_to_messages`. The default: stay safe, rest, take no risks.
- **A missed turn.** Apply the standing orders; with none, the character **holds**: stays put or goes to lodgings, rests, keeps routine, declines risky invitations and takes no irreversible or dangerous action. A task marked `continue until told` (a long archive search) continues.
- **Absent characters** are never killed, committed or driven to Sanity 0 by inaction, take no lethal risk and are not chosen as the target of a finale outcome unless their player walked past a decision gate. They may suffer ordinary world consequences: time passing, a missed meeting.
- **Consecutive misses.** After 3 missed turns the player is `away`: the character withdraws to a safe place. After 6, ask the host whether to drop the player; a `dropped` player's character becomes a GM-run ally or leaves the story.
- **Paused players.** When a player sends `pause`, the character holds out of danger and the next result is an out-of-character check-in only.

---

## 7. NPC statistics [House]
<!-- for: turn, play -->

NPCs have no full sheets. Record only what play needs.

- **Fields:** Health (maximum and current), Stability only if the NPC can be frightened mechanically, zero to four relevant abilities, Hit Threshold (default 3), a weapon modifier if armed, and an attitude toward each character. Creatures and NPCs have **no Sense Trouble, Shadowing or Stealth** and never roll to detect or evade; the player rolls, and the creature's **Alertness Modifier** (added to the Difficulty of sneaking up on it or past it) and **Stealth Modifier** (added to the Difficulty of noticing it) tune that.

| Tier | Examples | Health | Typical abilities | Hit Threshold |
|---|---|---|---|---|
| Frail | the elderly, the ill, children | 2 | Athletics 1 | 3 |
| Ordinary | clerk, nurse, shopkeeper, hobo | 4 | Athletics 3, Scuffling 2 | 3 |
| Trained | cop, orderly, laborer, thug, gang member | 6 | Athletics 5 to 7, Scuffling 6, Weapons 4 | 3 |
| Dangerous | soldier, killer, expert fighter, cult enforcer | 8 | Athletics 8 to 9, Scuffling 8, Firearms 5, Weapons 7 | 4 |
| Creature | see below | by creature | Athletics, Scuffling, Weapons | 3 to 5 |

- **NPC tests.** An NPC acting against a character rolls a d6 from the stream plus the relevant rating against the character's Difficulty, or in a contest. Ordinary NPCs do not spend points; a named antagonist may spend up to 2 points per turn, noted in the GM-only notes. NPC pools may be recorded as ratings; the AI Master tracks the points they spend.
- **Social outcomes** between characters and NPCs use the characters' Investigative abilities, not NPC rolls. Crowds are handled in narration.
- **Creature statistics** (an adventure supplies them): Athletics, Health, Scuffling or Weapons, Hit Threshold, weapon modifier, armor, Alertness and Stealth Modifiers, **Stability Loss** (the additional loss over the standard one for sighting it, fighting it or watching its attacks) and special powers. A creature dies, vanishes or is banished when Health falls **below 0**. **Refresh:** a creature not encountered for 24 hours refreshes all pools except Health, which recovers d6 per day; one met again the same day refreshes only to half its ratings and no Health. A creature with two ratings by mode (land and air) loses or gains the extra points once only when it changes mode.
- **Keeping monsters fresh [craft].** Vary a creature's powers, spoor and behavior; stress the features that horrify most and contradict lesser details. The Mythos is protean.
- **Every NPC stat block** lives in the NPC's record. Update Health and attitudes as they change.

---

## 8. Era, craft and campaigns
<!-- for: turn, setup -->

### 8.1 The 1930s in play

- The decade is a desperate one: poverty and unemployment, hunger, the shadow of the Great War and the next one, race segregation, and the rise of totalitarian states. Use it as color, pressure and obstacle, not as lecture.
- Technology: telephones and telegrams, cars and trains, radio, flashbulb photography, Dictaphone cylinders, wire recorders, no computers. Searches take days. Records are on paper. A character cannot "look it up" faster than a trip to the library.
- Equipment is a matter of Credit Rating and plausibility (Preparedness, §3.2). Money matters at the lower classes and is narrative for the upper ones.

### 8.2 Craft notes for the Master

- **Design the horrible truth first, then the clue trail.** Each scene gives a core clue that points to the next, with alternatives so no single test or ability gates it. Include at least three ways to reach any essential piece of information.
- **Keep menace alive.** Something should happen to the Investigators even when they do nothing: a warning, a follower, a missing contact, a date on a clock.
- **Mix the idioms** with care: a Purist dread can hold a Pulp action scene; keep the tests honest.
- **Costs are the story.** The Mythos asks for Stability, Sanity, Health, rating points, friends and Sources. Give the players a choice at each price.
- **Do not let a scene end in a die roll.** The investigation moves on even after a failure.

### 8.3 Campaign frames and advancement

A campaign states its frame in the adventure or the host's setup: the group's premise, the build point totals, ability caps, a shared base, and what refreshes between cases. Advancement follows §4.10. In a campaign the AI Master tracks Sanity, Pillars, Sources and illnesses across cases and keeps the Credit Rating consistent.

---

## Appendix A. Sheet layout for this ruleset

The state contract fixes the outer shape of a character. This ruleset fills three fields as follows.

**`sheet`**
- `groups.investigative`: each Investigative ability as `{ "max": n, "cur": n }`, including Credit Rating and Cthulhu Mythos when above 0. An Occupational ability is marked in `sheet.derived.occupational` (a list of names).
- `groups.general`: each General ability as `{ "max": n, "cur": n }`, including Health, Stability and **Sanity**. For Sanity, `max` is the current rating and `cur` the current points.
- `derived.hit_threshold`: 3, or 4 with Athletics 8 or more. `derived.occupation` and `derived.occupational` as above.
- `unrated`: the abilities the character does not have.

**`ruleset_state`**
- `mode`: `purist` or `pulp`.
- `drive`: `{ "name": "...", "kind": "hard|soft", "secret": bool }`.
- `pillars`: `[{ "name": "...", "intact": bool }]`.
- `sources_of_stability` (module on): `[{ "name", "phrase", "unlocked": bool, "last_used_day": n|null }]`.
- `haven`: `{ "last_used_day": n|null, "breached": bool }`.
- `mental_illness`: `[{ "kind", "detail", "since_turn": n }]`.
- `mythos_tomes`: `[{ "title", "read": "skimmed|pored", "mythos_gain": n }]`; `spells`: `[{ "name", "difficulty": n, "cost": "...", "source": "..." }]`.
- `dedicated_pools`: `[{ "for": "...", "ability": "...", "max": n, "cur": n }]`.
- `risk_factor_paid`: a list of turns when a Drive cost was paid.

**`gm_only`** (never shown): `flags`, the true Sanity and Stability losses pending, hidden Drive details.

**NPC `base_stats` and `npc_state.stats`** use the tiers of §7: `tier`, `health`, `stability` (or `null`), `abilities`, `hit_threshold`, `weapon_mod`. A creature adds `armor`, `alertness_mod`, `stealth_mod`, `stability_loss`, `inertia` and `special` (a list).

**Game-level values** live in `game.gm_state`: `tension` (1 to 6), `heat` (0 to 7), `intensity` (`mild`, `moderate`, `severe`), `clock_steps`.
