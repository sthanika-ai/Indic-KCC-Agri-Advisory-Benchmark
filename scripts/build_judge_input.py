"""Build the Stage 2 judge input JSONL from Stage 1 `--log_samples` output.

Stage 1 (lm_eval with --log_samples) writes one ``samples_<task>_<ts>.jsonl``
per task. Each line carries the benchmark row (``doc``, including the reference
``answer``) and the candidate's generation, so no separate join against the
dataset is needed. This script flattens those lines into the fields
eval/indic_agri_judge/utils.py reads:
crop, query_type, language, script_form, question, reference_answer,
candidate_answer, model_key.

    python scripts/build_judge_input.py \\
        --samples results/<candidate>/stage1 --model-key <candidate>

``--samples`` takes sample files or directories (searched recursively), so one
call can cover all 11 languages. Output defaults to the path the judge YAML
reads, eval/indic_agri_judge/judge_input/_current.jsonl.

Reasoning is stripped from the candidate answer (<think>...</think>), so the
judge scores the answer only. An unterminated <think> block (generation ran out
of tokens mid-reasoning) leaves an empty answer, which the judge will score low.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "eval" / "indic_agri_judge" / "judge_input" / "_current.jsonl"

_TASK_RE = re.compile(r"samples_indic_agri_advisory_finalised_([a-z]{2})_")
_THINK_RE = re.compile(r"<think>.*?</think>", re.S | re.I)


def strip_reasoning(text: str) -> str:
    text = _THINK_RE.sub("", text)
    if "</think>" in text.lower():      # opening tag was in the prompt, not the output
        text = re.split(r"</think>", text, flags=re.I)[-1]
    if "<think>" in text.lower():       # never closed: truncated mid-reasoning
        text = re.split(r"<think>", text, flags=re.I)[0]
    return text.strip()


def sample_files(paths):
    for p in map(Path, paths):
        found = sorted(p.rglob("samples_*.jsonl")) if p.is_dir() else [p]
        yield from found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--samples", nargs="+", required=True,
                    help="Stage 1 samples_*.jsonl files or directories")
    ap.add_argument("--model-key", required=True, help="candidate model name shown to the judge")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    files = list(sample_files(args.samples))
    if not files:
        print("ERROR: no samples_*.jsonl found under --samples", file=sys.stderr)
        return 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    n = n_empty = 0
    with open(out, "w", encoding="utf-8") as fo:
        for f in files:
            m = _TASK_RE.search(f.name)
            lang = m.group(1) if m else ""
            with open(f, encoding="utf-8") as fi:
                for line in fi:
                    s = json.loads(line)
                    doc = s["doc"]
                    resp = (s.get("filtered_resps") or s["resps"][0])[0]
                    if isinstance(resp, list):
                        resp = resp[0]
                    cand = strip_reasoning(resp or "")
                    n_empty += not cand
                    fo.write(json.dumps({
                        "id": doc.get("id"),
                        "crop": doc.get("crop", ""),
                        "query_type": doc.get("query_type", ""),
                        "language": doc.get("language") or lang,
                        "script_form": doc.get("script_form", ""),
                        "question": doc.get("question") or doc.get("text", ""),
                        "reference_answer": doc.get("answer", ""),
                        "candidate_answer": cand,
                        "model_key": args.model_key,
                    }, ensure_ascii=False) + "\n")
                    n += 1
    print(f"wrote {n} rows from {len(files)} file(s) -> {out}")
    if n_empty:
        print(f"WARNING: {n_empty} row(s) have an empty candidate answer after stripping "
              f"reasoning (likely truncated mid-<think>; raise max_gen_toks in Stage 1)",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
