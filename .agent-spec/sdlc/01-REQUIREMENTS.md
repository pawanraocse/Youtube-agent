# 01 — Requirements: story-to-video creator

| | |
|---|---|
| Gate | 0 — REQUIREMENTS |
| Feature | `story-to-video-creator` — the whole creator, delivered milestone by milestone |
| Built from | `00-INTENT.md` (commit `54c6aa6`); six gate-0 decisions (§2) and answers A-7–A-22 in `00-INTENT.md`; `requirement.md`; the approved plan |
| Absorbs | The earlier `kokoro-narration` draft of this file. Its requirements now live in §4.3, REQ-034, REQ-036 and NFR-014; its open questions are Q-001 and Q-005 |
| Relation to `requirement.md` | That file stays the record of the source brief. **This file is the traced specification**: its R-numbers appear in the Traces column, and new work cites REQ-numbers from here |
| Template | None ships with the install; structure follows the identifiers gate 8 traces |

Traces use: **I-What / I-Why / I-Con / I-Non** for sections of `00-INTENT.md`, **A-n** for the
originator's answers in `00-INTENT.md` §Answers, **D-n** for §2, **Rn** for `requirement.md` §3,
and **Plan §…** for the approved plan.
State is **Built** (exists and is tested), **Partial**, **Specified** (planned, no code), or
**Missing** (neither planned nor built).

---

## 1. Problem

The originator wants a YouTube creator that "takes story and create AI videos", and earns
money from them across platforms, at DramaBox production quality, using only free tools on
this machine.

Today the pipeline skeleton, the gates and the text agents exist. One real script,
`trade-atlas-EP01` (the Panama Canal water story), is written and held at LOCK 1. Voice,
picture, music and publishing still run on mock providers. An animated chart renderer exists
but is not yet called by the pipeline.

## 2. Decisions made at gate 0

Asked one at a time, answered by the originator on 2026-09-15. D-1 to D-6 are the same answers as
A-1 to A-6 in `00-INTENT.md`. The later answers, A-7 to A-22, are recorded only there and traced
below as **A-n**, so the two files cannot drift.

| ID | Question | Decision |
|---|---|---|
| D-1 | Which kind of AI video is built and published first? | **Finish the data-explainer first** — the Panama Canal episode, told as a story with charts and narration. Character story video comes next. |
| D-2 | What does the creator take in? | **Either a topic or the operator's finished story.** A finished story skips research and writing but still passes the critic and LOCK 1. |
| D-3 | Song remixes, recreated movie scenes, a kids channel? | **Only the forms that pay:** original AI songs, film analysis with original visuals, general-audience stories. The rights check refuses the risky form and names the paying one. Original AI songs were parked by D-5, then allowed by D-6. |
| D-4 | How is success judged? | **Two checkpoints.** Month 12: at least one channel accepted into the YouTube Partner Program. Month 18: at least $500 a month across all channels. |
| D-5 | Original AI songs need a music model, but `CONSTITUTION.md` §4 says "never generate music". What happens to AI song videos? | **Park them.** The rule stands. Song videos wait until a free, commercially licensed music model is found and verified; background music stays a downloaded, cleared library. **Superseded by D-6.** |
| D-6 | What music can the creator use without paying — can it alter, mix or generate music? *(asked after a licence search)* | **AI first, free library fallback.** Background music is generated locally by a model verified for commercial use: ACE-Step 1.5 (MIT, under 4 GB) first, Stable Audio 3 (Stability AI Community License, free under $1M a year) second. The fallback is a free library: Incompetech (CC BY 4.0, credit required) and Pixabay (no credit, but Content ID claims possible). A track is altered or mixed only when its licence allows it. **Supersedes D-5.** |

## 3. User stories

