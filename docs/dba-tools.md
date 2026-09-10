# Herramientas DBA offline

Todas las herramientas trabajan con texto proporcionado o archivos UTF-8 dentro de `workspace/`. No existe conexión a SQL Server.

## `analyze_statistics_io`

Acepta `text` o `relative_path`, nunca ambos. Extrae por tabla los campos presentes: `scan_count`, `logical_reads`, `physical_reads` y `read_ahead_reads`. Si un campo no aparece, no lo inventa.

## `analyze_statistics_time`

Extrae muestras de `cpu_time_ms` y `elapsed_time_ms`. Reporta valores; no concluye automáticamente que exista un problema.

## `analyze_execution_plan`

Acepta `.sqlplan` XML. Extrae operadores físicos y lógicos, filas estimadas, filas reales cuando existen, costo estimado, warnings, spills, sugerencias de missing index y categorías de scans, seeks, lookups y joins. La salida está marcada como hechos y recuerda que los operadores requieren contexto.

## `analyze_deadlock_xml`

Acepta `.xml` o `.xdl`. Extrae víctima, procesos, statements disponibles, database ID, recursos, propietarios, waiters y lock modes.

## Controles comunes

- Workspace only y rutas relativas.
- Path traversal y symlink escape bloqueados.
- Límite de tamaño y rechazo de binarios.
- Extensiones permitidas explícitamente para XML.
- DTD y entidades XML bloqueadas.
- Argumentos validados por `ToolRegistry`.

Los archivos en `workspace/dba-samples/` son sintéticos y sirven para demostración; no contienen datos de producción.
