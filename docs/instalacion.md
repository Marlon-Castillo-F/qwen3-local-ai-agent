# Instalación y operación

La configuración de cada equipo depende del modelo y del hardware. Esta guía separa los requisitos generales de las decisiones específicas del laboratorio validado.

## Requisitos generales

- Linux x86-64.
- Python 3.12 o una versión compatible con las dependencias.
- Git.
- `llama.cpp` compilado con soporte de servidor.
- Un modelo instruct compatible con tool calling en formato GGUF.
- Memoria suficiente para la cuantización y el contexto elegidos.

El modelo se descarga por separado. Los archivos `*.gguf` no deben añadirse al repositorio.

## Instalación genérica del agente

No existe todavía una URL remota configurada. Sustituye el placeholder al publicar el repositorio:

```bash
git clone <URL_DEL_REPOSITORIO>
cd ai-agent
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -q
```

Configura `AI_AGENT_API_BASE` y `AI_AGENT_MODEL` si el servidor no usa los valores predeterminados:

```bash
export AI_AGENT_API_BASE=http://127.0.0.1:8080
export AI_AGENT_MODEL='<IDENTIFICADOR_DEL_MODELO>'
python -m app.main
```

## Configuración validada en el laboratorio

| Elemento | Valor |
|---|---|
| Sistema | Ubuntu Server 24.04.4 LTS en VMware ESXi |
| CPU/RAM | 24 vCPU, 39 GiB RAM, sin GPU |
| Agente | `/home/soporte/ai-agent` |
| Runtime | `/opt/llama.cpp`, commit `85d5703` |
| Modelo | Qwen3-Coder-30B-A3B-Instruct Q4_K_M |
| Servicio | `llama-server.service`, usuario `llama` |
| API | `127.0.0.1:8080` |
| Inferencia | 24 threads, 24 batch threads, contexto 8192, un slot |

El modelo se presenta en `/var/lib/llama/models/` mediante un enlace duro al blob ya existente. Esta decisión evitó una segunda copia de aproximadamente 18 GB sin dar al servicio acceso a `/root`.

## Particularidad del runtime compilado

El ejecutable conservaba un RUNPATH absoluto hacia el árbol original. La unidad define:

```ini
Environment=LD_LIBRARY_PATH=/opt/llama.cpp/build/bin
```

`ldd` confirmó que el servidor carga las bibliotecas de `/opt/llama.cpp/build/bin`. No fue necesario recompilar ni modificar `/root/llama.cpp`.

## systemd

La copia versionada de la unidad está en `deploy/llama-server.service`. Antes de instalarla en otro equipo, ajusta rutas, alias, threads y contexto.

```bash
sudo install -o root -g root -m 0644 \
  deploy/llama-server.service \
  /etc/systemd/system/llama-server.service
sudo systemctl daemon-reload
sudo systemctl enable --now llama-server.service
```

Verificación:

```bash
systemctl status llama-server.service --no-pager
systemctl is-enabled llama-server.service
systemctl is-active llama-server.service
ss -ltnp | grep ':8080'
curl -fsS http://127.0.0.1:8080/health
curl -fsS http://127.0.0.1:8080/v1/models
```

En el laboratorio, la carga CPU-only del modelo tarda aproximadamente 1 minuto 45 segundos después del reboot. Durante ese intervalo systemd puede mostrar el proceso como activo antes de que `/health` responda `ok`; es tiempo de carga, no un fallo.

## Inicio del agente

```bash
cd /home/soporte/ai-agent
source .venv/bin/activate
python -m app.main
```

El cliente interactivo no se instala como daemon. Consulta [Arquitectura](arquitectura.md) y [Seguridad](seguridad.md) antes de adaptar el despliegue.
