"""Rebuild data/finalised_<lang>_test.jsonl from source/finalised_kcc_translated.csv.

The JSONL files under data/ are already built and committed -- you do not
need to run this to use the benchmark. It exists so the split is
reproducible and auditable: given the source CSV, this script deterministically
regenerates the exact same per-language JSONL files and manifest.

Source CSV column -> JSONL field mapping:
    question         -> text     (doc_to_text reads doc['text'], see
                                   eval/indic_agri_advisory/utils.py)
    answer           -> answer   (doc_to_target: "{{answer}}")
    target_language  -> language
    everything else (id, idx, crop, state, district, query_type, season,
    sector, question_en, answer_en, source_answer_used, script_form, chrfpp,
    qc_pass, back_translation, error) is carried through unchanged, for
    traceability -- it is not read by doc_to_text/doc_to_target.

By default every row is kept (5,500 = 500 questions x 11 languages),
matching source/finalised_split_manifest.json. Pass --qc-pass-only to keep
only rows where qc_pass == 'True' (rows with an automated translation-quality
gate on the round-trip chrF++ score of the target-language translation
against the reference chrF++ threshold).

Usage:
    python scripts/build_finalised_kcc_splits.py
    python scripts/build_finalised_kcc_splits.py --qc-pass-only
"""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'source' / 'finalised_kcc_translated.csv'
DATA_DIR = ROOT / 'data'
MANIFEST = ROOT / 'source' / 'finalised_split_manifest.json'


def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--qc-pass-only', action='store_true',
                    help="Keep only rows where qc_pass == 'True'. "
                         "Default: keep every row (5,500 total).")
    args = ap.parse_args()

    if not SOURCE.exists():
        raise SystemExit(f"ERROR: source CSV not found: {SOURCE}")

    by_lang = defaultdict(list)
    skipped = 0
    with open(SOURCE, encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f):
            if args.qc_pass_only and row.get('qc_pass') != 'True':
                skipped += 1
                continue
            doc = dict(row)
            doc['text'] = row['question']
            doc['language'] = row['target_language']
            # CSV round-trips everything as strings. Cast qc_pass/chrfpp back
            # to real JSON bool/float so `datasets` infers proper column
            # types and `ds.filter(lambda r: r['qc_pass'])` / `r['chrfpp'] >= 50`
            # work as documented in the README -- shipping these as the
            # strings "True"/"10.69" would make `qc_pass == True` silently
            # match zero rows for downstream users.
            doc['qc_pass'] = row.get('qc_pass') == 'True'
            try:
                doc['chrfpp'] = float(row['chrfpp']) if row.get('chrfpp') not in (None, '') else None
            except ValueError:
                doc['chrfpp'] = None
            by_lang[doc['language']].append(doc)

    manifest = {
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'source_csv': SOURCE.name,
        'source_sha256': sha256_of_file(SOURCE),
        'keep_all': not args.qc_pass_only,
        'rows_skipped_not_qc_pass': skipped,
        'fewshot_pool': None,
        'fewshot_note': ('No fewshot split exists: every row here is scored. '
                         'Reported 0-shot.'),
        'languages': {},
    }

    total = 0
    DATA_DIR.mkdir(exist_ok=True)
    for lang, rows in sorted(by_lang.items()):
        out_path = DATA_DIR / f"finalised_{lang}_test.jsonl"
        with open(out_path, 'w', encoding='utf-8') as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + '\n')
        manifest['languages'][lang] = {'test': len(rows)}
        total += len(rows)
        print(f"  {lang}: {len(rows):,} test")

    manifest['total_test'] = total
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding='utf-8')

    qc_note = f'{skipped:,} rows dropped, not qc_pass' if args.qc_pass_only \
        else 'kept ALL rows (default), including non-qc_pass'
    print(f"\ntotal: {total:,} test rows across {len(by_lang)} languages ({qc_note})")
    print(f"manifest: {MANIFEST}")


if __name__ == '__main__':
    main()
