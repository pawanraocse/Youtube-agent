# 00 — Intent: the story-to-video YouTube creator

The originator's idea, in their own words, before gate 0 turns it into requirements.
Quoted text keeps the originator's wording; only spelling, capitals and dashes are
normalised, and `[brackets]` mark the places a typo had to be read. Unquoted text is a paraphrase and says
so. Nothing here is a requirement or a design.

**Originator:** Pawan · **Captured:** 2026-09-15 · **Updated:** 2026-09-15 with the originator's answers · **Drawn from:** the originator's messages
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

*(The order is set by A-18 and A-19: one channel first, more once it has been learned from.)*

It has to keep working:

> "even after 12 months — it should have 70% chance it must work"

*(Measured by A-4 and A-7: checkpoints at months 12 and 18, counted from the first public video.)*

What it comes down to, in the originator's closing words:

> "this is our job to earn money and make good content" *(2026-09-15)*

## Constraints

- **Free.** "we should be able to create free — using WSL, Ollama, Claude subscription we
  have or any free open source tool" · "we can use Hugging Face or Google or anything that
  can help" *(refined by A-9)*
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
- **Free music.** "we must use music for which we don't have to pay — we can alter music
  or create mix, change something .. Just AI generated may be — try searching music which
  can be used for free" *(2026-09-15)*
- **Stick with the plan.** "Stick with plan and HLD" *(2026-09-15)*. The approved plan
  stands as the baseline. No HLD document exists yet — gate 3 produces one. *(Note, not the
  originator's words: where an answer below differs from the plan — A-13, A-18 — the answer
  is the newer instruction.)*
- **Local only**, chosen at onboarding *(2026-09-12)*: nothing leaves the machine except
  finished uploads.
- **Language and length**, chosen from options while planning *(2026-09-12)*: English
  first with a Hindi dub, and long-form episodes cut into Shorts *(timing and cadence set by A-20 and A-21)*.
- **Channel first.** "we don't need dual for now — first focus is to get the YouTube
  content automated and ready" *(2026-09-12)*
- **The machine** — a fact of the hardware, not a choice: one laptop GPU with 8 GB of video
  memory, which is why full AI video cannot render every shot.

## Non-goals

- **A product for other creators.** "we don't need dual for now"; and at onboarding the
  studio was chosen to be own tooling, not a product.
- **Copying code** from any reference project.
- **Needing paid tools.** The creator must work for free; spending is a case-by-case choice
  when results are promising (A-9).
- **The originator on camera or narrating** — "Never, fully AI" (A-10).
- **Closing a channel** — a failing channel is improved, then paused, "but won't close it" (A-13).
- **Publishing from personal accounts** — new brand accounts only (A-22).
- **Fixing the genre up front** — "content we will decide later".

## Open questions

These were open when this file was first written. The originator has since answered all
four — see **Answers** below. They stay here so the reasoning behind each answer is kept.

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

## Answers

The originator's answers, given on 2026-09-15. Most were picked from options Claude offered:
the quoted label is what they chose, and the rest says what it means in plain words. Where
the originator wrote their own words, those are quoted instead.