| ID | Story | Served by |
|---|---|---|
| US-001 | As the operator, I give the creator a topic and get back an episode ready for my approval, so I do not research or write it myself. | REQ-001, REQ-004–006, REQ-031 |
| US-002 | As the operator, I give the creator a story I wrote and get back a video of it, reviewed the same way. | REQ-002 |
| US-003 | As a viewer, I recognise the same characters in every episode, so I come back for them. | REQ-008, REQ-009, REQ-021 |
| US-004 | As a viewer on a phone, I see a sharp picture and hear a clear voice over a background with depth. | REQ-015, REQ-024, REQ-027–029, NFR-004 |
| US-005 | As the operator, I approve the script, the picture and the finished master, and nothing publishes without me. | REQ-031 |
| US-006 | As the operator, each approved episode goes out as long-form and Shorts across YouTube, Facebook, Instagram and TikTok. | REQ-038, REQ-039 |
| US-007 | As the operator, I can ask what to make next, what could harm us, how to stay safe, and what earns more. | REQ-007 |
| US-008 | As the operator, I can open a channel in any genre without anyone changing the core code. | REQ-042 |
| US-009 | As the operator, I know within ninety days whether a channel is worth continuing. | REQ-043 |
| US-010 | As the operator, a crashed render resumes where it stopped, so compute is never paid twice. | REQ-046 |

## 4. Functional requirements

### 4.1 Story input and development

| ID | Requirement | Traces | Priority | State |
|---|---|---|---|---|
| REQ-001 | From a topic, produce a demand verdict, tiered sources with claim-level citations, and a series map. | I-What; D-2; R2 | MUST | Built |
| REQ-002 | Accept an operator-supplied finished story, skip research and writing, and send it through the same script review and LOCK 1. | D-2 | MUST | Missing |
| REQ-003 | Refuse, at the rights check, any concept whose revenue goes to someone else — song remixes, recreated film scenes, made-for-kids content — and name the form that pays. | D-3; R18 | MUST | Built |
| REQ-004 | Write packaging before the script: title variants, a thumbnail concept, and a promise of eight words or fewer. | R4 | MUST | Built |
| REQ-005 | Write a beat sheet with timings and clippable moments marked. | R5 | MUST | Built |
| REQ-006 | Write the script one sentence per chunk with an authored pause, every factual claim citing a source. | R3; R6 | MUST | Built |
| REQ-007 | An advisor answers what to make next, what could harm us, how to stay safe and what earns more, from live data, tagging every figure measured or assumed. | I-What; R33 | SHOULD | Specified |

### 4.2 Characters and look

| ID | Requirement | Traces | Priority | State |
|---|---|---|---|---|
| REQ-008 | Characters are defined once, versioned, and reused in every video of a series and across channels. Shots name characters by id, never by description. | I-What; R24 | MUST | Specified |
| REQ-009 | A registered character is recognisable across unrelated scenes. | I-What; R24 | MUST | Specified |
| REQ-010 | A character that resembles a real, identifiable person is refused at registration. | R23 | MUST | Specified |
| REQ-011 | Each show locks a bible before episode one: look, locations and audio palette. | R25; Plan §The show bible | SHOULD | Specified |

### 4.3 Voice

| ID | Requirement | Traces | Priority | State |
|---|---|---|---|---|
| REQ-012 | Narration is synthesised on this machine, chunk by chunk — Kokoro-82M, as the plan selects — with no network call and no per-unit cost. The provider is chosen by the format's configuration, and the mock stays available for tests. | I-Con; R7; `CONSTITUTION.md` §3 | MUST | Missing |
| REQ-013 | Exactly the chunk's authored pause of silence follows each chunk, within ±10 ms. | R6 | MUST | Partial — mock only |
| REQ-014 | A timeline gives each chunk's start and end, agreeing with the delivered audio within ±20 ms by the last chunk. | R7 | MUST | Partial — mock only |
| REQ-015 | Narration is delivered at 48 kHz mono, with adjacent chunks within ±2 LU of each other, so the level never jumps between sentences. | Plan §The production standard | MUST | Partial — format built, level matching missing |
| REQ-016 | Each character's and each channel's voices are set in configuration, never in code. A channel may alternate between two or three narrator voices. | Plan §Characters; A-15 | MUST | Missing |
| REQ-017 | A chunk whose text, voice, speed and model are unchanged is never synthesised again. | R26; R27 | MUST | Missing |
| REQ-018 | Numbers, years, money, identifiers and recurring names are spoken as a listener expects. `trade-atlas-EP01` has 14 chunks containing digits, and uses "Gatun" throughout. | I-Con (quality) | MUST | Missing |
| REQ-019 | Every new character and channel goes through a repeatable voice audition: the same passage in candidate voices, so the operator chooses by ear. | US-004; A-15 | MUST | Missing |
| REQ-020 | A chunk whose spoken duration is implausible for its word count is flagged before a human listens. | Plan §Review loops | SHOULD | Missing |
| REQ-021 | Story episodes voice each character with its own voice. | I-What; Plan §Provider tiers | MUST | Specified |
| REQ-022 | Once English works, a Hindi dub is added to the same videos as a second audio track, time-fitted per beat within ±8%. Whether Kokoro has usable Hindi voices is settled at gate 1. | I-Con; R11; A-21 | SHOULD | Specified |

