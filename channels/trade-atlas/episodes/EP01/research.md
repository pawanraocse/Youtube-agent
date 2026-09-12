# EP01 — Research: the Panama Canal as a water market

Topic: *Why the world's busiest shipping shortcut is running out of water.*
Angle under test: a transit slot is a price on drinking water. Divide an auction bid by the
water a transit spends, compare it to what a Panama City household pays per cubic metre.

**Verdict on the angle: it holds, and it is stronger than the producer wrote it.** The canal
does not merely *imply* a price for water — it publishes one. See "The counter-intuitive
fact" below. Three numbers in the brief need correcting before they go on screen; they are
flagged in **CORRECTION** blocks and each correction makes the argument better, not worse.

---

## 1. The spine: three prices for the same cubic metre

Everything the episode argues reduces to one chart with three bars, all in $/m³ of Gatún Lake
water. All three are computed below from opened sources, and every intermediate step is shown
so the writer can caption the arithmetic rather than assert it.

| What | $/m³ | Kind of number |
|---|---|---|
| Panama City household, 2018 | **$0.21** [s9] | Measurement (revenue ÷ volume sold) |
| The canal's own average, FY2025 | **~$2.13** [s4] | Derived estimate — see working |
| Record auction slot, 1 Sept 2026 | **~$27** [s15][s16] | Derived estimate — see working |

### The water a transit spends

A Panamax transit spends about **52 million US gallons ≈ 197,000 m³** of Gatún Lake water.
**This figure has no primary ACP source that I could open.** The ACP's own public pages
[s6][s7] talk in hm³/day, savings percentages and "transits' worth of water", never in
gallons per transit. Every gallons-per-transit number in circulation traces back to press and
engineering restatements. What I *can* verify from ACP directly is the system-level flow: in
the 2023 drought, outflows ran **ten hm³/day against seven hm³/day of inflow** [s6]. At the
31–34 transits/day the ACP was running then [s7][s13], ten hm³/day divided across transits is
of the order of 300,000 m³ each — which includes municipal draw, evaporation and spill, so
~200,000 m³ of *lockage* water per transit is consistent with the ACP's own hydrology. Treat
197,000 m³ as an **estimate with a ±10% band**, and caption it as such.

> **CORRECTION 1 — the record bid was a Neopanamax transit, not a Panamax one.**
> The G. Spirit is a 54,502 dwt gas carrier [s19]; VLGCs of that class do not fit the
> 32.31 m Panamax chambers and take the Neopanamax locks, which is why the ACP advisory
> shows the Neopanamax auction slot as the one in play [s1]. So the divisor should be the
> *Neopanamax net* figure, not the Panamax one. This does not break the arithmetic: the
> Neopanamax chambers draw far more water per lockage but recover about 60% of it in their
> water-saving basins, landing within about 7% of the Panamax figure. **The two are close
> enough that ~200,000 m³ works for both — but the script must not say "Panamax" while
> pricing a Neopanamax bid.** Say "a large-lock transit" and give the band.
> *I could not verify the 7% figure against a primary or academic source — it appears only in
> secondary engineering write-ups. Do not put "7%" on screen.*

### Working

```
Record bid          $5,300,000 ÷ ~197,000 m³ = $26.90/m³   → say "about $27"
Previous record     $4,600,000 ÷ ~197,000 m³ = $23.35/m³
Mar–Apr 2026 avg      $385,000 ÷ ~197,000 m³ =  $1.95/m³
Pre-conflict base     $137,500 ÷ ~197,000 m³ =  $0.70/m³
Feb 2026 median        $55,000 ÷ ~197,000 m³ =  $0.28/m³

Canal average, FY2025:
  13,404 transits × ~200,000 m³ = ~2.7 billion m³ of lockage water   [s4]
  B/.5,705,000,000 revenue ÷ 2.7 bn m³            = $2.13/m³         [s4]

Ratio to household:  $26.90 ÷ $0.21 = 128×   |   $26.90 ÷ $0.26 = 103×
```

> **CORRECTION 2 — say "about a hundred times", not "$27 against $0.26".**
> The household figure is old and there are two of them: **$0.21/m³ for 2018** from an
> ACP-commissioned study using IDAAN's own revenue and volume [s9], and **$0.26/m³ for 2012**
> from Wikipedia's reading of ASEP [s22]. The producer's brief used the 2012 one. Prefer
> [s9]: it is eight years fresher, it is hosted by the ACP itself, and its method is stated
> (total revenue ÷ total volume sold). Either way the ratio lands between 103× and 128×, so
> the honest on-screen claim is **"roughly a hundred times"**, captioned with the year of the
> tariff. Do not put a decimal ratio on screen.

