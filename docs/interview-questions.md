# Preguntas de entrevista

Estas respuestas se basan únicamente en decisiones y resultados verificados en el proyecto.

## 1. ¿Qué problema resuelve el proyecto?

Convierte un modelo local orientado a código en un agente capaz de trabajar con información real de un workspace sin darle acceso libre al sistema. El modelo puede solicitar operaciones, pero Python conserva la autoridad y aplica controles antes de ejecutarlas.

## 2. ¿Por qué llama.cpp y no Ollama?

No realicé un benchmark comparativo contra Ollama. Elegí continuar con llama.cpp porque ya estaba compilado y validado, ofrecía una API compatible con OpenAI, soportaba la plantilla de Qwen3-Coder y permitía controlar directamente threads, contexto, slots, bind y tool calling. Añadir otra capa no resolvía un problema del MVP.

## 3. ¿Por qué Qwen3-Coder?

Por su orientación a programación y tareas técnicas. El objetivo era un agente para archivos, Git y pruebas, así que un modelo especializado en código encajaba mejor que uno puramente conversacional. Yo integré el modelo; no lo entrené.

## 4. ¿Qué significa Q4_K_M?

Es una cuantización GGUF de aproximadamente 4 bits con una estrategia mixta. Reduce el tamaño y la memoria necesarios respecto a pesos de mayor precisión. En este laboratorio permitió ejecutar el modelo de 30B en una VM con 39 GiB de RAM y sin GPU. No hice una comparación de calidad contra otras cuantizaciones.

## 5. ¿Qué es tool calling?

Es un protocolo en el que el modelo devuelve una estructura con el nombre de una función y argumentos. No ejecuta la función. El agente recibe esa estructura, la valida, ejecuta código permitido y devuelve el resultado al modelo para que responda con información real.

## 6. ¿Cómo sabes que no fue una llamada simulada?

Las pruebas inspeccionan `message.tool_calls` y `finish_reason=tool_calls`; no analizan texto que parezca una llamada. También capturan el evento ejecutado, el resultado del handler y verifican que la respuesta final incluya datos que existían realmente en el workspace.

## 7. ¿Cómo evitas que el modelo ejecute cualquier comando?

Existe un registro explícito de herramientas. Un nombre desconocido se rechaza. Cada herramienta tiene un esquema de argumentos y un handler fijo. No hay `eval`, resolución dinámica de funciones ni shell libre. `run_tests` solo admite dos comandos de pytest definidos en código.

## 8. ¿Por qué no usas `shell=True`?

Con `shell=True`, texto controlado por el modelo podría interpretarse como operadores, redirecciones o sustituciones del shell. El proyecto pasa listas de argumentos directamente a `subprocess.run`, limita las opciones y aplica timeout.

## 9. ¿Qué es path traversal y cómo lo bloqueaste?

Es intentar escapar del directorio permitido mediante rutas como `../../etc/passwd`. La implementación exige rutas relativas, resuelve el destino y comprueba que permanezca bajo el workspace. También rechaza componentes symlink para evitar que un enlace aparentemente interno apunte fuera.

## 10. ¿Por qué la API escucha solo en localhost?

El único consumidor es el agente en la misma VM. Exponer llama-server a la red aumentaría la superficie de ataque sin aportar valor al caso de uso. El servicio usa `127.0.0.1:8080` y CORS limitado a localhost.

## 11. ¿Por qué llama-server no se ejecuta como root?

El proceso solo necesita leer el modelo, cargar bibliotecas y abrir un puerto no privilegiado. Un usuario dedicado sin shell reduce el impacto si el servidor o una plantilla fallan. Además, systemd restringe capacidades, filesystem, dispositivos y acceso a hogares.

## 12. ¿Por qué systemd?

Proporciona arranque automático, supervisión, logs mediante journal, límites y reinicio controlado. El agente interactivo no necesita ser daemon; solo el servidor de inferencia permanece activo.

## 13. ¿Cómo verificaste el arranque automático?

Después de habilitar la unidad reinicié Ubuntu de forma controlada, volví a conectar usando el acceso normal y comprobé `enabled`, `active`, el socket, `/health`, `/v1/models`, usuario del proceso y cantidad de instancias. Luego repetí tool calling y las 32 pruebas.

## 14. ¿Por qué 24 threads?

Fue una decisión empírica. El prompt alcanzó aproximadamente 21,5 tok/s con 12 threads, 23,7 con 18 y 27,4 con 24. La generación se mantuvo alrededor de 10 tok/s, por lo que 24 ofreció el mejor equilibrio para un agente que reprocesa contexto.

## 15. ¿Qué ocurrió con NUMA distribute?

Con 24 threads redujo el prompt de aproximadamente 27,4 a 14,4 tok/s y apenas cambió la generación. En esta VM concreta fue contraproducente, así que se eliminó de la configuración final.

## 16. ¿Qué pasa si Qwen alucina una herramienta o un resultado?

Si inventa un nombre o argumentos inválidos, `ToolRegistry` los bloquea. Si afirma en texto haber realizado una acción sin un tool call, Python no la ejecuta y las pruebas no la aceptarían como válida. La respuesta final aún puede contener errores generativos, por eso el proyecto no se presenta como sistema infalible.

## 17. ¿Cómo funciona la memoria?

Cada sesión tiene un `session_id` y sus mensajes se almacenan en SQLite. `/history` consulta la sesión actual. `/clear` empieza otra sesión y reduce el contexto enviado al modelo, pero no borra los registros previos. No hay embeddings, búsqueda semántica ni RAG.

## 18. ¿Qué registran los logs?

Inicio y fin de sesión, peticiones y duración del modelo, herramientas solicitadas, aceptadas o bloqueadas, tamaños de resultados y errores. No se guardan prompts ni resultados completos de archivos. Los logs rotan para limitar crecimiento.

## 19. ¿Cuál fue el bug más importante?

El cliente prototipo no enviaba `tools` ni procesaba `tool_calls`, aunque Qwen y llama.cpp sí eran compatibles. Una petición directa aisló el problema. La solución fue implementar el protocolo completo, no crear una simulación basada en texto.

## 20. ¿Qué limitaciones reconoces?

La inferencia CPU-only es relativamente lenta y el arranque tarda cerca de 1 minuto 45 segundos. La censura de secretos es heurística. El modelo puede equivocarse y la API no está preparada para exposición pública multiusuario.

## 21. ¿Qué mejorarías en una fase 2?

Evaluaría RAG sobre documentos, memoria más útil, observabilidad, evaluaciones automáticas, workspaces multiproyecto, una interfaz web autenticada y herramientas adicionales con políticas específicas. Ninguna de esas funciones está implementada en la fase actual.
