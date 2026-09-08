from pathlib import Path

import requests


API_BASE = "http://127.0.0.1:8080"
API_URL = f"{API_BASE}/v1/chat/completions"

MODEL_NAME = "Qwen3-Coder-30B-A3B-Instruct Q4_K_M"
ENGINE = "llama.cpp"
THREADS = 24
CONTEXT_SIZE = 8192
WORKSPACE = Path.home() / "ai-agent" / "workspace"


SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        f"Eres un agente de IA local basado en {MODEL_NAME} ejecutado mediante {ENGINE} "
        "dentro de Ubuntu Server "
        "No eres Claude ChatGPT Gemini ni ningún otro modelo "
        f"Si preguntan qué modelo utilizas responde {MODEL_NAME} mediante {ENGINE} "
        "Ayudas con programación Linux SQL Server análisis de código pruebas y administración técnica "
        "No inventes resultados de comandos archivos herramientas ni acciones "
        "Si necesitas información real que no tienes debes indicarlo o solicitar una herramienta"
    ),
}


def show_info():
    print()
    print("=== INFORMACIÓN DEL AGENTE ===")
    print(f"Modelo configurado : {MODEL_NAME}")
    print(f"Motor              : {ENGINE}")
    print(f"API                : {API_BASE}")
    print(f"Contexto           : {CONTEXT_SIZE} tokens")
    print(f"Threads            : {THREADS}")
    print(f"Workspace          : {WORKSPACE}")

    try:
        response = requests.get(
            f"{API_BASE}/v1/models",
            timeout=5,
        )
        response.raise_for_status()

        data = response.json()

        models = data.get("data") or data.get("models") or []

        if models:
            model = models[0]
            detected = (
                model.get("id")
                or model.get("name")
                or model.get("model")
                or "Modelo detectado"
            )
            print("Estado del modelo   : CONECTADO")
            print(f"Modelo detectado    : {detected}")
        else:
            print("Estado del modelo   : CONECTADO")
            print("Modelo detectado    : respuesta recibida sin nombre")

    except requests.RequestException:
        print("Estado del modelo   : DESCONECTADO")

    print("==============================")
    print()


messages = [SYSTEM_MESSAGE]

print("Agente IA local")
print(f"Modelo: {MODEL_NAME}")
print("Comandos: /info | /clear | /exit")
print()

while True:
    try:
        user_input = input("Tú> ").strip()

        if not user_input:
            continue

        command = user_input.lower()

        if command in {"/exit", "/quit"}:
            print("Saliendo...")
            break

        if command == "/clear":
            messages = [SYSTEM_MESSAGE]
            print("Contexto limpiado")
            print()
            continue

        if command == "/info":
            show_info()
            continue

        messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        payload = {
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1024,
        }

        response = requests.post(
            API_URL,
            json=payload,
            timeout=300,
        )

        response.raise_for_status()

        data = response.json()
        answer = data["choices"][0]["message"]["content"]

        messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        print()
        print("IA>", answer)
        print()

    except requests.exceptions.ConnectionError:
        print()
        print("ERROR: No puedo conectar con llama-server en 127.0.0.1:8080")
        print()

    except requests.exceptions.Timeout:
        print()
        print("ERROR: El modelo tardó demasiado en responder")
        print()

    except KeyboardInterrupt:
        print()
        print("Saliendo...")
        break

    except Exception as e:
        print()
        print(f"ERROR: {e}")
        print()
