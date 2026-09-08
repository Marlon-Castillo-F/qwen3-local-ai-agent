# Resumen para portafolio

## Una línea para CV

Implementé y aseguré un agente de IA completamente local con Qwen3-Coder, llama.cpp y Python, incorporando tool calling real, memoria SQLite, systemd y 32 pruebas automatizadas en una VM CPU-only.

## CV o LinkedIn

- Integré Qwen3-Coder 30B Q4_K_M con llama.cpp y un agente Python mediante una API compatible con OpenAI, sin depender de inferencia cloud durante la operación.
- Implementé un ciclo real de tool calling en el que Python valida nombres y argumentos, ejecuta handlers permitidos y devuelve los resultados al modelo.
- Aseguré operaciones de archivos, Git y pytest mediante workspace restringido, protección contra path traversal y symlinks, allowlists y timeouts.
- Configuré llama-server como servicio systemd no-root, limitado a localhost y endurecido con privilegios y filesystem restringidos.
- Optimicé la inferencia CPU-only mediante benchmarks de threads y validé el sistema con 32 pruebas, incluidas dos pruebas end-to-end contra el modelo real.

## Explicación técnica para entrevista

Desarrollé la integración de un agente de IA local sobre una VM Ubuntu Server CPU-only. Partí de un prototipo incompleto que podía conversar con Qwen3-Coder mediante llama.cpp, pero que no enviaba las definiciones de herramientas ni procesaba tool calls. Verifiqué primero que el servidor y la plantilla del modelo sí soportaban el protocolo nativo y luego implementé el ciclo completo: el modelo solicita una herramienta, Python valida el nombre y los argumentos, ejecuta un handler registrado, devuelve el resultado como mensaje `role=tool` y Qwen genera la respuesta final.

La seguridad fue parte central del diseño. Las herramientas de archivos están limitadas a un workspace, bloquean path traversal y symlinks, rechazan binarios y aplican límites de tamaño. Git es solo lectura y pytest se ejecuta mediante una allowlist, sin `shell=True` y con timeout. Añadí memoria SQLite, logging rotativo y censura heurística de secretos.

También migré llama-server desde una ejecución manual como root a un servicio systemd con usuario dedicado, bind exclusivo en localhost y controles de endurecimiento. Evalué 12, 18 y 24 threads; 24 sin NUMA distribute obtuvo el mejor procesamiento de prompt. Finalmente validé el arranque automático tras reboot y una suite de 32 pruebas, incluidas llamadas reales a `list_files` y `read_file`.

Este proyecto integra tecnologías existentes; no entrené Qwen ni desarrollé llama.cpp.
