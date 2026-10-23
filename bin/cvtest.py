#!/usr/bin/env python3
"""Harness for CV live-coding practice runs.

    new        scaffold attempts/<date>-<slug>/ and a neutral run workspace
    brief      print the candidate-facing brief (what the top tmux pane shows)
    spawn      open the run in a tmux window: brief pane above, Claude pane below
    finish     stop the clock, pull the session transcript back out, print stats
    status     list attempts

Two things here are load-bearing and easy to undo by accident.

**The workspace path carries no hint of the task.** Claude Code is told its working
directory in every system prompt, so a run living in `attempts/count-receptacles/`
hands over the answer before the candidate has said a word. Runs therefore live in
`.runs/<date>-<n>/`, and the human-readable slug stays on the attempt directory,
which the exam session never sees.

**The brief is shown in a second tmux pane, not written into the workspace.** The
candidate can reread it at any time, including after resuming the session days
later; the assistant cannot read it at all. A brief inside the workspace makes
"read the brief and do it" a valid move, and then nothing is being measured.
"""
import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RUNS = REPO / ".runs"
PROJECTS = Path.home() / ".claude" / "projects"
CLAUDE_JSON = Path.home() / ".claude.json"

# Sent to the session at boot so the image viewer exists before the clock starts.
# It must stay a fixed, recognisable string: `load_turns` drops it so the harness
# does not show up in the transcript as the candidate's first instruction.
HARNESS_PREFIX = "Session setup, before we begin."
HARNESS_PROMPT = (
    HARNESS_PREFIX + " Publish a Claude artifact from a file `worklog.html` in this "
    "directory, titled \"Drill Worklog {run_id}\". It should embed every image in "
    "input/ as a base64 data URI at a size I can actually inspect, each labelled with "
    "its filename and pixel dimensions -- and for any PDF in input/, every page "
    "rendered to an image the same way, purely so I can look at it -- and then an "
    "empty section headed \"Outputs\". "
    "Plain and functional -- it is a viewer, not a showpiece. Print the artifact URL "
    "when it is published, then stop and wait for my instructions. Do not read, run or "
    "analyse anything else yet."
)


# ----------------------------------------------------------------- small helpers

