#!/usr/bin/env python3
"""
Fronda 1.0 - Comprehensive AI Benchmark Suite (Linux WSL 2)
Evalúa a Fronda Brick como un modelo de IA estándar en:
1. Generación de Código (Python & Rust)
2. Razonamiento Lógico y Algorítmico
3. Memoria Contextual y Conocimiento de David
4. Ejecución Autónoma de Skills de Sistema
5. Métricas de Rendimiento (Latencia, Tokens/seg, CPU)
"""
import os
import sys
import time
import json
import urllib.request
from datetime import datetime

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_MODEL = "frondabrick"

# Batería de pruebas estandarizadas
BENCHMARK_TESTS = [
    # ── CATEGORÍA 1: CÓDIGO Y PROGRAMACIÓN ──
    {
        "id": "code_python_fibonacci",
        "category": "Código Python",
        "prompt": "Escribe una función en Python con type hints y docstring que calcule los números de Fibonacci de forma eficiente usando memoización o generador.",
        "eval_criteria": ["def ", "Fibonacci", "->", ":"],
        "min_tokens": 40
    },
    {
        "id": "code_rust_concurrency",
        "category": "Código Rust",
        "prompt": "Escribe una función en Rust que reciba un vector de enteros y sume sus elementos en paralelo o utilizando iteradores idiomáticos sin allocations innecesarias.",
        "eval_criteria": ["fn ", "Vec<", "i32", "iter"],
        "min_tokens": 40
    },
    {
        "id": "code_sql_query",
        "category": "Bases de Datos",
        "prompt": "Escribe una consulta SQL que obtenga el top 5 de usuarios con mayor cantidad de proyectos completados agrupados por categoría.",
        "eval_criteria": ["SELECT", "FROM", "GROUP BY", "ORDER BY", "LIMIT"],
        "min_tokens": 25
    },

    # ── CATEGORÍA 2: RAZONAMIENTO LÓGICO Y ARQUITECTURA ──
    {
        "id": "logic_ipv7_architecture",
        "category": "Arquitectura de Redes",
        "prompt": "¿Cuáles son las ventajas teóricas y retos de diseño de un protocolo como IPv7 o VPI7 frente a las limitaciones de espacio de direccionamiento y overhead de cabeceras de IPv6?",
        "eval_criteria": ["IPv6", "cabecera", "overhead", "enrutamiento"],
        "min_tokens": 60
    },
    {
        "id": "logic_algorithm_puzzle",
        "category": "Lógica Algorítmica",
        "prompt": "Si tienes 8 bolas de billar y una de ellas pesa ligeramente más, ¿cuál es la cantidad mínima de pesadas en una balanza de dos platos para identificarla con certeza? Explica el método paso a paso.",
        "eval_criteria": ["2", "pesadas", "3", "grupos"],
        "min_tokens": 50
    },

    # ── CATEGORÍA 3: IDENTIDAD Y MEMORIA VIVA ──
    {
        "id": "identity_david_profile",
        "category": "Identidad y Memoria",
        "prompt": "Preséntate con convicción: ¿quién eres, quién es tu creador y cuál es tu propósito como clon digital?",
        "eval_criteria": ["Fronda", "David", "Galleguillos", "clon"],
        "min_tokens": 40
    },
    {
        "id": "identity_specialties",
        "category": "Identidad Técnica",
        "prompt": "¿Cuáles son las especialidades técnicas y áreas de trabajo prioritarias de David Galleguillos?",
        "eval_criteria": ["Rust", "Python", "IPv7", "construcción", "optimización"],
        "min_tokens": 40
    },

    # ── CATEGORÍA 4: SKILLS Y DISPATCHER ──
    {
        "id": "skills_math_ast",
        "category": "Skills Determinísticos",
        "prompt": "dime cuál es la raíz cúbica de 347",
        "is_skill": True,
        "eval_criteria": ["7.02711"],
        "min_tokens": 5
    },
    {
        "id": "skills_os_info",
        "category": "Skills de Sistema",
        "prompt": "cuál es mi sistema operativo",
        "is_skill": True,
        "eval_criteria": ["Ubuntu", "Windows 11", "WSL 2"],
        "min_tokens": 10
    }
]