### 4.4 Picture

| ID | Requirement | Traces | Priority | State |
|---|---|---|---|---|
| REQ-023 | Data shots render as animated charts cut to the narration, crediting their sources in frame. | D-1 | MUST | Partial — renderer built, not called by the pipeline |
| REQ-024 | Story shots render as stills with 2.5D parallax. AI video is used only for a fixed per-episode budget of hero shots. | I-Con (machine); R8 | MUST | Specified |
| REQ-025 | Cuts land on clause boundaries, taken from word-level alignment of the narration. | R8 | MUST | Specified |
| REQ-026 | Each show commits to a stylised look rather than photoreal human faces. | Plan §The production standard | MUST | Specified |
| REQ-048 | Lip-sync is applied only to the few story shots where a character is seen speaking, using a commercially licensed model. | I-What (DramaBox); Plan §Provider tiers | COULD | Specified |

### 4.5 Post-production and master

| ID | Requirement | Traces | Priority | State |
|---|---|---|---|---|
| REQ-027 | Music sits under narration, ducked and high-passed at 200 Hz, with room tone and foley beneath every scene. | I-What (DramaBox audio) | MUST | Missing |
| REQ-028 | Word-level captions are burned in: at least 56 px at 1080 width, two lines at most, inside the platform's safe area. | Plan §The production standard | MUST | Partial — check built, rendering missing |
| REQ-029 | Every master meets the production standard's numeric targets before LOCK 3. | I-What (DramaBox); R9 | MUST | Built — as checks |
| REQ-030 | Each episode gets a thumbnail featuring the channel's host. | Plan §Characters | SHOULD | Specified |
| REQ-049 | Background music is either generated locally by a model verified for commercial use, or taken from a free library whose licence allows commercial use. Music is altered or mixed only when its licence allows it. Every track records its source, licence and any required credit, and a required credit is written into the description. | D-6; I-Con (free) | MUST | Missing |

### 4.6 Review and compliance

| ID | Requirement | Traces | Priority | State |
|---|---|---|---|---|
| REQ-031 | Nothing advances past the script, picture or master lock, or publishes, without a recorded human decision. | I-Con (review); R13 | MUST | Built |
| REQ-032 | Deterministic checks run before any critic; no agent reviews its own work; rubrics cannot be edited by agents; revision stops after three rounds. | I-Con (review); R14–R17 | MUST | Built |
| REQ-033 | Story episodes are scored against a rubric built for story — character consistency, emotional arc, hook, pacing. | I-What | MUST | Missing |
| REQ-034 | Every model weight is commercially licensed and verified by a human before real use. | I-Con (free); R19 | MUST | Partial — audit built, no weight yet verified |
| REQ-035 | Music is cleared for every platform it is posted to. | R20 | MUST | Built — as a check |
| REQ-036 | AI-generated visuals and synthetic voices are disclosed on every platform that requires it, and a master cannot ship without the disclosure set. Each episode records which models and voices produced it. | R21 | MUST | Missing |
| REQ-037 | Originality — what the viewer learns or feels that the first search result would not give them — is scored, so interchangeable content cannot pass review. | R22 | MUST | Missing |

