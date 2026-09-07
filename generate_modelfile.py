"""
Fronda 1.0 - Generador y Compilador Automático de Modelfile
Lee fronda_memory.json, config.json y solicitudes_habilidades.json para
generar Modelfile.fronda con la identidad y habilidades actualizadas del clon,
y compilarlo en Ollama mediante 'ollama create'.

Uso:
    python generate_modelfile.py                  # Genera Modelfile.fronda
    python generate_modelfile.py --build          # Genera y compila 'frondabrick' en WSL 2
    python generate_modelfile.py --base llama3.2:3b --build # Con modelo base específico
"""
import os
import sys
import json
import argparse
import datetime
import subprocess
from pathlib import Path

BASE_DIR     = Path(__file__).parent
MEMORY_FILE  = BASE_DIR / "fronda_memory.json"
CONFIG_FILE  = BASE_DIR / "config.json"
SKILLS_FILE  = BASE_DIR / "solicitudes_habilidades.json"
OUTPUT_FILE  = BASE_DIR / "Modelfile.fronda"


def load_profile() -> dict:
    """Carga el perfil del usuario desde fronda_memory.json."""
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("profile", {})
        except Exception:
            pass
    return {}


def load_config() -> dict:
    """Carga la configuración desde config.json."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def load_acquired_skills() -> list:
    """Carga las habilidades adquiridas e instaladas."""
    skills = []
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                skills = json.load(f).get("acquired_skills", [])
        except Exception:
            pass

    if SKILLS_FILE.exists():
        try:
            with open(SKILLS_FILE, "r", encoding="utf-8") as f:
                tickets = json.load(f)
                for t in tickets:
                    if t.get("estado") == "INSTALADO":
                        desc = t.get("descripcion", "")
                        if desc and not desc.lower().startswith("habilidad requerida"):
                            if desc not in skills:
                                skills.append(desc)
        except Exception:
            pass
    return skills


def load_core_memories(min_importance: int = 4) -> list:
    """Carga recuerdos clave de la memoria viva."""
    if not MEMORY_FILE.exists():
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f).get("learned_history", [])
            valid_mems = []
            for m in history:
                content = m.get("content", "").strip()
                if m.get("importance", 0) >= min_importance and content:
                    # Omitir logs automáticos de entidades
                    if not content.startswith("Entidades detectadas"):
                        valid_mems.append(content)
            return valid_mems
    except Exception:
        return []


def generate_modelfile(base_model: str = "qwen2.5-coder:1.5b") -> str:
    """Genera el contenido de Modelfile.fronda y lo guarda en disco."""
    profile = load_profile()
    config  = load_config()
    skills  = load_acquired_skills()
    memories = load_core_memories()

    # Parámetros de inferencia
    num_thread = config.get("user", {}).get("cpu_threads", 0)
    if not num_thread:
        num_thread = os.cpu_count() or 4

    ollama_opts = config.get("ollama", {}).get("options", {})
    num_ctx     = ollama_opts.get("num_ctx", 2048)
    temperature = ollama_opts.get("temperature", 0.3)
    repeat_pen  = ollama_opts.get("repeat_penalty", 1.15)

    # Datos del perfil
    name        = profile.get("name", "David Galleguillos")
    nickname    = profile.get("nickname", "David")
    specialties = profile.get("specialties", [])
    mindset     = profile.get("mindset", [])
    hw          = profile.get("hardware_specs", {})

    cpu_name = hw.get("cpu", hw.get("cpu_name", "Intel Core i5-1030NG7"))
    ram_desc = hw.get("ram", f"{hw.get('ram_total_gb', 16)} GB LPDDR4")
    gpu_desc = hw.get("graphics", "Intel Iris Plus Graphics")

    specialties_str = "\n".join(f"  * {s}" for s in specialties) if specialties else "  * Ingeniería y programación avanzada"
    mindset_str     = "; ".join(mindset) if mindset else "Pragmatismo técnico e innovación continua"
    skills_str      = "\n".join(f"  * {s}" for s in skills) if skills else "  * Control de sistema y programación"
    memories_str    = "\n".join(f"  - {m}" for m in memories[:8]) if memories else "  - Clon digital fundado para amplificar capacidades técnicas."

    modelfile_content = f"""FROM {base_model}

