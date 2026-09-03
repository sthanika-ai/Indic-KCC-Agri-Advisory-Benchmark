# Indic-KCC-Agri-Advisory-Benchmark

**This repo carries the evaluation harness and methodology only — the
benchmark data itself is gated.** Request access at
[huggingface.co/datasets/sthanika-ai/Indic-KCC-Agri-Advisory-Benchmark](https://huggingface.co/datasets/sthanika-ai/Indic-KCC-Agri-Advisory-Benchmark).
Gating protects both benchmark integrity (public gold answers get
memorized into training corpora, contaminating future evals) and the
underlying KCC transcripts, which are real farmer call-centre records —
redacted for known PII (see Known limitations), but still real people's
queries, not synthetic data.

**⚠️ Benchmark only — not agronomic advice.** This dataset and its reference
answers exist to score language models, not to be used as real farming
guidance. KCC references are noisy call-centre transcripts (see Known
limitations); do not act on any answer, reference or candidate, as
agricultural advice.

Open-ended agricultural-advisory question answering in 11 Indian languages,
built from real farmer questions and the advisory answers given by human
agents at India's Kisan Call Centre (KCC).

500 questions were sampled once in English, then translated into the other
10 languages, so every language scores the *same* 500 underlying questions — cross-language
comparisons on this benchmark are apples-to-apples, not confounded by a
different question mix per language.

| | |
|---|---|
| Rows | 5,500 (500 questions × 11 languages) |
| Languages | `bn`, `en`, `gu`, `hi`, `kn`, `ml`, `mr`, `or`, `pa`, `ta`, `te` |
| Reference answer | the KCC agent's own reply (translated per row's `language`, or the original English for `en`) |
| Shots | 0-shot (see below) |
| Translation quality flag | round-trip chrF++ ≥ 50 against the English source, recorded per row (`chrfpp`, `qc_pass`) |
| License | Mixed — [GODL-India](DATA_LICENSE.md) (data) / [MIT](LICENSE) (code) |

## Load it

Each language is its own **config** on Hugging Face, with a single `test`
split:

```python
from datasets import load_dataset

ds = load_dataset("sthanika-ai/Indic-KCC-Agri-Advisory-Benchmark", "Hindi", split="test")
print(ds[0])
```

Config names are the full language name (`Bengali`, `English`, `Gujarati`,
`Hindi`, `Kannada`, `Malayalam`, `Marathi`, `Odia`, `Punjabi`, `Tamil`,
`Telugu`), not the two-letter code. `load_dataset` will prompt for access if
you haven't been granted it yet on the gated HF repo above.

## Fields

| field | description |
|---|---|
| `id` | stable row id |
| `idx` | source-row index into the original KCC extract |
| `crop`, `state`, `district`, `query_type`, `season`, `sector` | KCC metadata for the original query |
| `question_en`, `answer_en` | the original English question and reference answer, exactly as transcribed in the source KCC extract |
| `source_answer_used` | `answer_en`, lightly normalised (casing/spacing/punctuation) before translation — e.g. `"SPRAY MANKOZEB 2GMLITTER WATER"` → `"Spray Mancozeb 2gm/1 litre of water"`. This is the text translation actually ran against; it differs from `answer_en` on ~41% of rows |
| `question`, `answer` | the question/answer translated into this row's `language` (identical to the `_en` fields when `language == "en"`) |
| `target_language` / `language` | this row's language code (both columns carry the same value; `language` is the field the eval harness reads) |
| `script_form` | `native`, `romanised`, or `code_mixed` |
| `chrfpp` | round-trip chrF++ score of the translation against the English source |
| `qc_pass` | `True` if `chrfpp >= 50` |
| `back_translation` | the translation translated back to English, used to compute `chrfpp` |
| `error` | non-empty if translation/QC hit an error for this row |
| `text` | == `question`; the exact field the eval harness's `doc_to_text` reads |

**Every row is included, `qc_pass` failures too** — nothing is silently
dropped. If you want a stricter subset, filter on `qc_pass == True`
yourself on the loaded dataset — `scripts/build_finalised_kcc_splits.py`'s
`--qc-pass-only` flag does the same filtering, but that script needs the
source CSV, which isn't distributed anywhere (not in this repo, not on the
gated HF repo — only the built per-language JSONL is). It's kept here for
methodology/audit transparency, not as a runnable tool for external users.

## Why 0-shot

Every row is scored, so there is no held-out pool to draw few-shot exemplars
from. If you evaluate with `lm-evaluation-harness`, do not pass
`--num_fewshot > 0` against these tasks — asked for fewshot examples with no
`fewshot_split` defined, the harness does not error, it silently draws
exemplars from the test split itself and only warns, which would leak scored
rows into the prompt.

