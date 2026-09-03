# Indic-KCC-Agri-Advisory-Benchmark

Open-ended agricultural-advisory question answering in 11 Indian languages, built from real farmer questions and the answers given by human agents at India's Kisan Call Centre (KCC).

[![Code: MIT](https://img.shields.io/badge/code-MIT-56BF4F?style=flat-square&labelColor=1E281F)](LICENSE)
[![Data: GODL-India](https://img.shields.io/badge/data-GODL--India-56BF4F?style=flat-square&labelColor=1E281F)](DATA_LICENSE.md)
[![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97%20dataset-gated-FFD21E?style=flat-square&labelColor=1E281F)](https://huggingface.co/datasets/sthanika-ai/Indic-KCC-Agri-Advisory-Benchmark)
[![Report](https://img.shields.io/badge/report-sthanika.ai-56BF4F?style=flat-square&labelColor=1E281F&logo=firefox&logoColor=white)](https://sthanika.ai/research/indic-agri-advisory-2026)

## What it measures

How well a model gives agricultural advice across languages: 500 real questions, asked in English and translated into 10 other languages (5,500 rows, 0-shot), each answer scored 1–5 by an LLM judge (`Qwen/Qwen3.6-35B-A3B-FP8`) against the KCC agent's own reply on correctness, naturalness, groundedness and safety. Details and methodology: [sthanika.ai/research/indic-agri-advisory-2026](https://sthanika.ai/research/indic-agri-advisory-2026).

Benchmark only, not agronomic advice: KCC references are noisy call-centre transcripts, so do not act on any answer as farming guidance. The data is gated on [Hugging Face](https://huggingface.co/datasets/sthanika-ai/Indic-KCC-Agri-Advisory-Benchmark); request access first.

## Quickstart

Scoring runs in two stages so the candidate and judge models never need to be loaded together. Run everything from the repo root.

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt vllm
huggingface-cli login
python scripts/download_data.py                      # writes data/finalised_<lang>_test.jsonl

# Stage 1: the candidate answers every question (swap hi for any of bn en gu hi kn ml mr or pa ta te,
# or use indic_agri_advisory_finalised for all 11)
lm_eval --model vllm \
    --model_args pretrained=Qwen/Qwen3-1.7B,dtype=auto \
    --tasks indic_agri_advisory_finalised_hi \
    --include_path eval/indic_agri_advisory \
    --apply_chat_template \
    --system_instruction "$(python -c 'from eval.prompt_common import SYSTEM_INSTRUCTION; print(SYSTEM_INSTRUCTION)')" \
    --log_samples --output_path results/Qwen3-1.7B/stage1

# Join the answers with their references (strips <think> reasoning from the answer)
python scripts/build_judge_input.py --samples results/Qwen3-1.7B/stage1 --model-key Qwen3-1.7B

# Stage 2: a different model judges (must not be the candidate); reasoning judges are fine,
# the default 3000-token limit leaves room for their thinking
lm_eval --model vllm \
    --model_args pretrained=Qwen/Qwen3-8B,dtype=auto \
    --tasks indic_agri_judge \
    --include_path eval/indic_agri_judge \
    --apply_chat_template \
    --output_path results/Qwen3-1.7B/stage2
```

Stage 2 reports the four axes plus `parse_ok`, the share of judge replies that parsed as valid JSON. A parse failure floors that row's four axes at 1, so report `parse_ok` with the scores and rerun if it is below 1.0. `--model hf` works in place of `--model vllm` but is much slower. Do not pass `--num_fewshot`: every row is scored, so the harness would draw exemplars from the test split.

## Results

21 baseline models have been evaluated. Per-model scores and run configurations are in [Indic-Agri-Benchmark-Model-Configs](https://github.com/sthanika-ai/Indic-Agri-Benchmark-Model-Configs); the full report is at [sthanika.ai](https://sthanika.ai/research/indic-agri-advisory-2026).

## Citation

If you use this benchmark, please cite both the original KCC data release and this derived dataset.

Original data: Kisan Call Centre transcripts, Government of India (Ministry of Agriculture & Farmers' Welfare), distributed via data.gov.in.

```bibtex
@dataset{indic_kcc_agri_advisory_benchmark,
  title        = {Indic-KCC-Agri-Advisory-Benchmark},
  author       = {Sthānika AI},
  year         = {2026},
  version      = {1.0},
  publisher    = {Hugging Face},
  url          = {https://huggingface.co/datasets/sthanika-ai/Indic-KCC-Agri-Advisory-Benchmark},
  note         = {Derived from Kisan Call Centre (KCC) transcripts, Government of India, licensed GODL-India; see DATA_LICENSE.md}
}
```

## License

Code is MIT ([LICENSE](LICENSE)); the data is GODL-India and must be attributed when reused ([DATA_LICENSE.md](DATA_LICENSE.md)).

## Related

- Dataset on Hugging Face (gated): [sthanika-ai/Indic-KCC-Agri-Advisory-Benchmark](https://huggingface.co/datasets/sthanika-ai/Indic-KCC-Agri-Advisory-Benchmark)
- Leaderboard and model configs: [Indic-Agri-Benchmark-Model-Configs](https://github.com/sthanika-ai/Indic-Agri-Benchmark-Model-Configs)
- Fine-tuned model judged on this benchmark: [gemma3-12b-kcc-advisory](https://huggingface.co/sthanika-ai/gemma3-12b-kcc-advisory)
- Site: [sthanika.ai](https://sthanika.ai)
