# Oracles and Generators
## Random tables and generators for any ruleset and any adventure

> **GM-FACING FILE.** These tables answer unknowns, generate material and seed adventures. Behavior is governed by the protocol, data shapes by the state contract, and mechanics by the ruleset in use. Facts in the adventure always win over a table result.
>
> **Spoiler warning for players:** §8 lists possible rational causes of strange events. Do not read it if you want to be surprised.
>
> **Dice:** every roll comes from the server's dice stream (state contract §5.1), used in order and logged. Never invent a number. d20 tables have 20 rows. d10 tables: treat 0 as 10. d6 tables have 6 rows.
>
> **Vocabulary note:** the tables use generic words. Read "character" for the player's character, "essential clue" for a clue the story cannot proceed without, "pressure" for the antagonist's reaction level, "safe place" for wherever the ruleset allows recovery, and "distortion" for a mistaken perception when the ruleset has a perception module. Everything here is mundane and era-neutral: adapt names, objects and technology to the declared era. Unless the adventure or the ruleset says otherwise, nothing is supernatural: only beliefs, suggestions, hazards, illnesses, lies and people.

---

## 1. When to use an oracle (and when not)

**Use it for:** a yes or no about the world that nothing defines; a new NPC; a random event when play stalls; an item or document; an atmosphere; a scene complication; a hazard; a hook for a new adventure.

**Do not use it for:**
- essential clues (they are never random).
- A player character's own actions or feelings.
- Anything a General test already covers: use the ruleset's test.
- Anything the adventure file or the players have already defined.
- A way to contradict the truth.

Oracle results inspire, they do not restrict. Fail forward: even a "No" brings a cost or a way around. The AI Master rolls and interprets, using the dice stream, and logs every roll. Record what an oracle establishes as a world fact (state contract §3.4) so later turns stay consistent.

---

## 2. The Yes or No Oracle (d20)

Ask a yes or no question. Choose likelihood. Two d20 means two consecutive values from the d20 stream:
- **Neutral:** roll 1d20.
- **Likely** (advantage, the right tool, the situation favors the characters): roll 2d20 and keep the **higher**.
- **Unlikely** (pressed for time, outnumbered, unprepared, in danger): roll 2d20 and keep the **lower**.

| d20 | Result | Meaning |
|---|---|---|
| 1 | No, and | A disaster: a negative consequence too |
| 2 to 6 | No | A simple failure |
| 7 to 10 | No, but | A failure with a small opening |
| 11 to 14 | Yes, but | A success with a minor complication or cost |
| 15 to 19 | Yes | Clean success |
| 20 | Yes, and | An exceptional success with a bonus |

**Perception skew (optional).** If the ruleset has a perception module and a character is at a high level of it and asks about something they *perceive* (not a physical fact), a natural 1 or 20 means the perception is a distortion: the answer is what they see, but it is not so.

---

## 3. Adventure seeds
<!-- needs: generated -->

Roll or choose. Combine with the Mundane Cause generator (§8) and the antagonist generator (§9).

**Hook (d10)**

| d10 | Hook |
|---|---|
| 1 | A friend writes asking for help, then a second letter contradicts the first |
| 2 | A relative stops answering calls and the institution says they are fine |
| 3 | A publisher, newspaper or authority assigns the characters to check a complaint |
| 4 | An inheritance or a legal duty requires them to visit a place |
| 5 | A new job or posting puts them inside the situation |
| 6 | A witness arrives with a story nobody believes |
| 7 | A missing colleague's notes arrive by post |
| 8 | A routine inspection finds something that does not add up |
| 9 | A storm, closure or breakdown traps them in a place |
| 10 | A phone call at night, a recorded message, a name they know |

**What is at stake (d10)**

| d10 | Stake |
|---|---|
| 1 | A friend's life or freedom |
| 2 | The reputation of an institution |
| 3 | A community's trust in a leader |
| 4 | A family's secret |
| 5 | A hidden crime |
| 6 | A mistake that killed someone |
| 7 | A source of income or funding |
| 8 | The characters' own sanity or safety |
| 9 | A vulnerable group (patients, children, elders) |
| 10 | A coming date: a transfer, a ceremony, a closing |

**Time pressure (d10)**

| d10 | Clock |
|---|---|
| 1 | A ceremony or gathering on a fixed date |
| 2 | A transfer or closure |
| 3 | An inspection that will clean up evidence |
| 4 | A storm or road closure |
| 5 | A legal deadline or hearing |
| 6 | A person's discharge, release or removal |
| 7 | A shipment or delivery that will remove proof |
| 8 | A rising number of victims each night |
| 9 | A budget or funding decision |
| 10 | A rumor reaching the wrong person |

