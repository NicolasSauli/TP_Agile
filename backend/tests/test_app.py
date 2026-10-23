import tempfile
import unittest
from pathlib import Path

from app import QUESTIONS, create_app


class ConversationApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temporary_directory.name) / "test.sqlite3"
        self.app = create_app(database_path)
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def start_conversation(self) -> str:
        response = self.client.post(
            "/api/conversations",
            json={"message": "Créer une application pour organiser des événements."},
        )
        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(payload["progress"], {"answered": 0, "total": len(QUESTIONS)})
        self.assertEqual(payload["next_question"]["id"], QUESTIONS[0]["id"])
        return payload["conversation_id"]

    def test_validates_initial_message(self) -> None:
        response = self.client.post("/api/conversations", json={"message": "  "})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_collects_written_answers_and_persists_conversation(self) -> None:
        conversation_id = self.start_conversation()
        for index, question in enumerate(QUESTIONS):
            response = self.client.post(
                f"/api/conversations/{conversation_id}/messages",
                json={"message": f"Réponse écrite {index + 1}"},
            )
            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertEqual(payload["progress"]["answered"], index + 1)

        self.assertEqual(payload["status"], "complete")
        self.assertIsNone(payload["next_question"])
        self.assertEqual(
            payload["summary"]["confirmed"]["Fonctionnalités principales"],
            "Réponse écrite 1",
        )
        self.assertEqual(payload["summary"]["unknown"], [])

        restored = self.client.get(f"/api/conversations/{conversation_id}")
        self.assertEqual(restored.status_code, 200)
        self.assertEqual(len(restored.get_json()["messages"]), 2 + 2 * len(QUESTIONS))

    def test_records_unknown_answers_without_inventing_a_value(self) -> None:
        conversation_id = self.start_conversation()
        response = self.client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={"message": "Je ne sais pas encore"},
        )
        payload = response.get_json()
        self.assertEqual(payload["progress"]["answered"], 1)

        for index in range(1, len(QUESTIONS)):
            response = self.client.post(
                f"/api/conversations/{conversation_id}/messages",
                json={"message": f"Réponse {index + 1}"},
            )
        summary = response.get_json()["summary"]
        self.assertIn(QUESTIONS[0]["title"], summary["unknown"])
        self.assertNotIn(QUESTIONS[0]["title"], summary["confirmed"])
        self.assertEqual(summary["hypotheses"], [])

    def test_rejects_messages_after_completion(self) -> None:
        conversation_id = self.start_conversation()
        for index in range(len(QUESTIONS)):
            self.client.post(
                f"/api/conversations/{conversation_id}/messages",
                json={"message": f"Réponse {index + 1}"},
            )
        response = self.client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={"message": "Encore une réponse"},
        )
        self.assertEqual(response.status_code, 409)

    def test_updates_and_persists_completed_answers(self) -> None:
        conversation_id = self.start_conversation()
        for index in range(len(QUESTIONS)):
            self.client.post(
                f"/api/conversations/{conversation_id}/messages",
                json={"message": f"Réponse {index + 1}"},
            )

        update = {
            "description": "Description mise à jour du projet.",
            "answers": {question["id"]: f"Nouvelle réponse {index + 1}" for index, question in enumerate(QUESTIONS)},
        }
        update["answers"]["budget"] = None
        response = self.client.patch(
            f"/api/conversations/{conversation_id}/answers",
            json=update,
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["summary"]["confirmed"]["Description initiale"], update["description"])
        self.assertEqual(
            payload["summary"]["confirmed"]["Fonctionnalités principales"],
            "Nouvelle réponse 1",
        )
        self.assertIn("Budget", payload["summary"]["unknown"])

        restored = self.client.get(f"/api/conversations/{conversation_id}")
        self.assertEqual(
            restored.get_json()["summary"]["confirmed"]["Fonctionnalités principales"],
            "Nouvelle réponse 1",
        )

    def test_rejects_invalid_answer_updates(self) -> None:
        conversation_id = self.start_conversation()
        update = {
            "description": "Description mise à jour.",
            "answers": {question["id"]: "Réponse" for question in QUESTIONS},
        }
        response = self.client.patch(
            f"/api/conversations/{conversation_id}/answers",
            json=update,
        )
        self.assertEqual(response.status_code, 409)

        for index in range(len(QUESTIONS)):
            self.client.post(
                f"/api/conversations/{conversation_id}/messages",
                json={"message": f"Réponse {index + 1}"},
            )

        update["answers"]["unexpected"] = "Valeur"
        response = self.client.patch(
            f"/api/conversations/{conversation_id}/answers",
            json=update,
        )
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
