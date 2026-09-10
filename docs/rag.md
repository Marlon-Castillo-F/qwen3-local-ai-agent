# RAG local con SQLite FTS5

## Diseño

El corpus vive en `knowledge/sql-server/` y contiene notas Markdown pequeñas con `title`, `topic`, `source` y fecha de consulta. `KnowledgeIndex` valida esos documentos y reconstruye un índice local en `data/knowledge.db`.

FTS5 tokeniza el título, tema y cuerpo, y ordena coincidencias con BM25. Antes de construir la expresión de búsqueda, Python normaliza acentos y expande un vocabulario pequeño y controlado de términos DBA español-inglés. `search_knowledge` devuelve ruta, título, tema, fragmento, score y URL de fuente. El archivo SQLite generado no se versiona.

## Por qué FTS5

- Está incluido en la distribución de SQLite de la VM validada.
- No requiere descargar embeddings ni varios gigabytes adicionales.
- Es determinístico, rápido y adecuado para terminología técnica distintiva.
- Permite reconstruir el índice completamente a partir del corpus versionado.

## Seguridad

- Solo se indexizan `.md` del directorio autorizado.
- Se bloquean symlinks, escapes y documentos demasiado grandes.
- Las consultas usan parámetros SQLite y `top_k` se limita a 1–10.
- Una consulta vacía se rechaza.
- Los documentos son resúmenes originales; no son dumps de documentación externa.

## Limitaciones

FTS5 recupera coincidencia léxica, no significado profundo. Una pregunta con vocabulario muy diferente puede no encontrar la nota correcta. La expansión controlada mitiga casos comprobados como `estimación` → `estimation` y `índice` → `index`, pero no constituye traducción general ni similitud semántica. Una evaluación humana sigue siendo necesaria.

## Reconstrucción y consulta

El índice se reconstruye al iniciar el agente. `/knowledge` muestra estadísticas reales y `search_knowledge` es el único camino por el que el modelo puede afirmar que consultó el corpus.
