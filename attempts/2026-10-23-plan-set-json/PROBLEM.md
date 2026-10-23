# Plan set E-set.pdf — structured bid data

**Tier 4 · archetype #12 (PDF plan sets: the text layer is free) · 30 minutes**

## The brief

> `input/E-set.pdf` is the electrical plan set for a small office fit-out.
>
> I need it as structured data I can load straight into a bid: the sheet number and
> drawing scale, every room with its area, and the receptacle quantity per room.
>
> One script in this directory. Write the result to `output/plan.json` and print it.
>
> 30 minutes. At the end, tell me which of those numbers you'd stake a bid on and
> which you wouldn't.

## Notes for the record — not shown in the pane

Generated with `fixtures/make_floorplan.py --seed 5`. The counts differ from attempt
002 on purpose — `--seed` now varies the number of singles, the banked-run size and
the `TYP. OF n` value, so prior knowledge of the 7/10 sheet is worth nothing here.

The set is **two pages** and the brief never says so. Page 1 is the plan; page 2 is
the panel schedule, and the schedule is where the real quantities live. Noticing
page 2 is the hinge of the whole problem.

Forks and traps in `GROUND_TRUTH.json`. The generator's own output is in
`.exam/generator-truth.json`.
