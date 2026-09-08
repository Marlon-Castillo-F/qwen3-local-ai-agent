# Benchmarks

Estas mediciones corresponden exclusivamente a la VM CPU-only del laboratorio. No son resultados públicos del modelo ni pretenden generalizar a otros procesadores, cuantizaciones o tamaños de contexto.

## Entorno

- VMware ESXi.
- 24 vCPU expuestas como Intel Xeon E5-2699 v4.
- 39 GiB de RAM y 8 GiB de swap.
- Sin GPU de cómputo.
- Qwen3-Coder-30B-A3B-Instruct GGUF Q4_K_M.
- llama.cpp compilado con optimizaciones nativas.

## Resultados observados

| Configuración | Procesamiento de prompt | Generación |
|---|---:|---:|
| 12 threads | ≈ 21,5 tok/s | ≈ 10,1 tok/s |
| 18 threads | ≈ 23,7 tok/s | ≈ 10,3 tok/s |
| 24 threads | **≈ 27,4 tok/s** | ≈ 10,2 tok/s |
| 24 threads + NUMA distribute | ≈ 14,4 tok/s | ≈ 10,4 tok/s |

## Decisión

La configuración final utiliza 24 threads para generación y 24 para procesamiento batch, sin `--numa distribute`, con contexto 8192 y un slot.

El aumento de 12 a 24 threads mejoró el prompt aproximadamente un 27 %, mientras la generación permaneció alrededor de 10 tok/s. `--numa distribute` conservó la generación, pero redujo el prompt casi a la mitad frente a 24 threads sin NUMA; por eso se descartó para un agente que procesa contexto y resultados de herramientas repetidamente.

## Contexto conversacional

También se observó que conversaciones largas aumentan el trabajo de prompt. `/clear` inicia una sesión nueva y reduce el contexto enviado; la persistencia SQLite conserva el registro sin obligar al modelo a reprocesarlo completo.

Durante pruebas funcionales aparecieron velocidades puntuales distintas por caché de prompt y tamaños de entrada variables. No se publican como benchmarks porque no se obtuvieron bajo una metodología comparable.

Consulta [Decisiones técnicas](decisiones.md) para el razonamiento operativo.
