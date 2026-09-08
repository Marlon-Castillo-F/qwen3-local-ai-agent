# Tool calling

## Diagnóstico

El prototipo definía `TOOLS` en `app/agent.py`, pero el bucle interactivo vivía en `app/client.py` y nunca:

- añadía `tools` al payload;
- inspeccionaba `message.tool_calls`;
- validaba o ejecutaba la herramienta;
- devolvía un mensaje `role=tool` al modelo.

Por ello Qwen respondía en lenguaje natural que no tenía acceso al filesystem.

## Compatibilidad comprobada

La compilación local `85d5703` contiene `models/templates/Qwen3-Coder.jinja`. `/props` declara soporte para tools, tool calls y argumentos como objetos. Una petición diagnóstica real produjo HTTP 200, `finish_reason=tool_calls` y `function.name=list_files`.

No fue necesario implementar un protocolo JSON alternativo ni interpretar texto como si fuera una llamada.

## Ciclo implementado

1. `LlamaClient.chat` envía mensajes, esquemas, `tool_choice=auto` y `parallel_tool_calls=false`.
2. Solo `tool_calls` estructurados se consideran solicitudes.
3. `ToolRegistry` valida nombre y argumentos.
4. Se ejecuta el handler registrado.
5. El resultado se añade con `role=tool`, `tool_call_id` y nombre.
6. Se llama otra vez a Qwen para obtener la respuesta final.
7. El ciclo se limita a ocho rondas configuradas.

Los eventos visibles `[tool]` y `[tool result]` proceden de esa ejecución real.

## Plantilla final

El servicio usa explícitamente:

```text
--jinja
--chat-template-file /opt/llama.cpp/models/templates/Qwen3-Coder.jinja
```

Aunque `--jinja` está habilitado por defecto en esta compilación, se conserva explícito para hacer reproducible la configuración.
