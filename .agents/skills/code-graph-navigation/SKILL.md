---
name: code-graph-navigation
description: Directiva obligatoria para navegar el proyecto mediante el grafo de conocimiento vectorial de código (Kùzu + MCP) antes de modificar archivos o refactorizar.
---

# Navegación Quirúrgica con Grafo de Código Vectorial

Esta habilidad instruye a los subagentes de Antigravity a utilizar el servidor MCP `codegraph-memory` para consultar la topología de software sin consumir tokens leyendo archivos completos de forma recursiva.

---

## Cuándo Utilizar las Herramientas del Grafo

1. **Antes de editar cualquier función o clase compartida**:
   - Ejecuta `codegraph_calculate_blast_radius` con el nombre de la función o módulo objetivo.
   - Si `risk_level` es `HIGH` o `CRITICAL`, revisa la lista de llamadores (`direct_and_indirect_callers`) para planificar modificaciones compatibles o actualizar los llamadores.

2. **Para entender la firma y contexto sin abrir el archivo entero**:
   - Ejecuta `codegraph_get_subgraph` con el nombre del símbolo.
   - Recibirás la firma exacta, líneas de inicio/fin, docstrings y los nodos salientes (`outgoing_calls`).

3. **Para descubrir componentes por propósito o funcionalidad**:
   - Ejecuta `codegraph_query` pasando una consulta en lenguaje natural (ejemplo: `"servidor websocket de voz"` o `"registro de habilidades"`).

4. **Al crear o renombrar módulos**:
   - Ejecuta `codegraph_reindex` para actualizar la base de grafos Kùzu inmediatamente.

---

## Partición de Tareas en Subagentes Paralelos

Cuando el orquestador principal de Antigravity divida un megaproyecto entre subagentes:
- Cada subagente debe recibir exclusivamente un subgrafo desacoplado.
- Los subagentes no deben editar archivos fuera de su componente asignado a menos que el grafo demuestre una arista directa.