### 4.7 Multiply and publish

| ID | Requirement | Traces | Priority | State |
|---|---|---|---|---|
| REQ-038 | Each episode yields a long-form master and 6–8 vertical clips, each with its own opening hook. | I-What (short clips); R10 | MUST | Partial — mock only |
| REQ-039 | From the first public video, every video goes to YouTube, Facebook, Instagram and TikTok at once — by API where approved, otherwise as a folder with the caption — from new brand accounts kept apart from the operator's personal ones. | I-Why; R12; A-12; A-22 | MUST | Partial — mock only |
| REQ-040 | Every description carries the channel's affiliate or product links from video one. | I-Why; R31 | SHOULD | Missing |
| REQ-041 | Original AI song videos are a supported genre, made with a music model verified for commercial use and with genuine creative input — written lyrics, visuals, editing — because prompts alone do not make anyone the author of the output. | D-3; D-6 | COULD | Specified |

### 4.8 Operating the channels

| ID | Requirement | Traces | Priority | State |
|---|---|---|---|---|
| REQ-042 | A new channel in any genre is configuration — subject pack times production format — with no change to core code or the agent roster. | I-Why; R28 | MUST | Built |
| REQ-043 | Each channel is reviewed at ninety days against numeric criteria. The review recommends improve, continue or pause; the operator decides, and no channel is ever closed or deleted. | I-Why; R29; A-13 | MUST | Partial — check built, but it returns `kill` |
| REQ-044 | Ideas and channels are ranked on expected earnings, cost to make — compute and operator time — and safety from claims, demonetisation and strikes. Personal interest is not a criterion. | I-Why; R30; A-17 | MUST | Partial — earnings per GPU hour computed per topic; operator time, safety and a ranked backlog missing |
| REQ-045 | Measured views, click-through, retention and revenue feed back into what is made next, and into when the next channel launches. | I-Why; R32; A-19 | SHOULD | Specified |
| REQ-046 | A crashed or repeated run resumes without redoing finished work. | R26; R27 | MUST | Built |
| REQ-047 | Title and thumbnail variants are tested against each other on the platform, and each post records which variant it used, so the packaging that earns clicks is learned rather than guessed. | I-Why ("get viral"); Plan §Lane C | SHOULD | Specified |
| REQ-050 | Every concept and script is checked against platform policy before LOCK 1. No topic is banned by choice, but content a platform would remove or demonetise is refused, with the reason. | A-11 | MUST | Specified |
| REQ-051 | Choosing a new channel is a repeatable process, run whenever needed, where the operator and Claude both give input and the decision is recorded: topic, format, characters, voices and look, scored as in REQ-044. | A-16 | MUST | Partial — topic stages A1–A3 exist; character, voice and look selection missing |

## 5. Non-functional requirements

