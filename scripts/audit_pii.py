"""Audit (and optionally fix) raw phone numbers / emails in
source/finalised_kcc_translated.csv.

This is the reproducible record of the PII audit completed 2026-09-03 (see
DATA_LICENSE.md and README's Known Limitations) -- given the source CSV,
--audit deterministically reproduces the same classification; --fix
deterministically reproduces the same redaction. Not run automatically by
build_finalised_kcc_splits.py -- run this first if you've changed
source/finalised_kcc_translated.csv (e.g. restored more rows, edited
answers), then re-run build_finalised_kcc_splits.py to propagate into
data/*.jsonl.

WHY THIS ISN'T A GENERIC "REDACT EVERY REGEX MATCH" TOOL: an 8-13-digit
regex alone can't tell a real phone number ("91-11-46604988") apart from
agronomic dosage/yield figures ("600 GRAMS STREPTOCYCLINE... 200 LITRES")
or OCR-corrupted digit noise (some rows are 40+ garbled digits with no
phone number in them at all). The 2026-09-03 audit found the regex alone
over-flagged ~21 ids; manual inspection of every hit's full text narrowed
that to 5 genuine source questions (77 rows across languages). --fix below
replaces exactly those 5 questions' confirmed raw strings -- it does NOT
auto-redact every future regex hit, because that would silently corrupt
legitimate agronomic numbers. If you add rows to the source CSV later
(e.g. restoring more of the original 500), run --audit again, manually
verify any new hits the same way (read the full row, not just the matched
span), and add genuine ones to CONFIRMED_PHONES/CONFIRMED_EMAILS below
before running --fix again.

Usage:
    python scripts/audit_pii.py --audit          # report only, no changes
    python scripts/audit_pii.py --fix            # apply the known, verified redactions
"""
import argparse
import csv
import re
from collections import defaultdict

HERE = __import__("pathlib").Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "source" / "finalised_kcc_translated.csv"

TEXT_FIELDS = ["question_en", "answer_en", "source_answer_used", "question", "answer", "back_translation"]

REDACTED_TOKENS = re.compile(
    r"\[(PHONE|EMAIL|ফোন|ફોન|फ़ोन|फोन|ಫೋನ್|ഫോൺ|தொலைபேசி)\]", re.IGNORECASE
)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PROVIDER_TLD_RE = re.compile(
    r"\b[a-zA-Z][a-zA-Z0-9]{1,}(?:gmail|yahoo|rediffmail|hotmail|outlook|ymail|indiatimes)"
    r"(?:com|co ?in|in|net|org)?\b",
    re.IGNORECASE,
)
# Maximal contiguous digit/separator cluster (not length-capped here --
# capped only when classifying, so one huge blob isn't chopped into
# several fake "phone numbers").
DIGIT_CLUSTER_RE = re.compile(r"\d[\d\-\. ]*\d|\d")

# Verified 2026-09-03 against the full text of every hit -- see the
# module docstring before adding to this list.
CONFIRMED_PHONES = [
    "91-11-46604988",
    "91-8130997511",
    "1800-11-7474",
    "06422 - 222191",
    "0422 - 6611228",
    "90033 54959",
    "0285- 2672080",
    "0285-2672080",  # same number, no-space variant found in hi/ml/mr/te back_translation
    "९००३३ ५४९५९",  # same number (90033 54959), Devanagari numerals -- found in mr 'answer'
    "०२८५- २६७२०८०",  # same number (0285- 2672080), Devanagari numerals -- found in mr 'answer'
]
CONFIRMED_EMAILS = [
    "kvkgoddagmailcom",
    "kvkgoddayahoocoin",
    "drskumar2009yahooin",
    "sbhushanbhu23rediffmailcom",
    "riteshd70gmailcom",
    "pragatika123gmail",
]
CONFIRMED_IDS = {
    "kcc_02e92528f089613e",
    "kcc_02c8819551df851a",
    "kcc_03255149cf814c7f#en_code_mixed",
    "kcc_03255149cf814c7f#en_native",
    "kcc_03255149cf814c7f#en_romanised",
    "kcc_07b71ff8b6e209e8",
    "kcc_0bfd728163d65aa1",
}