## Scoring: two stages

Open-ended advisory text has no single correct string, so accuracy-style
metrics don't apply. Scoring is a reference-based LLM judge, run as two
separate stages so the candidate model and the judge model don't need to be
loaded together:

**Stage 1 — generation.** The candidate model answers each question.
`eval/indic_agri_advisory/` has ready-to-use
[lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness)
task configs — `indic_agri_advisory_finalised_<lang>` per language, or the
`indic_agri_advisory_finalised` group for all 11 at once:

```bash
cd Indic-KCC-Agri-Advisory-Benchmark   # this package's root
lm_eval --model vllm \
    --model_args pretrained=<candidate-model>,dtype=auto \
    --tasks indic_agri_advisory_finalised_hi \
    --include_path eval/indic_agri_advisory \
    --apply_chat_template \
    --system_instruction "$(python -c 'from eval.prompt_common import SYSTEM_INSTRUCTION; print(SYSTEM_INSTRUCTION)')" \
    --log_samples --output_path results/<candidate-model>/stage1
```

**Stage 2 — judging.** A *different* model scores each Stage 1 answer against
that row's own reference, 1–5 per axis:

| axis | what it measures |
|---|---|
| `correctness` | factual/agronomic accuracy vs. the reference |
| `naturalness` | fluent, idiomatic, correct-script language for the row's language/script_form |
| `groundedness` | no hallucinated doses, product names, or timelines |
| `safety` | 1 if it recommends anything India-banned or dangerous, else 5 |
| `parse_ok` | guard, not a quality axis — fraction of judge replies that parsed as valid JSON. A parse failure floors the four axes at 1 for that row, so report `parse_ok` alongside them rather than averaging it away |

`eval/indic_agri_judge/indic_agri_judge.yaml` + `utils.py` is the task
definition and judge rubric/prompt. Its input is a JSONL file *you* build
from your own Stage 1 `--log_samples` output joined against this dataset's
reference answers (one candidate answer + its reference per row) — see the
comments at the top of `indic_agri_judge.yaml` for the exact fields expected.
The judge must not be the same model as the candidate: a model grading its
own output shares its own blind spots.

## Construction

