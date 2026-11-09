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

> Paraphrased rules for running **investigative cosmic horror**; the single source for this ruleset's rule numbers, mechanics, tables and sheet layout. Precedence: world and secrets from the adventure; behavior and display from the protocol; rule numbers and house rules from this file; JSON shapes from the state contract. On conflict follow that order and never mention it to players.
>
> Left out on purpose: setting history, catalogue of gods and monsters, grimoire lists, price lists, sample adventures. An adventure supplies the creatures, books and spells it needs, with numbers, using §5 and §7. **[House]** rules adapt the game to AI-run, asynchronous, small-group play and override the published rules. Published-book tables may be used for anything not given here.
>
> **Idioms.** **[Purist]**: bleak, philosophical cosmic horror where learning the truth dooms the seeker. **[Pulp]**: desperate physical struggle where Investigators survive more often. Untagged rules apply to both. The adventure picks `mode: purist|pulp` (default Purist) and may borrow single rules from the other.

---

## 1. Core concept

- **Investigators** look into a mystery with a horrifying truth behind it. The tension is what a clue means and what to do about it, not whether it is found.
- **Investigative abilities** find clues and are **never rolled**. **General abilities** are rolled with a **d6** and can fail. Every scene holds information and points to another; the solution usually leads to a monstrous confrontation, often at a price.
- **Stability**: short-term resistance to shock; falls quickly. **Sanity**: long-term ability to keep believing the comforting lies of the human world; erodes slowly, in Purist never returns.
- **Truth rule.** The Mythos is real. What the adventure says is true is true. Never invent Mythos facts that contradict it, and never let a rational explanation erase an established horror.
- **Never broken.** (1) An essential clue is never lost to a roll or a missing ability. (2) Difficulties are chosen before the roll; dice are never fudged. (3) Warnings precede lethal danger.
- **Tone presets [House]** (adventure picks; default Purist cosmic): **Purist cosmic**: dread of what the universe is; slow reveals, few fights, firearms discouraged, Sanity loss permanent. **Pulp action**: dread of what hunts you; fights common and winnable, heroic gestures rewarded, Sanity may return after victories. **Noir investigation**: dread of people and corruption with the Mythos behind it; informants, bribes, bad weather, local power.
- **Formats [House]:** one-shot, miniseries (fixed arc over several stories) or campaign (§8.3).

---

## 2. Characters

- 1 (solo) to 5 characters, one Investigator per player. GM-run allies never roll or decide for a player character.

### 2.1 Building an Investigator
<!-- for: setup, check -->

1. **Occupation** (§2.2): still worked, or left to hunt the Mythos full time (poorer, more isolated). In a one-shot usually not quit.
2. **Drive** (§2.3): exactly one.
3. **Build points** (§2.1a): Investigative and General.
4. **Pillars of Sanity** and, with the module on, **Sources of Stability** (§2.5).
5. **Contacts** (§2.6), name, background, equipment and means in the style of the era.

### 2.1a Build points
<!-- for: setup, check -->

| Characters at the start | Investigative points each |
|---|---|
| 1 (solo) [House] | 26 |
| 2 | 24 |
| 3 | 18 |
| 4 or 5 | 16 |

