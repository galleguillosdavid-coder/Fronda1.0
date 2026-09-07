# Regla: Arquitectura Topológica de Código (Graph-First)

1. **Consulta de Impacto Obligatoria**: Antes de realizar modificaciones estructurales o renombrar funciones en módulos troncales (`core/`, `fronda_memory.py`, `fronda_bridge.py`, etc.), se debe consultar el radio de impacto (`codegraph_calculate_blast_radius`).
2. **Uso Eficiente de Tokens**: No inspeccionar directorios enteros con lecturas recursivas de archivos. Utilizar `codegraph_get_subgraph` para obtener firmas y dependencias directas.
3. **Mantenimiento del Grafo**: Tras agregar nuevos módulos o dependencias cruzadas significativas, ejecutar `codegraph_reindex` para mantener el grafo Kùzu sincronizado.
