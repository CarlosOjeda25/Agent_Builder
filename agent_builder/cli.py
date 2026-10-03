#!/usr/bin/env python3
"""
Agent Builder CLI — Consola interactiva minimalista estilo Gentle-AI
Maneja onboarding/setup de primera vez, selección de proveedor y modelos,
autenticación de API keys y ejecución del orquestador SDD.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

# Ajuste de codificación para consola Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = BASE_DIR / ".agentbuilder.json"
ENV_FILE = BASE_DIR / ".env"

# Asegurar import de profiles y orchestrator
sys.path.insert(0, str(BASE_DIR))
import profiles
import orchestrator


def leer_entrada(prompt: str, default: str = "") -> str:
    """Solicita una entrada por consola con valor por defecto."""
    if default:
        p = f"{prompt} [{default}]: "
    else:
        p = f"{prompt}: "
    try:
        val = input(p).strip()
        return val if val else default
    except (KeyboardInterrupt, EOFError):
        print("\nOperación cancelada por el usuario.")
        sys.exit(0)


def obtener_modelos_ollama_locales() -> list[str]:
    """Consulta la API local de Ollama para listar los modelos instalados."""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", headers={"User-Agent": "AgentBuilder"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def cargar_configuracion_guardada() -> dict:
    """Carga configuración persistente si existe."""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def guardar_configuracion(config: dict):
    """Guarda la configuración en JSON y actualiza el archivo .env."""
    CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

    # Actualizar o generar .env
    env_lines = [
        f"# Agent Builder Environment Configuration",
        f"ACTIVE_PROJECT={config.get('project', 'default')}",
        f"MODEL_PROFILE={config.get('profile', 'local')}",
        f"REASONING_MODEL={config.get('reasoning', '')}",
        f"CODING_MODEL={config.get('coding', '')}",
        f"FAST_MODEL={config.get('fast', '')}",
    ]
    if config.get("api_key_name") and config.get("api_key_value"):
        env_lines.append(f"{config['api_key_name']}={config['api_key_value']}")

    ENV_FILE.write_text("\n".join(env_lines) + "\n", encoding="utf-8")

    # Aplicar al entorno del proceso activo y a los JSONC de agentes
    os.environ["ACTIVE_PROJECT"] = config.get("project", "default")
    os.environ["MODEL_PROFILE"] = config.get("profile", "local")
    os.environ["REASONING_MODEL"] = config.get("reasoning", "")
    os.environ["CODING_MODEL"] = config.get("coding", "")
    os.environ["FAST_MODEL"] = config.get("fast", "")
    if config.get("api_key_name") and config.get("api_key_value"):
        os.environ[config["api_key_name"]] = config["api_key_value"]

    profiles.apply_profile_to_agents(config.get("profile", "local"))
    orchestrator.set_active_project(config.get("project", "default"))


def wizard_setup() -> dict:
    """Asistente de configuración paso a paso en consola limpia."""
    print("\n" + "=" * 65)
    print("  CONFIGURACIÓN INICIAL DE AGENT BUILDER (Gentle-AI)")
    print("=" * 65)

    current_dir_name = Path.cwd().name
    project_name = leer_entrada("1. Nombre del proyecto / orquestador", default=current_dir_name)

    print("\n2. Selecciona el proveedor de modelos:")
    print("   [1] Ollama (Local, 100% offline, sin costo)")
    print("   [2] Anthropic Claude (Requiere ANTHROPIC_API_KEY)")
    print("   [3] OpenRouter (Multi-modelo, requiere OPENROUTER_API_KEY)")
    print("   [4] OpenAI / Codex (Requiere OPENAI_API_KEY)")
    print("   [5] Personalizado (Custom)")

    opcion_prov = leer_entrada("Elige una opción (1-5)", default="1")
    prov_map = {
        "1": "local",
        "2": "claude",
        "3": "openrouter",
        "4": "openai",
        "5": "custom",
    }
    profile = prov_map.get(opcion_prov, "local")

    api_key_name = ""
    api_key_val = ""

    if profile == "claude":
        api_key_name = "ANTHROPIC_API_KEY"
        env_val = os.environ.get("ANTHROPIC_API_KEY", "")
        api_key_val = leer_entrada(f"Ingresa tu {api_key_name}", default=env_val)
    elif profile == "openrouter":
        api_key_name = "OPENROUTER_API_KEY"
        env_val = os.environ.get("OPENROUTER_API_KEY", "")
        api_key_val = leer_entrada(f"Ingresa tu {api_key_name}", default=env_val)
    elif profile == "openai":
        api_key_name = "OPENAI_API_KEY"
        env_val = os.environ.get("OPENAI_API_KEY", "")
        api_key_val = leer_entrada(f"Ingresa tu {api_key_name}", default=env_val)

    # Selección de Modelos para los 3 Slots de Gentle-AI
    print("\n3. Personalización de los 3 Slots de Modelos:")
    preset_default = profiles.PRESETS.get(profile, profiles.PRESETS["local"])

    # Si es Ollama, intentar listar modelos reales instalados
    modelos_ollama = []
    if profile == "local":
        modelos_ollama = obtener_modelos_ollama_locales()
        if modelos_ollama:
            print("   Modelos detectados en tu Ollama local:")
            for idx, m in enumerate(modelos_ollama, start=1):
                print(f"     [{idx}] {m}")

    def elegir_modelo(slot_name: str, default_val: str) -> str:
        prompt_txt = f"   • Modelo para [{slot_name.upper()}]"
        if modelos_ollama:
            elegido = leer_entrada(f"{prompt_txt} (nombre o número)", default=default_val)
            if elegido.isdigit() and 1 <= int(elegido) <= len(modelos_ollama):
                return f"ollama/{modelos_ollama[int(elegido)-1]}"
            if not elegido.startswith("ollama/"):
                return f"ollama/{elegido}"
            return elegido
        else:
            return leer_entrada(prompt_txt, default=default_val)

    reasoning_model = elegir_modelo("Reasoning (Arquitecto, PO, Líder QA)", preset_default["reasoning"])
    coding_model = elegir_modelo("Coding (Backend, Frontend, DevOps, QA Auto)", preset_default["coding"])
    fast_model = elegir_modelo("Fast (QA Junior, Backend Junior, Analista)", preset_default["fast"])

    config = {
        "project": project_name,
        "profile": profile,
        "reasoning": reasoning_model,
        "coding": coding_model,
        "fast": fast_model,
        "api_key_name": api_key_name,
        "api_key_value": api_key_val,
    }

    guardar_configuracion(config)
    print("\n[OK] Configuración guardada exitosamente.")
    return config


def mostrar_encabezado(config: dict):
    print("\n" + "=" * 65)
    print("  AGENT BUILDER — SDD ORCHESTRATOR CONSOLE (Gentle-AI)")
    print("=" * 65)
    print(f"  Proyecto activo: {config.get('project', 'default')}")
    print(f"  Perfil de LLM:   {config.get('profile', 'local')}")
    print(f"  [Reasoning]:     {config.get('reasoning')}")
    print(f"  [Coding]:        {config.get('coding')}")
    print(f"  [Fast]:          {config.get('fast')}")
    print("=" * 65)


def menu_interactivo(config: dict):
    """Bucle principal de la consola de trabajo."""
    while True:
        mostrar_encabezado(config)
        print("\nOpciones de ejecución:")
        print("  [1] Nueva Solicitud / Idea (Team PO: Propuesta, Specs y Backlog)")
        print("  [2] Team PO: Preparar Refinamiento (Paquete Three Amigos)")
        print("  [3] Teams Técnicos: Refinamiento (Dev + QA auditan specs y tareas)")
        print("  [4] Team PO: Consolidar Refinamiento (Specs definitivas + tasks.md)")
        print("  [5] Team Dev: Diseño Técnico (Modelo C4, Contratos API, CI/CD)")
        print("  [6] Team Dev: Implementación (TDD, AAA, data-testid)")
        print("  [7] Team QA: Preparar Pruebas (Auditoría AAA + Mutation Testing)")
        print("  [8] Team QA: Preparar Scripts (API Desplegada + Playwright E2E)")
        print("  [9] Team QA: Validar Resultados (Gate de Calidad Final)")
        print("  [C] Cambiar Configuración / Perfil / Modelos")
        print("  [0] Salir")

        eleccion = leer_entrada("\nSelecciona una opción o escribe directamente tu idea", default="1")

        if eleccion == "0":
            print("\nHasta luego, che. Éxitos con el código.")
            break
        elif eleccion in ("C", "c", "config"):
            config = wizard_setup()
        elif eleccion == "1":
            solicitud = leer_entrada("\nDescribe la idea o requerimiento para el Team PO")
            if solicitud:
                orchestrator.fase_po_definicion(solicitud)
        elif eleccion == "2":
            orchestrator.fase_po_preparar()
        elif eleccion == "3":
            print("\n--- Ejecutando Refinamiento de Desarrollo ---")
            orchestrator.fase_dev_refinamiento()
            print("\n--- Ejecutando Refinamiento de QA (Auditoría de Specs y Tareas) ---")
            orchestrator.fase_qa_refinamiento()
        elif eleccion == "4":
            orchestrator.fase_po_consolidar()
        elif eleccion == "5":
            orchestrator.fase_dev_disenar()
        elif eleccion == "6":
            orchestrator.fase_dev_implementar()
        elif eleccion == "7":
            orchestrator.fase_qa_preparar()
        elif eleccion == "8":
            orchestrator.fase_qa_preparar_ejecucion()
        elif eleccion == "9":
            orchestrator.fase_qa_validar()
        else:
            # Si el usuario escribió directamente texto libre largo, se toma como solicitud de producto
            print(f"\nIniciando Definición de Producto para: '{eleccion}'")
            orchestrator.fase_po_definicion(eleccion)

        leer_entrada("\nPresiona [Enter] para volver al menú principal...")


def main():
    config = cargar_configuracion_guardada()
    if not config or "--setup" in sys.argv:
        config = wizard_setup()
    else:
        # Asegurar que las variables de entorno activas coincidan con la config guardada
        os.environ["ACTIVE_PROJECT"] = config.get("project", "default")
        os.environ["MODEL_PROFILE"] = config.get("profile", "local")
        os.environ["REASONING_MODEL"] = config.get("reasoning", "")
        os.environ["CODING_MODEL"] = config.get("coding", "")
        os.environ["FAST_MODEL"] = config.get("fast", "")
        if config.get("api_key_name") and config.get("api_key_value"):
            os.environ[config["api_key_name"]] = config["api_key_value"]
        profiles.apply_profile_to_agents(config.get("profile", "local"))
        orchestrator.set_active_project(config.get("project", "default"))

    menu_interactivo(config)


if __name__ == "__main__":
    main()
