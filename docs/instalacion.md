# Instalación y operación

## Requisitos existentes

- Ubuntu Server 24.04.4 LTS.
- Python 3.12.3.
- Runtime llama.cpp commit `85d5703`.
- GGUF Q4_K_M descargado localmente.

No se debe clonar, recompilar ni volver a descargar el modelo para operar esta instalación.

## Agente

```bash
cd /home/soporte/ai-agent
python3 -m venv .venv             # solo si no existiera
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m py_compile $(find app tests -name '*.py' -type f)
.venv/bin/python -m pytest -q
```

Inicio interactivo:

```bash
cd /home/soporte/ai-agent
source .venv/bin/activate
python -m app.main
```

## Runtime del modelo

Ubicaciones finales:

- Runtime: `/opt/llama.cpp` (`root:root`).
- Modelo: `/var/lib/llama/models/Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf` (`root:llama`, `0640`).
- Caché escribible: `/var/lib/llama/cache` (`llama:llama`).
- Unidad: `/etc/systemd/system/llama-server.service`.

El binario compilado conserva un RUNPATH absoluto hacia `/root/llama.cpp/build/bin`. La unidad define `LD_LIBRARY_PATH=/opt/llama.cpp/build/bin`, verificado mediante `ldd`, para cargar únicamente las bibliotecas copiadas en `/opt`.

Comandos:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now llama-server.service
systemctl status llama-server.service
systemctl is-enabled llama-server.service
ss -ltnp | grep ':8080'
curl -fsS http://127.0.0.1:8080/health
curl -fsS http://127.0.0.1:8080/v1/models
```

La copia versionada de la unidad está en `deploy/llama-server.service`.
