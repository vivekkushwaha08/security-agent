"""Load and render the latest prompt JSON at job execution time."""
import re
from app.config_store import get_prompt

TOKEN = re.compile(r"{{([a-zA-Z0-9_]+)}}")


def render_prompt(prompt_id: str, context: dict[str, object]) -> dict[str, object]:
    prompt = get_prompt(prompt_id)
    if not prompt.get("enabled", True):
        raise ValueError(f"Prompt {prompt_id} is disabled")
    template = prompt["template"]
    rendered = TOKEN.sub(lambda match: str(context.get(match.group(1), "")), template)
    return {
        "id": prompt["id"],
        "version": prompt.get("version", 1),
        "system": prompt.get("system", ""),
        "template": rendered,
        "output_format": prompt.get("output_format", "json"),
    }