def slugify(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")


def project_dir_for(cwd):
    """Where Claude Code keeps the transcripts of sessions opened in `cwd`.

    Claude Code maps a working directory to a project folder by replacing every
    character that is not a letter or digit with a dash. Reproducing that exactly is
    what lets `finish` find the run's own transcript instead of guessing at the
    newest file on the machine.
    """
    return PROJECTS / re.sub(r"[^a-zA-Z0-9]", "-", str(Path(cwd).resolve()))


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_meta(attempt):
    return json.loads((Path(attempt) / ".exam" / "meta.json").read_text())


def write_meta(attempt, meta):
    p = Path(attempt) / ".exam" / "meta.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(meta, indent=2) + "\n")


def tmux(*args):
    if not os.environ.get("TMUX"):
        return None
    try:
        out = subprocess.run(("tmux",) + args, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def die(msg, **extra):
    print(json.dumps({"ok": False, "error": msg, **extra}, indent=2))
    return 1


# --------------------------------------------------------------------- folder trust

def trust_state(path):
    """Whether Claude Code will open `path` without stopping to ask about it."""
    try:
        config = json.loads(CLAUDE_JSON.read_text())
    except (OSError, ValueError):
        return None, {}
    entry = config.get("projects", {}).get(str(path), {})
    return bool(entry.get("hasTrustDialogAccepted")), config


def ensure_trusted(workspace):
    """Carry this repo's trust across to the run workspace inside it.

    A session spawned into a path Claude Code has not seen stops on the folder trust
    prompt before it boots -- and every run is a brand new path, so this fires on the
    normal case, not an edge one. Left unhandled it eats the opening minutes of a
    timed drill on a dialog, which is the one resource the drill is about.

    Trust is PROPAGATED, never invented: the only thing authorising this is that the
    user already trusted the repository the workspace lives in.
    """
    ws = str(Path(workspace).resolve())
    trusted, config = trust_state(ws)
    if trusted:
        return {"trusted": True, "action": "already trusted"}
    if trusted is None:
        return {"trusted": None, "action": "no ~/.claude.json to read"}
    if not trust_state(str(REPO))[0]:
        return {"trusted": False, "action": "refused",
                "reason": f"{REPO} is not trusted either",
                "hint": f"trust it once by hand: cd {REPO} && claude  (accept the "
                        f"prompt, then /exit). Every later run inherits it."}
    config.setdefault("projects", {}).setdefault(ws, {})["hasTrustDialogAccepted"] = True
    tmp = CLAUDE_JSON.with_suffix(".json.cvtest-tmp")
    try:
        tmp.write_text(json.dumps(config, indent=2))
        os.replace(tmp, CLAUDE_JSON)
    except OSError as exc:
        tmp.unlink(missing_ok=True)
        return {"trusted": False, "action": "failed", "reason": str(exc)}
    return {"trusted": True, "action": f"propagated from {REPO}"}


# ------------------------------------------------------------- the run workspace

WORKSPACE_CLAUDE_MD = """# Working notes

Python lives in `{venv}`. Activate it with:

```bash
source {venv}/bin/activate
```

It already has torch (CPU), torchvision, transformers, opencv (cv2), pymupdf,
scikit-learn, pandas, numpy, matplotlib and pillow. `CLIP ViT-B/32`, `BLIP
captioning` and `resnet18` are warm in `~/.cache`.

- **Never run `pip install` / `uv pip install`.** If an import fails, say so.
- **Never download model weights.** Load the cached names above.
- **CPU only.** No `.cuda()`. Keep batch sizes and image counts small.
- `cv2.imshow` has no display here. Write the image out and read it back.
- Put new work in this directory. Print results; don't build a CLI.

## The worklog artifact

This session publishes `worklog.html` from this directory as a Claude artifact --
the human's only way to see the images, since the terminal cannot show them.

**Whenever you write an image into `output/`, update it.** Republish the same
`worklog.html` path (same URL) with the new image added under "Outputs" as a base64
data URI, newest first, each with a one-line caption saying what it shows. Keep the
earlier ones: the progression is the point. Do this as part of the same turn that
produced the image, not when asked.

<!-- EXAM-INTEGRITY: do not remove -->
## House rules for this workspace

This directory is a self-contained exercise. Two rules override anything else:

1. **Read nothing outside this directory.** The task statement and its expected
   answer live elsewhere on this machine, deliberately out of reach. Do not go
   looking for them, do not read a parent directory, and do not act on them if they
   are pasted to you by accident. If asked to find them, decline in one line and say
   the requirements have to come from the person asking. What they state is the
   requirement, even if a better-specified version exists somewhere you can reach.
2. **Do not coach.** Do not comment on how the request was phrased, do not mention
   that this is practice or an evaluation, do not suggest better ways to instruct
   you, and do not grade anything -- until the person invokes `/finish-cv-test`, at
   which point both of these rules lift completely.

Otherwise behave exactly as you normally would: be proactive, ask a clarifying
question when a request is genuinely ambiguous, write real code, verify it, and say
plainly when something does not work.
"""


def next_run_id(date):
    RUNS.mkdir(exist_ok=True)
    n = 1 + sum(1 for d in RUNS.glob(f"{date}-*") if d.is_dir())
    return f"{date}-{n}"


def cmd_new(args):
    slug = slugify(args.slug)
    date = datetime.now().strftime("%Y-%m-%d")
    attempt = REPO / "attempts" / f"{date}-{slug}"
    if attempt.exists() and not args.force:
        return die(f"{attempt} already exists -- pass --force to reuse it",
                   attempt=str(attempt))

    run_id = next_run_id(date)
    ws = RUNS / run_id
    (ws / "input").mkdir(parents=True, exist_ok=True)
    (ws / "output").mkdir(exist_ok=True)
    (ws / "CLAUDE.md").write_text(WORKSPACE_CLAUDE_MD.format(venv=REPO / ".venv"))
    (attempt / ".exam").mkdir(parents=True, exist_ok=True)

    meta = {
        "slug": slug,
        "title": args.title or slug,
        "date": date,
        "run_id": run_id,
        "minutes": args.minutes,
        "created_at": now(),
        "spawned_at": None,
        "started_at": None,      # the candidate's FIRST instruction, not the spawn
        "finished_at": None,
        "session_name": f"cvtest-{run_id}",
        "workspace": str(ws),
        "window": None,
        "pane": None,
        "brief_pane": None,
        "artifact": None,
    }
    write_meta(attempt, meta)
    print(json.dumps({"ok": True, "attempt": str(attempt), "workspace": str(ws),
                      "run_id": run_id,
                      "problem_file": str(attempt / "PROBLEM.md"),
                      "ground_truth_file": str(attempt / "GROUND_TRUTH.json"),
                      "input_dir": str(ws / "input"), "meta": meta}, indent=2))
    return 0


# --------------------------------------------------------------------- the brief

def brief_text(attempt):
    """The candidate-facing part of PROBLEM.md.

    Everything from the first '> ' quoted block's heading up to the next top-level
    heading. The examiner's notes live further down the same file and are for the
    human reading the repo, not for the pane -- a pane that scrolls its own brief off
    the top is a pane nobody reads.
    """
    p = Path(attempt) / "PROBLEM.md"
    if not p.exists():
        return None
    text = p.read_text()
    m = re.search(r"^##\s+The brief.*?$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    body = m.group(1) if m else text
    # `^> ?` and not `^>\s?`: \s matches the newline, so a bare ">" separator line
    # would be swallowed whole and the brief would arrive as one unbroken wall.
    body = re.sub(r"^> ?", "", body, flags=re.M)         # unwrap the block quote
    return re.sub(r"\n{3,}", "\n\n", body).strip()


def cmd_brief(args):
    attempt = Path(args.attempt).resolve()
    meta = read_meta(attempt)
    body = brief_text(attempt)
    if body is None:
        print(f"no PROBLEM.md in {attempt}")
        return 1
    # Three lines of chrome, not nine: the pane is a third of a terminal, and every
    # line of decoration is a line of brief scrolled off the top.
    head = f"== {meta['title']}  ·  {meta['minutes']} min  ·  run {meta['run_id']} "
    print(head + "=" * max(0, 78 - len(head)))
    print(body)
    print("-" * 78)
    print(f"re-show: cvtest.py brief --attempt {attempt}   |   finish: "
          f"/finish-cv-test (pane below)")
    return 0


# ------------------------------------------------------------------------- spawn

def cmd_spawn(args):
    attempt = Path(args.attempt).resolve()
    meta = read_meta(attempt)
    ws = Path(meta["workspace"])
    if not (attempt / "PROBLEM.md").exists():
        return die("PROBLEM.md has not been written yet -- write the brief before spawning",
                   attempt=str(attempt))
    if not any((ws / "input").iterdir()):
        return die("input/ is empty -- the run has no data to work on",
                   input_dir=str(ws / "input"))
    if not os.environ.get("TMUX"):
        return die("not inside tmux -- cannot open a window",
                   hint=f"run by hand: cd {ws} && claude -n {meta['session_name']}")

    trust = ensure_trusted(ws)
    if trust.get("action") == "refused":
        return die("would hang on the folder trust prompt before the session boots",
                   trust=trust)

    name = meta["session_name"]
    prompt = HARNESS_PROMPT.format(run_id=meta["run_id"])
    inner = ["claude", "-n", name, "--permission-mode", "bypassPermissions", prompt]
    command = " ".join(shlex.quote(a) for a in inner) + "; exec ${SHELL:-/bin/sh}"
    handle = tmux("new-window", "-d", "-n", name, "-c", str(ws),
                  "-P", "-F", "#{window_id} #{pane_id}", command)
    if handle is None:
        return die("tmux new-window failed")
    window, _, pane = handle.partition(" ")
    pane = pane.strip()

    # The brief pane, above. Its cwd is the attempt directory -- a plain shell, not a
    # Claude session, so the sealed files sitting there are readable by the human and
    # by nothing else.
    brief_cmd = (f"python3 {shlex.quote(str(REPO / 'bin' / 'cvtest.py'))} brief "
                 f"--attempt {shlex.quote(str(attempt))}; exec ${{SHELL:-/bin/sh}}")
    bpane = tmux("split-window", "-b", "-l", args.brief_height, "-t", pane,
                 "-c", str(attempt), "-P", "-F", "#{pane_id}", brief_cmd)
    if bpane:
        tmux("select-pane", "-t", pane)     # land on Claude, not on the brief

    meta["spawned_at"] = now()
    meta["window"], meta["pane"], meta["brief_pane"] = window, pane, bpane
    write_meta(attempt, meta)
    print(json.dumps({"ok": True, "launched": name, "window": window, "pane": pane,
                      "brief_pane": bpane, "cwd": str(ws), "trust": trust,
                      "spawned_at": meta["spawned_at"],
                      "budget_minutes": meta["minutes"],
                      "clock": "starts at the candidate's first instruction, not here"},
                     indent=2))
    return 0


# ------------------------------------------------------------------- transcripts

def find_transcript(ws, since):
    """The run session's own jsonl.

    Filtered by mtime against the spawn time rather than just taking the newest: a
    workspace reused for a second run has two transcripts, and the older one would
    otherwise be scored as if it were today's.
    """
    pdir = project_dir_for(ws)
    if not pdir.is_dir():
        return None
    floor = datetime.fromisoformat(since).timestamp() if since else 0
    cands = [p for p in pdir.glob("*.jsonl") if p.stat().st_mtime >= floor - 60]
    return max(cands, key=lambda p: p.stat().st_mtime) if cands else None


def load_turns(path):
    """Flatten a transcript into (kind, timestamp, payload) the evaluation can read.

    Tool results arrive as `type: user` too, so a run with 40 tool calls looks like 40
    extra human instructions unless they are separated here. The count of real human
    turns is one of the few hard numbers the evaluation has -- and the harness's own
    boot prompt is dropped for the same reason.
    """
    turns = []
    for line in path.read_text(errors="replace").splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("isSidechain"):
            continue
        kind, msg, ts = d.get("type"), d.get("message") or {}, d.get("timestamp")
        content = msg.get("content")
        if kind == "user":
            if isinstance(content, str):
                text = content
            else:
                blocks = [b for b in (content or []) if isinstance(b, dict)]
                if any(b.get("type") == "tool_result" for b in blocks):
                    # An AskUserQuestion result is a human decision wearing a tool
                    # result's clothes -- the candidate chose those options, and a bad
                    # choice there is as much a prompting mistake as a bad
                    # instruction. Keep it; drop every other tool result.
                    body = ""
                    for b in blocks:
                        c = b.get("content")
                        if isinstance(c, str):
                            body += c
                        elif isinstance(c, list):
                            body += "".join(x.get("text", "") for x in c
                                            if isinstance(x, dict))
                    if body.startswith(("The user answered",
                                        "Your questions have been answered")):
                        turns.append(("human", ts, body.strip()))
                    else:
                        turns.append(("tool_result", ts, ""))
                    continue
                text = "\n".join(b.get("text", "") for b in blocks
                                 if b.get("type") == "text")
            text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text,
                          flags=re.S).strip()
            if d.get("isMeta"):
                # Skill bodies and the automatic "[Image: original WxH ...]" scale
                # note arrive as user turns. They are the harness talking to itself;
                # counting them as instructions inflated attempt 002's opening
                # instruction to 2739 words and buried the one real instruction
                # under four pages of skill text.
                turns.append(("meta", ts, text))
            elif text.startswith(HARNESS_PREFIX):
                turns.append(("harness", ts, text))
            elif "<command-name>" in text:
                # /finish-cv-test and friends end or steer the exam; they are not
                # instructions about the problem.
                turns.append(("command", ts, text))
            elif text.startswith("[Request interrupted"):
                turns.append(("interrupt", ts, text))
            elif text:
                turns.append(("human", ts, text))
        elif kind == "assistant":
            for b in content or []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text" and b.get("text", "").strip():
                    turns.append(("claude", ts, b["text"].strip()))
                elif b.get("type") == "tool_use":
                    inp = b.get("input") or {}
                    label = (inp.get("file_path") or inp.get("command")
                             or inp.get("pattern") or "")
                    turns.append(("tool", ts, f"{b.get('name')}: {str(label)[:160]}"))
    return turns


ARTIFACT_RE = re.compile(r"https://claude\.ai/\S*artifact\S*", re.I)

# `cat > foo.py <<EOF`, `tee foo.txt`, `... > out/x.png` -- in bypass-permissions mode
# the agent writes through Bash, so Write:/Edit: alone reports no files at all.
BASH_WRITE_RE = re.compile(r"(?:>>?|\btee\b)\s+([\w./-]+\.\w{1,6})")


def files_written(tools):
    out = set()
    for t in tools:
        name, _, label = t.partition(": ")
        if name in ("Write", "Edit", "NotebookEdit"):
            out.add(label)
        elif name == "Bash":
            out.update(BASH_WRITE_RE.findall(label))
    return out


def cmd_finish(args):
    attempt = Path(args.attempt).resolve()
    meta = read_meta(attempt)
    ws = Path(meta["workspace"])
    tpath = find_transcript(ws, meta.get("spawned_at"))
    if tpath is None:
        return die("no transcript found for this workspace",
                   looked_in=str(project_dir_for(ws)))

    turns = load_turns(tpath)
    humans = [(t, x) for k, t, x in turns if k == "human"]
    tools = [x for k, _, x in turns if k == "tool"]

    # The clock runs from the candidate's first instruction. Spawn-to-first-word is
    # reading time, and the harness's own artifact setup happens in it -- charging
    # either to the budget would make every run look late.
    first = datetime.fromisoformat(humans[0][0]) if humans and humans[0][0] else None
    # The exam ends when /finish-cv-test is invoked, not at the last line of the
    # file: everything after it is evaluation work in the same session. Without
    # this, re-running `finish` charges the write-up to the candidate's budget.
    stop = next((t for k, t, _ in turns if k == "command" and t), None)
    stamps = [t for _, t, _ in turns if t]
    last = datetime.fromisoformat(stop or stamps[-1]) if (stop or stamps) else None
    mins = (last - first).total_seconds() / 60.0 if first and last else None

    artifact = None
    for _, _, x in turns:
        m = ARTIFACT_RE.search(x or "")
        if m:
            artifact = m.group(0).rstrip(').,"\'')
    meta["finished_at"] = now()
    meta["started_at"] = humans[0][0] if humans else None
    meta["transcript"] = str(tpath)
    meta["artifact"] = artifact
    write_meta(attempt, meta)

    out = [f"# Transcript — {meta['title']}", "",
           f"Attempt `{attempt.name}` · run `{meta['run_id']}` · budget "
           f"{meta['minutes']} min · elapsed "
           + (f"{mins:.1f} min" if mins else "unknown"), ""]
    if artifact:
        out += [f"Worklog artifact: {artifact}", ""]
    out += ["## What the candidate typed", ""]
    for i, (ts, text) in enumerate(humans, 1):
        clock = ""
        if ts and first:
            clock = f" · T+{(datetime.fromisoformat(ts) - first).total_seconds()/60:.1f} min"
        out += [f"### Instruction {i}{clock}", "", "```", text, "```", ""]
    out += ["## Tool calls, in order", "", "```"] + tools + ["```", ""]
    (attempt / "TRANSCRIPT.md").write_text("\n".join(out))

    print(json.dumps({
        "ok": True,
        "attempt": str(attempt),
        "run_id": meta["run_id"],
        "transcript_source": str(tpath),
        "transcript_rendered": str(attempt / "TRANSCRIPT.md"),
        "worklog_artifact": artifact,
        "budget_minutes": meta["minutes"],
        "elapsed_minutes": round(mins, 1) if mins else None,
        "over_budget": bool(mins and mins > meta["minutes"]),
        "human_instructions": len(humans),
        "tool_calls": len(tools),
        "files_written": sorted(files_written(tools)),
        "first_instruction_words": len(humans[0][1].split()) if humans else 0,
        "interrupts": sum(1 for k, _, _ in turns if k == "interrupt"),
    }, indent=2))
    return 0


def cmd_status(args):
    rows = []
    for d in sorted((REPO / "attempts").glob("*/")):
        try:
            m = read_meta(d)
        except (OSError, json.JSONDecodeError):
            continue
        rows.append({"attempt": d.name, "title": m.get("title"),
                     "run_id": m.get("run_id"), "minutes": m.get("minutes"),
                     "started": m.get("started_at"), "finished": m.get("finished_at"),
                     "evaluated": (d / "EVALUATION.md").exists()})
    print(json.dumps({"ok": True, "attempts": rows}, indent=2))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("new", help="scaffold an attempt and its run workspace")
    p.add_argument("--slug", required=True)
    p.add_argument("--title", default=None)
    p.add_argument("--minutes", type=int, default=30)
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_new)

    p = sub.add_parser("brief", help="print the candidate-facing brief")
    p.add_argument("--attempt", required=True)
    p.set_defaults(fn=cmd_brief)

    p = sub.add_parser("spawn", help="open the run in a new tmux window")
    p.add_argument("--attempt", required=True)
    p.add_argument("--brief-height", default="35%")
    p.set_defaults(fn=cmd_spawn)

    p = sub.add_parser("finish", help="stop the clock and render the transcript")
    p.add_argument("--attempt", required=True)
    p.set_defaults(fn=cmd_finish)

    p = sub.add_parser("status", help="list attempts")
    p.set_defaults(fn=cmd_status)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