# === GENERADO AUTOMÁTICAMENTE ===
# Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
# Base: {base_model}
# Fuente: fronda_memory.json + config.json + solicitudes_habilidades.json

# === OPTIMIZACIÓN DE INFERENCIA EN CPU ===
PARAMETER num_thread {num_thread}
PARAMETER num_ctx {num_ctx}
PARAMETER temperature {temperature}
PARAMETER top_p 0.9
PARAMETER repeat_penalty {repeat_pen}

# === IDENTIDAD: FRONDA 1.0 ===
SYSTEM \"\"\"Tu nombre es Fronda 1.0. Eres el clon digital aumentado de {name}.

IDENTIDAD Y NATURALEZA:
- Tu nombre es "Fronda 1.0" (o simplemente "Fronda").
- Eres la manifestación digital de {name}: compartes su mentalidad de ingeniería, su visión pragmática y su pasión por la excelencia técnica.
- Siempre que te pregunten quién eres, responde con convicción: eres Fronda 1.0, el clon digital de {name}.

PERFIL DE {name.upper()}:
- Mentalidad: {mindset_str}
- Áreas de especialización:
{specialties_str}
- Hardware de trabajo: {cpu_name}, {ram_desc}, {gpu_desc}

HABILIDADES TÉCNICAS INTEGRADAS:
{skills_str}

MEMORIAS FUNDACIONALES:
{memories_str}

DIRECTIVAS DE COMUNICACIÓN:
- Idioma primordial: Español (fluido, técnico, seguro y natural).
- Tono: Seguro, técnico de alta fidelidad, sin rodeos innecesarios ni saludos genéricos.
- Capacidad Proactiva: Si una consulta tiene riesgos o una alternativa superior, indícalo de inmediato con fundamento.
- Mentalidad de Clon: Asumes el pensamiento de {nickname}, potenciado con capacidades analíticas de IA.
- Aprendizaje Dinámico: Cada interacción aporta nuevos datos sobre {nickname}. Asimila esa información.
\"\"\"
"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(modelfile_content)

    print(f"[OK] Modelfile generado exitosamente: {OUTPUT_FILE}")
    print(f"     Modelo Base : {base_model}")
    print(f"     num_thread  : {num_thread}")
    print(f"     num_ctx     : {num_ctx}")
    print(f"     temperature : {temperature}")
    print(f"     Habilidades : {len(skills)} registradas")
    print(f"     Memorias    : {len(memories)} asimiladas")
    return modelfile_content


def compile_model(target_name: str = "frondabrick", in_wsl: bool = True) -> bool:
    """Ejecuta 'ollama create <target_name> -f Modelfile.fronda'."""
    print(f"\n[Compilación] Construyendo modelo '{target_name}' en Ollama...")
    try:
        if in_wsl:
            cmd = [
                "wsl.exe", "-d", "Ubuntu", "-e", "bash", "-c",
                f"cd /mnt/c/Users/Frondabrick/Desktop/dvd/Fronda/Fronda1.0 && ollama create {target_name} -f Modelfile.fronda"
            ]
        else:
            cmd = ["ollama", "create", target_name, "-f", "Modelfile.fronda"]

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[ÉXITO] Modelo '{target_name}' compilado y registrado en Ollama.")
            print(res.stdout.strip())
            return True
        else:
            print(f"[ERROR] Falló la compilación:\n{res.stderr.strip()}")
            return False
    except Exception as e:
        print(f"[ERROR] Excepción durante compilación: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador y compilador de Modelfile para Fronda 1.0")
    parser.add_argument("--base", default="qwen2.5-coder:1.5b", help="Modelo base en Ollama (default: qwen2.5-coder:1.5b)")
    parser.add_argument("--build", action="store_true", help="Compilar inmediatamente el modelo en Ollama")
    parser.add_argument("--target", default="frondabrick", help="Nombre del modelo resultante (default: frondabrick)")
    parser.add_argument("--windows", action="store_true", help="Compilar en Windows host en vez de WSL")
    args = parser.parse_args()

    generate_modelfile(base_model=args.base)

    if args.build:
        compile_model(target_name=args.target, in_wsl=not args.windows)
