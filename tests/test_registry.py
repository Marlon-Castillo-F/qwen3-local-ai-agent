import pytest

from app.tools.base import (
    ToolNotAllowedError,
    ToolRegistry,
    ToolSpec,
    ToolValidationError,
)


def registry() -> ToolRegistry:
    value = ToolRegistry()
    value.register(
        ToolSpec(
            name="echo",
            description="test",
            parameters={
                "type": "object",
                "properties": {"value": {"type": "string"}},
                "required": ["value"],
                "additionalProperties": False,
            },
            handler=lambda value: value,
        )
    )
    return value


def test_tool_not_allowed():
    with pytest.raises(ToolNotAllowedError):
        registry().execute("rm", {})


@pytest.mark.parametrize(
    "arguments",
    ["not-json", "[]", {}, {"value": 7}, {"value": "x", "sudo": True}],
)
def test_invalid_arguments(arguments):
    with pytest.raises(ToolValidationError):
        registry().execute("echo", arguments)


def test_valid_arguments():
    assert registry().execute("echo", '{"value": "ok"}') == "ok"