**Twist (d10)**

| d10 | Twist |
|---|---|
| 1 | The one who asked for help is part of the problem |
| 2 | The leader is not who they appear to be |
| 3 | The "cure" is the cause |
| 4 | The authority that should help is complicit |
| 5 | The victim does not want to be saved |
| 6 | The hazard is older than the current antagonist |
| 7 | The most reliable witness is the most affected |
| 8 | An ally has been quietly gathering evidence the whole time |
| 9 | The cause is well meaning and still lethal |
| 10 | The characters have already been exposed for longer than they thought |

---

## 4. Scene Test and Events

### 4.1 Tension and the Scene Test
Keep a **Tension** score from 1 to 6, starting at 2, in the game's GM-only state. Once per turn for each thread (a group of characters in one place), at the start of the thread's first Block, roll a d6. If the result is equal to or lower than Tension, the scene is **altered**. Roll a d6:
- **1 to 2, Complication:** roll on the Complication table (§10).
- **3 to 4, Interruption:** roll an Event Meaning (§4.2) and add it to the scene.
- **5 to 6, Escalation:** tick the clock, raise the antagonist's pressure or an NPC's belief state by one.

Raise Tension by 1 when the characters make noise, fail forward or waste a Block. Lower it by 1 after a quiet scene or a safe recovery. Tension never goes below 1 or above 6.

### 4.2 Event Meaning (d20 + d20)
Roll one from each column and interpret in context.

| d20 | Action | Subject |
|---|---|---|
| 1 | Withhold | A document |
| 2 | Confess | A witness |
| 3 | Lie | A locked room |
| 4 | Warn | A routine |
| 5 | Accuse | A rumor |
| 6 | Hide | A debt |
| 7 | Follow | A key |
| 8 | Interrupt | A record that does not match |
| 9 | Deny | A sound |
| 10 | Bargain | A resident or patient |
| 11 | Offer | An authority |
| 12 | Betray | A family member |
| 13 | Plead | A meal or drink |
| 14 | Threaten | A medicine |
| 15 | Disappear | A vehicle |
| 16 | Repeat | A telephone, message or letter |
| 17 | Mislabel | A photograph |
| 18 | Delay | A ritual or habit |
| 19 | Reveal | A stranger |
| 20 | Protect | A deadline |

---

## 5. Setting and places

**Setting archetype (d12)**

| d12 | Setting |
|---|---|
| 1 | A psychiatric hospital or sanatorium |
| 2 | A remote village or hamlet |
| 3 | An isolated research station or observatory |
| 4 | A boarding school or seminary |
| 5 | A religious community or retreat |
| 6 | A ship, oil rig or lighthouse |
| 7 | A mountain lodge or ski resort off season |
| 8 | A factory, mill or mine |
| 9 | A hotel or guesthouse in a storm |
| 10 | An apartment block or tenement |
| 11 | A prison, barracks or detention center |
| 12 | A rural estate or monastery turned something else |

**Why they cannot just leave (d10)**

| d10 | Isolation |
|---|---|
| 1 | A storm or flood closes the road |
| 2 | Legal custody or commitment |
| 3 | Phones and devices are confiscated or dead |
| 4 | A quarantine or lockdown |
| 5 | A contract, debt or promise |
| 6 | Social pressure: leaving means being branded as unwell |
| 7 | An island, remote valley or distance with no transport |
| 8 | A friend or relative is inside |
| 9 | Their means are exhausted and the next train is days away |
| 10 | A deadline they cannot abandon |

**Location concept (d20)**

| d20 | Place |
|---|---|
| 1 | A back corridor with grilled windows |
| 2 | A linen or storage room with a too-bright lamp |
| 3 | A service stair with scuffed treads |
| 4 | A dispensary or pharmacy cupboard |
| 5 | A chapel, prayer room or meeting hall |
| 6 | A records office with a clerk who does not look up |
| 7 | A tunnel, basement or boiler room |
| 8 | A greenhouse, potting shed or kitchen garden |
| 9 | A reservoir, pond or cistern |
| 10 | A lane, path or service road |
| 11 | A common room or dining hall |
| 12 | A kitchen or larder |
| 13 | An office with locked cabinets |
| 14 | A sleeping ward or dormitory |
| 15 | A laundry or workshop |
| 16 | A lecture theater or amphitheater |
| 17 | A staff room with half-finished tea |
| 18 | A visitors' parlor with worn furniture |
| 19 | A garage, yard or outbuilding |
| 20 | A cemetery, burial ground or old wall |

**Environmental feature (d20)**

