import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import patch

from backend.check_gemini_key import main


class CheckGeminiKeyTests(unittest.TestCase):
    @patch("backend.check_gemini_key.genai.Client")
    @patch("backend.check_gemini_key.load_dotenv")
    def test_makes_minimal_request_and_does_not_print_key(
        self, load_dotenv: object, gemini_client: object
    ) -> None:
        client = gemini_client.return_value
        output = StringIO()
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-secret"}, clear=True):
            with redirect_stdout(output):
                result = main()

        self.assertEqual(result, 0)
        load_dotenv.assert_called_once()
        gemini_client.assert_called_once_with(api_key="test-secret")
        client.models.generate_content.assert_called_once()
        self.assertIn("Clé valide", output.getvalue())
        self.assertNotIn("test-secret", output.getvalue())

    @patch("backend.check_gemini_key.genai.Client")
    @patch("backend.check_gemini_key.load_dotenv")
    def test_reports_missing_key_without_calling_api(
        self, load_dotenv: object, gemini_client: object
    ) -> None:
        output = StringIO()
        with patch.dict("os.environ", {}, clear=True):
            with redirect_stderr(output):
                result = main()

        self.assertEqual(result, 1)
        load_dotenv.assert_called_once()
        gemini_client.assert_not_called()
        self.assertIn("GEMINI_API_KEY", output.getvalue())


if __name__ == "__main__":
    unittest.main()
