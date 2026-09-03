"""Download the gated benchmark data into the paths the Stage 1 task YAMLs read.

The Hugging Face repo stores one config per language, named with the full
language name (``Hindi``, ``English``, ...), while the task YAMLs read
``data/finalised_<code>_test.jsonl`` (``hi``, ``en``, ...). This script bridges
the two so nothing has to be renamed by hand.

    huggingface-cli login          # the dataset is gated; request access first
    python scripts/download_data.py                  # all 11 languages
    python scripts/download_data.py --langs hi en    # a subset

Run from the repo root. Writes data/finalised_<code>_test.jsonl (git-ignored).
"""
import argparse
import sys
from pathlib import Path

REPO_ID = "sthanika-ai/Indic-KCC-Agri-Advisory-Benchmark"
ROOT = Path(__file__).resolve().parents[1]

# code -> accepted config names (case-insensitive); Odia is also spelled Oriya.
LANGS = {
    "bn": ("Bengali",),
    "en": ("English",),
    "gu": ("Gujarati",),
    "hi": ("Hindi",),
    "kn": ("Kannada",),
    "ml": ("Malayalam",),
    "mr": ("Marathi",),
    "or": ("Odia", "Oriya"),
    "pa": ("Punjabi",),
    "ta": ("Tamil",),
    "te": ("Telugu",),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--langs", nargs="+", default=list(LANGS), choices=list(LANGS),
                    help="language codes to fetch (default: all 11)")
    ap.add_argument("--out-dir", default=str(ROOT / "data"))
    args = ap.parse_args()

    from datasets import get_dataset_config_names, load_dataset

    configs = {c.lower(): c for c in get_dataset_config_names(REPO_ID)}
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for code in args.langs:
        name = next((configs[a.lower()] for a in LANGS[code] if a.lower() in configs), None)
        if name is None:
            print(f"ERROR: no config for '{code}' (looked for {LANGS[code]}; "
                  f"repo has {sorted(configs.values())})", file=sys.stderr)
            return 1
        ds = load_dataset(REPO_ID, name, split="test")
        dest = out_dir / f"finalised_{code}_test.jsonl"
        ds.to_json(str(dest), force_ascii=False)
        print(f"{code}: {len(ds)} rows ({name}) -> {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
