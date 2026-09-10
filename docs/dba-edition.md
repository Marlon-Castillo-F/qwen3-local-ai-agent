# DBA Edition 1.1

DBA Edition convierte las bases de datos —especialmente SQL Server— en el dominio principal del agente sin modificar los pesos de Qwen. El modelo continúa siendo **Qwen3-Coder-30B-A3B-Instruct Q4_K_M** servido por llama.cpp.

## Qué implementa la especialización

- Un system prompt versionado que exige diagnóstico basado en evidencia y evita absolutos sobre scans, seeks, lookups, joins e índices.
- Un corpus pequeño de notas originales basadas principalmente en Microsoft Learn.
- Retrieval local mediante SQLite FTS5 y la herramienta `search_knowledge`.
- Normalización de acentos y equivalencias DBA controladas en español e inglés para consultas léxicas comprobadas.
- Herramientas offline para `STATISTICS IO`, `STATISTICS TIME`, execution plans y deadlock XML.
- Una evaluación repetible de 23 escenarios antes y después de la especialización.

## Qué no implementa

- Fine-tuning, LoRA, QLoRA o cambios en el GGUF.
- Otro LLM o un modelo de embeddings.
- Conexiones a SQL Server, ejecución T-SQL o almacenamiento de credenciales.
- Acceso a bases corporativas o datos internos.

## Principio operativo

El modelo propone una herramienta. `ToolRegistry` valida nombre y argumentos. Python consulta el corpus o procesa un archivo seguro, y devuelve hechos estructurados. Solo entonces el modelo formula una interpretación. No se acepta como evidencia una afirmación textual de haber consultado o analizado algo.

Los analizadores de `.sqlplan`, `.xml` y `.xdl` solo se ofrecen al modelo cuando el usuario menciona explícitamente una extensión compatible. Este gate determinista se añadió después de observar rutas inventadas en preguntas conceptuales.

## Uso

```bash
python -m app.main
```

`/dba` muestra el perfil activo y `/knowledge` obtiene directamente de Python la cantidad de documentos y categorías indexadas.

Consulta [RAG](rag.md), [Herramientas DBA](dba-tools.md), [Evaluación](dba-evaluation.md) y [Seguridad](seguridad.md).
