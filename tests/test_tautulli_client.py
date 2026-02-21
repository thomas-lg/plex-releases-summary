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


class TestTautulliClientSanitizeEdgeCases:
    """Edge-case tests for _sanitize_error and _sanitize_exception."""

    @pytest.mark.unit
    def test_sanitize_error_with_empty_api_key(self):
        """_sanitize_error should still run APIKEY_PATTERN redaction even when api_key is empty."""
        client = TautulliClient("http://tautulli:8181", "")  # empty api_key → falsy
        error = RuntimeError("request to http://t:8181?apikey=leaked&cmd=test failed")
        message = client._sanitize_error(error)
        # Pattern should still redact 'apikey=leaked' even when api_key is empty string
        assert "apikey=***" in message


class TestTautulliClientHappyPaths:
    """Tests for successful (happy-path) API responses."""

    @pytest.mark.unit
    def test_get_recently_added_dict_format_returns_typed_payload(self, monkeypatch):
        """Valid dict-format response should be returned as a dict with 'recently_added' key."""
        client = TautulliClient("http://tautulli:8181", "test-key")

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "response": {
                "result": "success",
                "data": {
                    "recently_added": [
                        {
                            "added_at": 1700000000,
                            "media_type": "movie",
                            "title": "Inception",
                        }
                    ]
                },
            }
        }
        monkeypatch.setattr("src.tautulli_client.requests.get", lambda *a, **kw: response)

        result = client.get_recently_added()

        assert isinstance(result, dict)
        assert "recently_added" in result
        assert result["recently_added"][0].get("title") == "Inception"

    @pytest.mark.unit
    def test_get_server_identity_returns_machine_identifier(self, monkeypatch):
        """Valid server identity response should be returned with machine_identifier."""
        client = TautulliClient("http://tautulli:8181", "test-key")

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "response": {
                "result": "success",
                "data": {
                    "machine_identifier": "abc123",
                    "version": "2.13.4",
                },
            }
        }
        monkeypatch.setattr("src.tautulli_client.requests.get", lambda *a, **kw: response)

        result = client.get_server_identity()

        assert isinstance(result, dict)
        assert result.get("machine_identifier") == "abc123"

    @pytest.mark.unit
    def test_get_server_identity_list_response_raises_runtime_error(self, monkeypatch):
        """Non-dict data in server identity response should raise RuntimeError."""
        client = TautulliClient("http://tautulli:8181", "test-key")

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "response": {
                "result": "success",
                "data": ["unexpected", "list"],  # List instead of dict
            }
        }
        monkeypatch.setattr("src.tautulli_client.requests.get", lambda *a, **kw: response)

        with pytest.raises(RuntimeError, match="expected dict"):
            client.get_server_identity()


class TestTautulliClientUnexpectedFormats:
    """Tests for unexpected API response format handling."""

    @pytest.mark.unit
    def test_get_recently_added_unexpected_format_raises_runtime_error(self, monkeypatch):
        """Response that is neither a dict nor a list should raise RuntimeError."""
        client = TautulliClient("http://tautulli:8181", "test-key")

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "response": {
                "result": "success",
                "data": "unexpected-string",  # Not a dict or list
            }
        }
        monkeypatch.setattr("src.tautulli_client.requests.get", lambda *a, **kw: response)

        with pytest.raises(RuntimeError, match="Unexpected response format"):
            client.get_recently_added()


class TestTautulliClientRetryLogic:
    """Tests for _request retry behaviour and logging."""

    @pytest.mark.unit
    def test_request_retries_then_succeeds(self, monkeypatch):
        """_request should retry after transient failures and return on eventual success."""
        sleep_calls: list[float] = []
        monkeypatch.setattr("src.tautulli_client.time.sleep", lambda s: sleep_calls.append(s))

        attempt_counter = {"n": 0}

        def mock_get(url, params, timeout):
            attempt_counter["n"] += 1
            if attempt_counter["n"] < 3:
                raise requests.RequestException("transient error")
            resp = Mock()
            resp.raise_for_status.return_value = None
            resp.json.return_value = {"response": {"result": "success", "data": {"recently_added": []}}}
            return resp

        monkeypatch.setattr("src.tautulli_client.requests.get", mock_get)

        client = TautulliClient("http://tautulli:8181", "key")
        client._request("get_recently_added", max_retries=3, count=10)

        assert attempt_counter["n"] == 3
        assert len(sleep_calls) == 2  # slept between attempt 1→2 and 2→3

    @pytest.mark.unit
    def test_request_logs_error_on_final_failure(self, monkeypatch, caplog):
        """Final failed attempt should produce an ERROR log entry."""
        monkeypatch.setattr("src.tautulli_client.time.sleep", lambda _: None)

        def always_fail(url, params, timeout):
            raise requests.RequestException("persists")

        monkeypatch.setattr("src.tautulli_client.requests.get", always_fail)

        client = TautulliClient("http://tautulli:8181", "key")
        caplog.set_level("ERROR")

        with pytest.raises(requests.RequestException):
            client._request("get_recently_added", max_retries=2)

        error_records = [r for r in caplog.records if r.levelname == "ERROR"]
        assert error_records, "Expected error-level log on final failed attempt"