| d20 | Feature |
|---|---|
| 1 | Grey dust like ash on a windowsill |
| 2 | Condensation on windows or grilles |
| 3 | A caged bird or a pet that droops |
| 4 | Damp stains in the shape of faces |
| 5 | Drowsy residents nodding in their chairs |
| 6 | Staff rubbing their temples |
| 7 | A film on standing water |
| 8 | A smell of wet leaves and cellars in a dry room |
| 9 | A freshly dug drain or ditch |
| 10 | Dew rings in the lawn where no one walks |
| 11 | A clock that is slightly wrong |
| 12 | A door that has been recently reinforced |
| 13 | Handwritten notices that repeat the same phrase |
| 14 | A pattern scratched into walls or furniture |
| 15 | Hot pipes that rattle on a rhythm |
| 16 | Windows painted shut |
| 17 | A smell of bleach covering something else |
| 18 | A fresh coat of paint in only one room |
| 19 | A drawing repeated in several rooms |
| 20 | A locked cabinet with fresh scratches around the lock |

**Sensory detail (d10 each)**

| d10 | Sound | Smell | Light | Touch or temperature | Object |
|---|---|---|---|---|---|
| 1 | A hum in the pipes | Boiled cabbage | Flat grey | Clammy air | A cracked mug |
| 2 | Distant singing | Wet wool | A lamp too bright | A draft from nowhere | A worn key |
| 3 | A door closing twice | Old tobacco | Flickering bulb | Warm floor | A stopped watch |
| 4 | A cough that repeats | Antiseptic | Candle and shadows | A cold doorknob | A ledger |
| 5 | Footsteps overhead | Earth after rain | Low sun through dust | Sticky banister | A faded photograph |
| 6 | Water in the walls | Burnt toast | Blue-white glare | Gritty windowsill | A broken spectacles lens |
| 7 | Faint radio or whispers | Mildew | Streetlight through blinds | A sweating wall | A hospital stamp |
| 8 | A kettle left to scream | Candle smoke | A window of fog | A fever warmth | A child's drawing |
| 9 | A clock that is too slow | Sweet rot | A red exit sign | Damp sheets | A string of beads |
| 10 | Complete silence | Metallic tang | Long slanting shadows | Stiff cold fingers | A pocketknife |

**Mood and ambience (d10 plus the highest distortion level in the scene, cap 10)**

| Result | Mood |
|---|---|
| 1 | Mundane, ordinary |
| 2 | Warm, welcoming |
| 3 | Busy, noisy |
| 4 | Melancholy |
| 5 | Silent |
| 6 | Tense |
| 7 | Oppressive |
| 8 | Stale, toxic |
| 9 | Dreamlike |
| 10 | Frenzied |

**Weather (d10)**

| d10 | Weather | Effect |
|---|---|---|
| 1 to 2 | Clear, cold | Windows open longer; Difficulties normal |
| 3 to 4 | Overcast | Normal |
| 5 | Fog | Fumes and smoke linger; sight tests +1 Difficulty |
| 6 to 7 | Rain | Windows shut; hazards stay indoors |
| 8 | Frost | Heating at full; outdoor physical tests are one step harder |
| 9 | Wind | Hazards scatter; a Block of exposure may be halved |
| 10 | Warm spell | Windows open; hazards diluted |

---

## 6. NPCs

**Role (d20)**

| d20 | Role |
|---|---|
| 1 | Guard, orderly or security |
| 2 | Nurse or carer |
| 3 | Night attendant |
| 4 | Assistant physician or junior official |
| 5 | Clerk or records keeper |
| 6 | Cook or kitchen hand |
| 7 | Gardener, laborer or maintenance worker |
| 8 | Resident, patient or inmate |
| 9 | Shopkeeper or cabman |
| 10 | Visitor or relative |
| 11 | Priest, chaplain or lay preacher |
| 12 | Police officer or constable |
| 13 | Local journalist or printer |
| 14 | Teacher or librarian |
| 15 | Landlord or landlady |
| 16 | Doctor in town |
| 17 | Official from a distant authority |
| 18 | Former employee who left in a hurry |
| 19 | Contractor or supplier |
| 20 | A child, an elder or someone nobody asks |

**Goal (d20)**

| d20 | Goal |
|---|---|
| 1 | Keep their position |
| 2 | Protect a vulnerable person |
| 3 | Protect a secret |
| 4 | Earn extra money |
| 5 | Leave the place |
| 6 | Obey a leader |
| 7 | Be heard by someone |
| 8 | Find a missing person |
| 9 | Settle a grudge |
| 10 | Be left alone |
| 11 | Hide a mistake |
| 12 | Pay a debt |
| 13 | Help the characters in secret |
| 14 | Recruit someone to a belief |
| 15 | Destroy evidence |
| 16 | Care for a sick relative |
| 17 | Win a promotion |
| 18 | Prove they are right |
| 19 | Atone for something |
| 20 | Keep the place open |

