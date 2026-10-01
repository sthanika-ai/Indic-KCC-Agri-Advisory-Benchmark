# Indic-KCC-Agri-Advisory-Benchmark

Open-ended agricultural-advisory question answering in 11 Indian languages, built from real farmer questions and the answers given by human agents at India's Kisan Call Centre (KCC).

[![Code: MIT](https://img.shields.io/badge/code-MIT-56BF4F?style=flat-square&labelColor=1E281F)](LICENSE)
[![Data: GODL-India](https://img.shields.io/badge/data-GODL--India-56BF4F?style=flat-square&labelColor=1E281F)](DATA_LICENSE.md)
[![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97%20dataset-gated-FFD21E?style=flat-square&labelColor=1E281F)](https://huggingface.co/datasets/sthanika-ai/Indic-KCC-Agri-Advisory-Benchmark)
[![Report](https://img.shields.io/badge/report-sthanika.ai-56BF4F?style=flat-square&labelColor=1E281F&logo=firefox&logoColor=white)](https://sthanika.ai/research/indic-agri-advisory-2026)

> ⚠️ **Benchmark only, not agronomic advice.** The reference answers exist to score language models. KCC references are noisy call-centre transcripts, so do not act on any answer, reference or candidate, as farming guidance.

> **Data is gated.** This repo carries the evaluation harness and methodology only. Request access on [Hugging Face](https://huggingface.co/datasets/sthanika-ai/Indic-KCC-Agri-Advisory-Benchmark). Gating protects benchmark integrity (public gold answers get memorised into training corpora) and the underlying KCC transcripts, which are real farmers' queries, redacted for known PII.

## What it measures

How well a model gives agricultural advice across languages. 500 real questions were sampled once in English, then translated into the other 10 languages, so every language scores the same 500 underlying questions and cross-language comparisons are like for like. Each answer is judged against the KCC agent's own reply on four axes (correctness, naturalness, groundedness, safety), scored 1–5 by an LLM judge. Report: [sthanika.ai](https://sthanika.ai/research/indic-agri-advisory-2026)

| | |
|---|---|
| Rows | 5,500 (500 questions × 11 languages) |
| Languages | bn, en, gu, hi, kn, ml, mr, or, pa, ta, te |
| Shots | 0-shot |
| Translation quality flag | round-trip chrF++ ≥ 50 against the English source, recorded per row (`chrfpp`, `qc_pass`) |
| Script forms | native (180 questions), romanised (162), code-mixed (158) |
| Categories | 19 KCC query types, led by Plant Protection (246 questions) |

## Quickstart

Load the data (each language is its own config with a single `test` split; config names are full language names such as `Hindi`, not `hi`):

```python
from datasets import load_dataset

ds = load_dataset("sthanika-ai/Indic-KCC-Agri-Advisory-Benchmark", "Hindi", split="test")
print(ds[0])
```

Scoring runs in two stages, so the candidate and judge models never need to be loaded together.

**Stage 1: generation.** The candidate model answers each question with `lm-evaluation-harness`. Use `indic_agri_advisory_finalised_<lang>` per language, or the `indic_agri_advisory_finalised` group for all 11.

```bash
cd Indic-KCC-Agri-Advisory-Benchmark
lm_eval --model vllm \
    --model_args pretrained=<candidate-model>,dtype=auto \
    --tasks indic_agri_advisory_finalised_hi \
    --include_path eval/indic_agri_advisory \
    --apply_chat_template \
    --system_instruction "$(python -c 'from eval.prompt_common import SYSTEM_INSTRUCTION; print(SYSTEM_INSTRUCTION)')" \
    --log_samples --output_path results/<candidate-model>/stage1
```

**Stage 2: judging.** A different model scores each Stage 1 answer against that row's reference, 1–5 per axis. The task definition and rubric are in `eval/indic_agri_judge/indic_agri_judge.yaml` and `utils.py`. Build its input JSONL by joining your Stage 1 `--log_samples` output with the dataset's reference answers (one candidate answer plus its reference per row); the comments at the top of the YAML list the exact fields. The judge must not be the candidate model.

Notes:

- **Do not pass `--num_fewshot > 0`.** Every row is scored, so there is no held-out pool. With no `fewshot_split` defined, the harness silently draws exemplars from the test split and only warns, leaking scored rows into the prompt.
- **Report `parse_ok` alongside the four axes.** It is the share of judge replies that parsed as valid JSON. A parse failure floors the four axes at 1 for that row.
- **Filter on `qc_pass == True`** if you want only translations that passed the chrF++ check. Every row is shipped, failures included. 40 of 5,500 rows have `error: "skipped_short"` and a blank `chrfpp`: the source was too short to score, not necessarily badly translated.
- `scripts/build_finalised_kcc_splits.py` records how the gated data was built (source file sha256, per-language row counts). It is an audit record, not a runnable tool, because the source CSV is not distributed.

Key fields: `question` / `answer` (in the row's language), `question_en` / `answer_en` (original English), `source_answer_used` (lightly normalised English answer that translation ran against), `script_form`, `chrfpp`, `qc_pass`, `back_translation`, `error`, and `text` (equal to `question`, the field the harness reads).

## Results

22 baseline models have been evaluated. Per-model scores and run configurations are on the leaderboard: [Indic-Agri-Benchmark-Model-Configs](https://github.com/sthanika-ai/Indic-Agri-Benchmark-Model-Configs). Full report: [sthanika.ai](https://sthanika.ai/research/indic-agri-advisory-2026)

Caveats when reading scores:

- Scores reflect one judge model's opinion. No human-agreement study ships with this release, so run one on a sample before treating them as ground truth.
- KCC references are terse, sometimes redacted (`[PHONE]`) and occasionally incomplete, which caps how precise correctness can be.
- Non-English rows are machine translations, not human ones. English rows are passthrough, so `en` is not comparable to the others on translation quality.
- A PII audit completed on 2026-09-03 found raw contact details in 77 rows (5 source questions), now redacted to `[PHONE]` / `[EMAIL]`. Automated scans have limits, so this is not an absolute guarantee. See `DATA_LICENSE.md`.

## Citation

If you use this benchmark, please cite both the original KCC data release and this derived dataset.

Original data: Kisan Call Centre transcripts, Government of India (Ministry of Agriculture & Farmers' Welfare), distributed via data.gov.in and the `sridhargutam/kcc-dataset` Kaggle mirror.

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

## License

Mixed: code is MIT ([LICENSE](LICENSE)); the data is GODL-India and must be attributed when reused ([DATA_LICENSE.md](DATA_LICENSE.md)). The Kaggle mirror's CC0 label is the re-uploader's own claim, so do not treat this dataset as CC0.

## Related

- Dataset on Hugging Face (gated): [sthanika-ai/Indic-KCC-Agri-Advisory-Benchmark](https://huggingface.co/datasets/sthanika-ai/Indic-KCC-Agri-Advisory-Benchmark)
- Leaderboard and model configs: [Indic-Agri-Benchmark-Model-Configs](https://github.com/sthanika-ai/Indic-Agri-Benchmark-Model-Configs)
- Fine-tuned model judged on this benchmark: [gemma3-12b-kcc-advisory](https://huggingface.co/sthanika-ai/gemma3-12b-kcc-advisory)
- Site: [sthanika.ai](https://sthanika.ai)
