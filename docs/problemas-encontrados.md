# Problemas encontrados

## Identidad incorrecta

Qwen se había identificado como Claude 3.5 Sonnet. El system prompt fija la identidad correcta y `/info` consulta configuración y `/v1/models`, sin confiar en una afirmación generada.

## Conversaciones largas

El contexto acumulado redujo el rendimiento. `/clear` inicia una sesión nueva y reduce el prompt enviado, mientras SQLite conserva sesiones anteriores.

## NUMA

`--numa distribute` redujo el procesamiento de prompt observado de 27,4 a 14,4 tok/s con 24 threads. La configuración final no lo usa.

## Tool calling ausente en el prototipo

El prototipo separaba las definiciones de herramientas del bucle principal. `client.py` no enviaba `tools` ni procesaba `tool_calls`, por lo que el modelo respondía texto normal. El cliente y el ciclo agentic fueron reestructurados.

## Puerto 8080 ocupado

Una instancia manual previa ejecutada como root ocupaba el puerto. Se identificó exactamente, se mantuvo durante el desarrollo y solo se terminó con SIGTERM después de validar la instancia no-root en 8081. Terminó en ocho segundos.

## RUNPATH hacia `/root`

La copia del ejecutable conservaba `/root/llama.cpp/build/bin` como RUNPATH. Se resolvió con `LD_LIBRARY_PATH` apuntando al runtime root-owned de `/opt`, sin abrir permisos de `/root`.

## Memoria durante validación paralela

Al cargar temporalmente servidores en 8080 y 8081, el swap alcanzó 5,4 GiB. La instancia duplicada se cerró inmediatamente después de las pruebas. El servicio final único usa alrededor de 13,7 GB según systemd.

## Fallos iniciales de tests

Dos pruebas fallaron porque `ChatResponse.content` era obligatorio aunque un tool call válido puede traer contenido vacío. Se hizo opcional con valor `""`; todas las pruebas posteriores pasaron.

## Respaldo

El primer comando de respaldo falló antes de crear un archivo válido porque PowerShell expandió variables destinadas al shell remoto. Se repitió con rutas absolutas y se verificó el archivo mediante SHA-256 y listado interno.