**The middle bar is the one nobody else has.** $2.13/m³ is the canal's *average* realised
price for the water it spends — a number that sits between the household tariff and the
auction spike and shows that the auction is not the canal's business model, it is the canal's
scarcity signal.

---

## 2. The counter-intuitive fact

**The Panama Canal already publishes a price for fresh water, and it is a logistic curve.**

ACP Official Tariff item 1500.0000 [s3] is not a metaphor. It charges every vessel over 300
feet LOA a **fixed $10,000 fresh water surcharge**, plus a **variable 0–10% of total tolls**
given by

```
f(x) = 0.10 / (1 + e^(0.6(x − 82)))
```

where *x* is the official Gatún Lake depth in feet on the day before the transit. The canal
has written the price of scarcity into a formula, with its inflection point at **82 feet** —
the level at which the surcharge is exactly 5% of tolls. Evaluated against the lake levels in
the record [s18]:

| Gatún Lake | Fresh water surcharge |
|---|---|
| 85.0 ft (normal pool) | 1.4% of tolls |
| 84.3 ft (early Aug 2026) | 2.0% |
| 82.8 ft (projected mid-Oct 2026) | 3.6% |
| 82.0 ft (curve inflection) | 5.0% |
| 79.0 ft (2023 drought floor) | 8.6% |

Ten channels have made "the lake is low, ships are queuing, here is the $1.6bn fix." None of
them has shown the audience that the canal's own tariff sheet contains a *water price curve*.
This is the cold open: a formula, on screen, that turns a lake level into money. It proves the
episode's premise from the ACP's own document rather than from the presenter's inference, and
it is a chart nobody else in the competitor set has drawn.

**Runner-up counter-intuitive fact,** for the Río Indio act: Panama is spending **$1.6 billion
to buy new water while losing 40–55% of the water it already treats.** Panama City's metro
system produced 303 MGD in 2015 with only 57% of customers metered [s10] — that is roughly
120–165 MGD leaking away, comparable to two or three transits' worth of lockage water every
day. And the ACP's *own consultant* priced the fix: leak reduction at 56 MGD for $2.6m/MGD
and metering 115,000 connections at 48 MGD for $1.2m/MGD — about **104 MGD recovered for
~$204 million**, roughly an eighth of Río Indio's price [s11]. That reframes Río Indio exactly
as the angle wants it reframed, but with the state's own numbers.

---

## 3. The auction price series (the main chart)

| Date | Clearing price | Source |
|---|---|---|
| Pre-Hormuz-conflict baseline | $135,000–$140,000 | [s17] — ACP Administrator, direct |
| February 2026 median | ~$55,000 | [s19] |
| March–April 2026 | ~$385,000 | [s17] |
| Aug 2026, Neopanamax high since late July | $3.78m | [s18] |
| Aug 2026, Panamax high since late July | $2.63m | [s18] |
| Aug 2026, Neopanamax average | $2.5m | [s18] |
| Aug 2026 (G. Arete, SK Shipping) | $4.6m | [s15][s16][s19] |
| 1 Sept 2026 (G. Spirit) | **$5.3m** | [s15][s16][s19] |

**The single most important caveat, and it must survive to LOCK 1:** the ACP advisory shows
that of the 34 daily slots (32 from 15 September), **exactly three go to auction** — one
Neopanamax, one Super, one Regular [s1]. So $27/m³ is the price of the *marginal* ~9% of
capacity, bid up by the 20–25% of vessels that arrive with no reservation [s17]. It is a
scarcity signal, not the price the canal charges the fleet. A script that says "the canal
charges $27 per cubic metre" is wrong; a script that says "the last three slots each day now
clear at a price that values the water at about $27 per cubic metre" is right.

The Administrator's own line is the best quote available for the angle: **"We do not set
prices; the market sets the price."** [s17] He also gives the bidder count: 18 bidders for one
slot at the peak, against a normal two to three [s17].

---

## 4. Verification status of every load-bearing figure

**Verified against two independent sources:**

- $5.3m record, G. Spirit, 1 September 2026 — [s15] gCaptain, [s16] Maritime Executive,
  [s19] Marine Insight. Three sources agree.
