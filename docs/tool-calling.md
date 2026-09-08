# Tool calling

## Qué significa en este proyecto

Tool calling no significa que el modelo tenga acceso directo a Linux. Qwen genera una solicitud estructurada con el nombre de una herramienta y argumentos; Python conserva la autoridad para aceptarla, rechazarla y ejecutarla.

```text
Usuario
  → mensajes + esquemas de herramientas
Qwen
  → tool_call estructurado
Python
  → valida nombre y argumentos
Handler permitido
  → produce un resultado real
Qwen
  → recibe role=tool y redacta la respuesta final
```

## Problema del prototipo

El prototipo declaraba herramientas en `app/agent.py`, pero el bucle interactivo estaba en `app/client.py`. Ese cliente no añadía `tools` al payload, no inspeccionaba `message.tool_calls` y no enviaba `role=tool` en una segunda petición. El modelo, por tanto, respondía en lenguaje natural que no tenía acceso al filesystem.

Una petición directa a `/v1/chat/completions` demostró que Qwen y la compilación instalada sí eran compatibles: HTTP 200, `finish_reason=tool_calls` y `function.name=list_files`.

## Implementación

1. `LlamaClient.chat` envía `messages`, esquemas, `tool_choice=auto` y `parallel_tool_calls=false`.
2. Solo el campo estructurado `tool_calls` se considera una solicitud; no se analizan imitaciones en texto.
3. `ToolRegistry` comprueba que el nombre exista y valida el objeto JSON contra el esquema permitido.
4. El handler registrado ejecuta la operación y devuelve texto acotado.
5. `Agent` añade un mensaje `role=tool` con el `tool_call_id` original.
6. Qwen recibe el resultado y genera la respuesta para el usuario.
7. El ciclo tiene un máximo configurado de rondas para evitar bucles indefinidos.

Si una herramienta o argumento se bloquea, el error de seguridad vuelve al modelo como resultado; Qwen no puede anular la decisión de Python.

## Plantilla y servidor

La compilación `85d5703` incluye `Qwen3-Coder.jinja` y declara soporte para tools, tool calls y argumentos como objetos. El servicio usa explícitamente:

```text
--jinja
--chat-template-file /opt/llama.cpp/models/templates/Qwen3-Coder.jinja
```

No fue necesario crear un protocolo JSON alternativo ni simular resultados.

## Ejemplo validado

```text
Tú> qué archivos tienes disponibles en tu workspace
[tool] list_files
[tool result]
[DIR] proyecto-demo
[FILE] prueba.txt
IA> ... proyecto-demo ... prueba.txt ...
```

La prueba end-to-end también verificó `read_file`: el modelo solicitó la herramienta, Python leyó el archivo y Qwen utilizó el contenido real en la respuesta.

Consulta [Arquitectura](arquitectura.md), [Seguridad](seguridad.md) y [Pruebas](pruebas.md).