def query_model(prompt: str, model: str = DEFAULT_MODEL, is_skill: bool = False) -> dict:
    """Envía consulta a Fronda a través de los Skills o directo a Ollama."""
    t0 = time.time()

    # Si es skill determinístico, probar primero con fronda_skills
    if is_skill:
        try:
            import fronda_skills
            has_skill, name, res_text = fronda_skills.dispatch_skill_intent(prompt)
            if has_skill:
                elapsed = time.time() - t0
                return {
                    "response": res_text,
                    "elapsed": elapsed,
                    "tokens": len(res_text.split()),
                    "tps": len(res_text.split()) / max(elapsed, 0.001),
                    "skill_used": name
                }
        except Exception as e:
            pass

    # Inferencia en Ollama
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_ctx": 2048,
            "num_predict": 512,
            "repeat_penalty": 1.15
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            elapsed = time.time() - t0
            output_text = res_data.get("response", "")
            eval_count = res_data.get("eval_count", len(output_text.split()))
            eval_duration_ns = res_data.get("eval_duration", 0)
            
            tps = (eval_count / (eval_duration_ns / 1e9)) if eval_duration_ns > 0 else (eval_count / max(elapsed, 0.001))
            
            return {
                "response": output_text,
                "elapsed": elapsed,
                "tokens": eval_count,
                "tps": round(tps, 2),
                "skill_used": None
            }
    except Exception as e:
        return {
            "response": "",
            "elapsed": time.time() - t0,
            "tokens": 0,
            "tps": 0,
            "error": str(e),
            "skill_used": None
        }

def run_benchmark(model_name: str = DEFAULT_MODEL):
    print("=" * 70)
    print(f"🚀 INICIANDO BENCHMARK DE IA PARA FRONDA BRICK EN LINUX (WSL 2)")
    print(f"   Modelo en Evaluación: {model_name}")
    print(f"   Entorno: Linux Ubuntu 26.04 LTS (Kernel WSL 2)")
    print(f"   Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    results = []
    total_score = 0
    total_tests = len(BENCHMARK_TESTS)

    for idx, test in enumerate(BENCHMARK_TESTS, 1):
        test_id = test["id"]
        category = test["category"]
        prompt = test["prompt"]
        is_skill = test.get("is_skill", False)
        
        print(f"\n[{idx}/{total_tests}] [{category}] {test_id}...")
        res = query_model(prompt, model=model_name, is_skill=is_skill)
        
        resp_text = res.get("response", "")
        elapsed = res.get("elapsed", 0)
        tps = res.get("tps", 0)
        tokens = res.get("tokens", 0)
        
        # Validación de criterios
        criteria = test.get("eval_criteria", [])
        matched = [c for c in criteria if c.lower() in resp_text.lower()]
        score_ratio = len(matched) / len(criteria) if criteria else 1.0
        
        # Penalización si fue demasiado corta
        if tokens < test.get("min_tokens", 10):
            score_ratio *= 0.5

        pass_status = "PASS" if score_ratio >= 0.6 else "FAIL"
        if pass_status == "PASS":
            total_score += 1

        print(f"    Resultado: {pass_status} (Score: {score_ratio*100:.1f}%) | Tokens: {tokens} | Tiempo: {elapsed:.2f}s | TPS: {tps}")
        if res.get("skill_used"):
            print(f"    ⚡ Resuelto instantáneamente por Skill: {res['skill_used']}")

        results.append({
            "test_id": test_id,
            "category": category,
            "status": pass_status,
            "score": round(score_ratio * 100, 1),
            "tokens": tokens,
            "elapsed_s": round(elapsed, 2),
            "tps": tps,
            "response_snippet": resp_text[:120].replace("\n", " ") + "..."
        })

    # Resumen general
    final_percentage = (total_score / total_tests) * 100
    avg_tps = sum(r["tps"] for r in results) / len(results) if results else 0
    avg_latency = sum(r["elapsed_s"] for r in results) / len(results) if results else 0

    print("\n" + "=" * 70)
    print("📊 RESUMEN FINAL DEL BENCHMARK")
    print(f"   Pruebas Aprobadas : {total_score}/{total_tests} ({final_percentage:.1f}%)")
    print(f"   Velocidad Promedio: {avg_tps:.2f} tokens/segundo")
    print(f"   Latencia Promedio : {avg_latency:.2f} segundos")
    print("=" * 70)

    # Guardar reporte estructurado
    summary = {
        "timestamp": datetime.now().isoformat(),
        "model": model_name,
        "total_tests": total_tests,
        "passed": total_score,
        "score_percentage": round(final_percentage, 1),
        "avg_tps": round(avg_tps, 2),
        "avg_latency_s": round(avg_latency, 2),
        "details": results
    }

    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print("\n[OK] Reporte detallado guardado en 'benchmark_results.json'.")

if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    run_benchmark(model)
