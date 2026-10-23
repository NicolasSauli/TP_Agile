import unittest

from backend.cli import main


class CliGeminiKeyTests(unittest.TestCase):
    def test_reports_missing_gemini_key(self) -> None:
        from contextlib import redirect_stderr
        from io import StringIO
        from unittest.mock import patch

        output = StringIO()
        with patch("backend.cli.load_dotenv"), patch.dict("os.environ", {}, clear=True):
            with redirect_stderr(output):
                result = main()

        self.assertEqual(result, 1)
        self.assertIn("GEMINI_API_KEY", output.getvalue())


if __name__ == "__main__":
    unittest.main()
