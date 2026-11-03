import json

from client import get_client, resolve_model_id
from config import DEFAULT_MODEL

SCORE_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_score": {
            "type": "integer",
            "description": "Overall prompt quality score from 1 (very poor) to 10 (excellent)",
        },
        "scorecard": {
            "type": "object",
            "properties": {
                "clarity": {"type": "integer", "description": "1-10: Is the request clear and unambiguous?"},
                "specificity": {"type": "integer", "description": "1-10: Enough concrete detail to act on, not vague"},
                "context": {"type": "integer", "description": "1-10: Provides necessary background, audience, or role"},
                "structure": {"type": "integer", "description": "1-10: Specifies the desired output format/structure"},
                "constraints": {"type": "integer", "description": "1-10: States tone, length, scope, or edge-case handling"},
                "actionability": {"type": "integer", "description": "1-10: An AI could act on this immediately without guessing"},
            },
            "required": ["clarity", "specificity", "context", "structure", "constraints", "actionability"],
            "additionalProperties": False,
        },
        "strengths": {
            "type": "array",
            "items": {"type": "string"},
            "description": "What the prompt already does well",
        },
        "improvement_points": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Specific, actionable gaps in the prompt",
        },
        "improved_prompt": {
            "type": "string",
            "description": (
                "A rewritten version of the prompt that fixes every weakness found, while preserving "
                "the user's original intent. Must be platform-agnostic — ready to paste into any "
                "AI tool, not reliant on features specific to one vendor."
            ),
        },
    },
    "required": ["overall_score", "scorecard", "strengths", "improvement_points", "improved_prompt"],
    "additionalProperties": False,
}

SCORER_SYSTEM_PROMPT = """You are an expert prompt engineer who reviews prompts written by non-experts and \
helps them improve. The prompt may end up running against any AI model or platform, not just Claude, so \
your scoring and your rewritten prompt must not rely on techniques specific to one vendor.

Score the prompt across these dimensions (each 1-10):
- clarity: Is the request clear and unambiguous?
- specificity: Does it include enough concrete detail to act on, rather than being vague?
- context: Does it provide necessary background, audience, or role information?
- structure: Does it specify the desired output format or structure?
- constraints: Does it state tone, length, scope, or how to handle edge cases?
- actionability: Could an AI act on this immediately without having to guess what's wanted?

Then write an improved version of the prompt that addresses every weakness you found, while preserving \
the user's original intent. The improved prompt should be ready to paste directly into any AI tool."""


def score_prompt(raw_prompt: str, model: str = DEFAULT_MODEL) -> dict:
    client = get_client()
    resolved_model = resolve_model_id(model, client)

    response = client.messages.create(
        model=resolved_model,
        max_tokens=4096,
        system=SCORER_SYSTEM_PROMPT,
        output_config={"format": {"type": "json_schema", "schema": SCORE_SCHEMA}},
        messages=[
            {
                "role": "user",
                "content": f"Here is the prompt to evaluate:\n\n<prompt>\n{raw_prompt}\n</prompt>",
            }
        ],
    )
    text = next(b.text for b in response.content if b.type == "text")
    result = json.loads(text)
    result["_meta"] = {
        "model": resolved_model,
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
    }
    return result
