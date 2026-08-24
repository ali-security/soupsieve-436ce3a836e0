"""Test attribute selectors."""
import signal
import time
import soupsieve as sv
from .. import util

# Seconds allowed for a malformed selector to fail. A malformed selector should fail
# almost immediately, so this is only generous enough to absorb a slow environment.
PARSE_TIMEOUT = 3


class TestAttribute(util.TestCase):
    """Test attribute selectors."""

    MARKUP = """
    <div id="div">
    <p id="0">Some text <span id="1"> in a paragraph</span>.</p>
    <a id="2" href="http://google.com">Link</a>
    <span id="3">Direct child</span>
    <pre id="pre">
    <span id="4">Child 1</span>
    <span id="5">Child 2</span>
    <span id="6">Child 3</span>
    </pre>
    </div>
    """

    def test_attribute_not_equal_no_quotes(self):
        """Test attribute with value that does not equal specified value (no quotes)."""

        # No quotes
        self.assert_selector(
            self.MARKUP,
            'body [id!=\\35]',
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def test_attribute_not_equal_quotes(self):
        """Test attribute with value that does not equal specified value (quotes)."""

        # Quotes
        self.assert_selector(
            self.MARKUP,
            "body [id!='5']",
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def test_attribute_not_equal_double_quotes(self):
        """Test attribute with value that does not equal specified value (double quotes)."""

        # Double quotes
        self.assert_selector(
            self.MARKUP,
            'body [id!="5"]',
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def assert_fails_fast(self, selector):
        """Assert the selector fails with a syntax error, not a timeout error."""

        def timeout_handler(signum, frame):
            """Turn a stalled parse into an immediate timeout error."""

            raise TimeoutError('Timed out parsing the selector')

        # `SIGALRM` is only available on Unix, so elsewhere we can only time the parse.
        alarm = hasattr(signal, 'SIGALRM')
        if alarm:
            original = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(PARSE_TIMEOUT)
        start = time.perf_counter()
        try:
            with self.assertRaises(sv.SelectorSyntaxError):
                sv.compile(selector)
        finally:
            if alarm:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, original)
        self.assertLess(time.perf_counter() - start, PARSE_TIMEOUT)

    def test_bad_attribute_unclused(self):
        """Test bad attribute fails for syntax error, not timeout error."""

        # A quoted attribute value with no closing quote must not send the
        # value pattern into catastrophic backtracking.
        self.assert_fails_fast('[a="' + ('x' * 300))
        self.assert_fails_fast("[a='" + ('x' * 300))

    def test_bad_value_unclosed_string(self):
        """Test string values with no closing quote fail for syntax error, not timeout error."""

        # Pseudo classes that accept string values reuse the same value pattern.
        self.assert_fails_fast(':lang("' + ('x' * 300))
        self.assert_fails_fast(":lang('" + ('x' * 300))
        self.assert_fails_fast(':-soup-contains("' + ('x' * 300))
        self.assert_fails_fast(":-soup-contains('" + ('x' * 300))