- $4.6m previous record, G. Arete — [s16], [s19].
- More than 50% of Panamanians drink from the canal watershed — ACP states it three separate
  ways: ">50% ... from Lakes Gatun and Alhajuela" [s5], "55% of the population" [s7], and
  "80% of the daily consumption in the provinces of Colon, Panama, and West Panama" [s6].
- Household tariff order of magnitude — $0.21/m³ 2018 [s9] and $0.26/m³ 2012 [s22] bracket
  each other; the ratio to the auction price is robust across both.
- 2023–24 was a record low — EIA says lowest lake levels since at least 1965 [s13]; ACP says
  2023 rainfall 25.6% below the 73-year average [s6]; UNCTAD says transits down over half from
  the Dec 2021 peak [s12].
- Río Indio cost and timeline — approval and six-year build from the ACP [s8]; 2027 start,
  four-year construction, 4,600 ha, 8.7 km tunnel from Mongabay [s20].
- FY2024 collapse — ACP's own release [s5] and UNCTAD's independent transit series [s12].

**Recorded on a single source only — the script must attribute these, not assert them:**

- The $135,000–$140,000 pre-conflict auction baseline and the ~$385,000 March–April figure.
  Only [s17], though it is the ACP Administrator speaking on the record, which is as good as a
  single source gets.
- Gatún Lake at 84.3 ft in early August 2026 and the 82.8 ft mid-October projection [s18].
  The ACP publishes a daily lake level but I could not retrieve the series (see §6).
- The fresh water surcharge formula [s3]. Single-sourced but it is the ACP's own tariff
  document, which is the primary; no second source is needed or possible.
- The 303 MGD / 40–55% UFW / 57% metered cluster and the leak-vs-Río-Indio cost comparison
  [s10][s11]. One document, but it is ACP-commissioned and cites IDAAN's Boletín Estadístico
  and INEC directly.

**Could not verify at all — do not put on screen as fact:**

- **197,000 m³ (52 million gallons) per Panamax transit.** No primary ACP source. Consistent
  with ACP's own hm³/day hydrology [s6] but not confirmed by it. Caption as an estimate.
- **The "7% less water" Neopanamax-vs-Panamax claim.** Secondary engineering write-ups only.
- **The 60% water-saving-basin recovery rate.** Widely repeated; I found no ACP or academic
  primary stating it. The ACP's own page claims water-saving procedures "add up to saving as
  much as 50% of this resource" [s7-adjacent], which is a different measure.
- **The G. Spirit's 36.60 m beam.** Appears in search summaries of Splash247, which returned
  403 to every fetch. Argue the Neopanamax point from the vessel class and the advisory's
  Neopanamax auction slot [s1][s19] instead of from a beam figure.

---

## 5. What is genuinely contested

1. **The FY2024 transit count has three different values, two of them from the ACP itself.**
   The FY24 release says **9,944 deep-draft transits** [s5]; the FY2025 release, comparing
   like for like, says FY2024 was **11,240 transits** [s4] (a total including small craft);
   trade press widely reports **9,936**. The script must pick one basis, say which, and hold
   it. Recommendation: use FY2025's own comparatives — 13,404 in FY2025 against 11,240 in
   FY2024, a 19.3% rebound — because both numbers come from the same ACP release on the same
   basis [s4].

2. **The auction "normal" price depends entirely on which normal you mean.** The ACP
   Administrator says $135,000–$140,000 pre-conflict [s17]; Bloomberg's median for the months
   to February 2026 was ~$55,000 [s19]. These are not in conflict — one is a typical clearing
   price in a tight market, the other a median across a slack one — but they differ by 2.5×
   and the multiple the script quotes ("100× normal" vs "40× normal") swings on the choice.
   Show both on the chart; that variance *is* the story.

3. **Río Indio's price tag.** $1.6 billion is the figure the ACP and most outlets use [s8-era
   reporting]; Mongabay reports **$1.5 billion** [s20]. Separately, the ACP's own 2018 study
   costed a Río Indio scheme at **$359 million** for dam, inter-basin transfer and
   appurtenances in 2018 dollars, escalated from a 2003 estimate [s11]. That is a different
   and narrower scope — the 2025 project carries around $400m of social compensation,
   resettlement and environmental mitigation — but a fourfold-plus real escalation in seven
   years is worth one honest sentence rather than being hidden.