| ID | Requirement | Measure | Traces |
|---|---|---|---|
| NFR-001 | Free by default. | The production path works with no paid API or tool; any spend is a recorded, case-by-case operator decision | I-Con; A-9 |
| NFR-002 | Local only. | Nothing leaves the machine except finished uploads | I-Con |
| NFR-003 | Fits this machine. | Peak VRAM within 8,151 MiB; stills plus parallax by default | I-Con |
| NFR-004 | DramaBox production quality. | Every numeric target in REQ-029, plus the operator's sign-off at LOCK 3 | I-What |
| NFR-005 | The creator works commercially. | Counted from the first public video: month 12, at least one channel accepted into the YouTube Partner Program; month 18, at least $500 a month across channels. More channels launch after the first has been monitored. The plan's 65–70% estimate assumed several channels at once and covers month 18 only; no estimate exists for starting with one channel. | I-Why; D-4; A-7; A-18; A-19 |
| NFR-006 | Episodes fit the GPU budget. | Per-format GPU hours measured, not assumed: data-explainer ~1 h, character story ~6 h **[NEEDS CLARIFICATION: estimates from the plan, unmeasured — gate 1]** | Plan §GPU hours |
| NFR-007 | Operating it fits the operator's week. | Three checks per video, auditions and uploads fit 10–20 hours a week | A-8; A-14 |
| NFR-008 | Simple. | No orchestration framework; agents and skills over a Python CLI; each new dependency justified in the constitution | I-Con |
| NFR-009 | Reference, never copy. | No code from any reference repository | I-Con; I-Non |
| NFR-010 | Testable without the models. | Default test suite needs no model weights; every check has a known-bad and a known-good fixture | `CONSTITUTION.md` §3 |
| NFR-011 | Episode length. | Long-form episodes of 6–8 minutes | Plan §Decisions |
| NFR-012 | Languages. | English first; Hindi as a dub | I-Con |
| NFR-013 | Identical inputs give identical audio and images, so cached work is valid. | Same inputs, same content hash **[NEEDS CLARIFICATION: model determinism unverified — gate 1]** | R27 |
| NFR-014 | Failures are loud and leave nothing misleading. | A missing model or dependency fails with a message naming it; no partial output is ever left under a finished file's name | `CONSTITUTION.md` §3 |
| NFR-015 | The first channel keeps a steady publishing rhythm. | Two long videos a week, each cut into short clips | A-20 |

## 6. Out of scope

- **A product for other creators.** I-Non.
- **Cloud rendering, and any upload of scripts or work in progress.** NFR-002. Paid tools are not banned, but none may be required (NFR-001, A-9).
- **Song remixes, recreated film scenes and made-for-kids content** in their risky forms. D-3.
- **Photoreal human faces** as a show's look, and **voice cloning of any real person**.
- **Copying code** from reference projects. I-Non.
- **Committing the studio to one genre.** I-Non — "content we will decide later".
- **The operator on camera or narrating.** A-10 — every host and voice is AI.
- **Closing or deleting a channel.** A-13 — a failing channel is improved, then paused.

## 7. Discrepancies with the code and config

| Where | What it says | Conflicts with |
|---|---|---|
| `studio/pipeline.py` `b5_voice` | `voice="af"` for every chunk | REQ-016, REQ-021 |
| `formats/character-narrative.yaml` | `length_minutes: [7, 10]` | NFR-011 — the plan decided 6–8 |
| `packs/mythology.yaml` | `rubric: rubrics/explainer-v1.yaml`; no story rubric exists | REQ-033 |
| `licenses.yaml` | Every allowed weight has `verified_on: null`, so `studio licence-audit` fails any real provider | REQ-034 — correct behaviour, recorded so it is not mistaken for a bug |
| `licenses.yaml` | No entry for ACE-Step 1.5 or Stable Audio 3, and no forbidden entry for YuE2 or the MuQ-MuLan encoder (both CC BY-NC 4.0) | D-6; REQ-034; REQ-049 |
| `studio/checks/__init__.py` `check_cohort` | Returns `kill`, `extend`, `keep` or `too_early` | REQ-043; A-13 — no channel is closed, so `kill` must become a recommendation to pause |
| Plan §Cohorts and kill gates; M7 | Kills channels at ninety days, and starts with a cohort of three | A-13, A-18 — improve then pause; one channel first |
| `.claude/` | 4 of the plan's 9 agents and 2 of its 9 skills exist | REQ-007, REQ-008–011, REQ-038–040 |
| `studio/pipeline.py` `b6_shots` | Sends every shot through the image provider; never calls the chart renderer | REQ-023 |

## 8. Delivery order

Per D-1 and the plan. Each milestone is accepted before the next starts.

