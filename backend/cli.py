import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import errors

from backend.agents import format_json
from backend.orchestrator import ProjectOrchestrator


def main() -> int:
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(
            "Erreur : la variable d'environnement GEMINI_API_KEY n'est pas définie.",
            file=sys.stderr,
        )
        return 1

    title = input("Intitulé du projet à transmettre au Product Owner : ").strip()
    if not title:
        print("Erreur : l'intitulé du projet ne peut pas être vide.", file=sys.stderr)
        return 1

    try:
        client = genai.Client(api_key=api_key)
        plan = ProjectOrchestrator().run(client, title)
    except (errors.APIError, ValueError, RuntimeError) as error:
        print(f"Erreur pendant la génération Gemini : {error}", file=sys.stderr)
        return 1

    print(format_json(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
