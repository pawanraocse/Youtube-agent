# Requirements — AI YouTube & Content Engine

**Status:** active. Supersedes nothing; this is the requirement of record, and the
implementation plan at `~/.claude/plans/we-create-plan-sleepy-moth.md` is how it gets built.

**Scope decision, 2026-09-12:** the original brief describes a *dual play* — run a channel,
and separately build an orchestration SaaS for other creators. **Only the first is in
scope.** The first objective is automated, published YouTube content. The SaaS is deferred,
not cancelled: §7 records what would have to be true to revisit it, and nothing in the
current design forecloses it.

---

## 1. The original brief

Reproduced because it is the source of the requirement and its judgements should stay
auditable, not because every figure in it survives contact with the decisions in §4.

> **Verdict: GO as a dual play** — run a channel for brand-building and cash flow;
> optionally build the orchestration SaaS for other creators.
>
> AI-powered YouTube channels are making real money in 2026. Top faceless channels earn
> $80,000+ per month. The AI production stack is mature: ChatGPT/Claude for scripts,
> ElevenLabs for voiceover, Pictory/Fliki for video, Canva/Midjourney for thumbnails. A
> single creator can produce 2–4 high-quality videos per week at a cost of ~$200/month in
> tools.
>
> **Pitch (Channel):** AI-powered content production that turns research into polished,
> monetizable videos at 10x the speed of traditional production.

**Why it works, as argued in the brief**

- Top AI-assisted faceless channels earn $80K+/month from AdSense alone.
- The AI production stack is mature and affordable.
- YouTube does not ban AI content; it rewards AI-assisted content with genuine human
  editorial value.
- 50M+ YouTube creators globally, most using fragmented tool stacks.
- No single platform orchestrates the full pipeline from idea to published video.
- AI channels can be launched alongside a primary startup as a brand and revenue multiplier.

**A note on the figures.** Several currency ranges in the source lost their lower bounds in
transit — "$80,000+ per month", "$200/month", "$40 per 1,000 views" were written as ranges
and arrived as single values. The upper bounds are reproduced as received. Nothing in this
document reconstructs a missing lower bound, because a guessed number that looks sourced is
worse than an obviously incomplete one.

### 1.1 The production stack as originally specified

| Phase | Original tools | Output |
|---|---|---|
| Research & ideation | ChatGPT / Claude; vidIQ / TubeBuddy | Topic plus structured outline |
| Script | ChatGPT / Claude, then human review for personality and fact-check | 1,500–3,000 words |
| Voiceover | ElevenLabs (stated gold standard); Murf; or own voice | 8–15 minutes of narration |
| Visuals | Pictory / Fliki for stock matching; Midjourney / DALL·E for stills and thumbnails; CapCut / Descript for edit | Finished video |
| Optimise & upload | AI title, description, tags; Canva thumbnail; YouTube Studio; OpusClip for Shorts | Published |

Stated economics: ~$200/month in tools, 2–4 hours per video, 2–4 videos per week.

### 1.2 Niches, as ranked by the brief

Personal finance / investing ($40 RPM), legal / tax explainers ($35), business /
entrepreneurship ($30), technology and AI tutorials ($25), crypto / Web3 ($25), health /
wellness ($20), history / documentaries ($15).

### 1.3 YouTube's 2026 AI rules, as understood by the brief

- AI content is not banned. "AI slop" is penalised.
- **Inauthentic content policy:** mass-produced, formulaic, interchangeable videos get
  demonetised.
- **Mandatory disclosure** of realistic AI-generated visuals or cloned voices.
- The algorithm rewards **net information gain** and high viewer retention.
- Punished: generic templates, bulk uploads with no human touch. Rewarded: unique editorial
  perspective, deep storytelling, genuine human review.

### 1.4 Risks the brief itself raised

| Risk | Severity | Response in the brief |
|---|---|---|
| Only ~3% of AI channels reach monetisation | High | Quality over quantity; high-RPM niche |
| YouTube tightens on AI content | Medium | Genuine human editorial value; follow disclosure rules |
| Content quality risk ("AI slop") | High | Human-in-the-loop review; brand voice; quality scoring |

