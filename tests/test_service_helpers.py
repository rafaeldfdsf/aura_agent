import unittest

from assistant.service import build_client_action, matches_memory_clear_command


class ServiceHelperTests(unittest.TestCase):
    def test_matches_memory_clear_command_requires_clear_intent(self):
        self.assertTrue(matches_memory_clear_command("limpa a memoria"))
        self.assertTrue(matches_memory_clear_command("esquecer preferencias antigas"))
        self.assertFalse(matches_memory_clear_command("memoria"))
        self.assertFalse(matches_memory_clear_command("limpa isto"))

    def test_build_client_action_normalizes_url_and_open_app(self):
        open_url = build_client_action(
            {"tool_name": "open_website", "arguments": {"url": "example.com"}}
        )
        open_youtube = build_client_action(
            {"tool_name": "open_app", "arguments": {"app_name": "youtube"}}
        )
        open_app = build_client_action(
            {"tool_name": "open_app", "arguments": {"app_name": "spotify"}}
        )

        self.assertEqual(open_url, {"type": "open_url", "url": "https://example.com"})
        self.assertEqual(
            open_youtube,
            {"type": "open_url", "url": "https://www.youtube.com"},
        )
        self.assertEqual(
            open_app,
            {"type": "open_app", "app_name": "spotify"},
        )


if __name__ == "__main__":
    unittest.main()
