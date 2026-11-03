def exact_match(output: str, expected: str) -> dict:
    passed = output.strip() == expected.strip()
    return {"passed": passed, "score": 1.0 if passed else 0.0}


def contains(output: str, expected: str) -> dict:
    passed = expected.strip().lower() in output.strip().lower()
    return {"passed": passed, "score": 1.0 if passed else 0.0}
