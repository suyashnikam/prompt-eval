import json

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {
            "type": "integer",
            "description": "Score from 1 (completely fails the rubric) to 5 (fully satisfies it)",
        },
        "passed": {"type": "boolean"},
        "reasoning": {"type": "string"},
    },
    "required": ["score", "passed", "reasoning"],
    "additionalProperties": False,
}

JUDGE_PROMPT_TEMPLATE = """You are grading an AI assistant's response against a rubric.

<input>
{input}
</input>

<response>
{output}
</response>

<rubric>
{rubric}
</rubric>

Score the response from 1 (completely fails the rubric) to 5 (fully satisfies the rubric). Set "passed" to true if the score is 4 or higher."""


def llm_judge(client, input_text: str, output: str, rubric: str, model: str) -> dict:
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        output_config={"format": {"type": "json_schema", "schema": JUDGE_SCHEMA}},
        messages=[
            {
                "role": "user",
                "content": JUDGE_PROMPT_TEMPLATE.format(
                    input=input_text, output=output, rubric=rubric
                ),
            }
        ],
    )
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)
