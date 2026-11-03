import os

import anthropic
from dotenv import load_dotenv

# Pick up ANTHROPIC_API_KEY / AWS_REGION / AWS_PROFILE from a local .env file, if present.
load_dotenv()


def get_client():
    """Return a first-party Anthropic client if ANTHROPIC_API_KEY is set,
    otherwise fall back to Claude on Amazon Bedrock."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return anthropic.Anthropic()

    from anthropic import AnthropicBedrockMantle

    aws_region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
    if not aws_region:
        raise RuntimeError(
            "No ANTHROPIC_API_KEY set, and no AWS_REGION / AWS_DEFAULT_REGION found "
            "for Bedrock. Export AWS_REGION=<your-region> (and AWS_PROFILE if needed)."
        )
    return AnthropicBedrockMantle(aws_region=aws_region)


def resolve_model_id(model: str, client) -> str:
    """Bedrock model IDs need an 'anthropic.' prefix; first-party IDs don't."""
    from anthropic import AnthropicBedrockMantle

    if isinstance(client, AnthropicBedrockMantle) and not model.startswith("anthropic."):
        return f"anthropic.{model}"
    return model