def classify_clusters(text):
    """Return (phone_like_spans, noise_spans) for one text field."""
    phone_like, noise = [], []
    for m in DIGIT_CLUSTER_RE.finditer(text):
        span = m.group(0)
        ndigits = sum(c.isdigit() for c in span)
        if ndigits < 8:
            continue
        (phone_like if ndigits <= 13 else noise).append(span.strip())
    return phone_like, noise


def audit():
    total_rows = 0
    rows_with_phone = rows_with_noise = rows_with_email = rows_with_redacted = 0
    phone_ids, noise_ids, email_ids = set(), set(), set()

    with open(SOURCE, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            total_rows += 1
            row_phone = row_noise = row_email = row_redacted = False
            for field in TEXT_FIELDS:
                text = row.get(field) or ""
                if not text:
                    continue
                if REDACTED_TOKENS.search(text):
                    row_redacted = True
                phones, noise = classify_clusters(text)
                row_phone = row_phone or bool(phones)
                row_noise = row_noise or bool(noise)
                if EMAIL_RE.search(text) or PROVIDER_TLD_RE.search(text):
                    row_email = True
            if row_phone:
                rows_with_phone += 1
                phone_ids.add(row.get("id"))
            if row_noise:
                rows_with_noise += 1
                noise_ids.add(row.get("id"))
            if row_email:
                rows_with_email += 1
                email_ids.add(row.get("id"))
            if row_redacted:
                rows_with_redacted += 1

    print(f"Total rows scanned: {total_rows}")
    print(f"Rows with a phone-shaped digit cluster (8-13 digits): {rows_with_phone} (ids: {len(phone_ids)})")
    print(f"Rows with a raw email: {rows_with_email} (ids: {len(email_ids)})")
    print(f"Rows with a long digit blob (14+ digits, likely OCR noise, not a phone number): {rows_with_noise} (ids: {len(noise_ids)})")
    print(f"Rows with an already-redacted [PHONE]/[EMAIL]-style marker: {rows_with_redacted}")
    print()
    print("ids flagged that are NOT in CONFIRMED_IDS (verify these by hand before adding them):")
    for i in sorted((phone_ids | email_ids) - CONFIRMED_IDS):
        print(" ", i)


def fix():
    rows, fieldnames = [], None
    total_replacements = rows_touched = 0

    with open(SOURCE, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row.get("id") in CONFIRMED_IDS:
                row_n = 0
                for field in TEXT_FIELDS:
                    text = row.get(field) or ""
                    if not text:
                        continue
                    for s in CONFIRMED_EMAILS:
                        if s in text:
                            row_n += text.count(s)
                            text = text.replace(s, "[EMAIL]")
                    for s in CONFIRMED_PHONES:
                        if s in text:
                            row_n += text.count(s)
                            text = text.replace(s, "[PHONE]")
                    row[field] = text
                if row_n:
                    rows_touched += 1
                    total_replacements += row_n
            rows.append(row)

    with open(SOURCE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Rows touched: {rows_touched}")
    print(f"Total substring replacements made: {total_replacements}")
    print(f"Total rows in file after rewrite: {len(rows)}")
    print("Now run scripts/build_finalised_kcc_splits.py to propagate into data/*.jsonl.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--audit", action="store_true", help="Report findings only, no changes.")
    group.add_argument("--fix", action="store_true", help="Apply the known, manually-verified redactions.")
    args = ap.parse_args()

    if not SOURCE.exists():
        raise SystemExit(f"ERROR: source CSV not found: {SOURCE}")

    if args.audit:
        audit()
    else:
        fix()


if __name__ == "__main__":
    main()