**Secret (d20)**

| d20 | Secret |
|---|---|
| 1 | They have been taking something to stay awake or numb |
| 2 | They falsified a record |
| 3 | They were there when someone died |
| 4 | They are related to a patient or victim |
| 5 | They have been paid to keep quiet |
| 6 | They are afraid of someone in the group |
| 7 | They have started to believe |
| 8 | They stole something small |
| 9 | They have been writing letters nobody sends |
| 10 | They know where a body is |
| 11 | They report to someone outside |
| 12 | They have been hiding a relative |
| 13 | They were dismissed elsewhere under suspicion |
| 14 | They have a debt to the antagonist |
| 15 | They keep a private journal |
| 16 | They have kept evidence for months |
| 17 | They tried to leave and were stopped |
| 18 | They are ill and hiding it |
| 19 | They have already talked to the authorities |
| 20 | They are the true origin of the trouble and do not know it |

**Visible trait (d20)**

| d20 | Trait |
|---|---|
| 1 | A torn or chewed ear |
| 2 | A bandaged hand |
| 3 | A scar running under a sleeve |
| 4 | Hums a hymn tune |
| 5 | Rubs temples constantly |
| 6 | Stares a beat too long |
| 7 | Smiles at the wrong moments |
| 8 | A very neat uniform and a very tired face |
| 9 | Missing fingers, handled lightly |
| 10 | Carries a rosary or a medal |
| 11 | Taps a rhythm on every surface |
| 12 | Wears a coat too heavy for the day |
| 13 | Speaks in a whisper |
| 14 | Always touching a particular button or ring |
| 15 | Chews a toothpick or a pencil |
| 16 | Very clean hands, very dirty boots |
| 17 | A stammer that vanishes when they lie |
| 18 | Never takes off gloves |
| 19 | Carries a small notebook and writes while listening |
| 20 | Looks younger or older than their voice |

**Voice and manner (d10)**

| d10 | Manner |
|---|---|
| 1 | Over-polite |
| 2 | Weary and flat |
| 3 | Warm, a little too warm |
| 4 | Clipped and official |
| 5 | Rambling |
| 6 | Whispering |
| 7 | Cheerful in a way that does not fit |
| 8 | Evasive, answers questions with questions |
| 9 | Pious |
| 10 | Frightened and quick |

**Disposition (d10)**

| d10 | Disposition |
|---|---|
| 1 | Hostile |
| 2 | Suspicious |
| 3 | Intimidated |
| 4 | Apathetic |
| 5 | Distracted |
| 6 | Curious |
| 7 | Friendly |
| 8 | Desperate |
| 9 | Wary ally |
| 10 | Overconfident |

