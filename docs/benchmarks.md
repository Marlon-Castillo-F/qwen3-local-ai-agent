# Benchmarks

Resultados observados antes de esta fase:

| Configuración | Prompt | Generación |
|---|---:|---:|
| 12 threads | 21,5 tok/s | 10,1 tok/s |
| 18 threads | 23,7 tok/s | 10,3 tok/s |
| 24 threads | 27,4 tok/s | 10,2 tok/s |
| 24 threads + NUMA distribute | 14,4 tok/s | 10,4 tok/s |

Decisión: 24 threads y 24 batch threads, sin `--numa distribute`, porque maximiza el procesamiento de contexto sin perjudicar materialmente la generación.

Durante la validación manual posterior, llama-server informó valores puntuales entre aproximadamente 30 y 62 tok/s de prompt y entre 9,4 y 11,1 tok/s de generación. No son un benchmark controlado: hubo caché de prompt y cargas distintas, por lo que no sustituyen la tabla anterior.

El arranque del servicio final tardó aproximadamente 67 segundos en cargar el modelo; el sondeo de salud iniciado después lo encontró listo tras 14 segundos.
