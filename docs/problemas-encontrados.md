# Problemas encontrados y aprendizajes

## Identidad incorrecta del modelo

Qwen llegó a identificarse como Claude 3.5 Sonnet. Una respuesta generativa no es una fuente confiable de identidad.

**Solución:** system prompt explícito y `/info` construido con configuración local y la respuesta real de `/v1/models`.

## Tool calling aparentemente ausente

El modelo respondía que no podía acceder al filesystem. La causa no era incompatibilidad: el cliente prototipo no enviaba `tools`, no procesaba `tool_calls` y no devolvía `role=tool`.

**Diagnóstico:** una petición directa a `/v1/chat/completions` produjo un tool call válido.

**Solución:** implementar el ciclo completo y mantener la validación en Python.

## Puerto 8080 ocupado

Un intento de iniciar otra instancia falló porque el puerto ya pertenecía a un servidor manual. Se identificaron PID, usuario, comando y socket antes de detener nada.

**Aprendizaje:** diagnosticar ownership y procedencia del proceso evita terminar servicios equivocados.

## Runtime dentro de `/root`

El binario y sus bibliotecas dependían de una ruta que un usuario de servicio no podía atravesar. Además, el ejecutable conservaba esa ruta en RUNPATH.

**Solución:** runtime root-owned en `/opt`, bibliotecas seleccionadas mediante `LD_LIBRARY_PATH` acotado y modelo presentado bajo `/var/lib/llama`.

## NUMA distribute redujo el prompt

Con 24 threads, `--numa distribute` bajó el procesamiento aproximado de 27,4 a 14,4 tok/s, mientras la generación permaneció cerca de 10 tok/s.

**Solución:** 24 threads sin NUMA distribute.

## Conversaciones largas

El crecimiento del contexto aumentó el coste de procesamiento de prompt.

**Solución:** `/clear` inicia una sesión limpia; SQLite conserva el historial sin reenviarlo completo al modelo.

## Respuestas de herramienta sin contenido textual

Dos tests iniciales fallaron porque el tipo interno exigía `content`, aunque una respuesta válida con `finish_reason=tool_calls` puede traer una cadena vacía.

**Solución:** aceptar `content=""` y conservar los tool calls como señal principal.

## Tiempo de arranque

Después del reboot, la instancia CPU-only tarda aproximadamente 1 minuto 45 segundos en cargar el GGUF. systemd inicia el proceso correctamente antes de que `/health` esté listo.

**Aprendizaje:** distinguir proceso activo de aplicación saludable y usar health checks con espera acorde al tamaño del modelo.

## Validación con dos instancias

Durante la migración se utilizó temporalmente otro puerto para validar el runtime no-root sin interrumpir el servidor original. La carga simultánea elevó el uso de memoria y swap.

**Solución:** ejecutar solo las pruebas necesarias, cerrar la instancia temporal y mantener una única instancia final.

Consulta [Decisiones técnicas](decisiones.md) y [Pruebas](pruebas.md).
