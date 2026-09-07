"""
Tests del SkillRegistry (Plugin System C9) — Fronda 1.0
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fronda_skill_registry import Skill, SkillRegistry


# ─── Skill de ejemplo para tests ─────────────────────────────────────────────
class EchoSkill(Skill):
    @property
    def name(self) -> str:
        return "echo_test"

    @property
    def description(self) -> str:
        return "Repite el texto enviado (solo para tests)"

    def matches(self, text: str) -> bool:
        return text.startswith("echo:")

    def execute(self, text: str) -> str:
        return text[5:].strip()


class GreetSkill(Skill):
    @property
    def name(self) -> str:
        return "greet_test"

    @property
    def description(self) -> str:
        return "Saluda al usuario (solo para tests)"

    def matches(self, text: str) -> bool:
        return "hola fronda" in text.lower()

    def execute(self, text: str) -> str:
        return "¡Hola! Sistema de plugins activo."


# ─── Tests ────────────────────────────────────────────────────────────────────

def test_registry_register():
    reg = SkillRegistry()
    reg.register(EchoSkill())
    assert len(reg) == 1


def test_registry_no_duplicate():
    reg = SkillRegistry()
    reg.register(EchoSkill())
    reg.register(EchoSkill())  # debe ignorar duplicado
    assert len(reg) == 1


def test_registry_dispatch_match():
    reg = SkillRegistry()
    reg.register(EchoSkill())
    result = reg.dispatch("echo: Hola mundo")
    assert result is not None
    name, output = result
    assert name == "echo_test"
    assert output == "Hola mundo"


def test_registry_dispatch_no_match():
    reg = SkillRegistry()
    reg.register(EchoSkill())
    result = reg.dispatch("mensaje sin match")
    assert result is None


def test_registry_dispatch_first_match_wins():
    """Si dos skills hacen match, el primero registrado gana."""
    reg = SkillRegistry()
    reg.register(EchoSkill())
    reg.register(GreetSkill())
    result = reg.dispatch("echo: test")
    assert result[0] == "echo_test"


def test_registry_list_skills():
    reg = SkillRegistry()
    reg.register(EchoSkill())
    reg.register(GreetSkill())
    skills_list = reg.list_skills()
    assert len(skills_list) == 2
    names = [s["name"] for s in skills_list]
    assert "echo_test" in names
    assert "greet_test" in names


def test_registry_get_by_name():
    reg = SkillRegistry()
    reg.register(EchoSkill())
    skill = reg.get("echo_test")
    assert skill is not None
    assert skill.name == "echo_test"


def test_registry_get_nonexistent():
    reg = SkillRegistry()
    skill = reg.get("no_existe")
    assert skill is None


def test_skill_interface_enforced():
    """No se puede instanciar Skill directamente."""
    import pytest
    with pytest.raises(TypeError):
        Skill()


def test_registry_type_error_on_non_skill():
    import pytest
    reg = SkillRegistry()
    with pytest.raises(TypeError):
        reg.register("esto no es un Skill")


def test_greet_skill_matches():
    skill = GreetSkill()
    assert skill.matches("hola fronda, ¿cómo estás?")
    assert not skill.matches("qué hora es")


def test_echo_skill_execute():
    skill = EchoSkill()
    assert skill.execute("echo: mensaje de prueba") == "mensaje de prueba"
