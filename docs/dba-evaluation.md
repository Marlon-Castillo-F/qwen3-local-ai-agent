# Evaluación DBA

## Objetivo y método

La evaluación compara el agente general de la versión 1.0 con DBA Edition usando exactamente el mismo archivo de 23 escenarios: `evals/dba_questions.json`. Las preguntas cubren backup y restore, índices, planes, joins, cardinalidad, Query Store, bloqueo, deadlocks, estadísticas, tempdb, seguridad, transacciones y alta disponibilidad.

Cada ejecución conserva la pregunta, la respuesta real de Qwen, la duración, las herramientas solicitadas, sus resultados y cualquier error. El runner usa un workspace, memoria, logs e índice de conocimiento temporales para evitar que una respuesta modifique el proyecto o contamine el caso siguiente.

La puntuación determinista comprueba grupos de conceptos esperados y patrones de afirmaciones absolutas prohibidas. Es una señal reproducible, no una medida completa de exactitud: redacción, causalidad, recomendaciones y matices técnicos requieren revisión humana.

## Resultados verificados

Las dos corridas usaron `Qwen3-Coder-30B-A3B-Instruct Q4_K_M`, llama.cpp y las mismas 23 preguntas. El baseline tardó 2098,453 segundos; la corrida final, etiquetada `dba-edition-final-3f08a55`, tardó 2560,993 segundos.

| Métrica | Baseline | DBA Edition | Diferencia |
|---|---:|---:|---:|
| Preguntas completadas | 23/23 | 23/23 | 0 |
| Errores de ejecución | 0 | 0 | 0 |
| Pases deterministas | 9 | 14 | +5 |
| Grupos conceptuales encontrados | 83/111 | 102/111 | +19 |
| Coincidencias de afirmaciones prohibidas | 1 | 0 | -1 |

El baseline solicitó `git_status` una vez, `list_files` cinco, `read_file` tres, `run_tests` dos y `write_file` seis. DBA Edition solicitó `search_knowledge` cinco veces, `analyze_statistics_io` una, `analyze_statistics_time` una y `list_files` una. No solicitó `analyze_execution_plan` ni `analyze_deadlock_xml` porque ninguna pregunta proporcionaba una ruta compatible.

Hubo siete cambios de `needs_review` a `pass`: `clustered-nonclustered`, `estimated-vs-actual-plan`, `slow-query-workflow`, `statistics-io`, `blocking`, `transaction-log-chain` y `spill-warning`. Dos casos cambiaron de `pass` a `needs_review`: `fragmentation` y `seek-with-lookups`. El resultado neto es +5, pero esas regresiones impiden interpretar el total como mejora uniforme.

## Ejemplos antes y después

### `clustered-nonclustered`

El baseline llamó `list_files` y `write_file`, creó un documento no solicitado y respondió principalmente que lo había creado. DBA Edition llamó `search_knowledge`, explicó qué contienen los niveles hoja y obtuvo un pase determinista. La respuesta final todavía usa una formulación demasiado fuerte sobre organización física; requiere matizar que el orden de resultados solo se garantiza mediante `ORDER BY`.

### `estimated-vs-actual-plan`

El baseline usó `write_file` sin necesidad. DBA Edition consultó el corpus y distinguió que el Estimated Plan no ejecuta la consulta ni aporta Actual Rows, mientras el Actual Plan añade contadores de runtime. También explicó correctamente que `SET SHOWPLAN_XML` devuelve un plan estimado.

### Selección de herramientas en `key-lookup` y `spill-warning`

Una corrida anterior de DBA Edition inventó rutas para `analyze_execution_plan`; Python las rechazó. Después del gate por extensión, la corrida definitiva registró `tool_calls=[]` en `key-lookup` y solo `tool_calls=["search_knowledge"]` en `spill-warning`. No hubo intento de abrir un `.sqlplan` inexistente.

### Hallazgos que el pase determinista no detectó

- En `statistics-io`, Qwen afirmó incorrectamente que `scan_count=1` demuestra un Scan. Esa métrica no identifica por sí sola el operador del plan.
- En `spill-warning`, Qwen recomendó revisar un plan real con `SET SHOWPLAN_XML`; ese comando no ejecuta la consulta y no sustituye un Actual Execution Plan.
- `key-lookup` quedó en `needs_review` con 3/4 grupos porque el matcher no encontró la variante exacta esperada de selectividad/pocas filas, aunque la respuesta sí discutió volumen bajo. Es un posible falso negativo textual.

Estos ejemplos demuestran que la mejora automatizada es real en cobertura y selección de herramientas, pero no equivale a exactitud DBA completa.

## Interpretación y límites

- Una coincidencia textual no demuestra por sí sola que toda la explicación sea correcta.
- La ausencia de un patrón prohibido tampoco descarta otras alucinaciones.
- Las llamadas de herramienta permiten comprobar si hubo retrieval o análisis real, pero no garantizan que la interpretación posterior de Qwen sea acertada.
- El muestreo es pequeño y el modelo generativo puede producir variación entre ejecuciones.
- DBA Edition sigue necesitando revisión profesional antes de aplicar recomendaciones en producción.

Los artefactos reproducibles están en `evals/results/baseline-dba.json`, `evals/results/dba-edition.json` y `evals/results/comparison.json`.
