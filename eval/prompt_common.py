"""Single source of truth for the farmer-facing prompt template used by this
benchmark's Stage 1 evaluation, so every task config imports the exact same
SYSTEM_INSTRUCTION and question formatting -- no copy-pasted strings to
drift out of sync across languages/tasks.
"""

SYSTEM_INSTRUCTION = (
    "You are an agricultural extension expert advising Indian farmers on crop "
    "pests, diseases, and cultivation practices. Answer the farmer's question "
    "directly and practically. Reply in the same language and script the "
    "question was asked in. If a photo is provided, base your diagnosis on it. "
    "If the question is outside your knowledge or not answerable with "
    "confidence, say so plainly instead of guessing."
)

QUESTION_LINE_TEMPLATE = "Farmer's question: {text}"


def question_line(text: str) -> str:
    return QUESTION_LINE_TEMPLATE.format(text=text)