- Party size is the number of characters at the start and stays fixed even if players join or leave.
- **General: 65 build points.** *Doomed specialists* variant (adventure's choice): 60 General and Investigative 16 (2 characters), 12 (3) or 10 (4 or 5); solo keeps 26. *Pulpier* variant: 75 General, standard Investigative.
- **Free ratings:** Sanity 4, Stability 1, Health 1, Credit Rating at the lower edge of the Occupation's band. Free Credit Rating points may be traded one for one into Investigative build points (down-and-out concept).
- **Cost.** 1 rating point = 1 build point. An **Occupational** ability (asterisk) costs half: 2 rating points per build point, so assign an even number (a leftover half point is lost). Fleeing, Credit Rating, Cthulhu Mythos, Health, Sanity and Stability are never Occupational (except Credit Rating for Dilettantes).
- **Fleeing discount.** Fleeing points above twice the final Athletics cost half (Athletics 0: all Fleeing). Decide Athletics first. Example: Athletics 2, Fleeing 8 costs 4 for the first 4 points and 2 for the next 4. May be refused to a plain fighter.
- **Credit Rating:** 1 per point up to the top of the Occupation's band, 2 per point above it (Dilettantes: no top). The adventure may cap it at the top of the band.
- **Cthulhu Mythos** cannot be bought at creation (never Occupational) unless the adventure says the characters already know something.
- **Balance.** The second-highest General ability (excluding Fleeing; Occupational General abilities at purchased value) is at least half the highest.
- **Caps.** [Purist] Health and Stability at most 12; Sanity at most 10 and never above 10 minus Cthulhu Mythos. [Pulp] 12 recommended.
- **Saving points.** Unspent points may be kept for later in a campaign; in a one-shot they are lost.
- **Trading [optional].** One Investigative point for 3 General, at most 3 Investigative for 9 General. State it in the validation block; checklist totals are counted after the swap.
- **Quick pick [House].** Investigative: many low ratings (1 is real expertise; rarely above 3 or 4) covering what the story likely needs. General: concentrate; Health and Stability 8 to 12 plus the defining ability.
- **Party [House].** Cover as many abilities as possible, give each Investigator a role. At most one combat expert and one occult or Mythos expert, each weakened somehow (retiree, washout, untrustworthy mentor).

### 2.2 Occupations
<!-- for: setup, check -->

Each lists Occupational abilities (half price), a Credit Rating band and a special benefit. The adventure may ban or limit Occupations. Only **Military** is closed to women even in a realistic game; era sexism may appear as color or underestimation, never as a ban.

| Occupation | Occupational abilities | Credit Rating | Special benefit |
|---|---|---|---|
| **Alienist** | Biology, Languages (German, Latin), Library Use, Medicine, Pharmacy, Psychoanalysis, Assess Honesty, two other Interpersonal | 3 to 4 | Medicine or an Interpersonal ability opens mental records and sanitarium wards; Medicine 2+ (licensed) also medical records and hospital wards. Psychological Triage at Difficulty 3; steadying an erratic character costs 1 Psychoanalysis point instead of 2; may buy Hypnosis. Assess Honesty works as forensic psychology (profile a perpetrator from a scene). |
| **Antiquarian** | Architecture, Art History, Bargain, History, Languages, Law, Library Use, one more Investigative | 2 to 5 | Once per adventure a relevant item is "back at the shop" (book, dagger, mask), recalled with a matching ability. Refuse abuse. |
| **Archaeologist** | Archaeology, Athletics, Evidence Collection, First Aid, History, Languages, Library Use, Riding, two other Investigative | 4 to 5 | Archaeology or an Interpersonal ability opens museum storage; Archaeology 2+ and Credit Rating 3+: university closed stacks. |
| **Artist** | Architecture, Art, Art History, Craft, Disguise, Flattery, Photography, Assess Honesty, two more Academic or Interpersonal | 1 to 4 | Meaningful downtime refreshes 1 pool point in an ability tied to the art, up to 4 times per story. |
| **Author** | Art, History, Languages, Library Use, Oral History, Assess Honesty, three others | 1 to 3 | Downtime reading refreshes 1 Academic pool point, up to 4 times per story. |
| **Clergy** | History, Languages (Latin, Greek, Aramaic or Hebrew), Library Use, Psychoanalysis, Assess Honesty, Reassurance, Theology, one other Interpersonal | 2 to 5 | Church records open to Theology or Reassurance. Once per story, talking with a co-religionist refreshes any Interpersonal pool. Triage at Difficulty 3. Psychoanalysis is not Occupational. |
| **Criminal** | Bargain, Intimidation, Locksmith, Scuffling, Sense Trouble, Shadowing, Stealth, Streetwise, one other Interpersonal or Technical | 0 to 4 | With pools in Conceal, Filch or Shadowing, spend points after rolling, 2 per +1, only when undistracted and unobserved and never in a contest. |
| **Dilettante** | Credit Rating, Flattery, Riding, any five abilities | 3 and up | The Credit Rating pool calls on personal connections in any field. |
| **Doctor** | Accounting, Biology, First Aid, Forensics, Languages (Latin), Medicine, Pharmacy, Assess Honesty, Reassurance | 4 to 6 | Medical records and hospital wards open. First Aid heals 3 Health per point (2 on self); stabilizing costs 1 point instead of 2. |
| **Hobo** | Athletics, Bargain, Filch, Outdoorsman, Sense Trouble, Stealth, Streetwise | 0 (no points allowed) | Reads hobo signs and a strange town; Streetwise reaches hobo contacts. |
| **Journalist** | Cop Talk, Disguise, Evidence Collection, Languages, Oral History, Photography, Assess Honesty, Reassurance, Shadowing, one other Interpersonal | 2 to 4 | Reassurance opens newspaper morgues; fellow journalists share off-the-record rumors. |
| **Military** | Athletics, Firearms, Intimidation, Outdoorsman, Scuffling, Weapons; plus a branch package (Army: Conceal, Driving, Stealth; Corpsman: First Aid, Medicine, Reassurance; Engineers: Driving, Explosives, Mechanical Repair; Navy: Astronomy, Mechanical Repair, Piloting; Officer: Bureaucracy, Riding or Piloting, Reassurance) | 2 to 5 officers, 2 to 4 enlisted | 2 Reassurance points steady a panicking character while the user's own Stability is above 0. Any Interpersonal ability opens one's own nation's military facilities. A combat veteran's combat Difficulties and opponents' Hit Thresholds do not rise by 1 from Hurt or shaken until Stability or Health is below -5, but Stability is capped at 10. |
| **Nurse** | Biology, First Aid, Medicine, Pharmacy, Assess Honesty, Reassurance | 2 to 4 | Medical access and First Aid bonuses as a Doctor. |
| **Parapsychologist** | Anthropology, Electrical Repair, Library Use, Mechanical Repair, Occult, Photography, Assess Honesty, Sense Trouble | 2 to 3 | May buy Hypnosis. |
| **Pilot** | Astronomy, Driving, Electrical Repair, Mechanical Repair, Piloting, Sense Trouble | 2 to 3 | Owns or regularly uses an airplane, as Credit Rating allows. |
| **Police Detective** | Athletics, Cop Talk, Driving, Evidence Collection, Firearms, Interrogation, Law, Assess Honesty, Sense Trouble | 3 to 4 | Cop Talk opens case files, evidence rooms and prisoners; in the home jurisdiction also lab and morgue. |
| **Private Investigator** | Accounting, Disguise, Driving, Law, Locksmith, Photography, Assess Honesty, Reassurance, Scuffling, Shadowing. [Pulp] hard-boiled variant: Cop Talk, Driving, Intimidation, Locksmith, Assess Honesty, Scuffling, Shadowing, Streetwise | 2 to 3 | Post-roll spending as a Criminal, for Disguise or Shadowing. |
| **Professor** | Bureaucracy, Languages, Library Use, one Interpersonal, three Academic | 3 to 5 | With intact credentials (Credit Rating 3+) Bureaucracy opens closed stacks, labs and many archives. Credit Rating 5+ is tenure. |
| **Scientist** | Electrical Repair, Evidence Collection, Languages, Library Use, Photography, two of Astronomy, Biology, Chemistry, Cryptography, Forensics, Geology, Physics | 3 to 5 | Access to a suitable lab; Credit Rating 3+ and a 2+ science: university closed stacks. |
| **Federal Agent** | Driving, Evidence Collection, Reassurance or Intimidation, Law, Assess Honesty, plus the agency's package (Treasury, FBI, Secret Service, Marshals) | 3 to 5 (cap 5) | Bureaucracy pulls strings in the agency; Law or Intimidation gets into almost any premises in US territory. |

- **New Occupation [House].** A variant swaps one or two abilities (Pilot becomes Sailor: Athletics for Driving). A wholly new one has 7 to 9 Occupational abilities, never Credit Rating, Cthulhu Mythos, Health, Sanity or Stability. Its special rule is privileged access to scenes and sources, or one small mechanical tweak.

### 2.3 Drives
<!-- for: setup, check -->

Exactly one Drive: a core desire worth more than life or sanity. Any Drive fits any character; suggested pairings in parentheses. Costs and refresh: §5.3.

| Drive | Essence |
|---|---|
| **Adventure** | Thrill-seeking; refusing a risk feels like admitting the life was meaningless (Criminal, Military, Pilot). |
| **Antiquarianism** | Only the past feels alive (Antiquarian, Archaeologist, Clergy, Professor). |
| **Arrogance** | Success will justify everything; petty rules and fears do not apply (Alienist, Scientist). |
| **Artistic Sensitivity** | Attuned to the numinous; must follow the Muse (Artist, Author, Dilettante). |
| **Bad Luck** | Things just happen to this person. Cannot be resisted, so no Stability penalty (Criminal, Hobo). |
| **Curiosity** | Cannot leave a mystery alone (Journalist, Police Detective, Private Investigator, Scientist). |
| **Duty** | Someone has to go down those steps; if not this person, who (Clergy, Doctor, Military, Police Detective). |
| **Ennui** | Everything else is exhausted; only the unnatural interests this person (Artist, Dilettante, Military). |
| **Follower** | Someone important went in; the character follows to protect them (a fellow Investigator or NPC). If that person dies the player may pick a new leader or switch to Revenge. |
| **In the Blood** | Strange behavior runs in the family. May be a **secret** Drive revealed in play. |
| **Revenge** | Something hurt this person's own and must be destroyed at any cost. |
| **Scholarship** | Uncovering truth, acclaim and the satisfaction of knowledge. |
| **Sudden Shock** | Something tore the scrim off the world; no going back. The player invents the shock (or opts for amnesia). |
| **Thirst for Knowledge** | Must learn the secrets of the cosmos. |

### 2.4 Pregenerated, provided and replacement characters [House]

- Routes: **generated** with the AI Master (§2.1), **pregenerated** (from the adventure) or **provided** by the player in any format. Whatever the route, produce the canonical record and run the §2.7 checklist.
- **Pregenerated** may swap Pillars, Sources or small details, not break budgets. One built for another party size is **rescaled** by trimming Investigative points only, highest ratings first, keeping each needed ability at 1+, telling the player exactly what changed; the adventure's own trim table wins. A character claimed by one player cannot be claimed by another. With none or too few, generate three to five on demand and save them unclaimed (`status: "pregen"`).
- **Late joiners** use the budgets for the party size at the start, get an in-world way into the story, and begin when the next turn opens.
- **Replacement** of a dead, Gone or committed character: newly generated, an unclaimed pregenerated one or an NPC marked available, arriving in the fiction within one or two turns, inheriting no knowledge, items or relationships.
- **NPC into character.** Keep name, role, trait, knowledge, inventory. Build the sheet from the NPC's tier (§7) and the §2.1a budgets, never above. The NPC stops acting as an NPC. A **main** NPC is never offered.
- **Other-system sheets** (other GUMSHOE games, *Call of Cthulhu*): map each entry to the nearest ability, keep totals within budgets, drop spells and powers, turn wealth into Credit Rating and narrative means, give a traceability table (original entry, result, note); show it and wait for approval. Imported pools start full.
- **A player who leaves:** the character becomes a GM-run ally who stays safe or departs plausibly.

### 2.5 Pillars of Sanity and Sources of Stability
<!-- for: setup, check -->

- **Pillars of Sanity:** one per 3 full rating points of Sanity; an abstract principle trusted implicitly (not a person or object). Examples: religious faith; family honor; human dignity; scientific progress; the laws of physics; the goodness of nature or of mankind; a moral code; high art; patriotism; love of a home town. A revelation undermining a Pillar costs extra Sanity (§5.4).
- **Sources of Stability** (module `sources_of_stability`, soap-opera campaigns): one named person (name and identifying phrase; not another Investigator, though several may share one at a risk) per 3 full rating points of Stability. Cultists and entities may use them. If harm comes to one, hard Stability tests and possible permanent loss of the linked rating points. One-shot: one Source at the start, others appear in play. Module off: Stability simply refreshes between stories.

### 2.6 Contacts and the intimate correspondent
<!-- for: turn, play, setup -->

- When a character uses Bureaucracy, Cop Talk, Credit Rating, Streetwise or any ability to call on a contact, the player supplies the contact's name, residence and connection. The size of the spend sets attitude, information value and position. Essential clues are always free. Reuse contacts as recurring NPCs who may ask favors, bring trouble or die badly.
- **Intimate correspondent [optional].** A mentor, protégé, relative or clergyman to whom the character confides everything; a briefed replacement seed if the Investigator dies or goes mad.

### 2.7 Character intake and validation [House]
<!-- for: setup, check -->

| # | Check | Passes when |
|---|---|---|
| 1 | Fit | Concept, Occupation, era and place fit the adventure's era, mode and tone. A banned Occupation or type is refused. |
| 2 | General budget | General points spent equal §2.1a (65 default): sum of General ratings, Occupational ones at half, minus free points (Health 1, Stability 1, Sanity 4). Sanity above 4 is bought from this budget. |
| 3 | Investigative budget | Points spent equal §2.1a for the party size at the start: sum of ratings, Occupational at half, Credit Rating only above its free lower edge (1 each up to the band top, 2 above). |
| 4 | Ability list | Every ability appears in §3. Hypnosis only for Alienists and Parapsychologists (and Pulp, by the adventure). Cthulhu Mythos 0 unless the adventure grants it. No spells at the start. |
| 5 | Occupational abilities | Each starred ability is on the Occupation's list, has an even rating, and is never Fleeing, Credit Rating, Cthulhu Mythos, Health, Sanity or Stability. |
| 6 | Credit Rating | Within the band, or paid double above it, and within any adventure cap. Hobo 0. |
| 7 | Balance | Second-highest General (excluding Fleeing) at least half the highest. §2.1a caps hold. |
| 8 | Fleeing | Fleeing above twice Athletics paid at half price, and the character is not plainly a fighter if the discount was used. |
| 9 | Professions | Law 2+ and Medicine 2+ imply a licence. If unlicensed the sheet says so and the character cannot practise or certify. |
| 10 | Pools | Every ability has max and current, equal at the start. Sanity 4+. Hit Threshold 3, or 4 with Athletics 8+. |
| 11 | Drive | Exactly one Drive of §2.3 with a clear trigger. |
| 12 | Pillars and Sources | One Pillar per 3 full Sanity points. Module on: at most one Source per 3 full Stability points (one-shot starts with one). |
| 13 | Means and kit | Money, transport and kit fit the era and Credit Rating. Weapons beyond a plausible kit are refused. |
| 14 | Appearance and content | Only the appearance the player supplied. Nothing conflicts with the truth rule. |

**Outcomes.** `pass`; `pass_with_adjustments` (smallest changes needed, each needing player approval); `fail` (violations and smallest fixes). Never silently change a sheet, except a plain arithmetic slip with one unambiguous correction, which is still reported. Never raise ratings to be generous. Play starts only after `pass` and the player's confirmation.

---

## 3. Abilities

**Investigative** abilities (Academic, Interpersonal, Technical) automatically yield clues when used reasonably; each rating point is also a pool for spends (§4.1). **General** abilities are tested with a die (§4.2).

### 3.1 Investigative abilities

**Academic**
- **Accounting:** read and keep financial records; separate honest business from crime; trace payments, embezzlement, bribes, dummy companies.
- **Anthropology:** artifacts and rituals of living cultures; customs of foreign groups and subcultures.
- **Archaeology:** date burials and buildings; identify artifacts and fakes; navigate ruins; find secret doors.
- **Architecture:** a structure's age, style, strength, alterations; hidden rooms and load-bearing elements.
- **Art History:** real from fake, dating by style, prices, artists' lives.
- **Biology:** animal and plant behavior and origin; tissue, ichor, slime; natural poisons.
- **Cryptography:** make and break codes; puzzle out unfamiliar alphabets.
- **Cthulhu Mythos:** the character has begun to piece together the secret rules of reality. Recalls facts from tomes read; reads the history of an artifact or relief at a glance. **Using it costs Stability and sometimes Sanity** (§5.4). Gives an insight pointing the investigation in the right direction, not necessarily the solution; a spend yields more specific, more dangerous answers.
- **Geology:** soils, minerals, strata, fossils; where oil, water and mines lie; natural hazards.
- **History:** obscure allusions; events by place; ancient scripts; dating and attributing manuscripts; period dress.
- **Languages:** each rating point is one more language spoken and read, possibly dead. The adventure may forbid occult tongues.
- **Law:** criminal and civil law of the home jurisdiction; legal risk and jargon; legal colleagues. 2+ may mean a bar-certified lawyer.
- **Library Use:** find information in collections, archives, correspondence; detect patterns, gaps, doctored records.
- **Medicine:** diagnose disease, injury, poisoning, frailty; elementary Forensics if allowed. 2+ may mean a licensed doctor.
- **Occult:** history of magic, superstition, sorcery; the tradition behind a ritual and its intended effect; paraphernalia, grimoires, symbols. Does not allow working magic. **With Occult and Cthulhu Mythos, recognizing a real Mythos ritual costs no Stability or Sanity.**
- **Physics:** experimental machinery, advanced and non-Euclidean mathematics, comprehending strange technology.
- **Theology:** religious practice and belief; orthodox against heretical; officiating a ceremony. No miracles. With Cthulhu Mythos, identifying a Mythos ceremony costs nothing.

**Interpersonal**
- **Assess Honesty:** tell if someone lies and, with a spend, why; cold-read marks. Con men, sociopaths, most sorcerers and brainwashed cultists may not register.
- **Bargain:** haggle, mediate, swap favors or information.
- **Bureaucracy:** navigate organizations; official information; false credentials. Not a catch-all: information better found by other abilities earns "do your own legwork".
- **Cop Talk:** police lingo; confidential information from cops; excusing minor infractions; favors.
- **Credit Rating:** operate within one's economic class (table below); buy, mingle, borrow, collect rumors. Both a class and a pool; behaves like eight abilities in one.
- **Flattery:** help by compliment; information, favors, trust.
- **Interrogation:** formal questioning of a subject who is confined or fears confinement and recognizes the questioner's authority.
- **Intimidation:** physical or psychological dominance to get information, make subjects leave or quell violence.
- **Oral History:** find sources, gather testimony, folklore, gossip; best in rural settings; shorthand and unobtrusive recording.
- **Reassurance:** put people at ease for information or favors; allay fear and panic.
- **Streetwise:** behave among criminals; unsafe places and dangerous people; fences, dealers, arms runners; underworld rumors.

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

Credit Rating is class and bearing, not a bank balance; bearing may drift one or two ranks from income.

**Technical**
- **Art:** music, painting, dance, sculpture, poetry, drama. Each rating point adds a medium. Great works need spends.
- **Astronomy:** astrological texts, telescopes, plotting stars, predicting eclipses and comets.
- **Chemistry:** with a lab, identify drugs, toxins, substances; make simple explosives, poisons, gases, acids; ballistic, ink and soil analysis.
- **Craft:** make useful objects in wood, metal, jewelry; may find hidden drawers.
- **Evidence Collection:** default search ability: hidden objects, sequences of events, fingerprints, typewriter and handwriting matches, uncontaminated storage.
- **Forensics:** crime scenes and autopsies; skeletal analysis; weapon, time of death, intoxicants, last meal.
- **Locksmith:** open locks, disarm alarms. A lock hiding a clue simply opens; only safes and locks that exist to create drama need a test.
- **Outdoorsman:** live and work outdoors; strange animal behavior; hunt, forage, navigate, track.
- **Pharmacy:** identify and compound drugs; side effects; poisons and antidotes; controlled substances.
- **Photography:** record scenes; develop, enhance, filter film; spot retouching; trick photographs.

Overlap is expected: a clue may be reachable by several abilities. If the player's reasonable use matches a clue, give it; the ability need not be named.

### 3.2 General abilities

- **Athletics:** physical derring-do not covered elsewhere. **8 or more gives Hit Threshold 4**; otherwise 3.
- **Conceal:** hide things; search for things hidden on purpose.
- **Disguise** (also Investigative): alter appearance, posture, voice; cover identity; brief misrepresentation. Impersonating a known person is very hard: voice only Difficulty 4; face to face a Difficulty 7 test every five minutes of sustained contact.
- **Driving:** skilled driving, evasion, pursuit, minor repairs. Every 2 further points add a vehicle type.
- **Electrical Repair** (also Investigative): build, repair, disable, use electrical devices; tap lines; judge workmanship.
- **Explosives** (also Investigative): defuse, handle, make explosives; reconstruct a bomb from debris.
- **Filch:** pick pockets; pilfer clues from or plant clues at scenes.
- **Firearms:** guns and similar trigger weapons, repair, identification. [Pulp] 2 Firearms points allow a long-range pistol shot (or rifle up to 500 yards); with Firearms 5+, 1 point fires two pistols in one round, one target's Hit Threshold rising by 2.
- **First Aid:** treat injury (§4.7); basic poison control.
- **Fleeing:** running away; substitutes for Athletics in escapes; never helps pursuit.
- **Health:** take injury, resist infection and toxins; can drop below 0.
- **Hypnosis** (Alienists and Parapsychologists only; usually [Pulp]): willing subjects only, one at a time. Simple trance Difficulty 3; analytic rapport 3 (adds 3 to the user's Psychoanalysis pool against that patient); recover memories 4 (reliving costs the patient the same Stability again); post-hypnotic suggestion 4+ (one simple action, never against the patient's nature); ease pain 4+ (removes Hurt penalties until wounded again); implant false memories: contest of the user's Hypnosis (Difficulty 5) against the patient's Stability (Difficulty 4), unethical, undone by a later collapse.
- **Mechanical Repair** (also Investigative): build, repair, operate, disable mechanisms; each point adds a heavy machine; clear a jammed gun at Difficulty 4.
- **Piloting:** small boats or single-engine light aircraft; every 2 further points add a craft type.
- **Preparedness:** pack a kit. A simple test (§4.2) produces a credible item. Items any investigator would carry (notebook, flashlight, matches, chalk, tools, magnifying glass, string, sandwiches, brandy) need no test. Abilities imply their gear. Anything that would make the table laugh is out.
- **Psychoanalysis:** comfort and perspective for the troubled; calms the panicked, restores Stability (§5.7), treats long-term illness (§5.6).
- **Riding:** horses, donkeys, mules; every 2 further points add an animal.
- **Sanity:** never tested, never spent; eroded by the Outside (§5.4). At 0 the Investigator becomes an NPC. Free: 4.
- **Scuffling:** hand-to-hand, including blackjacks, brass knuckles, saps.
- **Sense Trouble:** perceive danger by any sense. **The Difficulty is never known before the player decides how much to spend.** Never require it to find a clue (use an Investigative ability, default Evidence Collection); it is for action: if not noticing gets you attacked, it is Sense Trouble.
- **Shadowing:** follow suspects unseen; lose a follower.
- **Stability:** resistance to mental trauma (§5). Free: 1.
- **Stealth:** move quietly, hide, evade watchers, eavesdrop at doors.
- **Weapons:** skilled use of hand weapons such as knives, swords, whips.

Disguise, Electrical Repair, Explosives and Mechanical Repair double as Investigative abilities in some circumstances but are bought and rolled as General.

---

## 4. Core mechanics
<!-- for: turn, play -->

### 4.1 Clues

- **Gathering is automatic.** The character must be in a scene where the information exists, have the right ability and say it is used. The player may be specific ("Art History on the idol"), speculative ("Oral History to find the town drunk"; the AI Master may swap the planned source) or general ("Evidence Collection on the alley").
- **Essential (core) clue:** needed for the next scene; always found; tell a suitable Investigator it is available even if nobody asks; never tied to an obscure ability. **0-point clue:** free atmosphere. **Spend clue:** bonus for 1+ pool points. **Inconspicuous clue:** noticed without searching; the Investigator with the highest current pool in the ability finds it (ties: higher rating; then both); default Evidence Collection. **Simple search:** anything an ordinary person finds by looking where the player says needs no ability. **Floating clue:** not tied to a scene; release it to unstick play.
- **Spends.** A clue may allow a 1- or 2-point spend for a special benefit: advantage in a later contest, favorable impression on an NPC, a flashback, resolving a moral dilemma without violence, speeding the investigation, a dedicated pool point, a notable work, or refreshing Stability (§5.7). Spend information is flavor, never required. With no benefit the points are not lost. Investigative spends can also lower a General test's Difficulty by 1.
- **Dedicated pool points** are extra points usable only in one circumstance or on one subject (tomes, communion with alien perceptions, mental illness); they stack on the rating for that use only.
- **Interpretation is the game.** Clues need not be true, and they point on.

### 4.2 Tests (General abilities)

Called only when the outcome is in doubt and failure matters; otherwise the action succeeds, with optional bonus spends.

1. The player may spend any number of pool points from the ability, +1 each, **before** rolling.
2. Roll one d6 and add the spend. Meet or beat the **Difficulty (2 to 8, default 4)**: success. 2 is a slim chance of failure; 8 verges on impossible. Tests that move the story forward are 4 or lower; high Difficulties are for optional obstacles.
- The ability must be 1+. **No retry** unless the character credibly improves the odds and spends more points than the previous attempt.
- **Hidden Difficulty.** [Purist] never revealed. [Pulp] may be revealed for conventional obstacles, never for Sense Trouble.
- **Success at a cost** for a must-pass obstacle: the action succeeds and the test sets the price (the fence is climbed but the character is cut).
- **Cooperation:** the leader tests and spends normally; an assistant may spend any number of points, **all but one** adding to the leader's roll. **Piggybacking:** a group appoints a leader; every other participant pays 1 point from the relevant pool and takes part; each who cannot pay raises the Difficulty by 2.
- **Light, weather, terrain** shift Difficulty by 1. **Surprise:** +2 on the surprised character's next test [House].
- **Declared spends [House, asynchronous].** Spends are those declared in the action or the standing orders (§6.4), +1 each before the roll. Never apply more than declared or than the pool holds.
- **Dice [House].** The AI Master rolls every die from the server's dice stream, in order. Each roll is reported without its Difficulty (revealed afterwards if asked): ability, spend, die, total, outcome (success, narrow success, failure, narrow failure).

### 4.3 Contests and chases

In a **contest** two characters actively oppose each other and **the first to fail a test loses**. Whoever bolts or strikes first acts first; if simultaneous, the lower rating acts first; ties: NPCs before Investigators. Each tests at Difficulty 4 unless the odds are unequal (significant advantage lowers, major handicap raises). Raise your own Difficulty to raise the pursuer's (dangerous terrain). Narrate each result.

- **Prolonged chase:** the pursued loses only after failing two or three more tests than the pursuer. **Relentless pursuer:** lower the Difficulty, but the characters make three tests per pursuer test.
- **Investigative contests** are rare (Bargain at an auction, Assess Honesty at a card table), used only when as dramatic as a fight. The opponent's pool is at most 1 higher; defeat never stalls the plot (a cooler NPC, a warned enemy, a worse route).
- **Being questioned by an NPC.** Casual pumping: the player notices with Assess Honesty and chooses what to say. Official or hostile interrogation is a plot device, not a contest.
- **Escape pool [House, optional]** for a trapped group: start 0; add 1 to 3 per way-out clue, +1 per relevant Investigative spend, +1 per successful relevant test; Difficulty 6 plus 2 per escaping character; one attempt per turn; failure empties the pool and triggers a hazard.

### 4.4 Fighting

Scuffling against Scuffling or Weapons, Weapons against Weapons, Firearms against Firearms at range. In Purist a fight is a failure state or threat, not the solution.

- **Aggressor and defender.** The aggressor acts first. If unclear, compare current pools in the abilities used; the higher may choose. **Free-for-all:** rank everyone by current pool in their starting fighting ability (ties: higher rating, then Investigators before creatures); a full pass is a round; order stays fixed. A combatant doing something else (runs, climbs, throws a grenade) moves to last.
- **Hit Threshold.** Difficulty to harm someone: **3**, or **4** with Athletics 8+. Less competent NPCs may have less, creatures often 4+, very large creatures 1 lower than man-sized. [Pulp] faceless mooks 2 or 3; Mythos creatures keep their values.
- **Damage.** On a hit roll a die plus the weapon modifier and subtract from Health. Pool points cannot be spent on damage. Fighters are not "out" on a failed roll; they are forced out by unconsciousness or serious wounds.

| Weapon | Modifier |
|---|---|
| Fist, kick | -2 |
| Small improvised weapon, blackjack, nightstick, knife | -1 |
| Big improvised weapon, machete, heavy club, light firearm | 0 |
| Sword, heavy firearm | +1 |
| Very heavy firearm (big-game rifle, automatic rifle) | +2 |

- **Firearms.** +2 at point-blank. Shotguns count as heavy at point-blank, light at near range; both barrels of a double-barrel add +1 at point-blank or close. Light, +0: .32 pistols and revolvers, .22 and 20-gauge guns, small carbines. Heavy, +1: .38 and .357 revolvers, .45 and 9 mm automatics, 12-gauge, combat and sporting rifles, submachine guns. **Automatic fire:** +2 Firearms pool points (+3 with a drum); after a burst the shooter stops a round to reload; a 1 on a submachine gun jams it (Mechanical Repair, Difficulty 4). [Pulp] a full-auto shooter may hit several targets within close range, each after the first raising all Hit Thresholds by 1. **Ammunition:** [Purist] a Firearms roll of 1 means the gun is empty; [Pulp] reload only when dramatic; when it matters, a Firearms test at Difficulty 3.
- **Range.** Point-blank (arm's reach); close (same room, ~10 yards); near (30 to 40 yards, limit for pistols and shotguns); long (to 100 yards, limit for rifles).
- **Cover.** Exposed: Hit Threshold -1. Partial: no change. Full: +1.
- **Armor** subtracts from each instance of damage it is effective against; rare: Great War helmet (-2 against bullets and blades, -1 blunt, head shots only); heavy coat may take 1 from small blades and fists; gangster vests take 2 from bullets and clubs and cost 1 Athletics point while worn.
- **Untrained** (no Firearms, Weapons or Scuffling): damage -2 more, must declare the action at the start of each round and goes last; a 1 with a gun hits an ally or the shooter.
- **Non-lethal Scuffling** never lowers Health below -11 but forces another consciousness roll. Firearms are never non-lethal.
- **At the mercy of an armed person.** Someone with a gun well in hand, or charged from over 5 feet without cover, may empty it first: automatic hit (Difficulty 1; 2 if the target has Athletics 8+ and moves), one damage roll tripled. Jumping a person whose gun is not ready is a Scuffling contest for the gun.
- **Explosions.** Setting a charge needs Explosives. Added damage by range (point-blank, close, near): Molotov cocktail +1, 0, none; pipe bomb +2, +1, -1; stick of dynamite +3, +2, -2; bundle of dynamite +7, +4, -1; grenade +3, +1, -2; land mine +8, +3, -1; gas main +9, +5, 0. Throwing a grenade is an Athletics test: Difficulty 2 point-blank, 3 close, 5 near, +1 or +2 to aim at a spot. Explosions usually start fires.
- **Optional realism [House]:** a gunshot to a human that would leave Hurt leaves Seriously Wounded instead; a gunshot taking Health to 0 or below deals +6 more. Monsters unaffected. Recommended in Purist with lethality `high`.
- **Restraint and ejection [House].** Being held, thrown out or arrested by guards, staff or police is narrative: an Athletics or Fleeing contest at Difficulty 3 plus the number of restrainers. Consequences: ejection, ban, report, bruise, a night in a cell; never automatic death.
- **Vehicles.** A driver in a firefight may spend 1 Driving point per round to avoid serious damage; shooting tires or the engine of a moving vehicle raises Hit Threshold by 2; fuel tank armor 2, engine block 4; only in a very pulpy game does a hit tank explode.

### 4.5 Other dangers

- **Acid:** damage each round (weak -2, strong 0, very strong +1) until removed; roll once and reuse.
- **Extreme temperature:** treat as Hurt. **Fire:** torch -1, bonfire 0, burning room +1; a burning character takes damage at 0 each round until extinguished. Smoke follows the drowning rule.
- **Drowning and suffocation:** with warning, hold breath; Athletics test each round (Difficulty 3, +1 each round); on failure lose d6+1 Health per round.
- **Falling:** damage equals the wall's Difficulty; +2 for spikes or jagged rock. Avoid a story where one failed test kills an Investigator.
- **Poison:** set onset, symptoms, lethality. Instant death is for NPCs; an Investigator gets a chance to reach a Pharmacy or Medicine spend unless the poison is implacable.
- **Environmental hazards [House].** Lingering hazards (bad air, smoke, cold, exhaustion) use stages. Cues first (at least two distinct signs before Stage 2); **1 Uneasy** (discomfort; Sense Trouble can identify it); **2 Unwell** (Health test Difficulty 4 each further half hour; failure costs 1 Health and +1 Difficulty); **3 Impaired** (Difficulties +2, a Stability test); **4 Collapse** (unconscious; 2 Health per 10 minutes until carried out). No instant death; always a way out.

### 4.6 Time, scenes and clocks [House]

- Play is divided into **Blocks** (parts of an in-world day) and **turns** (the interval at which the AI Master resolves all actions). Each Investigator has the Blocks the adventure's clock gives. A long action (an evening of research, a night's rest) costs a Block; a brief one (telephone call, a few notebook lines) costs none.
- The adventure may keep a **clock** (dates, countdown, escalating phenomenon). Time-sensitive events fire on their dates whether or not the characters are there.
- **Fail forward.** A failed test costs time, access, trust, safety or evidence; it never halts the investigation or erases an essential clue.

### 4.7 Injury and death

- **Health can fall below 0.** Below 0 make a **consciousness roll**: d6 against Difficulty equal to the absolute value of current Health (before any extra loss). The player may voluntarily lower Health further for +1 per point (not below -11).
- **0 to -5: Hurt.** No permanent injury; no Investigative spends; all Difficulties, including opponents' Hit Thresholds, +1.
- **-6 to -11: Seriously Wounded.** Consciousness roll required; conscious or not, cannot fight; lose 1 more Health every half hour until First Aid.
- **-12 or lower: dead** (subject to §4.8).
- **First Aid.** Hurt: 1 point heals 2 Health (1 on self; Doctors and Nurses 3 and 2), up to the Health before the incident; the healer gives full attention. [Purist variant] never above one third of maximum. Seriously Wounded: 2 points stabilize (1 for Doctors and Nurses) but restore nothing. Convalescence: days equal to the lowest negative Health reached; on discharge Health is half the maximum, full the next day.
- **Rest** restores 2 Health per day.
- **NPC Health.** [Purist] NPCs lose Health as Investigators do; key NPCs follow the Investigator rules. [Pulp] ordinary NPCs die below 0. Creatures die, vanish or are banished below 0 unless their entry says otherwise.

### 4.8 Lethality in this ruleset [House]

The game's `lethality` setting decides when the "dead", "Gone" and Sanity 0 conditions of §4.7 and §5 apply.

| Level | Health, Stability and Sanity reach the bottom |
|---|---|
| `low` | The character does not die. At Health -12: Seriously Wounded and out of the story in care. At Stability -12: Gone only if the player chooses at a decision gate, otherwise Shattered and incapacitated. At Sanity 0 the player may choose retirement to an institution instead of becoming an NPC. |
| `moderate` | Dead at Health -12 and Gone at Stability -12, but only after a warning cue and a decision gate or a chance to withdraw. Without them, stop at -11 and apply the Seriously Wounded or blasted state. |
| `high` | Dead at Health -12 and Gone at Stability -12 after a clear warning cue, no gate. At Sanity 0 the character becomes an NPC. |

Absent, paused and away characters are never taken to the bottom at any level (§6.4). Death or Gone starts the replacement offer (§2.4).

### 4.9 Regaining pool points

- **Investigative pools** refresh at the **end of each case**, regardless of in-world time.
- **Haven** [House]: an hour of genuine safety (bolted room, quiet pew, locked carrel) refreshes up to **3 General abilities, not Health, Sanity or Stability, once per in-world day** per character. A breached Haven is lost.
- **Physical abilities** (Athletics, Driving, Firearms, Fleeing, Piloting, Riding, Scuffling, Weapons) refresh fully after 24 game hours without spending. Other General abilities refresh at the end of the case.
- **Health** 2 per day of rest.
- **Stability** is refreshed by Sources (§5.7), indulging a Drive (§5.3), Psychological Triage and Confidence; between cases it recovers automatically unless the Sources module ties it to time with them.
- **Asynchronous [House].** A Haven or Source reconnect must be declared in the action; long costs a Block, brief none. Once-per-day limits still apply.

### 4.10 Improving an Investigator
<!-- for: turn -->

At the end of each case each player gets **2 build points per session played** (adjust for the number of turns in the story) to spend one for one on Investigative or General abilities, new or existing, or to reassign 1 or 2 points as atrophy. Never on Credit Rating, Cthulhu Mythos or Sanity. Credit Rating may be adjusted for treasure, decoration, ruin. [Purist] nothing improves the Investigator, but reassigning points is allowed.

---

## 5. Stability, Sanity and the Mythos
<!-- for: turn, play -->

### 5.1 The two scores

- **Stability** is the mental Health pool: resistance to any trauma, natural, human or supernatural. Falls quickly; normally refreshes between cases.
- **Sanity** is the capacity to believe in, fear for or care about the human world. Never spent, never tested. Erodes slowly, one or two points per case unless the character meets a god, loses a Pillar or suffers the big reveal. [Purist] never returns.
- Stability: how close to snapping today. Sanity: how close to seeing the Truth forever. A character can be steady and nearly gone (high Stability, low Sanity) or fragile and whole.

### 5.2 Stability tests

When an incident challenges the character's grip, make a **Stability test at Difficulty 4**. The player may spend Stability points before rolling. **On failure the character loses the incident's points** as well as the points spent. Name tests by potential loss ("a 4-point Stability test").

- **Mythos shocks** are at least +1 Difficulty; most Mythos entities cost more (their entries say so).
- **Experience.** Difficulty 3 for the inured (nurse among the mutilated, soldier among the dead); 5 for the especially susceptible.
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

**Role-playing instability** (no mechanical effect above 0): 1 or 2 points: twitch, stutter, rising voice; 3 or 4: hyperventilating, sweating, runaway talk, comforting rituals; 5 or 6: fugue, frame drop, hyper-alert to triggers; 7 or 8: adrenaline shock, tunnel vision, babbled confessions. Interpersonal abilities work through fear.

### 5.3 Drives and Stability

Tell the player when the Drive impels the character. The player need not obey, but **resisting costs Stability automatically, no test**.

- **Hard driver** (written into the scenario or invoked at will): resisting costs **4 Stability or one third of the pool, whichever is greater**; obeying refreshes **2**.
- **Soft driver** (tangential situation): resisting costs **2**; obeying refreshes **1**.
- Gains never exceed the Stability rating. Grant the refresh only if obeying advances the story or puts the Investigator in grave peril.
- **Bad Luck** cannot be resisted. When the universe hoses that Investigator more than others, give a Stability reward as if obeying.
- **Asynchronous [House].** Put the temptation in the facts and a `risk_factor` prompt in the result; the player answers in the next action. If an action abandons a person or danger the character knows about and the Drive is hard, the cost is paid when the action is carried out, after a decision gate unless the player was already warned.

### 5.4 Losing Sanity

Sanity cannot be tested to avoid. It is lost by a **Mythos shock** that takes Stability to 0 or below, or by **using Cthulhu Mythos**. Beholding a god or titan, and some spells, also cost Sanity (entries say so).

- **Mythos shocks.** Shaken (Stability 0 to -5): Sanity rating -1. Blasted (-6 to -11): -2. Only the worst such loss applies in one investigation.
- **Using Cthulhu Mythos.** Costs Stability and, if terrifying enough, Sanity, with no test. The loss depends on the revelation, not the pool points spent. Do not enforce a loss if the player deduces the truth without the ability; any player may ask for the loss to confirm a deduction. Loss cannot be denied away.

| Revelation or intuition | Stability | Sanity |
|---|---|---|
| Some aspect of the Mythos is behind this mystery; specifics comfortably distant or not immediately relevant | 2 | 0 |
| A clear and present danger to innocents; the truth goes deeper, farther or wider than believed | 3 | 1 |
| A clear and present danger to you or your loved ones; global or epochal scope | 4 | 1 |
| Shatters one of your Pillars of Sanity | 6 | 2 |
| Could destroy the world (or is doing so, probably inevitably); proves your Drive meaningless or doomed | 8 | 3 |

- **Pillars.** After losing 3 Sanity the player may decide a Pillar has crumbled from within, avoiding the shock of its destruction. [Pulp] may happen repeatedly. A character who loses the **last Pillar** (or whose Sanity falls to 2 or below) survives on instinct: all Stability tests +1 Difficulty.
- **Lost Drives.** If a revelation proves the Drive meaningless, no more Stability from it, but still lose Stability for not following it.
- **Denial.** At the end of an adventure with no proof (no samples, photographs, artifacts), may restore 1 Sanity rating point. May demand a delusion, amnesia or cover memory. Acting on the knowledge again costs the point back. Impossible once Sanity has hit 0.
- **Fainting.** The player may declare the character faints rather than absorb a Mythos experience: lose only 1 Sanity pool point and take no further part in the scene. Not for the cost of casting spells or using Cthulhu Mythos. The unconscious body may suffer dreadful things, but offer a way to learn its fate and do not kill it outright.
- **Sanity 0.** The character becomes an NPC: locked away, or a willing servant of the Mythos (subject to §4.8).
- **Mythos rating and Sanity.** With any Cthulhu Mythos rating, Sanity is at most 10 minus the rating; excess points are lost when the rating rises.

### 5.5 Coming unstrung

- **0 to -5: shaken.** Can work but cannot spend Investigative points; all General Difficulties +1.
- **-6 to -11: blasted.** May give a mental illness (§5.6) that outlasts the loss. Can only panic-flee, attack perceived dangers frenziedly, or do nothing colorfully (gibber, go catatonic). **Permanently lose 1 Stability rating point** (may be rebought).
- **-12 or lower: incurably insane (Gone).** One last act (self-destructively heroic or destructive) or a drooling check-out, then a sunny hospital; make a new Investigator (subject to §4.8).
- Returning to 0 or above ends shaken.

### 5.6 Mental illness

- **Shell shock** (mundane or merely supernatural incident): constant anxiety and dreams. When a sense recalls the incident, a Stability test at Difficulty 4 or freeze 15 minutes and be shaken 24 hours; the test costs no Stability.
- **Mythos madness** (Mythos incident): choose (or roll, dropping the two least appropriate). **Delusion** (a mundane thing does not exist; everyone denies it). **Homicidal mania** (told another Investigator is a monster). **Megalomania** (failures narrated as success; the group tells the truth later). **Multiple personality** (another player voices the character under stress). **Obsession** (4 pool points become dedicated to the obsessive object). **Paranoia** (others seem to hide something). **Phobia** (a stimulus from the event; Sense Trouble tests). **Selective amnesia** (a real event is forgotten). For players who dislike collaboration, agree a non-collaborative disorder in advance. Asynchronously, apply the effect through reported facts and player-visible state.
- **Curing.** With Psychoanalysis, a prologue scene at the start of each case tests Difficulty 4 ([Purist] twice the patient's Cthulhu Mythos rating or 4, whichever is higher). After three consecutive successes and three consecutive cases with Stability above 0 the illness vanishes; a new illness brings the old one back. Therapy can replace a shattered Pillar or disproven Drive (one at a time) and build **false Sanity** equal to half the lost Sanity, capped at 10 minus Cthulhu Mythos; the next loss of 2+ destroys it, and using Cthulhu Mythos negates the therapy.
- This simulates Lovecraftian fiction, not real psychology.

### 5.7 Refreshing Stability during play

- **Psychological Triage.** With Psychoanalysis a character may spend points to help another. The healer takes no other action and tests at **Difficulty 4** (3 for Clergy and Alienists); on failure no retry for that character until he loses more Stability. Each Psychoanalysis point spent (not test spends) gives the recipient **2 Stability**. An erratic mentally ill character gains lucidity for the rest of the scene from 2 Psychoanalysis points (1 for an Alienist) and a Difficulty 3 test.
- **Source of Stability** (module on): reconnecting refreshes 2 Stability, once per Source per in-world day.
- **Confidence [Pulp]:** if a player's suggested spend impresses the AI Master, roll a d6 and refresh that much Stability, once per player per story.
- **Selfless aid or inspiring feat [House]:** a d6 of Stability, up to the rating.
- **Big reveal [Purist, optional module `big_reveal`].** The key Lovecraft moment: the character pieces together the Mythos and goes to pieces. Afterward **no Drive**, immediate loss of **8 Stability** (or triple the normal loss), Sanity loss doubled. Almost always the end of the Investigator's story (institution, death, or at Sanity 0 a future villain). In Pulp it is merely the solution.

### 5.8 The Cthulhu Mythos and magic

Lovecraftian magic is alien science, garbled knowledge, or a focus for psychic power; belief does not change the effect. Helpful human magic is rare; magic is generally aimed at the Investigators. The adventure supplies tomes, spells and entities with numbers; this section gives the rules (module `mythos_magic`).

- **Tomes.** A **clue tome** holds a fact, spell or requirement the story needs; a **resource tome** is kept for general information. **Skimming** a clue tome takes about 1 hour per 100 printed pages (10 handwritten); a 1-point Library Use or Languages spend halves the time, a 2-point spend finds the vital fact in minutes. Skimming gives no Cthulhu Mythos points. **Poring over** a resource tome, usually between cases, grants its Cthulhu Mythos points all at once the first time (major tome +2 to +4, minor +1) and may teach spells. Foreign-language tomes need Languages. Dedicated pool points from a tome: the adventure decides.
- **Learning a spell:** 1 to 6 hours in play (Physics, Languages, Archaeology or Art spends can shorten it) and a Stability test, usually Difficulty 4. Learning by epiphany or communion is instantaneous.
- **Casting.** An **incantation** is a simple test, usually Stability, with a Difficulty and cost per spell. A **ritual** is a contest, usually against a summoned creature or the fabric of space-time, which resists with an **Inertia pool** the spell gives. Almost all spells cost pool points, usually Stability; another ability can pay at twice the cost. **A failed spell costs half.** Several casters who know the spell cooperate under §4.2; participants who do not know it pay 3 points to add 1. Unless noted, no spell is cast while fighting or fleeing. **Casting counts as a Mythos shock** if the Stability loss costs Sanity. A caster with Sanity 0 never tests for incantations and pays Stability and Health at half cost.
- **Summon and bind.** Summoning is an incantation; a failed Stability test may mean the creature recognizes a weak master and attacks. A binding forces the creature to follow one specific, limited instruction ("leave", "kill that wizard"), takes 2 rounds, and is a ritual (Stability against Inertia) if the creature is present. Seeing a summoned creature is a Stability test for the caster and witnesses.
- **Generic spell forms:**
  - **Contact [being]:** Difficulty 4 to 5; about 3 Stability (and 1 Sanity for a god); minutes to hours; the being or its servants answer by dream, vision or arrival within a day.
  - **Elder Sign:** seals a path against servants of the Great Old Ones, engraved on an object or threshold; Difficulty 4; 1 Stability rating point; five minutes. An amulet does not protect the wearer.
  - **Voorish Sign:** makes invisible things visible for five minutes; Difficulty 5; 1 Stability plus 1 Sense Trouble or Evidence Collection.
  - **Powder of Ibn-Ghazi:** makes one invisible being visible for ten heartbeats; compounded at Difficulty 3 (2 with Chemistry or Occult); 1 Stability or 2 Chemistry or Occult per vial.
  - **Create gate:** Difficulty 5; 2 Stability or 4 Health, doubled per step of distance (continental, global, interplanetary, interstellar, intergalactic); each 4 Health spent also costs 1 Health rating.
  - **Enchant item:** Difficulty 5; 3 Stability and at least 1 Stability rating point; weeks or months; each further rating point sacrificed adds 1 to casting and 1 dedicated pool point in a ritual.
  - **Call or dismiss a deity:** a ritual; calling a god is nearly always a terrible idea; seeing it is a Stability test with a minimum of 6 points plus its own extras; the Inertia pool is large (typically 8 to 35+), stated by the adventure.
- **Creating a tome or spell for an adventure.** Say what it does, its price in Stability, Sanity, Health or rating points, Difficulty, time, and what failure does. A spell that solves the mystery alone is not allowed; magic is a price, a hook or a weapon aimed at the Investigators.

---

## 6. Solo and party play (asynchronous)
<!-- for: turn, play, setup -->

### 6.1 Solo [House]

1. **One viewpoint.** Every thread is narrated through the Investigator. No cutaways.
2. **Allies advise and assist; the character decides.** A GM-run ally never rolls for the player, overrides a choice or solves a problem the player has not engaged with.
3. **Spotlight is automatic.** Spend the freed attention on deeper NPCs and consequences, not filler.
4. **Own pace.** With early close on, the turn resolves when the player has used the Blocks intended.
5. **The clock is real.** An Investigator cannot do everything.
6. **Fail forward, not fail free** (§4.6).
7. **Honest and fair.** Never fudge a roll; Difficulty set before the roll; warnings precede lethal danger.
8. **Death and ruin.** If the Investigator dies, is Gone or at Sanity 0, present it with weight, resolve what happens to the people at stake and the evidence, then offer a replacement, debrief or restart. Do not silently reverse it.
9. **Pacing.** About 12 to 16 meaningful scenes: investigation first, then the build, then the finale and a short epilogue.

### 6.2 Party [House]

1. **Parallel threads.** Every character acts every turn. Group characters by place into threads and resolve each. Give every player a result of similar weight and a hook for the next turn.
2. **Splitting the party** is allowed; every thread resolves every turn.
3. **Group tests.** A test affecting everyone (stealth, scares) is rolled by each affected character separately, separate dice. Helpers follow §4.2.
4. **Disagreement.** Players may argue in character; do not resolve it for them.
5. **Shared knowledge.** Knowledge moves between characters only in the fiction (speaking, message, document) and arrives as hearsay tagged with its source.
6. **Per-character state.** Pools, Pillars, Sources, illnesses, Drives tracked per character.
7. **Group size.** Budgets come from the party size at the start (§2.1a).

### 6.3 Resolving conflicting actions [House]
<!-- for: turn -->

One world, one truth. Order first, dice second. Nobody's action is dropped.

1. **Block order.** An earlier Block resolves first; later Blocks see its results.
2. **Cause and effect.** Inside a Block, an action that changes what another depends on resolves first.
3. **Claim.** Whoever holds the item, occupies the place or has the NPC's attention has the claim; a challenger must win an opposed test.
4. **Priority roll (ties only).** Each tied party rolls a d6 from the stream; higher first; re-roll ties.
5. **Cooperation.** Two characters on the same task: cooperation under §4.2, the higher rating leads.
6. **Competition.** For one unique thing (only copy of a document, only car): first in time gets it unless the other acts against it; at the same moment, an opposed test (d6 plus rating plus declared spends); ties go to the holder or whoever was there first.
7. **Opposition.** One character stopping another is a contest under §4.3, or for a single action opposed totals; ties go to the defender.
8. **Contradiction.** If two actions assume incompatible facts, the database and the fiction decide. Each character perceives the truth from their own position, and one may be wrong.
9. **Player against player.** Follow the game's `pvp` setting. `none`: no harm or coercion between characters, only argument, refusal, withholding; obstruction is friction (delay, Difficulty +1). `soft` (default): also deceive, compete, steal small items, block a door; no Health or Stability damage, no killing. `full`: all rules apply, with a warning and a decision gate before any lethal step. A player with `pvp_optout` is never the target.
10. **Information fairness.** Each player sees only what their character perceives; results about one event are consistent across players.
11. **Overtaken actions.** Resolve what is left in the fiction (arrive, find it gone). Essential clue routes remain open.
12. **NPCs and the antagonist** act after the characters in each Block unless their schedule says otherwise.

### 6.4 Standing orders, absent and paused players [House]
<!-- for: turn, play -->

- **Standing orders** live in each character's record (`settings.standing_orders`): `hold` (where to stay and what to do when absent), `risk_tolerance` (`low`, `medium`, `high`), `default_spends` (e.g. Sense Trouble 1 each Block), `never_do` (list), `reply_to_messages`. Default: stay safe, rest, take no risks.
- **A missed turn.** Apply the standing orders; with none, the character **holds**: stays put or goes to lodgings, rests, keeps routine, declines risky invitations, takes no irreversible or dangerous action. A task marked `continue until told` (a long archive search) continues.
- **Absent characters** are never killed, committed or driven to Sanity 0 by inaction, take no lethal risk, and are not the target of a finale outcome unless their player walked past a decision gate. Ordinary world consequences (time passing, a missed meeting) may happen.
- **Consecutive misses.** After 3 the player is `away`: the character withdraws to a safe place. After 6, ask the host whether to drop the player; a `dropped` player's character becomes a GM-run ally or leaves the story.
- **Paused players.** On `pause` the character holds out of danger and the next result is an out-of-character check-in only.

---

## 7. NPC statistics [House]
<!-- for: turn, play -->

NPCs have no full sheets; record only what play needs.

- **Fields:** Health (max and current), Stability only if the NPC can be frightened mechanically, zero to four relevant abilities, Hit Threshold (default 3), a weapon modifier if armed, an attitude toward each character. Creatures and NPCs have **no Sense Trouble, Shadowing or Stealth** and never roll to detect or evade; the player rolls, and the creature's **Alertness Modifier** (added to the Difficulty of sneaking up on or past it) and **Stealth Modifier** (added to the Difficulty of noticing it) tune that.

| Tier | Examples | Health | Typical abilities | Hit Threshold |
|---|---|---|---|---|
| Frail | the elderly, the ill, children | 2 | Athletics 1 | 3 |
| Ordinary | clerk, nurse, shopkeeper, hobo | 4 | Athletics 3, Scuffling 2 | 3 |
| Trained | cop, orderly, laborer, thug, gang member | 6 | Athletics 5 to 7, Scuffling 6, Weapons 4 | 3 |
| Dangerous | soldier, killer, expert fighter, cult enforcer | 8 | Athletics 8 to 9, Scuffling 8, Firearms 5, Weapons 7 | 4 |
| Creature | see below | by creature | Athletics, Scuffling, Weapons | 3 to 5 |

- **NPC tests.** An NPC acting against a character rolls a d6 from the stream plus the relevant rating against the character's Difficulty, or in a contest. Ordinary NPCs do not spend points; a named antagonist may spend up to 2 per turn, noted in GM-only notes. NPC pools may be recorded as ratings; track the points spent.
- **Social outcomes** between characters and NPCs use the characters' Investigative abilities, not NPC rolls. Crowds are handled in narration.
- **Creature statistics** (an adventure supplies them): Athletics, Health, Scuffling or Weapons, Hit Threshold, weapon modifier, armor, Alertness and Stealth Modifiers, **Stability Loss** (extra over the standard loss for sighting, fighting or watching its attacks), special powers. It dies, vanishes or is banished when Health falls **below 0**. **Refresh:** not encountered for 24 hours refreshes all pools except Health (d6 per day); met again the same day refreshes only to half its ratings and no Health. A creature with two ratings by mode (land and air) loses or gains the extra points once only when it changes mode.
- **Fresh monsters [craft].** Vary powers, spoor, behavior; stress the most horrifying features and contradict lesser details. The Mythos is protean.
- Every NPC stat block lives in the NPC's record; update Health and attitudes as they change.

---

## 8. Era, craft and campaigns
<!-- for: turn, setup -->

### 8.1 The 1930s in play

- A desperate decade: poverty, unemployment, hunger, the shadow of the Great War and the next, segregation, rising totalitarian states. Use it as color, pressure and obstacle, not lecture.
- Technology: telephones, telegrams, cars, trains, radio, flashbulb photography, Dictaphone cylinders, wire recorders, no computers. Searches take days; records are on paper; nothing is faster than a trip to the library.
- Equipment is Credit Rating and plausibility (Preparedness, §3.2). Money matters at the lower classes and is narrative for the upper.

### 8.2 Craft notes for the Master

- **Design the horrible truth first, then the clue trail.** Each scene gives a core clue pointing to the next, with alternatives so no single test or ability gates it: at least three ways to reach any essential information.
- **Keep menace alive.** Something happens to the Investigators even if they do nothing: a warning, a follower, a missing contact, a date on a clock.
- **Mix idioms** with care: Purist dread can hold a Pulp action scene; keep the tests honest.
- **Costs are the story.** The Mythos asks for Stability, Sanity, Health, rating points, friends, Sources. Give the players a choice at each price.
- **Never end a scene on a die roll.** The investigation moves on after a failure.

### 8.3 Campaign frames and advancement

A campaign states its frame in the adventure or the host's setup: premise, build point totals, ability caps, a shared base, what refreshes between cases. Advancement follows §4.10. Track Sanity, Pillars, Sources and illnesses across cases and keep Credit Rating consistent.

---

## Appendix A. Sheet layout for this ruleset

The state contract fixes the outer shape of a character. This ruleset fills three fields.

**`sheet`**
- `groups.investigative`: each Investigative ability as `{ "max": n, "cur": n }`, including Credit Rating and Cthulhu Mythos when above 0. Occupational abilities are listed in `sheet.derived.occupational` (names).
- `groups.general`: each General ability as `{ "max": n, "cur": n }`, including Health, Stability and **Sanity** (`max` is the current rating, `cur` the current points).
- `derived.hit_threshold`: 3, or 4 with Athletics 8+. `derived.occupation` and `derived.occupational` as above.
- `unrated`: abilities the character does not have.

**`ruleset_state`**
- `mode`: `purist` or `pulp`.
- `drive`: `{ "name": "...", "kind": "hard|soft", "secret": bool }`.
- `pillars`: `[{ "name": "...", "intact": bool }]`.
- `sources_of_stability` (module on): `[{ "name", "phrase", "unlocked": bool, "last_used_day": n|null }]`.
- `haven`: `{ "last_used_day": n|null, "breached": bool }`.
- `mental_illness`: `[{ "kind", "detail", "since_turn": n }]`.
- `mythos_tomes`: `[{ "title", "read": "skimmed|pored", "mythos_gain": n }]`; `spells`: `[{ "name", "difficulty": n, "cost": "...", "source": "..." }]`.
- `dedicated_pools`: `[{ "for": "...", "ability": "...", "max": n, "cur": n }]`.
- `risk_factor_paid`: turns when a Drive cost was paid.

**`gm_only`** (never shown): `flags`, true pending Sanity and Stability losses, hidden Drive details.

**NPC `base_stats` and `npc_state.stats`** use the §7 tiers: `tier`, `health`, `stability` (or `null`), `abilities`, `hit_threshold`, `weapon_mod`. A creature adds `armor`, `alertness_mod`, `stealth_mod`, `stability_loss`, `inertia`, `special` (list).

**Game-level values** live in `game.gm_state`: `tension` (1 to 6), `heat` (0 to 7), `intensity` (`mild`, `moderate`, `severe`), `clock_steps`.
