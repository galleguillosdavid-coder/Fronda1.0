"""
Fronda 1.0 - skills package
Exporta los motores de habilidades: matemático y de sistema.
"""
from skills.math_engine import evaluate_math_expression, SAFE_MATH_OPERATORS
from skills.system_engine import (
    get_system_telemetry,
    get_os_info,
    detect_hardware_specs,
)

from skills.research_engine import (
    search_duckduckgo,
    search_wikipedia,
    search_github,
    synthesize_research,
)

__all__ = [
    "evaluate_math_expression",
    "SAFE_MATH_OPERATORS",
    "get_system_telemetry",
    "get_os_info",
    "detect_hardware_specs",
    "search_duckduckgo",
    "search_wikipedia",
    "search_github",
    "synthesize_research",
]
