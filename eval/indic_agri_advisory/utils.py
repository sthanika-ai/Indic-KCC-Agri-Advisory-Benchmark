"""doc_to_text for the indic_agri_advisory_finalised task family (STAGE 1:
generation).

Imports SYSTEM_INSTRUCTION and question_line from eval/prompt_common.py
(one directory up) rather than redefining them here -- one prompt, shared by
every task/language, so there is no copy-pasted string to drift out of sync.
"""
import os
import sys
from pathlib import Path

_EVAL_DIR = Path(__file__).resolve().parent.parent  # .../eval
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from prompt_common import SYSTEM_INSTRUCTION, question_line  # noqa: E402

# Set this env var for the one candidate in your lineup with no chat template
# (a base model, not an instruct/chat model). When set, the full system
# instruction is flattened into doc_to_text itself and you should invoke
# lm_eval WITHOUT --apply_chat_template/--system_instruction. When unset
# (every chat/instruct candidate), doc_to_text returns just the user turn and
# you supply --system_instruction + --apply_chat_template so each model's own
# chat template formats it correctly.
_FLAT_PROMPT = os.environ.get('INDIC_AGRI_FLAT_PROMPT') == '1'


def doc_to_text(doc) -> str:
    question = question_line(doc['text'])
    if _FLAT_PROMPT:
        return f"{SYSTEM_INSTRUCTION}\n\n{question}\nAnswer:"
    return question