| Milestone | Delivers | Requirements |
|---|---|---|
| M1.5 — First real episode | `trade-atlas-EP01` published unlisted on YouTube | REQ-012–020, REQ-023, REQ-025, REQ-027–029, REQ-034–036, REQ-039 (YouTube only), REQ-049 |
| M2 — Look and cast | Reusable characters, story look | REQ-008–011, REQ-026, REQ-030 |
| M3 — Voice and picture for story | Character voices, parallax stills, hero shots | REQ-021, REQ-024, REQ-033, REQ-048 |
| M4 — Post and master | Full production standard on story episodes | REQ-027–029 extended from data to story episodes; REQ-037 |
| M5 — Ship | First public video on all four platforms, Hindi dub, verticals | REQ-022, REQ-038–040, REQ-050 |
| M6 — Advisor and learning | Advisor, performance feedback, packaging tests | REQ-007, REQ-045, REQ-047 |
| M7–M8 — More channels | Second and later channels once the first has been monitored; supplied stories; more genres | REQ-002, REQ-041–044, REQ-051 |

REQ-001, REQ-003–006, REQ-031–032, REQ-046 are already built and are regression-tested in
every milestone. Placing REQ-002 and REQ-041 in M7–M8 is a proposal: the plan schedules neither.

## 9. Open questions

| ID | Question | Owner |
|---|---|---|
| Q-001 | Which voice and accent narrates trade-atlas? **Resolved by A-15:** chosen by audition (REQ-019), possibly two or three alternating voices. | Operator |
| Q-002 | When does month 1 of NFR-005 begin? **Resolved by A-7:** the day the first video goes public. | Operator |
| Q-003 | Can AI song videos be made without breaking "never generate music"? **Resolved by D-5, then D-6:** a commercially licensed local model exists, so the rule changed and AI music is allowed. | Operator |
| Q-004 | How many hours a week can the operator give? **Resolved by A-8:** 10–20. | Operator |
| Q-005 | How should "item 1500.0000" be spoken? An editorial call for the writer before LOCK 1. | Writer |

## 10. Acceptance criteria

Gate 8 validates each milestone against the requirements listed for it in §8.

| ID | Criterion | Verifies |
|---|---|---|
| AC-001 | `trade-atlas-EP01` uploaded unlisted to YouTube: charts cut to real narration, every production-standard target met, all three locks opened by recorded human decisions, and the AI disclosure set. | M1.5 requirements; REQ-031; REQ-036; NFR-004; NFR-011 |
| AC-002 | A host and one cast character render recognisably across ten stills in three unrelated scenes; a character resembling a real person is refused. | REQ-008–010 |
| AC-003 | A story episode scores against the story rubric, with each character in its own voice. | REQ-021; REQ-033 |
| AC-004 | One episode is live as long-form on YouTube and Facebook, with at least twenty derived posts across four platforms and a Hindi track. | REQ-022; REQ-038–040; NFR-012 |
| AC-005 | The advisor answers all four kinds of question against real published data, tagging every figure. | REQ-007; REQ-045 |
| AC-006 | An operator-written story becomes an episode without research or writing stages, and still stops at LOCK 1. | REQ-002 |
| AC-007 | Month 12 and month 18 checkpoints of NFR-005 evaluated from real channel data. | NFR-005 |
| AC-008 | The full test suite passes without model weights present. | NFR-010 |
| AC-009 | A full production run makes no paid API call and no upload but the finished video, with peak VRAM measured within 8,151 MiB. | NFR-001–003 |
| AC-010 | Gate 6 review finds no orchestration framework, every new dependency justified in the constitution, and no code from a reference repository. | NFR-008; NFR-009 |
| AC-011 | A deliberately missing model makes its stage fail with a message naming it, and no finished-named file exists afterwards. | NFR-014 |
| AC-012 | The first real episode records its GPU hours, the operator's time at each lock, and zero regenerated chunks on a repeat run. | NFR-006; NFR-007; NFR-013 |
| AC-013 | The first public channel sustains two long videos a week for its first month, within 10–20 operator hours a week. | NFR-007; NFR-015 |
| AC-014 | A ninety-day review never closes or deletes a channel; its lowest outcome is a recommendation to pause. | REQ-043 |
| AC-015 | Choosing a second channel produces a recorded decision covering topic, format, characters, voices and look, scored on earnings, cost and safety. | REQ-044; REQ-051 |
