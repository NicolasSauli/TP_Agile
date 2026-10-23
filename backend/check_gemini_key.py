import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import errors
from google.genai import types

from backend.agents import MODEL


def main() -> int:
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(
            "Erreur : GEMINI_API_KEY est absente du fichier .env ou de l'environnement.",
            file=sys.stderr,
        )
        return 1

    try:
        client = genai.Client(api_key=api_key)
        client.models.generate_content(
            model=MODEL,
            contents="Réponds uniquement : OK",
            config=types.GenerateContentConfig(max_output_tokens=1),
        )
    except errors.APIError as error:
        if error.code == 401 or error.code == 403:
            print(
                "Échec : la clé Gemini est invalide, révoquée ou n'a pas accès à l'API.",
                file=sys.stderr,
            )
            return 1
        if error.code == 429:
            print(
                "La clé Gemini a été transmise, mais la requête a atteint une limite "
                "de quota ou de débit. Vérifiez les quotas et la facturation Google AI.",
                file=sys.stderr,
            )
            return 1
        print(
            f"Échec de l'appel API Gemini (HTTP {error.code}) : {error}",
            file=sys.stderr,
        )
        return 1

    print(f"Clé valide : appel réussi avec le modèle {MODEL}.")
    print("Cet appel de test est minimal et peut entraîner un coût API minime.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
