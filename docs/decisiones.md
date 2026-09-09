# Decisiones técnicas

## llama.cpp en vez de una capa adicional

El servidor ya estaba compilado, ofrecía una API compatible con OpenAI, exponía la plantilla del modelo y devolvía tool calls estructurados. Usarlo directamente redujo componentes y permitió controlar threads, contexto, bind y plantilla. No se realizó una comparación experimental contra Ollama; la decisión se basa en control y en el estado técnico existente.

## Qwen3-Coder Q4_K_M

Qwen3-Coder se eligió por su orientación a tareas de programación. Q4_K_M permitió ejecutar el modelo de 30B en los recursos CPU/RAM disponibles con una calidad y tamaño operables. El proyecto integra el modelo; no lo entrena ni modifica.

## Tool calling nativo

Se mantuvo el protocolo nativo porque una petición real demostró compatibilidad. Analizar JSON o XML emitido como texto habría añadido ambigüedad y riesgo de aceptar una simulación.

## Autoridad en Python

El modelo propone; Python decide. Un registro explícito evita resolver nombres dinámicamente y los esquemas limitan argumentos. Las operaciones de archivos, Git y tests tienen controles específicos en vez de compartir una función genérica de shell.

## Memoria SQLite

SQLite aporta persistencia local, transacciones y consultas sencillas sin desplegar otro servicio. `/clear` crea un nuevo `session_id`: reduce el contexto de inferencia sin borrar el historial guardado.

## Especialización sin entrenamiento

DBA Edition conserva exactamente Qwen3-Coder-30B-A3B-Instruct Q4_K_M. No se aplicó fine-tuning, LoRA ni QLoRA. La especialización se logra con un system prompt auditable, retrieval local, herramientas determinísticas y una evaluación antes/después. Esto reduce costo y evita exagerar el alcance del proyecto.

## SQLite FTS5 en vez de embeddings

La terminología de SQL Server contiene tokens distintivos como `STATISTICS IO`, `Key Lookup`, `Query Store` y `tempdb`. FTS5 ofrece BM25, instalación cero adicional y un índice pequeño y reproducible. La contrapartida es que la búsqueda es léxica y puede perder equivalencias semánticas; el corpus incluye sinónimos en español e inglés para mitigarlo.

## Herramientas DBA offline

La primera versión no incorpora drivers ni credenciales de base de datos. Analizar archivos del workspace mantiene una frontera clara: Python extrae hechos y Qwen interpreta. Una futura conexión de solo lectura requeriría un diseño de autorización, auditoría y manejo de secretos separado.

## Usuario dedicado para inferencia

Se eligió `llama` en vez de root o el usuario del agente para separar responsabilidades. El usuario carece de shell, capacidades y acceso de escritura al runtime o al modelo.

## Runtime fuera de `/root`

El runtime se copió a `/opt/llama.cpp` y quedó propiedad de root. Como el binario conservaba un RUNPATH absoluto hacia el árbol original, la unidad define un `LD_LIBRARY_PATH` acotado a `/opt`; `ldd` confirmó las bibliotecas cargadas. Esto evitó recompilar o abrir `/root`.

## Reutilización del GGUF

Origen y destino estaban en el mismo filesystem, por lo que un enlace duro presentó el modelo en `/var/lib/llama/models/` sin duplicar aproximadamente 18 GB. El servicio no necesita recorrer el directorio privado del administrador.

## 24 threads sin NUMA distribute

24 threads obtuvieron el mejor procesamiento de prompt medido. `--numa distribute` redujo ese valor casi a la mitad sin mejorar de forma relevante la generación, así que se descartó.

## systemd solo para el servidor

La inferencia necesita arrancar con Ubuntu y recuperarse de fallos; el cliente sigue siendo interactivo. La unidad usa `Restart=on-failure`, bind en localhost y endurecimiento de filesystem, capacidades y dispositivos.

Consulta [Benchmarks](benchmarks.md), [Seguridad](seguridad.md) y [Problemas encontrados](problemas-encontrados.md).
