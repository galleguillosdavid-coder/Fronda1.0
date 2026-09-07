"""
Fronda 1.0 - Plugin System (C9)
Interfaz base `Skill` y `SkillRegistry` para cargar skills dinámicamente.
Cada skill implementa: matches(text) -> bool, execute(text) -> str.
"""
from __future__ import annotations
import importlib
import pkgutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from fronda_logger import get_logger

log = get_logger("fronda.skill_registry")


class Skill(ABC):
    """Interfaz base que debe implementar cada skill de Fronda."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Identificador único del skill (ej: 'math_calc')."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Descripción breve del skill para /api/skills."""

    @abstractmethod
    def matches(self, text: str) -> bool:
        """Retorna True si este skill puede manejar el texto dado."""

    @abstractmethod
    def execute(self, text: str) -> str:
        """Ejecuta el skill y retorna la respuesta en texto."""

    def __repr__(self) -> str:
        return f"<Skill:{self.name}>"


class SkillRegistry:
    """
    Registro central de skills.
    Carga automáticamente todos los módulos en skills/plugins/
    que expongan una clase que herede de Skill.
    """

    def __init__(self):
        self._skills: List[Skill] = []

    def register(self, skill: Skill) -> None:
        """Registra un skill manualmente."""
        if not isinstance(skill, Skill):
            raise TypeError(f"Se esperaba una instancia de Skill, no {type(skill)}")
        if any(s.name == skill.name for s in self._skills):
            log.warning(f"Skill '{skill.name}' ya registrado, omitiendo duplicado.")
            return
        self._skills.append(skill)
        log.debug(f"Skill registrado: {skill.name}")

    def load_from_package(self, package_path: Path, package_name: str) -> int:
        """
        Carga automáticamente todos los módulos del paquete dado.
        Busca clases que hereden de Skill y las instancia.
        Retorna el número de skills cargados.
        """
        loaded = 0
        if not package_path.exists():
            return 0
        for finder, module_name, _ in pkgutil.iter_modules([str(package_path)]):
            full_name = f"{package_name}.{module_name}"
            try:
                module = importlib.import_module(full_name)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, Skill)
                        and attr is not Skill
                    ):
                        try:
                            instance = attr()
                            self.register(instance)
                            loaded += 1
                        except Exception as e:
                            log.warning(f"No se pudo instanciar {attr_name} de {full_name}: {e}")
            except Exception as e:
                log.warning(f"No se pudo importar módulo de skills {full_name}: {e}")
        return loaded

    def dispatch(self, text: str) -> Optional[tuple[str, str]]:
        """
        Itera los skills registrados y retorna (nombre, resultado) del primero que haga match.
        Retorna None si ningún skill aplica.
        """
        for skill in self._skills:
            try:
                if skill.matches(text):
                    result = skill.execute(text)
                    return skill.name, result
            except Exception as e:
                log.error(f"Error en skill '{skill.name}': {e}")
        return None

    def list_skills(self) -> List[dict]:
        """Retorna lista de dicts con name y description de cada skill registrado."""
        return [{"name": s.name, "description": s.description} for s in self._skills]

    def get(self, name: str) -> Optional[Skill]:
        """Busca un skill por nombre."""
        return next((s for s in self._skills if s.name == name), None)

    def __len__(self) -> int:
        return len(self._skills)

    def __repr__(self) -> str:
        return f"<SkillRegistry [{len(self._skills)} skills]>"


# ─── Instancia global ─────────────────────────────────────────────────────────
registry = SkillRegistry()

# ─── Auto-carga de plugins desde skills/plugins/ ──────────────────────────────
_PLUGINS_DIR = Path(__file__).parent / "skills" / "plugins"
if _PLUGINS_DIR.exists():
    n = registry.load_from_package(_PLUGINS_DIR, "skills.plugins")
    if n:
        log.info(f"SkillRegistry: {n} plugin(s) cargados desde skills/plugins/")