---

## 2. Objective

Produce and publish monetisable video, on multiple platforms, without a per-unit cost, and
without a human doing the work that a machine can do — while keeping a human at every point
where a machine's judgement would put the money at risk.

Success is **≥$500/month across a portfolio by month eighteen, at 65–70% confidence.**

---

## 3. Functional requirements

Numbered for traceability. "Built" means it exists and is covered by a test; "specified"
means the plan defines it and no code implements it yet.

### Content production

| # | Requirement | State |
|---|---|---|
| R1 | Take a topic and produce a published episode without per-step human authoring | Built through B4; B5–B11 built against mock media |
| R2 | Research a topic into tiered sources, each tied to the specific claim it supports | Built (A2) |
| R3 | Refuse to write a claim that no source supports | Built (`check_script`) |
| R4 | Package before scripting — title variants, thumbnail concept, an eight-word promise | Built (B1) |
| R5 | Structure into beats with clippable moments marked at the beat sheet | Built (B2) |
| R6 | Narration chunked per sentence with authored pauses | Built (B3) |
| R7 | Voice-over as the timing spine; picture cut to it, never the reverse | Built against mock TTS (B5) |
| R8 | Generate picture locally; cut on clause boundaries | Built against mock providers (B6) |
| R9 | Master to the production standard, enforced numerically | Built (B9, `check_master`) |
| R10 | Multiply one episode into ~25 assets across four platforms | Built against mocks (B10) |
| R11 | Hindi dub, time-fitted per beat | Specified |
| R12 | Publish to YouTube, Facebook, Instagram, TikTok; degrade to a folder drop | Built against mock publisher (B11) |

### Quality and compliance

| # | Requirement | State |
|---|---|---|
| R13 | Three human locks — script, picture, master. No agent advances past one | Built |
| R14 | Deterministic checks run before any critic | Built |
| R15 | No agent reviews work it produced | Built (writer ≠ critic; producer ≠ compliance) |
| R16 | Rubrics are versioned and agent-immutable | Built |
| R17 | Review loops cap at three iterations, then escalate with the score trend | Built |
| R18 | Refuse an unmonetisable concept at A1 and name the version that pays | Built (`check_demand`) |
| R19 | Every model weight permits commercial use | Built (`studio licence-audit`) |
| R20 | Music cleared per platform, checked at LOCK 3 | Built |
| R21 | **Disclose AI-generated visuals and synthetic voices on every platform that requires it** | **Not built — see §6** |
| R22 | **Score net information gain as a rubric dimension** | **Not built — see §6** |
| R23 | Refuse a character resembling a real identifiable person | Specified (M2) |

### Recurrence and reuse

| # | Requirement | State |
|---|---|---|
| R24 | Reusable characters registered once at studio level, reused across channels | Specified (M2) |
| R25 | A show bible — locations, look, audio palette — locked before episode one | Specified |
| R26 | Resume after a crash without re-paying for completed work | Built |
| R27 | Identical prompts never regenerate | Built (content-addressed store) |

### Business operation

| # | Requirement | State |
|---|---|---|
| R28 | Run several channels at once; adding one must not touch `studio/core/` | Built (`packs/` × `formats/`) |
| R29 | Cohorts of three, evaluated at ninety days on numeric criteria | Built (`studio check-cohort`) |
| R30 | Rank ideas by revenue per GPU hour | Built (computed at A1 ingest) |
| R31 | Affiliate configuration written into every description from video one | Specified (`channel.yaml`, A0 — **neither exists**) |
| R32 | Feed measured performance back into what gets made next | Specified (M6) |
| R33 | Answer what to make next, what could harm us, how to stay safe, what pays more | Specified (`/studio-advisor`) |

---

## 4. Where this requirement differs from the original brief

Each of these is a deliberate reversal with a reason. The brief is the requirement; these
are the places where following it literally would have cost money or time.

