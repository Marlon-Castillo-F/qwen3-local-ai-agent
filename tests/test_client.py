import requests

import pytest

from app.client import LlamaClient, ModelConnectionError


class FakeResponse:
    def __init__(self, payload, status_error=None):
        self.payload = payload
        self.status_error = status_error

    def raise_for_status(self):
        if self.status_error:
            raise self.status_error

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.last_json = None

    def get(self, *args, **kwargs):
        if self.error:
            raise self.error
        return self.response

    def post(self, *args, **kwargs):
        self.last_json = kwargs["json"]
        if self.error:
            raise self.error
        return self.response


def test_info_uses_real_models_endpoint(settings):
    session = FakeSession(FakeResponse({"data": [{"id": "real-model"}]}))
    info = LlamaClient(settings, session=session).model_info()
    assert info["connected"] is True
    assert info["detected_model"] == "real-model"


def test_connection_error(settings):
    session = FakeSession(error=requests.ConnectionError("offline"))
    with pytest.raises(ModelConnectionError):
        LlamaClient(settings, session=session).model_info()


def test_chat_parses_tool_calls_and_sends_tools(settings):
    payload = {
        "choices": [
            {
                "finish_reason": "tool_calls",
                "message": {
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call-1",
                            "type": "function",
                            "function": {
                                "name": "list_files",
                                "arguments": "{}",
                            },
                        }
                    ],
                },
            }
        ],
        "model": "real-model",
    }
    session = FakeSession(FakeResponse(payload))
    response = LlamaClient(settings, session=session).chat(
        [{"role": "user", "content": "lista"}],
        [{"type": "function", "function": {"name": "list_files"}}],
    )
    assert response.tool_calls[0].name == "list_files"
    assert session.last_json["tool_choice"] == "auto"
    assert session.last_json["parallel_tool_calls"] is False
