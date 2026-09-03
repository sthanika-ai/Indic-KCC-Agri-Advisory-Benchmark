Government Open Data License - India (GODL)
=============================================

This applies to the **dataset content only** — the CSV/JSONL
question-and-answer data under `data/` and `source/`. The accompanying code
(everything under `eval/` and `scripts/`) is licensed separately under
MIT — see [LICENSE](LICENSE).

This dataset is derived from Kisan Call Centre (KCC) farmer query/answer
transcripts, originally published by the Government of India (Ministry of
Agriculture & Farmers' Welfare) and distributed via data.gov.in:
https://www.data.gov.in/resource/kisan-call-centre-kcc-transcripts-farmers-queries-answers

**License basis: confirmed at both the platform level and the specific
resource level.** data.gov.in's own Terms of Use / Policies page
(https://www.data.gov.in/policies) states in its footer: "The content
published on data.gov.in is owned by the respective
Ministry/State/Department/Organization and licensed under the Government
Open Data License - India." Its Copyright Policy section requires accurate,
non-misleading reproduction with the source prominently acknowledged. Full
GODL text:
https://www.data.gov.in/government-open-data-license-india

The specific KCC resource page itself
(https://www.data.gov.in/resource/kisan-call-centre-kcc-transcripts-farmers-queries-answers,
Catalog Info tab) was also checked directly. Its own metadata does not
override the platform default: it lists "Released Under: National Data
Sharing and Accessibility Policy (NDSAP)" (the original 2012 government
open-data policy, of which GODL-India is the specific license instrument
data.gov.in uses to implement that policy platform-wide — consistent with,
not contradicting, the GODL default) and "Contributor: Ministry of
Agriculture and Farmers Welfare / Department of Agriculture and Farmers
Welfare." No separate or conflicting license field was found on that page.

This project obtained the raw transcripts via a Kaggle mirror
(https://www.kaggle.com/datasets/sridhargutam/kcc-dataset, which cites
ICAR's KCC-CHAKSHU portal as its own source and self-declares a CC0 label).
That CC0 label is the re-uploader's own claim on a re-hosted copy, not
authoritative over the government source's actual terms above — do not
treat this dataset as CC0.

**You must comply with GODL-India (including its attribution requirement)
when you reuse the data files.** Summary of GODL terms (see the full text
above for the authoritative version): you are free to access, use, share,
and adapt this data, including for commercial purposes, provided you:
  1. Attribute the source (Government of India / data.gov.in, Kisan Call
     Centre) and this derived dataset.
  2. Reproduce it accurately, not in a derogatory manner or misleading
     context.
  3. Do not imply endorsement by the original data provider.
  4. Comply with any other conditions on the original data.gov.in resource
     page.

**Required attribution statement.** Include this (or an equivalent) wherever
you redistribute or publish results derived from this data:

> This work uses data derived from Kisan Call Centre (KCC) transcripts,
> Government of India (Ministry of Agriculture & Farmers' Welfare),
> distributed via [data.gov.in](https://www.data.gov.in/resource/kisan-call-centre-kcc-transcripts-farmers-queries-answers)
> and licensed under the Government Open Data License – India (GODL-India).
> Derived and translated by the Indic-KCC-Agri-Advisory-Benchmark project
> (sthanika-ai).

This derived data (translations into 10 additional Indian languages,
quality-flagged by round-trip chrF++) is released under the same GODL
terms. It carries no additional restriction beyond GODL.

**PII audit (completed 2026-09-03).** All 5,500 rows were scanned across
every text field (`question_en`, `answer_en`, `source_answer_used`,
`question`, `answer`, `back_translation`) for raw phone numbers and email
addresses, with matches manually verified against false positives (agronomic
dosage/yield figures and OCR-corrupted digit noise, which a naive regex
otherwise over-flags). This found raw contact information in 5 of the 500
source questions (77 of 5,500 rows, across all 11 languages): an
institution's phone numbers, a university department's phone number, two
seed/sapling vendors' phone numbers, and one row with several individuals'
personal emails and a phone number. All have been redacted to `[PHONE]`/
`[EMAIL]` in both `source/finalised_kcc_translated.csv` and `data/*.jsonl`.
No raw phone numbers or emails are known to remain as of this audit;
automated regex scans have inherent limits (e.g. non-standard formats not
covered here), so this is not an absolute guarantee.

Before relying on this for a commercial product, verify current terms
directly on the specific data.gov.in resource page yourself, as license
text and per-resource metadata can be updated by the publisher at any time
after this documentation was written.
