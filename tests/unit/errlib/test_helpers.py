"""Comprehensive unit tests for resources.lib.errlib.helpers module."""
import pytest
import responses
import requests
from unittest.mock import patch, call
from datetime import datetime, timezone

from resources.lib.errlib.helpers import (
    download_url,
    strip_tags,
    convert_timestamp,
    get_subtitle_language,
    get_colour,
)
from resources.lib.errlib.constants import USER_AGENT


# ---------------------------------------------------------------------------
# download_url tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestDownloadUrl:
    """Tests for the download_url function."""

    TEST_URL = "https://services.err.ee/api/v2/test"

    @responses.activate
    @patch("resources.lib.errlib.helpers.time.sleep")
    def test_success_on_first_attempt(self, mock_sleep):
        """download_url returns response on first successful attempt."""
        # Arrange
        responses.add(responses.GET, self.TEST_URL, json={"ok": True}, status=200)

        # Act
        result = download_url(self.TEST_URL)

        # Assert
        assert result.status_code == 200
        assert result.json() == {"ok": True}
        assert len(responses.calls) == 1
        mock_sleep.assert_not_called()

    @responses.activate
    @patch("resources.lib.errlib.helpers.time.sleep")
    def test_retry_on_timeout(self, mock_sleep):
        """download_url retries when a timeout occurs and succeeds."""
        # Arrange
        responses.add(
            responses.GET,
            self.TEST_URL,
            body=requests.exceptions.Timeout("Connection timed out"),
        )
        responses.add(responses.GET, self.TEST_URL, json={"ok": True}, status=200)

        # Act
        result = download_url(self.TEST_URL)

        # Assert
        assert result.status_code == 200
        assert result.json() == {"ok": True}
        assert len(responses.calls) == 2
        mock_sleep.assert_called_once_with(0.5)

    @responses.activate
    @patch("resources.lib.errlib.helpers.time.sleep")
    def test_retry_on_connection_error(self, mock_sleep):
        """download_url retries when a ConnectionError occurs."""
        # Arrange
        responses.add(
            responses.GET,
            self.TEST_URL,
            body=requests.exceptions.ConnectionError("Connection refused"),
        )
        responses.add(responses.GET, self.TEST_URL, json={"ok": True}, status=200)

        # Act
        result = download_url(self.TEST_URL)

        # Assert
        assert result.status_code == 200
        assert len(responses.calls) == 2
        mock_sleep.assert_called_once_with(0.5)

    @responses.activate
    @patch("resources.lib.errlib.helpers.time.sleep")
    def test_retry_on_http_500(self, mock_sleep):
        """download_url retries when server returns HTTP 500."""
        # Arrange
        responses.add(responses.GET, self.TEST_URL, json={"error": "server"}, status=500)
        responses.add(responses.GET, self.TEST_URL, json={"ok": True}, status=200)

        # Act
        result = download_url(self.TEST_URL)

        # Assert
        assert result.status_code == 200
        assert result.json() == {"ok": True}
        assert len(responses.calls) == 2
        mock_sleep.assert_called_once_with(0.5)

    @responses.activate
    @patch("resources.lib.errlib.helpers.time.sleep")
    def test_exponential_backoff_timing(self, mock_sleep):
        """download_url uses exponential backoff: 0.5s, 1s, 2s, 4s."""
        # Arrange  -- 4 failures then success on 5th attempt
        for _ in range(4):
            responses.add(
                responses.GET,
                self.TEST_URL,
                body=requests.exceptions.ConnectionError("fail"),
            )
        responses.add(responses.GET, self.TEST_URL, json={"ok": True}, status=200)

        # Act
        result = download_url(self.TEST_URL)

        # Assert
        assert result.status_code == 200
        assert len(responses.calls) == 5
        expected_calls = [call(0.5), call(1.0), call(2.0), call(4.0)]
        assert mock_sleep.call_args_list == expected_calls

    @responses.activate
    @patch("resources.lib.errlib.helpers.time.sleep")
    def test_exhausts_retries_raises_runtime_error(self, mock_sleep):
        """download_url raises RuntimeError after 5 failed attempts."""
        # Arrange -- all 5 attempts fail
        for _ in range(5):
            responses.add(
                responses.GET,
                self.TEST_URL,
                body=requests.exceptions.ConnectionError("refused"),
            )

        # Act & Assert
        with pytest.raises(RuntimeError, match=r"Could not open URL after 5 attempts"):
            download_url(self.TEST_URL)

        assert len(responses.calls) == 5
        # Sleep is NOT called after the last (5th) attempt
        assert mock_sleep.call_count == 4

    @responses.activate
    @patch("resources.lib.errlib.helpers.time.sleep")
    def test_runtime_error_includes_url(self, mock_sleep):
        """RuntimeError message includes the URL that failed."""
        # Arrange
        for _ in range(5):
            responses.add(
                responses.GET,
                self.TEST_URL,
                body=requests.exceptions.Timeout("timed out"),
            )

        # Act & Assert
        with pytest.raises(RuntimeError, match=self.TEST_URL):
            download_url(self.TEST_URL)

    @responses.activate
    @patch("resources.lib.errlib.helpers.time.sleep")
    def test_runtime_error_includes_last_error(self, mock_sleep):
        """RuntimeError message includes the last exception details."""
        # Arrange
        for _ in range(5):
            responses.add(
                responses.GET,
                self.TEST_URL,
                body=requests.exceptions.Timeout("timed out"),
            )

        # Act & Assert
        with pytest.raises(RuntimeError, match=r"Last error:"):
            download_url(self.TEST_URL)

    @responses.activate
    @patch("resources.lib.errlib.helpers.time.sleep")
    def test_custom_headers_preserved(self, mock_sleep):
        """Custom headers passed to download_url are sent in the request."""
        # Arrange
        responses.add(responses.GET, self.TEST_URL, json={"ok": True}, status=200)
        custom_headers = [("X-Custom", "value123"), ("Accept", "application/json")]

        # Act
        download_url(self.TEST_URL, header=custom_headers)

        # Assert
        sent_headers = responses.calls[0].request.headers
        assert sent_headers["X-Custom"] == "value123"
        assert sent_headers["Accept"] == "application/json"

    @responses.activate
    @patch("resources.lib.errlib.helpers.time.sleep")
    def test_user_agent_always_added(self, mock_sleep):
        """User-Agent header is always set to the constant USER_AGENT value."""
        # Arrange
        responses.add(responses.GET, self.TEST_URL, json={"ok": True}, status=200)

        # Act
        download_url(self.TEST_URL)

        # Assert
        sent_headers = responses.calls[0].request.headers
        assert sent_headers["User-Agent"] == USER_AGENT

    @responses.activate
    @patch("resources.lib.errlib.helpers.time.sleep")
    def test_user_agent_with_custom_headers(self, mock_sleep):
        """User-Agent is set even when custom headers are provided."""
        # Arrange
        responses.add(responses.GET, self.TEST_URL, json={"ok": True}, status=200)
        custom_headers = [("Accept-Language", "et")]

        # Act
        download_url(self.TEST_URL, header=custom_headers)

        # Assert
        sent_headers = responses.calls[0].request.headers
        assert sent_headers["User-Agent"] == USER_AGENT
        assert sent_headers["Accept-Language"] == "et"

    @patch("resources.lib.errlib.helpers.time.sleep")
    def test_custom_timeout(self, mock_sleep):
        """download_url passes the custom timeout to requests.get."""
        # Arrange & Act -- patch requests.get directly to inspect call args
        with patch("resources.lib.errlib.helpers.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.raise_for_status.return_value = None
            mock_response.status_code = 200

            download_url(self.TEST_URL, timeout=30)

            # Assert
            mock_get.assert_called_once_with(
                self.TEST_URL,
                headers={"User-Agent": USER_AGENT},
                timeout=30,
                verify=True,
            )

    @patch("resources.lib.errlib.helpers.time.sleep")
    def test_default_timeout_is_10(self, mock_sleep):
        """download_url uses default timeout of 10 seconds."""
        # Arrange & Act
        with patch("resources.lib.errlib.helpers.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.raise_for_status.return_value = None

            download_url(self.TEST_URL)

            # Assert
            mock_get.assert_called_once_with(
                self.TEST_URL,
                headers={"User-Agent": USER_AGENT},
                timeout=10,
                verify=True,
            )

    @patch("resources.lib.errlib.helpers.time.sleep")
    def test_https_verify_true(self, mock_sleep):
        """download_url sets verify=True for HTTPS certificate checking."""
        # Arrange & Act
        with patch("resources.lib.errlib.helpers.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.raise_for_status.return_value = None

            download_url(self.TEST_URL)

            # Assert
            _, kwargs = mock_get.call_args
            assert kwargs["verify"] is True

    @responses.activate
    @patch("resources.lib.errlib.helpers.time.sleep")
    def test_no_custom_headers(self, mock_sleep):
        """download_url works when no custom headers are provided (header=None)."""
        # Arrange
        responses.add(responses.GET, self.TEST_URL, json={"data": 1}, status=200)

        # Act
        result = download_url(self.TEST_URL)

        # Assert
        assert result.status_code == 200
        sent_headers = responses.calls[0].request.headers
        assert sent_headers["User-Agent"] == USER_AGENT


# ---------------------------------------------------------------------------
# strip_tags tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestStripTags:
    """Tests for the strip_tags function."""

    def test_removes_simple_html_tags(self):
        """strip_tags removes basic HTML tags."""
        # Arrange
        html = "<p>Hello World</p>"

        # Act
        result = strip_tags(html)

        # Assert
        assert result == "Hello World"

    def test_handles_none_input(self):
        """strip_tags returns empty string for None input."""
        # Arrange / Act
        result = strip_tags(None)

        # Assert
        assert result == ""

    def test_handles_empty_string(self):
        """strip_tags returns empty string for empty string input."""
        # Arrange / Act
        result = strip_tags("")

        # Assert
        assert result == ""

    def test_removes_nested_tags(self):
        """strip_tags removes nested HTML tags."""
        # Arrange
        html = "<div><p><strong>Bold text</strong></p></div>"

        # Act
        result = strip_tags(html)

        # Assert
        assert result == "Bold text"

    def test_removes_tags_with_attributes(self):
        """strip_tags removes tags that have attributes."""
        # Arrange
        html = '<a href="https://err.ee" class="link">Click here</a>'

        # Act
        result = strip_tags(html)

        # Assert
        assert result == "Click here"

    @pytest.mark.parametrize(
        "html_input, expected",
        [
            ("<br/>", ""),
            ("<img src='test.jpg'/>", ""),
            ("No tags here", "No tags here"),
            ("<b>one</b> and <i>two</i>", "one and two"),
            ("<span style='color:red'>red</span>", "red"),
            ("<h1>Title</h1><p>Body</p>", "TitleBody"),
        ],
        ids=[
            "self-closing-br",
            "self-closing-img",
            "no-tags",
            "multiple-inline-tags",
            "tag-with-style",
            "multiple-block-tags",
        ],
    )
    def test_various_html_inputs(self, html_input, expected):
        """strip_tags handles various HTML patterns correctly."""
        assert strip_tags(html_input) == expected


# ---------------------------------------------------------------------------
# convert_timestamp tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestConvertTimestamp:
    """Tests for the convert_timestamp function."""

    def test_valid_unix_timestamp(self):
        """convert_timestamp converts a known Unix timestamp correctly."""
        # Arrange
        # Use a timestamp and derive the expected value from the same function
        # to be timezone-independent.
        timestamp = 1700000000
        expected = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        # Act
        result = convert_timestamp(timestamp)

        # Assert
        assert result == expected

    def test_zero_timestamp(self):
        """convert_timestamp converts Unix epoch (0) correctly."""
        # Arrange
        expected = datetime.fromtimestamp(0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        # Act
        result = convert_timestamp(0)

        # Assert
        assert result == expected

    def test_string_timestamp(self):
        """convert_timestamp accepts a string representation of a timestamp."""
        # Arrange
        timestamp = 1700000000
        expected = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        # Act
        result = convert_timestamp("1700000000")

        # Assert
        assert result == expected

    def test_output_format(self):
        """convert_timestamp returns string in YYYY-MM-DD HH:MM:SS format."""
        # Arrange / Act
        result = convert_timestamp(1700000000)

        # Assert -- verify format with regex
        import re

        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", result)


# ---------------------------------------------------------------------------
# get_subtitle_language tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestGetSubtitleLanguage:
    """Tests for the get_subtitle_language function."""

    @pytest.mark.parametrize(
        "lang_input, expected",
        [
            (0, "ET"),
            (1, "VA"),
            (2, "RU"),
        ],
        ids=["estonian", "voice-over", "russian"],
    )
    def test_known_language_mappings(self, lang_input, expected):
        """get_subtitle_language maps known integer values correctly."""
        # Act
        result = get_subtitle_language(lang_input)

        # Assert
        assert result == expected

    @pytest.mark.parametrize(
        "unknown_input",
        [3, 10, 99, -1],
        ids=["three", "ten", "ninety-nine", "negative-one"],
    )
    def test_unknown_language_defaults_to_et(self, unknown_input):
        """get_subtitle_language returns 'ET' for unknown language codes."""
        # Act
        result = get_subtitle_language(unknown_input)

        # Assert
        assert result == "ET"

    @pytest.mark.parametrize(
        "string_input, expected",
        [
            ("0", "ET"),
            ("1", "VA"),
            ("2", "RU"),
            ("5", "ET"),
        ],
        ids=["string-0-ET", "string-1-VA", "string-2-RU", "string-5-default"],
    )
    def test_string_input_converted(self, string_input, expected):
        """get_subtitle_language accepts string input and converts to int."""
        # Act
        result = get_subtitle_language(string_input)

        # Assert
        assert result == expected


# ---------------------------------------------------------------------------
# get_colour tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestGetColour:
    """Tests for the get_colour function."""

    @pytest.mark.parametrize(
        "color_input, expected",
        [
            (0, "white"),
            (1, "ivory"),
            (2, "silver"),
            (3, "gray"),
            (4, "limegreen"),
            (5, "green"),
            (6, "lightblue"),
            (7, "blue"),
            (8, "deeppink"),
            (9, "turquoise"),
            (10, "gold"),
            (11, "yellow"),
            (12, "brown"),
            (13, "orange"),
            (14, "red"),
        ],
        ids=[
            "0-white",
            "1-ivory",
            "2-silver",
            "3-gray",
            "4-limegreen",
            "5-green",
            "6-lightblue",
            "7-blue",
            "8-deeppink",
            "9-turquoise",
            "10-gold",
            "11-yellow",
            "12-brown",
            "13-orange",
            "14-red",
        ],
    )
    def test_all_valid_colors(self, color_input, expected):
        """get_colour returns the correct color name for all 15 valid inputs."""
        # Act
        result = get_colour(color_input)

        # Assert
        assert result == expected

    @pytest.mark.parametrize(
        "unknown_input",
        [15, 20, 100, -1],
        ids=["fifteen", "twenty", "hundred", "negative-one"],
    )
    def test_unknown_color_defaults_to_blue(self, unknown_input):
        """get_colour returns 'blue' for unknown color codes."""
        # Act
        result = get_colour(unknown_input)

        # Assert
        assert result == "blue"

    @pytest.mark.parametrize(
        "string_input, expected",
        [
            ("0", "white"),
            ("7", "blue"),
            ("14", "red"),
            ("99", "blue"),
        ],
        ids=["string-0-white", "string-7-blue", "string-14-red", "string-99-default"],
    )
    def test_string_input_converted(self, string_input, expected):
        """get_colour accepts string input and converts to int."""
        # Act
        result = get_colour(string_input)

        # Assert
        assert result == expected
