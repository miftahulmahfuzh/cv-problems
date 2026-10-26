# Evaluation — route-intake

**Result: passed, in 21.4 of 30 minutes.** The classification is correct
(`table`, confidence 0.992 after cleanup), the full probability vector is
printed to `output/classification.json`, and the routed handler
(`ocr_table_extractor`) matches the predicted type. Verification happened —
a prompt was identified as image-tailored and ablated, and a per-prompt
breakdown was produced — but it happened a beat later than it should have,
and reactively. That is the real story of this run: a correct, well-checked
answer arrived at by a process with a specific, fixable gap in it.

Scored against the seven dimensions in `reference/prompting-playbook.md`. A
cold-read subagent scored the same transcript independently, without seeing
this account; disagreements are marked explicitly below.

---

## 1. Requirement capture — **weak**

Instruction 1 pastes the brief, adds a precise description of the image (see
§2), states the confidence-printing requirement — and then hands the entire
taxonomy and method decision to Claude:

> *"we need to discuss what kind of router that we want to make here. what
> are the classification classes? ... ask me any confusing things you find"*

The brief genuinely leaves the taxonomy open (that is the documented fork),
so asking is not wrong. But asking *open-ended*, with no candidate taxonomy
of your own on the table, converted the single highest-leverage move in this
drill — stating a decision and asking for correction — into a full
round-trip at T+1.8 for a decision you could have proposed yourself in the
same message:

> *"Use six classes: chart, diagram, photo, scanned_document, table, other.
> Write the table prompts around what a table looks like — ruled grid, rows
> of small glyphs — not what it's about. Print the full distribution and the
> handler name to `output/classification.json`."*

Even a tentative version of that, open to correction, keeps the decision
yours and removes the round-trip. The cold read scored this dimension
**weak** for the same reason; I would have been inclined to call it
*adequate* on the strength of everything else packed into instruction 1 —
the cold read's harder line is the more useful one to carry forward.

## 2. Data literacy — **strong**

> *"right now, i am seeing a table of settlement's trade confirmation,
> containing a list of stock tickers, each with its trading details
> (buy/sell, quantity, price, value, fee)."*

This is exactly the "transfer what you saw" move the playbook rewards —
specific, done before any code existed, and accurate. Worth naming the
twist: this same accurate description is where the one overfit-prone prompt
(`"a trade confirmation table listing tickers, quantities and prices"`)
came from. Good data literacy and a planted leak shared a root cause here —
describing content precisely is good instruction-writing and a hazard for
prompt-based zero-shot labels at the same time. Worth knowing going in, not
a reason to describe images less precisely.

## 3. Decomposition — **adequate**

Four coherent instructions across 21 minutes: frame the task and ask →
confirm the three decisions → name a specific robustness worry → demand two
concrete checks. No vague "still wrong, try again" thrash, no quarter-hour
single dump either.

## 4. Verification — **adequate**

> *"i am afraid right now we got a correct result because we already see
> what the image is. so there is a chance that this will become an
> 'overfit'."*

The instinct — distrust a result that looks too convenient — is exactly
right, and it is the bonus behavior `GROUND_TRUTH.json` calls "the senior
move this archetype is testing for." But the cold read is correct that this
was reactive, not initiated: instruction 3 opens by quoting Claude's own
prior disclosure (*"you said: 'this result depends on the exact prompt
wording...'"*) rather than the candidate independently interrogating a
99.67% confidence on a brand-new classifier before being told to worry about
it. Credit for *catching* the trap belongs to the assistant; credit for
*not letting it slide* — pushing for the ablation and the per-prompt
breakdown rather than accepting the caveat as a shrug — belongs to the
candidate. Next time, the cheaper and more independent version is to ask for
the per-prompt breakdown in the same first instruction, before any result
comes back: *"Show me the softmax per individual prompt, not just the
class average — I want to see if one prompt is carrying a class."*

## 5. Correction quality — **adequate**

No result was ever wrong, so there is nothing to "correct" in the classic
sense, but instruction 4 is close enough to a correction to score: it states
intent (*"we need to make sure that our router can be abstract enough
whilst maintaining a good accuracy"*) without naming which prompt, which
class, or which number is suspected. It worked because the assistant
supplied the specific diagnosis unprompted. A sharper version names the
object of suspicion directly: *"the `table` prompt about tickers and fees
looks copied from what I just told you is in the image — drop that one and
re-run."*

## 6. Domain vocabulary — **adequate**

"Overfit," "confidence score," "test set," "router," "classification
classes" are real, correctly-used ML vocabulary and name the actual risk
precisely. What never appears on the candidate's side: "zero-shot,"
"embedding," "cosine similarity," "softmax," "prompt" — all introduced by
Claude. For this archetype (models, not geometry), that second set is the
vocabulary that would let you specify *which* lever to pull without Claude
deciding it for you.

## 7. Scope control — **strong (not exercised, no issue arose)**

No instruction ever had to rein in scope, and none was needed — the
diagnostic script in instruction 4 is proportionate to a real correctness
question, not feature creep. Final workspace is two short scripts and two
JSON outputs; nothing resembling a CLI or package was built.

---

## Requirement drift

None found. Each clarifying-question answer resolved an open fork the brief
genuinely left open (taxonomy, handler names, method) without narrowing or
silently changing anything the brief stated outright. Accepting the
"(Recommended)" CLIP option without asking what the alternatives would have
cost is a minor missed chance to probe, not drift.

## The two planted traps

1. **Prompt wording encoding semantics instead of appearance, producing a
   confidently wrong answer.** Not hit. The six-class taxonomy happened to
   keep `chart`'s prompts purely visual (`"a bar chart"`, `"a line chart
   with axes"`) rather than finance-themed, so there was no competing class
   for the financial vocabulary in the `table` prompts to leak into. Avoided
   by taxonomy design, not by a stated principle — the "describe what it
   looks like, not what it's about" rule was never said aloud by either
   party until the ablation was run and interpreted after the fact.
2. **Trusting a high-confidence number just because it's high.** Avoided,
   deliberately, in instructions 3–4 — this is the one place the candidate's
   own judgement, not the assistant's default, is the reason the final
   `output/classification.json` is backed by an ablation instead of a single
   lucky run.

---

## Carry into the next attempt

1. **Propose a taxonomy before asking for one.** When a brief leaves a fork
   open, state your best guess and ask for correction, rather than opening
   with "what should the categories be?" — same clarifying function, zero
   round-trip cost.
2. **Ask for the per-prompt (not per-class-averaged) breakdown in the first
   instruction**, for any zero-shot classification task. It is the cheapest
   available defence against exactly the trap this archetype plants, and it
   costs nothing to request upfront instead of after a suspicious result.
3. **When something feels like it might be overfit, name the specific
   suspect** (which prompt, which word) instead of describing the worry in
   general terms — it turns a vague correction into a one-line ablation.
4. **Reach for "zero-shot," "embedding," "softmax" explicitly** when the
   archetype is models rather than geometry — it is the domain-vocabulary
   dimension's equivalent of "contour" and "bounding box" for this ladder
   tier.

## Next archetype

**#8, caption/VQA with a VLM** (`reference/problem-ladder.md`). Its trap is
the mirror image of what this run's gap actually was: a VLM that
hallucinates a specific, confident wrong fact, with no assistant-side hint
to lean on first. This run showed the right instinct (don't trust a
suspiciously confident number) but only after the assistant supplied the
reason to doubt it. #8 removes that scaffold and tests whether the same
instinct fires unprompted.