| Original | Decision | Why |
|---|---|---|
| ~$200/month tool stack — ElevenLabs, Pictory, Midjourney | **Zero marginal cost. Local models only** | A per-unit cost multiplied across a portfolio is the thing that kills the portfolio. Five channels at four videos a week is not a $200 bill. The cost of this choice is real and is paid in quality ceiling and GPU hours, not in dollars |
| One channel, 2–4 videos/week | **A portfolio in cohorts of three, with ninety-day kill gates** | The brief's own risk table says ~3% of AI channels reach monetisation. That number argues against betting on one channel far more strongly than it argues for trying harder on one |
| $20K+/month by month 12–18 | **≥$500/month by month eighteen at 65–70% confidence** | $80K/month channels exist and are the top of a power law. A plan that promises the top decile as its median is wrong, and the honest per-channel figure is 25–30% |
| 8–15 minute narration | **6–8 minute episodes** | 50–100 videos of algorithm signal in four to seven months instead of six to twelve |
| Human review "adds personality and fact-checks" | **Three hard locks with a recorded decision each** | Same intent, enforced. `gate_is_open()` rejects a NULL decision and rejects `'agent'`, so the audit trail exists whether or not anyone remembers to care |
| Niches ranked by RPM | **Ranked by revenue per GPU hour** | RPM alone prefers niches with no audience. The two rankings largely agree — finance, business and legal/tax score well on both — but the brief's own history/documentary pick fails on GPU cost |
| Dual play: channel plus SaaS | **Channel only** | Developer instruction, 2026-09-12 |
| "AI as a tool = fine" | Same, and **stylised rather than photoreal** | 8 GB of VRAM cannot beat the uncanny valley. A clean stylised render at 1080×1920 with excellent audio reads as high production value; a mediocre photoreal attempt reads as slop |

---

## 5. Non-requirements

Explicitly out of scope, so that nobody builds them by drift:

- The orchestration SaaS, in any form — no multi-tenancy, no auth, no billing, no API
  stability obligation.
- Any cloud render path. Nothing leaves this machine except finished uploads.
- Any paid API on the production path.
- Music generation. The library is downloaded once and tagged.
- Content the brief's own analysis shows destroys its revenue: song remixes and mashups,
  film-scene recreation, and anything "made for kids" under COPPA.
- Code copied from any reference repository.

---

## 6. Gaps this document opens

Two requirements come from the original brief, are load-bearing for monetisation, and have
no implementation and no plan entry. Both were found by writing this document.

**R21 — AI disclosure.** The brief lists mandatory disclosure of realistic AI-generated
visuals and cloned voices as a platform rule. Searching the repository for it returns
nothing: no check, no config field, no metadata written by `studio-distributor`. The
`/studio-advisor` risk sweep mentions "AI-disclosure exposure" as something to look at,
which is not the same as a master that cannot ship without the flag set. Since undisclosed
synthetic media is one of the few things that gets a channel demonetised outright, this
belongs as a deterministic check at LOCK 3 and a per-platform field written at B11 —
exactly where music clearance already sits.

**R22 — net information gain.** The brief identifies it as what the algorithm rewards. The
`explainer-v1` rubric scores factual fidelity, hook strength, pacing and sensitivity. A
script can score 100 on all four while telling a viewer nothing they could not have found
in the first search result — which is the precise definition of the "interchangeable"
content the inauthentic-content policy demonetises. This should be a rubric dimension with
real weight.

**R31 is also unbuilt in a way the plan does not admit.** `channel.yaml` does not exist
anywhere in the repository and stage A0 is an enum value with no implementation. Affiliate
revenue is the one stream that can start at video one rather than at 1,000 subscribers, so
this is the cheapest unbuilt thing on the list.

---

## 7. What would reopen the SaaS question

Recorded so the decision is revisited on evidence rather than on enthusiasm. The plan's own
assessment is that operating this pipeline for other people is the highest-probability
revenue in the document — closer to 80%, paying sooner, and independent of any
recommendation algorithm. That remains true and is deliberately not being acted on.

Revisit when all three hold:

1. The pipeline has produced published episodes on at least two channels without manual
   intervention between the locks.
2. At least one channel has cleared its ninety-day cohort gate on measured data.
3. Someone who is not the developer has asked to use it.

Until then it is a business option, not a design constraint, and no abstraction in this
codebase may be justified by it.
