import json
import os
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, g, jsonify, request


QUESTIONS = [
    {
        "id": "features",
        "title": "Fonctionnalités principales",
        "text": "Quelles sont les fonctionnalités indispensables pour la première version ?",
    },
    {
        "id": "target_users",
        "title": "Utilisateurs cibles",
        "text": "À qui s’adresse principalement le produit ?",
    },
    {
        "id": "technical_constraints",
        "title": "Contraintes techniques",
        "text": "Avez-vous des contraintes techniques ou une technologie à respecter ?",
    },
    {
        "id": "developer_count",
        "title": "Équipe disponible",
        "text": "Combien de développeurs seront disponibles pour ce projet ?",
    },
    {
        "id": "budget",
        "title": "Budget",
        "text": "Quel budget est prévu pour le projet ? Vous pouvez répondre « je ne sais pas encore ».",
    },
    {
        "id": "deadline",
        "title": "Date limite",
        "text": "Quelle est la date limite ou le délai souhaité pour la livraison ?",
    },
]

UNKNOWN_ANSWERS = (
    "je ne sais pas",
    "je n'ai pas encore",
    "je n’ai pas encore",
    "inconnu",
    "inconnue",
    "à définir",
    "pas encore défini",
    "pas encore définie",
)


def create_app(database_path: str | Path | None = None) -> Flask:
    app = Flask(__name__)
    default_database = Path(__file__).with_name("conversations.sqlite3")
    app.config["DATABASE"] = str(
        database_path or os.environ.get("CHATBOT_DATABASE_PATH", default_database)
    )

    database = Path(app.config["DATABASE"])
    database.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                answers_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL REFERENCES conversations(id),
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )

    @app.before_request
    def connect_database() -> None:
        connection = sqlite3.connect(app.config["DATABASE"])
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.database = connection

    @app.teardown_appcontext
    def close_database(error: BaseException | None = None) -> None:
        connection = g.pop("database", None)
        if connection is not None:
            connection.close()

    def current_database() -> sqlite3.Connection:
        return g.database

    def timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    def next_question(answers: dict[str, dict[str, Any]]) -> dict[str, str] | None:
        return next(
            (question for question in QUESTIONS if question["id"] not in answers),
            None,
        )

    def make_summary(
        description: str, answers: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        confirmed = {"Description initiale": description}
        unknown = []
        for question in QUESTIONS:
            answer = answers[question["id"]]
            if answer["status"] == "confirmed":
                confirmed[question["title"]] = answer["value"]
            else:
                unknown.append(question["title"])
        return {"confirmed": confirmed, "unknown": unknown, "hypotheses": []}

    def conversation_state(row: sqlite3.Row) -> dict[str, Any]:
        answers = json.loads(row["answers_json"])
        question = next_question(answers)
        state: dict[str, Any] = {
            "conversation_id": row["id"],
            "status": "collecting" if question else "complete",
            "progress": {"answered": len(answers), "total": len(QUESTIONS)},
            "next_question": question,
            "messages": [
                {"role": message["role"], "content": message["content"]}
                for message in current_database().execute(
                    """
                    SELECT role, content FROM messages
                    WHERE conversation_id = ? ORDER BY id
                    """,
                    (row["id"],),
                )
            ],
        }
        if question is None:
            state["summary"] = make_summary(row["description"], answers)
        return state

    def add_message(conversation_id: str, role: str, content: str) -> None:
        current_database().execute(
            """
            INSERT INTO messages (conversation_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (conversation_id, role, content, timestamp()),
        )

    def get_conversation(conversation_id: str) -> sqlite3.Row | None:
        return current_database().execute(
            "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()

    def read_message() -> tuple[str | None, tuple[Any, int] | None]:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return None, (jsonify(error="Le corps de la requête doit être un objet JSON."), 400)
        message = payload.get("message")
        if not isinstance(message, str) or not message.strip():
            return None, (jsonify(error="Le message ne peut pas être vide."), 400)
        if len(message) > 10000:
            return None, (jsonify(error="Le message ne peut pas dépasser 10 000 caractères."), 400)
        return message.strip(), None

    @app.post("/api/conversations")
    def create_conversation() -> tuple[Any, int]:
        description, error = read_message()
        if error:
            return error

        conversation_id = str(uuid.uuid4())
        answers: dict[str, dict[str, Any]] = {}
        question = next_question(answers)
        assistant_message = (
            "Merci, j’ai noté votre description. Pour préparer une synthèse fidèle, "
            f"je vais préciser les informations manquantes une par une. {question['text']}"
        )
        database = current_database()
        now = timestamp()
        database.execute(
            """
            INSERT INTO conversations (id, description, answers_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (conversation_id, description, json.dumps(answers), now, now),
        )
        add_message(conversation_id, "user", description)
        add_message(conversation_id, "assistant", assistant_message)
        database.commit()
        return jsonify(conversation_state(get_conversation(conversation_id))), 201

    @app.get("/api/conversations/<conversation_id>")
    def read_conversation(conversation_id: str) -> tuple[Any, int] | Any:
        conversation = get_conversation(conversation_id)
        if conversation is None:
            return jsonify(error="Cette conversation n’existe pas."), 404
        return jsonify(conversation_state(conversation))

    @app.patch("/api/conversations/<conversation_id>/answers")
    def update_conversation_answers(conversation_id: str) -> tuple[Any, int]:
        conversation = get_conversation(conversation_id)
        if conversation is None:
            return jsonify(error="Cette conversation n’existe pas."), 404
        if next_question(json.loads(conversation["answers_json"])) is not None:
            return jsonify(error="Terminez les questions avant de modifier la synthèse."), 409

        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="Le corps de la requête doit être un objet JSON."), 400

        description = payload.get("description")
        if not isinstance(description, str) or not description.strip():
            return jsonify(error="La description du projet ne peut pas être vide."), 400
        if len(description) > 10000:
            return jsonify(error="La description ne peut pas dépasser 10 000 caractères."), 400

        submitted_answers = payload.get("answers")
        question_ids = {question["id"] for question in QUESTIONS}
        if not isinstance(submitted_answers, dict) or set(submitted_answers) != question_ids:
            return jsonify(error="Les réponses doivent contenir toutes les informations attendues."), 400

        answers: dict[str, dict[str, Any]] = {}
        for question in QUESTIONS:
            value = submitted_answers[question["id"]]
            if value is not None and not isinstance(value, str):
                return jsonify(error=f"La réponse « {question['title']} » doit être du texte."), 400
            if isinstance(value, str) and len(value) > 10000:
                return jsonify(error=f"La réponse « {question['title']} » dépasse 10 000 caractères."), 400

            is_unknown = value is None or not value.strip() or value.casefold().startswith(UNKNOWN_ANSWERS)
            answers[question["id"]] = {
                "value": None if is_unknown else value.strip(),
                "status": "unknown" if is_unknown else "confirmed",
            }

        database = current_database()
        database.execute(
            """
            UPDATE conversations
            SET description = ?, answers_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                description.strip(),
                json.dumps(answers, ensure_ascii=False),
                timestamp(),
                conversation_id,
            ),
        )
        database.commit()
        return jsonify(conversation_state(get_conversation(conversation_id)))

    @app.post("/api/conversations/<conversation_id>/messages")
    def add_conversation_message(conversation_id: str) -> tuple[Any, int]:
        message, error = read_message()
        if error:
            return error
        conversation = get_conversation(conversation_id)
        if conversation is None:
            return jsonify(error="Cette conversation n’existe pas."), 404

        answers = json.loads(conversation["answers_json"])
        question = next_question(answers)
        if question is None:
            return jsonify(error="La synthèse de cette conversation est déjà complète."), 409

        normalized_message = message.casefold()
        is_unknown = normalized_message.startswith(UNKNOWN_ANSWERS)
        answers[question["id"]] = {
            "value": None if is_unknown else message,
            "status": "unknown" if is_unknown else "confirmed",
        }
        following_question = next_question(answers)
        if following_question is None:
            assistant_message = (
                "Merci, j’ai terminé la collecte. Voici la synthèse des informations "
                "confirmées et des points qui restent à préciser."
            )
        elif is_unknown:
            assistant_message = (
                f"Bien noté : « {question['title']} » reste à préciser. "
                f"{following_question['text']}"
            )
        else:
            assistant_message = (
                f"Merci, j’ai noté votre réponse pour « {question['title']} ». "
                f"{following_question['text']}"
            )

        database = current_database()
        add_message(conversation_id, "user", message)
        add_message(conversation_id, "assistant", assistant_message)
        database.execute(
            "UPDATE conversations SET answers_json = ?, updated_at = ? WHERE id = ?",
            (json.dumps(answers, ensure_ascii=False), timestamp(), conversation_id),
        )
        database.commit()
        return jsonify(conversation_state(get_conversation(conversation_id)))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
