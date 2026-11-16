from app.prompt_engine import render_prompt


def test_render_prompt_uses_saved_template():
    result = render_prompt("code_review", {
        "commit_sha": "abc123",
        "scanner_findings": "[]",
        "code_context": "safe sample",
    })
    assert result["version"] >= 1
    assert "abc123" in result["template"]
    assert "{{commit_sha}}" not in result["template"]