4. **Whether Río Indio should be built at all.** 38 farming communities and about 2,000
   residents face displacement; opponents want the existing Bayano reservoir expanded instead
   and allege the ACP failed to follow the Escazú Agreement [s20]. The pack sets
   `reverence_required: false` and bans no depictions, but this is a live dispute with named
   opponents, so the episode must say "contested" rather than "approved and proceeding".

5. **Which operator bid the $5.3m.** gCaptain and Maritime Executive say **SK Gas** [s15][s16];
   Marine Insight says **SK Shipping** [s19]. They are related SK Group entities. Say
   "South Korea's SK group" and avoid the sub-entity.

6. **Whether the drying is structural.** Muñoz et al. [s14] is a *projection* from 27 climate
   models under emissions scenarios, not a measurement and not a forecast of the next five
   years. Its finding is conditional: disruptive low-water conditions become common under
   moderately-high and high emissions, and do not under low emissions. The script may say
   "under high-emissions pathways, this becomes normal"; it may not say "this will become
   normal". Note also that the 2026 squeeze is attributed by the ACP to a forecast 2026–27 El
   Niño [s2], which is a weather event, not a climate trend — conflating the two is the single
   easiest way for the critic to fail factual fidelity.

---

## 6. What I could not find

- **A current household water tariff.** Nothing later than 2018 [s9]. IDAAN's and ASEP's
  current tariff schedules were not reachable. The episode is comparing a September 2026
  auction price to an eight-year-old tariff, and must caption the year on screen. If the
  writer wants a 2026 number, someone has to pull the IDAAN tariff directly — I could not.
- **The ACP's daily Gatún Lake level series.** The ACP publishes the official level (the
  tariff formula in [s3] depends on it) but I could not retrieve the machine-readable series.
  For the affiliate Data Pack this is a gap that has to be closed by hand.
- **A primary ACP statement of water consumed per transit in any unit.** See §4. This is the
  single weakest link in the episode's arithmetic and the writer should know it.
- **The full text of Muñoz et al. 2025.** AGU, scite and the DOI all returned 403.
  Bibliographic record confirmed via Altmetric; findings taken from Northeastern University's
  own release [s21] and press coverage. Do not quote the abstract; quote Muñoz's on-record
  statements in [s21].
- **An IMF or World Bank source specific to this argument.** The World Bank's Panama water
  indicator page timed out on every attempt. Nothing was lost: the ACP is the statistical
  authority for every canal figure here, and the ACP-commissioned demand study [s9][s10][s11]
  carries the IDAAN and INEC municipal data the angle actually needs.

---

## 7. Numbers the writer can use, with ids

- 3% of global maritime trade volume passes through the canal [s12]
- 13,404 transits, 489.1m tons, B/.5,705m revenue, B/.4,134m net profit, FY2025 [s4]
- 9,944 deep-draft transits FY2024, 21% below FY2023 [s5]
- Transits cut to 24/day on 7 Nov 2023, against a typical 34–36 [s13]
- 34 daily slots from 4 Sept 2026, 32 from 15 Sept 2026; **3 of them at auction** [s1]
- Rainfall 34% below and inflows 44% below the historical average, May–Aug 2026 [s2]
- 2023 rainfall 25.6% below the 73-year average [s6]
- Outflow 10 hm³/day vs inflow 7 hm³/day in the 2023 drought; 1.2 million m³/day saved by
  operational measures [s6]
- Gatún Lake: 85 ft normal, 84.3 ft Aug 2026, 82.8 ft projected Oct 2026, just over 79 ft in
  the 2023 drought, lowest since at least 1965 [s18][s13]
- Fresh water surcharge: $10,000 fixed over 300 ft LOA, plus 0–10% of tolls,
  f(x) = 0.10/(1+e^(0.6(x−82))) [s3]
- 55% of Panama's population drinks canal-watershed water [s7]
- Panama City: $0.21/m³ (2018), 303 MGD produced (2015), 104 GPCD, 40–55% unaccounted-for,
  57% metered [s9][s10]
- Río Indio: approved 21 Feb 2025, ~$1.6bn, 2027 start, four to six years, 4,600 ha flooded,
  8.7 km tunnel, 38 communities, ~2,000 people displaced [s8][s20]
- Leak reduction + metering: ~104 MGD for ~$204m, per the ACP's own consultant [s11]