| # | Question, in short | Answer |
|---|---|---|
| A-1 | Which kind of video first? *(open question 2)* | "Finish data-explainer first" — the Panama Canal episode, told as a story with charts and narration, ships first. Character story videos come next. |
| A-2 | What does it take in? *(open question 1)* | "Either a topic or my story" — usually a topic the studio researches and writes; sometimes a finished story, which skips research and writing but is still reviewed. |
| A-3 | Song remixes, movie scenes, kids' channel? *(open question 3)* | "Only the forms that pay" — original AI songs, film analysis with original visuals, and stories for a general audience instead. |
| A-4 | How is success judged? *(open question 4)* | "Two checkpoints" — month 12: at least one channel accepted into the YouTube Partner Program. Month 18: at least $500 a month across all channels. |
| A-5 | AI songs, given the old "never generate music" rule? | "Park them for now" — **replaced by A-6.** |
| A-6 | Music we don't pay for | In their words: "we must use music for which we don't have to pay — we can alter music or create mix, change something .. Just AI generated may be". After a licence search they chose "AI first, free library fallback": music is generated by a free model licensed for commercial use (ACE-Step 1.5 first), with free libraries (Incompetech, Pixabay) as fallback, and a track is altered only when its licence allows it. |
| A-7 | When do the month-12 and month-18 checkpoints start counting? | "From first public video" — month 1 begins the day the first video goes public; building time does not count. |
| A-8 | How many hours a week can the originator give — reading scripts, approving videos, uploading? | "10–20 hours" — a serious side project. |
| A-9 | Must everything stay free, or is some spending ever OK? | In their words: "it would depend for sure — if things are promising I can ok to spend. but can't spend millions. once start earning then it is more flexible to spend — no issues". Free by default; spending is a case-by-case decision when results are promising, and easier once channels earn. |
| A-10 | Will the originator's own face or voice ever appear? | "Never, fully AI" — an AI host and AI voices only; the originator stays behind the scenes. |
| A-11 | Which topics should the channels never touch? | In their words: "Nothing as of now — open for anything as long as I can and it seems valuable". No topic is ruled out by choice. *(Note, not the originator's words: platform policy and the rights check still refuse what cannot be published or monetised.)* |
| A-12 | Where do videos go first when they go public? | "All four at once" — YouTube, Facebook, Instagram and TikTok together from the first public video. |
| A-13 | If a channel isn't working after 90 days, is it shut down? | In their words: "will decide case by case — since this will be fully automated — I will try to revise, find out it is not working, make improvements — at a point if I feel this is not working then will try to work on other channel but won't close it — if find solution and can improve I will try to". Channels are improved, then paused if still failing — **never closed**. *(Note, not the originator's words: this replaces the approved plan's 90-day kill rule; the 90-day numbers become advice, not a verdict.)* |
| A-14 | "Fully automated" — how much does each video still stop for the originator? | "Keep all 3 checks" — script, rough cut and final video each wait for the originator's OK. "Fully automated" means everything between those three checks runs on its own. |
| A-15 | What should the narrator voice sound like? | In their words: "We can create a process for each character and channel — in beg[inning] we will hear couple of voices and finalise — may be in some cases two or 3 voices will be used in alternate". Voice is chosen by a repeatable audition for every character and every channel. A channel may alternate two or three voices. *(Note, not the originator's words: the plan assumed one voice per character; alternating voices is new.)* |
| A-16 | Which story channel comes after the Panama data channel? | In their words: "we need to have a proper pipeline and process for deciding it time to time and finalise based on certain parameters — where we both share inputs... it includes steps — decide topic, characters, voices, etc etc etc". Choosing a new channel is itself a repeatable process, run whenever needed, scored on agreed criteria, with both the originator and Claude giving input. It covers topic, characters and voices. |
| A-17 | What should count most when deciding the next channel or topic? | "Expected earnings", "Cost to make" and "Safety" — likely earnings, computer and operator time per video, and low risk of claims, demonetisation or strikes. The originator's personal interest was offered and **not** chosen. |
| A-18 | When videos go public, how many channels run at once? | In their words: "depends — nothing decided yet — it will depend as we proceed — we will first try with 1 channel — try that for sometime with full energy — on its response we will take call with learnings". **One channel first**, run properly for a while; more channels only after learning from it. *(Note, not the originator's words: the plan's 65–70% figure assumed several channels at once.)* |
| A-19 | One channel lowers the odds — what happens to the month-12 and month-18 goals? | In their words: "for sure — we will start another channel — even after some time we can try to work in channels in parallel. important is to take learnings too — when we launch first — we have to monitor for sometime — then launch second, third or as many we like and decide". More channels will follow: launch one, monitor it, learn, then add the second, third and more, eventually in parallel. The originator did not ask to lower the goals. |
| A-20 | How often does the first channel publish a new long video? | "Two a week" — two long videos a week, with short clips cut from each automatically. |
| A-21 | Hindi versions — when and how? | "Later, as a dub" — English first; once English works, Hindi narration is added to the same videos rather than a separate channel. |
| A-22 | Which accounts publish the videos? | "Create new ones" — new brand accounts on YouTube, Facebook, Instagram and TikTok, kept apart from the originator's personal accounts. |
