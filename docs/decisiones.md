# Decisiones técnicas

## Tool calling nativo

Se conservó el protocolo OpenAI nativo porque fue comprobado con una respuesta estructurada real. Un parser de JSON o XML generado como texto sería menos fiable y no aporta valor en esta versión.

## Registro de herramientas

Las herramientas se registran como objetos `ToolSpec`; el nombre nunca se transforma en una función o comando arbitrario. La validación ocurre antes de ejecutar cualquier handler.

## Memoria

SQLite proporciona persistencia sencilla sin introducir RAG ni servicios externos. `/clear` comienza un nuevo `session_id`; no borra sesiones antiguas de la base.

## Runtime sin root

Se eligió un usuario dedicado `llama` en vez de `soporte` para separar inferencia y agente. El runtime se copió a `/opt` y permanece propiedad de root.

El binario tenía RUNPATH absoluto hacia `/root`. Se prefirió `LD_LIBRARY_PATH` restringido a `/opt/llama.cpp/build/bin` en la unidad, después de validar con `ldd`, en vez de recompilar o alterar binarios.

## Reutilización del modelo

Como origen y destino pertenecen al mismo filesystem, se creó un enlace duro. Así el servicio no atraviesa `/root`, no se descargó otra copia y no se consumieron otros 18 GB.

## Systemd

El agente interactivo no es un daemon. Solo llama-server arranca con Ubuntu y usa `Restart=on-failure`, no reinicio incondicional.
