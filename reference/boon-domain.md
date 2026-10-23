# Boon: what they actually do

Researched 2026-10-23 from getboon.ai and press coverage. Worth ten minutes before
the test — the domain vocabulary is half the interview.

## The company

**Boon** — "the intelligence layer for construction". San Mateo, founded 2023 by
Deepti Yenireddy (ex-Samsara). Raised ~$20.5M; $15.5M Series A led by Redpoint
Ventures and Marathon, Dec 2024. Started in fleet/logistics workflow automation,
pushed into construction.

Reported scale: 66,000+ drawing pages read, 14M+ sq ft of building area, $4.5B+ in
project value analysed.

## The product

An **AI estimator**. A construction estimator's job is to read a full plan-and-spec
set — hundreds of sheets — and produce a priced bid. That takes about three weeks.
Boon claims to do it in an afternoon:

- **Takeoff** — counting and measuring quantities from drawings. How many
  receptacles, how many linear feet of conduit, how much ductwork, how much
  structural steel. Per trade: electrical, HVAC, plumbing, structural.
- **Bid levelling** — normalising subcontractor bids so they can be compared.
- **Spec clash detection** — the drawings say one thing, the written spec says
  another; find the contradiction.

Published accuracy floors: electrical fixtures and conduit ≥ 0.90, architectural
≥ 0.85, mechanical ≥ 0.74.

## The technology claim

A single **"Construction Vision Model"** — one foundation model trained across all
30+ trades with specialised heads, explicitly not "a zoo of narrow models". They
emphasise **cross-trade transfer**: structure learned on electrical sheets helping
on mechanical ones.

So the HR description — "they build CV models from scratch" — is roughly accurate,
though in practice almost certainly a pretrained vision backbone plus heavy
domain-specific training, not a model trained from random init.

## The three hard problems they name

From their own writing on reading construction drawings. These are the sentences to
have ready, because they show you understand the domain rather than the exercise.

**1. Symbol grammar.** Drawings do not repeat a symbol once per real object. They
use notation: one explicit symbol, a "repeat" marker, an end symbol — a *banked run*.
A model that counts pixels counts the drawn symbols, not the installed devices, and
is wrong in a way that looks right. The convention set is roughly: single symbol,
banked run, repeat pattern, schedule reference.

**2. Cross-sheet relational reasoning.** The panel schedule is on one sheet; the
devices that panel feeds are on sheets ten pages away. The answer exists in the
*relationship* between sheets, not on any one of them. This is a retrieval-and-join
problem over a document set — which is, notably, **your** background rather than a
classical CV one.

**3. Topological closure.** A duct must connect at both ends. A run that terminates
into open space is a detection error or a drawing error, and distinguishing those
matters. Validity is a graph property, not a per-pixel one.

Their framing: this is a **spatial reconstruction** problem, not a pixel-detection
problem.

## "Denah internal bangunan"

Indonesian for *internal building floor plan*. That matches their input exactly: the
architectural sheets of a plan set. The HR contact did not know what the output
should be — the honest answer is that it depends on the trade, and the safe one is:
*a structured, scaled, machine-readable reconstruction of what the sheet depicts —
rooms, walls, openings, symbols, and their quantities — tied back to sheet
coordinates so it can be audited.*

That "tied back so it can be audited" clause is worth saying. In estimating, a
number nobody can trace back to a drawing is a number nobody will bid on.

## Where your background is an advantage

Say these if the conversation allows.

- **Document → structured data.** You converted PDF regulations into structured data
  with rule-based systems at Prosa. A plan set is the same shape of problem with
  geometry attached.
- **Retrieval and joins across a corpus.** Cross-sheet reasoning is retrieval. You
  have built Elasticsearch systems over regulation corpora; "which sheet defines
  this panel" is a retrieval problem wearing a CV hat.
- **Multimodal LLM orchestration.** Your current work passes images as native vision
  input through a planner and into tool calls. That is the agentic half of what they
  describe.
- **Evaluation discipline.** Their published per-trade accuracy floors imply a real
  eval harness. Ask about it — how they build ground truth for takeoff, and whether
  accuracy is per-symbol or per-quantity. It is a senior question.

## Where you are thin, and how to hold it

You have not trained a detection model or worked with CAD. Do not pretend otherwise.
The defensible position: *"My CV depth is newer than my NLP depth — I'm comfortable
with the classical geometry stack and with VLM/CLIP-style models, and the parts of
your problem that are retrieval, document structure and evaluation are squarely what
I've done for eight years."* Then demonstrate the classical stack working, fast.
