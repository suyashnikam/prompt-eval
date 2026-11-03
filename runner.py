#!/usr/bin/env python3
import argparse
import json
import time
from pathlib import Path

import yaml

from client import get_client, resolve_model_id
from config import DEFAULT_JUDGE_MODEL, DEFAULT_MODEL, MAX_TOKENS
from graders.exact_match import contains, exact_match
from graders.llm_judge import llm_judge

ROOT = Path(__file__).parent


def load_yaml(path: Path):
    with open(path) as f:
        return yaml.safe_load(f)


def run_eval(prompt_path: Path, test_cases_path: Path, model: str, judge_model: str, out_path: Path):
    prompt_cfg = load_yaml(prompt_path)
    test_cases = load_yaml(test_cases_path)

    client = get_client()
    model = resolve_model_id(model, client)
    judge_model = resolve_model_id(judge_model, client)

    results = []
    for case in test_cases:
        user_content = prompt_cfg.get("template", "{input}").format(input=case["input"])

        kwargs = {
            "model": model,
            "max_tokens": MAX_TOKENS,
            "messages": [{"role": "user", "content": user_content}],
        }
        if prompt_cfg.get("system"):
            kwargs["system"] = prompt_cfg["system"]

        response = client.messages.create(**kwargs)
        output_text = next((b.text for b in response.content if b.type == "text"), "")

        grader = case.get("grader", "exact_match")
        if grader == "exact_match":
            grade = exact_match(output_text, case.get("expected", ""))
        elif grader == "contains":
            grade = contains(output_text, case.get("expected", ""))
        elif grader == "llm_judge":
            grade = llm_judge(client, case["input"], output_text, case.get("rubric", ""), model=judge_model)
        else:
            raise ValueError(f"Unknown grader: {grader}")

        results.append({
            "id": case.get("id"),
            "input": case["input"],
            "output": output_text,
            "grader": grader,
            **grade,
        })
        status = "PASS" if grade.get("passed") else "FAIL"
        print(f"[{status}] {case.get('id')}")

    passed = sum(1 for r in results if r.get("passed"))
    total = len(results)
    summary = {
        "prompt": str(prompt_path),
        "model": model,
        "judge_model": judge_model,
        "passed": passed,
        "total": total,
        "pass_rate": passed / total if total else 0,
        "results": results,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{passed}/{total} passed ({summary['pass_rate']:.0%})")
    print(f"Report written to {out_path}")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Run a prompt evaluation")
    parser.add_argument("--prompt", required=True, help="Path to prompt YAML")
    parser.add_argument("--test-cases", required=True, help="Path to test cases YAML")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--judge-model", default=DEFAULT_JUDGE_MODEL)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    out_path = Path(args.out) if args.out else ROOT / "reports" / f"run_{int(time.time())}.json"
    run_eval(Path(args.prompt), Path(args.test_cases), args.model, args.judge_model, out_path)


if __name__ == "__main__":
    main()