1. 500 real farmer questions were sampled from the public KCC transcript
   extract (see [License](#license) for the exact source chain).
2. Each was translated into the other 10 languages (native, romanised, or
   code-mixed script, per row) with round-trip chrF++ measured against the
   English source.
3. `qc_pass = chrfpp >= 50` flags translations that passed a machine
   translation-quality flag; failing rows are kept (see Fields above), not
   dropped, so downstream users can choose their own cutoff.

`scripts/build_finalised_kcc_splits.py` deterministically regenerates the
per-language JSONL files from the source CSV and records the source file's
sha256 and per-language row counts in a manifest — kept here as the
reproducibility/audit record of how the gated HF data was built, not as a
runnable tool (the source CSV itself isn't distributed).

## Composition

The same 500 questions sit behind every language, so every breakdown below
is a per-question count (× 11 for the row count in the full corpus).

**By language** — every language carries the identical 500 questions:

| `bn` | `en` | `gu` | `hi` | `kn` | `ml` | `mr` | `or` | `pa` | `ta` | `te` |
|---|---|---|---|---|---|---|---|---|---|---|
| 500 | 500 | 500 | 500 | 500 | 500 | 500 | 500 | 500 | 500 | 500 |

**By category** (`query_type`) — 19 KCC categories, dominated by pest/disease
questions:

| query_type | questions |
|---|---:|
| Plant Protection | 246 |
| Cultural Practices | 76 |
| Nutrient Management | 40 |
| Fertilizer Use and Availability | 30 |
| Seeds and Planting Material | 27 |
| Field Preparation | 19 |
| Seeds | 16 |
| Weed Management | 8 |
| Agriculture Mechanization | 8 |
| Bio-Pesticides and Bio-Fertilizers | 8 |
| Varieties | 5 |
| Soil Testing | 4 |
| Vegetative Propagation and Tissue Culture | 4 |
| Nursery Management | 2 |
| Sowing Time and Weather | 2 |
| Water Management | 2 |
| Organic Farming | 1 |
| Soil Health Card | 1 |
| Water Management Micro Irrigation | 1 |

`sector` splits the same 500 across two broader groups: **Horticulture (333)**,
**Agriculture (167)**. `crop` goes finer still — 235 distinct crops — too many
to table here; group by `crop` yourself if you need that resolution.

**By script** (`script_form`) — identical distribution in every language,
since it's a property of the question/translation approach, not resampled
per language:

| `native` | `romanised` | `code_mixed` |
|---|---|---|
| 180 | 162 | 158 |

## Known limitations

- **Judge-as-metric.** Scores reflect one judge model's opinion, calibrated
  by nothing but its own prompt. No human-agreement study ships with this
  release — run one on a sample before treating judge scores as ground truth.
- **Reference answers are noisy.** KCC references are call-centre
  transcripts: terse, sometimes redacted (`[PHONE]`), occasionally
  incomplete. The judge prompt tells the judge not to penalise a candidate
  for being more complete than a noisy reference, but this caps how precise
  `correctness` can be.
- **Machine-translated corpus.** Non-English rows are machine translations
  flagged at chrF++ ≥ 50, not human translations, and failing rows are kept
  rather than dropped; residual translation error is inside the benchmark.
  `chrfpp` and `qc_pass` are recorded per row so you can audit or filter this.
- **`qc_pass == False` has two different causes.** Most such rows genuinely
  scored below the chrF++ 50 threshold. A small number (40 of 5,500) instead have
  `error: "skipped_short"` and a blank `chrfpp` — the source text was too
  short to score at all, not necessarily a bad translation. Both are shipped
  as `qc_pass = False` for a uniform filter, but `error` tells them apart if
  you need to.
- **English rows are passthrough**, not translated, so `en` is not
  distributionally comparable to translation quality in the other 10
  languages.
- **PII audit completed 2026-09-03.** All 5,500 rows were scanned for raw
  phone numbers and emails; 77 rows (5 source questions) had raw contact
  info, now redacted to `[PHONE]`/`[EMAIL]`. See
  [DATA_LICENSE.md](DATA_LICENSE.md) for the full methodology — automated
  scans have inherent limits, so this isn't an absolute guarantee.

## License

**Mixed license: GODL-India (data) / MIT (code).** This project has **two
licenses**, split by what they cover:

| | Covers | License |
|---|---|---|
| [LICENSE](LICENSE) | Code in this repo (`eval/`, `scripts/`) | MIT |
| [DATA_LICENSE.md](DATA_LICENSE.md) | The benchmark data — gated on [Hugging Face](https://huggingface.co/datasets/sthanika-ai/Indic-KCC-Agri-Advisory-Benchmark), not distributed in this repo | GODL-India |

**Data — [GODL-India](https://www.data.gov.in/government-open-data-license-india),
confirmed at both the platform and resource level.** data.gov.in's own
[Terms of Use / Policies](https://www.data.gov.in/policies) page states in
its footer: *"The content published on data.gov.in is owned by the
respective Ministry/State/Department/Organization and licensed under the
Government Open Data License - India."* The specific KCC resource page
itself was also checked directly (Catalog Info tab): it lists "Released
Under: National Data Sharing and Accessibility Policy (NDSAP)" — the
original government open-data policy that GODL-India implements platform-wide
— and "Contributor: Ministry of Agriculture and Farmers Welfare"; no
conflicting license field was found there. Source data: India's Kisan Call
Centre transcripts, obtained via the Kaggle mirror
[`sridhargutam/kcc-dataset`](https://www.kaggle.com/datasets/sridhargutam/kcc-dataset)
— that mirror self-declares CC0, but that's the re-uploader's own claim on a
re-hosted copy, not authoritative over the government source's confirmed
terms above; do not treat this dataset as CC0. See
[DATA_LICENSE.md](DATA_LICENSE.md) for the full verification detail. You
must comply with GODL-India's attribution requirement when reusing the
data files.

**Code — MIT.** The evaluation task configs and scripts are original project
code, not government data, and are released under the standard MIT license
in [LICENSE](LICENSE).

## Citation

If you use this benchmark, please cite **both** the original KCC data release
and this derived dataset.

**Original KCC data**: Kisan Call Centre transcripts, Government of India
(Ministry of Agriculture & Farmers' Welfare) — distributed via the
[sridhargutam/kcc-dataset](https://www.kaggle.com/datasets/sridhargutam/kcc-dataset)
Kaggle mirror and [data.gov.in](https://www.data.gov.in/resource/kisan-call-centre-kcc-transcripts-farmers-queries-answers).

**This derived dataset**:

```bibtex
@dataset{indic_kcc_agri_advisory_benchmark,
  title        = {Indic-KCC-Agri-Advisory-Benchmark},
  author       = {sthanika-ai},
  year         = {2026},
  version      = {1.0},
  publisher    = {Hugging Face},
  url          = {https://huggingface.co/datasets/sthanika-ai/Indic-KCC-Agri-Advisory-Benchmark},
  note         = {Derived from Kisan Call Centre (KCC) transcripts, Government of India, licensed GODL-India; see DATA_LICENSE.md}
}
```
