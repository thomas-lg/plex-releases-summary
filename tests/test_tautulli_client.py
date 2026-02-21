"""Unit tests for Tautulli client behavior and security safeguards."""

from unittest.mock import Mock

import pytest
import requests

from src.tautulli_client import TautulliClient


class TestTautulliClient:
    """Tests for TautulliClient."""

    @pytest.mark.unit
    def test_sanitize_error_redacts_api_key(self):
        """Sanitizer should redact explicit API key values from exception text."""
        client = TautulliClient("http://tautulli:8181", "super-secret")
        error = RuntimeError("request failed with token super-secret")

        message = client._sanitize_error(error)

        assert "super-secret" not in message
        assert "***" in message

    @pytest.mark.unit
    def test_request_failure_logs_redacted_query_string(self, monkeypatch, caplog):
        """Log output should redact apikey query values on request exceptions."""
        client = TautulliClient("http://tautulli:8181", "super-secret")

        def raise_request_exception(url, params, timeout):
            raise requests.RequestException(
                "failed calling " f"{url}?apikey={params['apikey']}&cmd={params['cmd']}&count={params.get('count', 0)}"
            )

        monkeypatch.setattr("src.tautulli_client.requests.get", raise_request_exception)

        caplog.set_level("ERROR")
        with pytest.raises(requests.RequestException):
            client._request("get_recently_added", max_retries=1, count=10)

        log_text = "\n".join(record.message for record in caplog.records)
        assert "super-secret" not in log_text
        assert "apikey=***" in log_text

    @pytest.mark.unit
    def test_request_failure_raises_redacted_exception(self, monkeypatch):
        """Raised request exceptions should be sanitized to avoid leaking secrets."""
        client = TautulliClient("http://tautulli:8181", "super-secret")

        def raise_request_exception(url, params, timeout):
            raise requests.RequestException(
                "failed calling " f"{url}?apikey={params['apikey']}&cmd={params['cmd']}&count={params.get('count', 0)}"
            )

        monkeypatch.setattr("src.tautulli_client.requests.get", raise_request_exception)

        with pytest.raises(requests.RequestException) as exc_info:
            client._request("get_recently_added", max_retries=1, count=10)

        error_message = str(exc_info.value)
        assert "super-secret" not in error_message
        assert "apikey=***" in error_message

    @pytest.mark.unit
    def test_unsuccessful_api_response_raises_safe_runtime_error(self, monkeypatch):
        """Unsuccessful API responses should raise concise command-scoped errors."""
        client = TautulliClient("http://tautulli:8181", "super-secret")

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "response": {
                "result": "error",
                "message": "access denied",
                "data": {},
            }
        }

        monkeypatch.setattr("src.tautulli_client.requests.get", lambda *args, **kwargs: response)

        with pytest.raises(RuntimeError) as exc_info:
            client._request("get_recently_added", max_retries=1, count=10)

        error_message = str(exc_info.value)
        assert "get_recently_added" in error_message
        assert "access denied" in error_message
        assert "super-secret" not in error_message

    @pytest.mark.unit
    def test_get_recently_added_missing_required_field(self, monkeypatch):
        """Malformed response missing required field should raise RuntimeError with validation details."""
        client = TautulliClient("http://tautulli:8181", "test-key")

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "response": {
                "result": "success",
                "data": {
                    "recently_added": [
                        {
                            "media_type": "movie",
                            "title": "Test Movie",
                            # Missing required 'added_at' field
                        }
                    ]
                },
            }
        }

        monkeypatch.setattr("src.tautulli_client.requests.get", lambda *args, **kwargs: response)

        with pytest.raises(RuntimeError) as exc_info:
            client.get_recently_added()

        error_message = str(exc_info.value)
        assert "validation failed" in error_message.lower()
        assert "added_at" in error_message.lower()

    @pytest.mark.unit
    def test_get_recently_added_wrong_type(self, monkeypatch):
        """Malformed response with wrong field type should raise RuntimeError."""
        client = TautulliClient("http://tautulli:8181", "test-key")

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "response": {
                "result": "success",
                "data": {
                    "recently_added": [
                        {
                            "added_at": "not-a-number",  # Should be int
                            "media_type": "movie",
                            "title": "Test Movie",
                        }
                    ]
                },
            }
        }

        monkeypatch.setattr("src.tautulli_client.requests.get", lambda *args, **kwargs: response)

        with pytest.raises(RuntimeError) as exc_info:
            client.get_recently_added()

        error_message = str(exc_info.value)
        assert "validation failed" in error_message.lower()

    @pytest.mark.unit
    def test_get_server_identity_missing_machine_id(self, monkeypatch):
        """Server identity response missing machine_identifier should raise RuntimeError."""
        client = TautulliClient("http://tautulli:8181", "test-key")

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "response": {
                "result": "success",
                "data": {
                    # Missing required 'machine_identifier' field
                    "version": "2.13.4"
                },
            }
        }

        monkeypatch.setattr("src.tautulli_client.requests.get", lambda *args, **kwargs: response)

        with pytest.raises(RuntimeError) as exc_info:
            client.get_server_identity()

        error_message = str(exc_info.value)
        assert "validation failed" in error_message.lower()
        assert "machine_identifier" in error_message.lower()

    @pytest.mark.unit
    def test_get_recently_added_list_format_validates(self, monkeypatch):
        """Older API returning list format should validate successfully."""
        client = TautulliClient("http://tautulli:8181", "test-key")

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "response": {
                "result": "success",
                "data": [
                    {
                        "added_at": 1234567890,
                        "media_type": "movie",
                        "title": "Test Movie",
                    }
                ],
            }
        }

        monkeypatch.setattr("src.tautulli_client.requests.get", lambda *args, **kwargs: response)

        result = client.get_recently_added()

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].get("title") == "Test Movie"
