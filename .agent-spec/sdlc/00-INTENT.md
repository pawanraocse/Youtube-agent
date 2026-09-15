# 00 — Intent: the story-to-video YouTube creator

The originator's idea, in their own words, before gate 0 turns it into requirements.
Quoted text keeps the originator's wording; only spelling, capitals and dashes are
normalised, and `[brackets]` mark the two places a typo had to be read. Unquoted text is a paraphrase and says
so. Nothing here is a requirement or a design.

**Originator:** Pawan · **Captured:** 2026-09-15 · **Drawn from:** the originator's messages
from 2026-09-12 to 2026-09-15, while this repository was planned and built.

---

## What

> "we want to create a YouTube content creator — who takes story and create AI videos"
> *(2026-09-15)*

The first description, paraphrased: give it a topic such as the Mahabharata, and it
researches it, works out the epic detail, defines the characters once so the same
characters appear in every video, makes the AI videos, and — in their words — will
"publish and monetise them". The topic was only ever an example: "Mahabharat is just an
example — we need to create full pipeline for doing this."

Characters are central:

> "Make sure these can be done with specific characters — so people can relate — we may
> need a skills to define and reuse the characters"

It is not tied to one kind of content:

> "we can have kids channel / songs mess up and create with AI / even reproduce movie
> screens with AI / History channel / geography / knowledge / Vedas / anything just
> anything — but plan to earn money"

> "may be not only drama — it can be anything / comedy / romance / songs / Veda /
> mythology / religious etc etc etc"

The production bar is the DramaBox app:

> "I want the same quality of videos — content we will decide later — but clarify
> [clarity], quality, audio, background etc this is something I want to achieve"

And it should advise the operator:

> "create skill who can answer questions and guide in content creation what topic we
> should pick, what can harm us and how to keep it safe and what next can be done for max
> profits"

## Why

> "my aim is to monetise and earn money" · "ONLY AIM to make money"

> "it must be able to monetise and get viral" · "this must be master piece to make viral
> content and monetise on various platforms"

Across platforms — "Facebook, Insta, YouTube etc etc" — and across as many channels as
there are ideas:

> "we can open as many channel and create any content — as ideas come — we will create —
> not stick to mythology" · "we are open to anything / create any content — where we can
> make max money"

It has to keep working:

> "even after 12 months — it should have 70% chance it must work"

## Constraints

- **Free.** "we should be able to create free — using WSL, Ollama, Claude subscription we
  have or any free open source tool" · "we can use Hugging Face or Google or anything that
  can help"
- **High quality.** "Make sure video is high quality and engaging" — to the DramaBox bar
  above.
- **Agents and skills, run from Claude.** "multiple AI agents for dedicated work and
  orchestration" · "we can run this from Claude — so even skills should be fine with hybrid
  Python framework — to keep it balance, dedicated, to the point, aligned and focused"
- **Professional, every stage reviewed.** "make sure agents are very professional level and
  all cycle like editing, testing validation" · "research / content in text / filtering and
  finalise with review until get it best / starting videos and short clips / review (until
  final) / editing, voice over, dubbing / review until final"
- **The stages a real creator needs, and no more.** "you need to decide the real stages
  which are necessary and helpful for a real content creator" · "think like a real content
  creator and add dedicated skill or agent or [for] each step — keep it simple and
  straight" · "if feel over engineering at any place — let's fix it"
- **Reference, never copy.** "we are not copying them — or give credit — only take
  reference and create our agent for video research and creation"
- **Stick with the plan.** "Stick with plan and HLD" *(2026-09-15)*. The approved plan
  stands as the baseline. No HLD document exists yet — gate 3 produces one.
- **Local only**, chosen at onboarding *(2026-09-12)*: nothing leaves the machine except
  finished uploads.
- **Language and length**, chosen from options while planning *(2026-09-12)*: English
  first with a Hindi dub, and long-form episodes cut into Shorts.
- **Channel first.** "we don't need dual for now — first focus is to get the YouTube
  content automated and ready" *(2026-09-12)*
- **The machine** — a fact of the hardware, not a choice: one laptop GPU with 8 GB of video
  memory, which is why full AI video cannot render every shot.

## Non-goals

- **A product for other creators.** "we don't need dual for now"; and at onboarding the
  studio was chosen to be own tooling, not a product.
- **Copying code** from any reference project.
- **Paid tools** on the production path — "create free".
- **Fixing the genre up front** — "content we will decide later".

## Open questions

Left for gate 0. Each is a place where the originator's words and what has been built so
far do not yet line up. Answering them here would put words in the originator's mouth.

1. **What does "takes story" take in?** The first description started from a topic that the
   studio researches into a story. Is that still the input, or does the operator sometimes
   hand over a finished story?
2. **Which kind of AI video comes first?** The words point at character-driven story video
   — recurring characters, DramaBox quality. On 2026-09-15 the originator approved a build
   order that makes a narrated data-explainer episode first (the Panama Canal water story,
   told with charts), because it needs no image model. Does "takes story and create AI
   videos" keep that order, or put character story video first?
3. **Songs, movie scenes and kids' content.** The originator proposed "songs mess up and
   create with AI", "reproduce movie screens with AI" and "kids channel". The approved plan
   excludes them on monetisation grounds: remixed songs send revenue to the rights holder,
   recreated film scenes infringe copyright, and made-for-kids content loses most of its
   ad revenue. Are these non-goals, or wanted in a form that pays — original AI songs, film
   analysis, general-audience stories?
4. **What does "it must work" mean?** The originator asked for a 70% chance of working after
   12 months. The approved plan instead targets at least $500 a month across a portfolio of
   channels by month eighteen, at 65–70% confidence. Which measure stands?