**Belief state (d6)** (the ruleset's belief states, if any)

| d6 | State |
|---|---|
| 1 | Clear |
| 2 | Uneasy |
| 3 | Clouded |
| 4 | Devout |
| 5 | Frenzied |
| 6 | Broken or exhausted |

---

## 7. Items and documents

**Item type (d20)**

| d20 | Item |
|---|---|
| 1 | A ring of keys |
| 2 | A ledger or register |
| 3 | A handwritten note |
| 4 | A lamp or a candle |
| 5 | A set of workman's tools |
| 6 | A uniform |
| 7 | A bottle of sedative or tonic |
| 8 | A garden tool |
| 9 | A faded photograph |
| 10 | A pocketknife or scissors |
| 11 | A set of keys to a locked cabinet |
| 12 | A map or floor plan |
| 13 | A ticket stub or receipt |
| 14 | A tin of food or a thermos |
| 15 | A sealed envelope |
| 16 | A set of spectacles |
| 17 | A medical chart |
| 18 | A rosary or lucky charm |
| 19 | A cassette, record or film (era permitting) |
| 20 | A toy or a child's object |

**Condition (d10)**

| d10 | Condition |
|---|---|
| 1 to 2 | Pristine |
| 3 to 4 | Worn |
| 5 to 6 | Dirty or damp |
| 7 | Damaged |
| 8 | Marked with an institution's stamp |
| 9 | Nearly used up |
| 10 | Locked or sealed |

**Document type (d10)**

| d10 | Document |
|---|---|
| 1 | A letter |
| 2 | A newspaper clipping |
| 3 | An official report |
| 4 | A ledger or logbook |
| 5 | A private diary |
| 6 | A telegram, memo or message |
| 7 | A patient or personnel file |
| 8 | A plan or map |
| 9 | A receipt or invoice |
| 10 | A drawing or children's rhyme |

**What it shows (d10)**

| d10 | Content |
|---|---|
| 1 | A number that does not match the census |
| 2 | A repeated complaint over months |
| 3 | A name crossed out |
| 4 | A change of date or handwriting |
| 5 | A purchase that makes no sense |
| 6 | A warning ignored |
| 7 | A record of a visit that did not happen |
| 8 | A prescription or order for unusual quantities |
| 9 | A plan to move someone |
| 10 | A line of text that appears in every document |

---

## 8. The Mundane Cause generator (the truth)
<!-- needs: generated -->

Use this to build the truth for a new adventure, or to answer a question about why something is happening. Roll or choose one entry in each of the four tables, then make them coherent. Never use real-world procedures or instructions; stay at the level of story.

**Source (d20)**

| d20 | What is actually causing the strangeness |
|---|---|
| 1 | A leaking combustion appliance or flue (carbon monoxide) |
| 2 | Mold or fungal contamination in the building, garden or food |
| 3 | A contaminated water supply |
| 4 | A tainted or adulterated medication or supplement |
| 5 | Low-frequency vibration or noise from machinery |
| 6 | Chronic sleep deprivation from shift work or noise |
| 7 | Isolation and sensory monotony |
| 8 | A fever or infection spreading through the group |
| 9 | A charismatic person's sustained suggestion and coercion |
| 10 | A hoax or staged effects by someone with a motive |
| 11 | Pesticide or industrial solvent residue |
| 12 | A badly ventilated enclosed space (carbon dioxide buildup) |
| 13 | Hunger, dehydration or malnutrition |
| 14 | A substance suddenly withdrawn from a group |
| 15 | A hidden scheme to manipulate someone (gaslighting) |
| 16 | Shared grief or trauma after a disaster |
| 17 | A rumor that became a panic (mass psychogenic illness) |
| 18 | A deliberate regime of sedatives or stimulants |
| 19 | Heavy-metal contamination in pipes, paint or cookware |
| 20 | A cult or ideology that controls sleep, food and contact |

**Delivery (d10)**

| d10 | How it reaches people |
|---|---|
| 1 | The air |
| 2 | The water |
| 3 | The food |
| 4 | Medication or a tonic |
| 5 | Noise or vibration |
| 6 | The daily schedule and routines |
| 7 | Social pressure and gossip |
| 8 | Printed material, preaching or propaganda |
| 9 | Light, heat or cold |
| 10 | A chain of rumor |

**Concealment (d10)**

| d10 | Why it stays hidden |
|---|---|
| 1 | The administration fears liability |
| 2 | Someone profits |
| 3 | The institution's reputation is at stake |
| 4 | The affected deny it |
| 5 | The place is remote |
| 6 | A jurisdiction gap lets everyone pass the problem on |
| 7 | An official report was shelved |
| 8 | Victims are discredited as unwell |
| 9 | The community is proud and closed |
| 10 | A trusted authority vouches for the place |

**Human factor (d10)**

| d10 | Who is involved |
|---|---|
| 1 | Someone profits |
| 2 | Someone covers up |
| 3 | Someone sincerely believes they are helping |
| 4 | Someone discovered it and was silenced |
| 5 | Someone exploits the situation |
| 6 | Someone innocently makes it worse |
| 7 | Someone left and tried to warn |
| 8 | Someone has been recording data |
| 9 | Someone is testing something on others |
| 10 | Someone was the first and most exposed |

**Uncanny effect and its rational cause (d20)**

| d20 | What it looks like | What it actually is |
|---|---|---|
| 1 | A figure in the corner of the room | Pareidolia in poor light, or a coat on a hook |
| 2 | Voices in an empty corridor | Pipes, ventilation or low-frequency noise |
| 3 | A sense of being watched | Fatigue, hypervigilance, a person at a window |
| 4 | Lost time | Sleep deprivation, sedatives or a faulty clock |
| 5 | A smell with no source | A slow leak, mold or contamination |
| 6 | A glowing light on the water | Reflection, decaying wood or a fungal film |
| 7 | A shared dream or image | Suggestion, discussion and a leader's phrasing |
| 8 | A cold spot | A draft, a poorly insulated wall or a damp patch |
| 9 | A person who looks wrong | Fatigue, illness or a twin or relative |
| 10 | Writing that appears overnight | A sleepwalker, a prankster or a hidden hand |
| 11 | Objects that move | Vibration, a settling floor or someone in the walls |
| 12 | A tune stuck in everyone's mind | Repetition, a daily ritual or a loudspeaker |
| 13 | Sudden illness in a group | Poisoned water, food or air |
| 14 | A "prophecy" that comes true | Selection, confirmation bias or a leader who arranges it |
| 15 | A sound like breathing in the walls | Air in pipes, a boiler or an animal |
| 16 | A dead person seen alive | A relative, a mistake or a deliberate imitation |
| 17 | Sleepwalking in unison | Shared schedule, drugs or a trigger sound |
| 18 | Animals behaving strangely | A hazard in air, water or soil |
| 19 | A door that locks itself | A latch, a draft or a resident |
| 20 | A voice that knows your name | A recording, an overheard remark or a hoax |

---

## 9. The antagonist
<!-- needs: generated -->

**Motivation (d20)**

| d20 | Motivation |
|---|---|
| 1 | Protect a secret |
| 2 | Avoid blame or liability |
| 3 | Protect the institution's reputation |
| 4 | Sincere zeal for a cause |
| 5 | Profit |
| 6 | Revenge |
| 7 | Cover for a crime |
| 8 | Preserve a family name |
| 9 | Hide a mistake |
| 10 | Gain or keep power |
| 11 | Belong to a group |
| 12 | A conviction that they are saving people |
| 13 | Fear of being exposed |
| 14 | Protect a particular person |
| 15 | Enforce order |
| 16 | Fulfill an ideology |
| 17 | Cover up a death |
| 18 | Keep research funding |
| 19 | Silence a witness |
| 20 | Complete a plan that cannot be stopped without public scandal |

**Method (d20)**

| d20 | Method |
|---|---|
| 1 | Bureaucratic delay |
| 2 | Social pressure |
| 3 | Discrediting a reputation |
| 4 | Surveillance |
| 5 | Intimidation |
| 6 | Bribery |
| 7 | Isolating the target |
| 8 | Forged documents |
| 9 | Gaslighting |
| 10 | Institutional commitment or confinement |
| 11 | Staged accidents |
| 12 | Sabotaging a vehicle or a lock |
| 13 | Withholding medication or food |
| 14 | Spreading rumors |
| 15 | Mobilizing the community |
| 16 | Police pressure |
| 17 | Legal threats |
| 18 | Flattery and co-optation |
| 19 | Controlled access |
| 20 | Violence by proxy |

**Weakness (d10)**

| d10 | Weakness |
|---|---|
| 1 | Needs the trust of an authority |
| 2 | Depends on one loyal subordinate |
| 3 | Keeps a record that proves everything |
| 4 | Has a fear of being alone |
| 5 | Has a relative outside who does not believe |
| 6 | Can be shamed in public |
| 7 | Is physically ill |
| 8 | Is exposed to the hazard more than anyone |
| 9 | Follows a routine that can be predicted |
| 10 | Has a rival who wants their place |

For the ladder of antagonist responses see the ruleset, if it has one.

---

## 10. Challenges, Consequences, Twists

**Challenge (d20)**

| d20 | Challenge |
|---|---|
| 1 to 2 | A locked door, a wall, a gate |
| 3 to 4 | A clerk or official who must be persuaded |
| 5 | A document or ledger to decode |
| 6 | A hazard: bad air, a slippery stair, unstable ground |
| 7 | Tracking a faint trail or a person before a deadline |
| 8 | A patrol or a shift change |
| 9 | A choice that costs time, trust or safety |
| 10 | A distortion that must be questioned |
| 11 | A witness who will not talk until fed or warmed |
| 12 | A suspicious ally who demands proof |
| 13 | A crowd that blocks the way |
| 14 | A weather problem that closes a route |
| 15 | A rule that cannot be broken without consequences |
| 16 | An argument within the group |
| 17 | A message that arrives too late |
| 18 | A medical emergency |
| 19 | A trap set by someone who expects them |
| 20 | A lie that must be maintained |

**Complication or consequence (d20)**

| d20 | Consequence |
|---|---|
| 1 | An unexpected ally or piece of information |
| 2 | The antagonist learns something |
| 3 | A new route or location appears |
| 4 | An innocent is hurt or frightened |
| 5 | A deadline tightens |
| 6 | Reputation shifts |
| 7 | A Block is lost |
| 8 | A bruise or a pool point is lost |
| 9 | Someone trusted hesitates |
| 10 | A distortion, if the character is exposed |
| 11 | A document is damaged or goes missing |
| 12 | An ally is pressured or moved |
| 13 | The weather worsens |
| 14 | A rumor spreads about the characters |
| 15 | A door that was open is locked |
| 16 | A witness changes their story |
| 17 | A relative or friend is touched by the problem |
| 18 | A mistake becomes known to the wrong person |
| 19 | The place gets quieter and more watchful |
| 20 | An exposure Block is added at the worst moment |

**Event and opportunity (d10)**

| d10 | Event |
|---|---|
| 1 | A message from an ally, brisk and useful |
| 2 | A telephone rings once and stops |
| 3 | A clerk misplaces a file, then finds it |
| 4 | A stranger takes the seat across from the characters |
| 5 | A resident presses a note into a hand |
| 6 | Rain begins and windows are shut |
| 7 | A delivery cart blocks the lane |
| 8 | A staff member drops a ring of keys, then picks it up too slowly |
| 9 | Someone met earlier turns up where they should not be |
| 10 | A door left unlocked |

---

## 11. Collective belief kit

Use for cults, panics, shared delusions and communities that harden around a belief. Everything is human and rational: suggestion, charisma, fear, a hazard, a ritual that binds.

**Core belief (d10)**

| d10 | Belief |
|---|---|
| 1 | A savior will arrive and take the faithful away |
| 2 | A hidden enemy lives among us |
| 3 | The end is near and only the pure will be spared |
| 4 | The place itself is tainted and must be cleansed |
| 5 | The authorities have betrayed us |
| 6 | A secret cure exists and is being withheld |
| 7 | A date has been fixed and must be met |
| 8 | A sacrifice, of property, privacy or a person, will set things right |
| 9 | We are being tested |
| 10 | The dead are speaking and must be answered |

**Ritual (d10)**

| d10 | Ritual |
|---|---|
| 1 | A daily telling of dreams |
| 2 | A shared meal or fast |
| 3 | A procession at fixed hours |
| 4 | A shared chant or phrase |
| 5 | A confession before the group |
| 6 | A mark or drawing placed on doors |
| 7 | A vigil or night watch |
| 8 | An exchange of gifts or possessions |
| 9 | A shared bathing, washing or cleansing |
| 10 | A gathering at a particular place and moment |

**Leader type (d10)**

| d10 | Leader |
|---|---|
| 1 | A doctor who sincerely believes |
| 2 | A priest or lay preacher |
| 3 | A patient or resident everyone follows |
| 4 | A teacher or mentor |
| 5 | A manager or director |
| 6 | A founder returning after absence |
| 7 | A pair of siblings or a married couple |
| 8 | A committee that hides behind a single face |
| 9 | A newcomer with a gift for talking |
| 10 | Nobody: the belief leads itself |

**Recruitment (d10)**

| d10 | Method |
|---|---|
| 1 | Kindness and attention |
| 2 | Shared secrets |
| 3 | Sleep and food control |
| 4 | Isolation from outsiders |
| 5 | Offering relief from pain or grief |
| 6 | Group pressure |
| 7 | A simple explanation for a hard loss |
| 8 | Promising status |
| 9 | Showing an apparent miracle or coincidence |
| 10 | Shame and fear |

**Signs of belief (d10)**

| d10 | Sign |
|---|---|
| 1 | Graffiti or a repeated mark |
| 2 | Shared phrases in ordinary talk |
| 3 | The same drawing in several hands |
| 4 | Staff and residents greeting one another in the same way |
| 5 | Changes in routine nobody explains |
| 6 | New rules about doors, lights or windows |
| 7 | A hush when outsiders enter |
| 8 | A calm that is too complete |
| 9 | A song or rhyme children and adults both know |
| 10 | A particular kind of kindness toward the characters |

---

## 12. Fear seeds and distortions

### 12.1 Fear seeds (d20)
Use with the fears the players named. When a distortion needs content, choose a seed and give it a concrete detail from the scene.

| d20 | Fear seed |
|---|---|
| 1 | Being watched |
| 2 | Not being believed |
| 3 | Being trapped |
| 4 | Something happening to a loved one |
| 5 | Losing time or memory |
| 6 | The body betraying you |
| 7 | Doubles and imposters |
| 8 | The group turning on you |
| 9 | Being committed or confined |
| 10 | Failing someone who relied on you |
| 11 | A familiar voice saying something wrong |
| 12 | Being the cause of the harm |
| 13 | A door that will not open |
| 14 | A crowd that turns its head together |
| 15 | A place that rearranges itself |
| 16 | A secret exposed |
| 17 | An ally who knows more than they say |
| 18 | A child's voice or drawing |
| 19 | A number or phrase that keeps returning |
| 20 | Comfort offered by the wrong person |

### 12.2 Distortion content
Distortion tables belong to the ruleset that uses a distortion module. If the ruleset gives none, build distortions from a fear seed and a concrete detail of the scene, always with a tell.

---

## 13. Unwanted attention, rumors, opportunities

**Unwanted attention (d10, human only)**

| d10 | Attention |
|---|---|
| 1 | A man in a brown overcoat at the next table |
| 2 | A cabman who follows too slowly |
| 3 | A "wrong number" on the telephone |
| 4 | A note on a pillow |
| 5 | A slashed tire |
| 6 | A smear on a windshield, a figure drawn in red |
| 7 | A loosened wheel nut (warn with a cue first) |
| 8 | A visit from a landlord's relative asking questions |
| 9 | A polite invitation from the antagonist |
| 10 | A figure at the station platform, then gone |

**Rumor (d10)**

| d10 | Rumor |
|---|---|
| 1 | The place has had a bad year |
| 2 | The last inspector left in a hurry |
| 3 | Someone died and it was not reported |
| 4 | A new director is not who he says he is |
| 5 | The garden or well is to blame |
| 6 | The doctor has not slept for weeks |
| 7 | Children in the village will not go near the place |
| 8 | A priest refused to visit |
| 9 | Someone is selling something to the staff |
| 10 | The place will close soon |

---

## 14. Quick reminders

- The oracle gives ideas, not essential clues.
- A distortion never carries an essential clue and never creates a lethal outcome without a warning cue and a chance to question it.
- Keep distortion a minority of the text. Mundane details make the wrong ones hurt.
- Every strange thing has a rational cause the GM knows.
- If a result clashes with the adventure file, the adventure file wins.
- Every roll comes from the server dice stream and is logged. Record what an oracle establishes.

---

## 15. Emergent adventure kit
<!-- needs: generated -->

Use this for `generated_full` and `generated_emergent` games (protocol §16). Everything here is private to the AI Master. All dice come from the stream and are logged.

### 15.1 The seed (stored as the GM-only adventure record)

Roll or choose, then make the parts coherent.

1. Setting archetype and why the characters cannot just leave (§5).
2. The Mundane Cause: source, delivery, concealment and human factor (§8).
3. Hook, stake, time pressure and, optionally, a twist (§3).
4. The antagonist: motivation, method and weakness (§9).
5. Four anchor NPCs: the antagonist, a helper, a witness and an authority (§6).
6. The first place (§5) and the opening handout (§7).
7. The clock in turns (§15.5).
8. If a hazard fits: its zones and cues (§5, §8).

Write each as one or two plain sentences. State the truth first.

### 15.2 Creating things as they are reached

- **A place:** Location concept (§5), Environmental feature (§5), one sensory detail (§5), the zone if a hazard exists, and one detail that hints at its past.
- **An NPC:** Role, Goal, Secret, Visible trait, Manner, Disposition and Belief state (§6), plus a stat tier (§15.4).
- **A document or item:** Item type, Condition, Document type and What it shows (§7).
- **A rumor, an unwanted attention, an event:** §13 and §10.

Save each one immediately (protocol §10).

### 15.3 Clue routes

For each essential conclusion create at least three routes (the three-clue rule). Choose route types from the table, tie each to an ability that some character actually has, and add a Simple Search route. Never route an essential clue through a distortion.

**Route type (d10)**

| d10 | Route |
|---|---|
| 1 | A document or a record |
| 2 | A witness who saw it |
| 3 | A physical trace: an object, a stain, damage |
| 4 | An expert's opinion |
| 5 | An insider who wants out |
| 6 | A change in someone's routine |
| 7 | A person who left and can be found |
| 8 | A hazard cue in the place |
| 9 | A rumor that can be checked |
| 10 | An ally's own research |

### 15.4 NPC quick stats

**Tier (d6)**: 1 Frail, 2 to 3 Ordinary, 4 to 5 Trained, 6 Dangerous (the ruleset's NPC tiers). Adjust by role: orderlies, guards and constables are Trained at least.

### 15.5 Clock and checkpoints

Set the deadline as a number of turns. A five-day adventure is five turns at a day span and twenty at a Block span. Checkpoints, as a share of the deadline:

| Share | What must have happened |
|---|---|
| 25% | The first essential clue is delivered and the hook has paid off |
| 50% | A twist or a reversal; the antagonist's pressure is moderate |
| 75% | The antagonist reacts directly (pressure is high); allies are pressured |
| 90% | The finale is designed and at least three fair warnings have begun |
| 100% | The finale resolves in crisis turns |

### 15.6 Consistency

- The rational truth, once stored, never changes.
- Established facts beat oracle results. Do not use an oracle to answer a question that stored facts already answer.
- Foreshadowing is a promise. Pay off what you plant.
