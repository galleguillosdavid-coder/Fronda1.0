"""
Esquema de Base de Datos para el Grafo de Conocimiento de Código (Kùzu).
Modela Nodos sintácticos (Module, Class, Function) y Relaciones topológicas
(CALLS, IMPORTS, DEFINES_FUNC, DEFINES_CLASS, CONTAINS_METHOD, INHERITS).
"""

SCHEMA_DDL = [
    """
    CREATE NODE TABLE IF NOT EXISTS Module (
        path STRING,
        name STRING,
        PRIMARY KEY (path)
    );
    """,
    """
    CREATE NODE TABLE IF NOT EXISTS Class (
        id STRING,
        name STRING,
        file_path STRING,
        line_start INT64,
        line_end INT64,
        docstring STRING,
        PRIMARY KEY (id)
    );
    """,
    """
    CREATE NODE TABLE IF NOT EXISTS Function (
        id STRING,
        name STRING,
        file_path STRING,
        line_start INT64,
        line_end INT64,
        docstring STRING,
        signature STRING,
        PRIMARY KEY (id)
    );
    """,
    """
    CREATE REL TABLE IF NOT EXISTS IMPORTS (
        FROM Module TO Module
    );
    """,
    """
    CREATE REL TABLE IF NOT EXISTS DEFINES_FUNC (
        FROM Module TO Function
    );
    """,
    """
    CREATE REL TABLE IF NOT EXISTS DEFINES_CLASS (
        FROM Module TO Class
    );
    """,
    """
    CREATE REL TABLE IF NOT EXISTS CONTAINS_METHOD (
        FROM Class TO Function
    );
    """,
    """
    CREATE REL TABLE IF NOT EXISTS INHERITS (
        FROM Class TO Class
    );
    """,
    """
    CREATE REL TABLE IF NOT EXISTS CALLS (
        FROM Function TO Function
    );
    """
]


def initialize_schema(conn) -> None:
    """Ejecuta los DDL para asegurar que todas las tablas existan en Kùzu."""
    for ddl in SCHEMA_DDL:
        clean_ddl = ddl.strip()
        if clean_ddl:
            conn.execute(clean_ddl)
