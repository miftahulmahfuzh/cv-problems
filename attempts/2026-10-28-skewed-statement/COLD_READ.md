## Scores

**1. Requirement capture: weak.** The first message pastes the brief and adds "the requirement is for us to straighten it." It has no constraints (no venv, no one-file limit), no output contract beyond the filenames, and it doesn't resolve either fork (output size, margin). "Straighten" also narrows the brief's "flat, upright, filling the frame."
- Cheaper: "Output 900x1150 portrait, no margin, corners ordered TL,TR,BR,BL. Print the output size and aspect, then show flat.png."

**2. Data literacy: weak.** "i see a skewed photograph of a trade confirmation table." That is all they transferred. They said nothing about the dark desk, the shadow, the lighting gradient or the perspective, and "trade confirmation table" isn't what the brief says (a broker statement).
- Cheaper: "Page is a white sheet on a dark desk, shot at an angle, with a shadow along two edges and uneven lighting."

**3. Decomposition: adequate.** There are two instructions, and the second is only a sign-off. The first mixes "let's discuss the approaches first" with "you need to write a script" in one message. The agent skipped the discussion and wrote the script anyway, and the candidate didn't push back.
- Cheaper: either "Give me two approaches in three lines, then implement the simpler one," or drop the discussion request.

**4. Verification: weak.** Asking "show me the flat.png so i can evaluate the correctness of the script myself" was the right move. The check itself was content-only: "1 header row + 5 content rows, all tickers are in there: BBCA, BBRI, TLKM, ASII, GOTO." That is a real, number-bearing check of the content, and it's credited.
- The candidate pasted `"output_aspect_w_over_h": 0.894` next to `"a4_aspect": 0.707` and never mentioned them. The expected aspect is about 0.783, so 0.894 is roughly 14% off. The GROUND_TRUTH check (warp to 900x1150 and compare) would fail on size.
- Nothing was said about the header band being horizontal, the shadow, or the lighting gradient.
- Cheaper: "Aspect is 0.894 but the page is about 0.78. Why? Resize to 900x1150 and confirm the header edges are horizontal."

**5. Correction quality: not exercised.** There was no correction turn. The one that was needed (aspect) never happened.

**6. Domain vocabulary: weak.** "skewed", "straighten", "flatten". "Perspective", "homography", "deskew" and "document rectification" never appear. The candidate says "this is new to me, so i just learned about 'HSV threshold..->warpPerspective'", which shows they learned the vocabulary from the agent rather than steering with it.
- Cheaper: "Perspective-correct with a 4-point homography."

**7. Scope control: adequate.** "write a script that outputs output/flat.png and output/notes.json" keeps scope tight. Nothing stopped the agent from also writing `debug_corners.png`, though that was harmless.

## Weakest instruction (verbatim)

> "but i checked your flat.png and compare it against the original image. everything is correct. no value changes because of this image flatting process"

It's an unstated-geometry sign-off. It says "everything is correct" while the notes.json pasted just above shows a 0.894 aspect against a roughly 0.78 page. It also ends the session ("we are done here") 4.1 minutes into a 20-minute budget, with the remaining time unused.

## Highest-leverage change

Before accepting, ask for geometry evidence and state the numbers yourself. For example: "Output is 935x1046, aspect 0.894. A4 is 0.707 and the page looked about 0.78, so that is stretched. Re-run at 900x1150 and print the angle of the header band." Choosing the output size up front would have settled the fork before the first run.

## Requirement drift

- The candidate's spec didn't change across replies.
- The first message's reading of the task ("a trade confirmation table", "straighten") narrowed "scanned: flat, upright, filling the frame" to a skew fix. The shadow and lighting gradient were silently dropped.
- The second message swapped the acceptance test from "as if scanned" (geometry and cleanliness) to "values unchanged" (content). That is a lower bar than the brief sets.
