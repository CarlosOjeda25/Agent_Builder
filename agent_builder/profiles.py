#!/usr/bin/env python3
"""
Agent Builder Model Profiles & Slot Manager
Decouples agent definitions from specific LLM providers.
Maps 11 agents into 3 conceptual slots:
  1. REASONING (Product Owner, QA Reviewer, Tech Lead, Architect)
  2. CODING (Senior, Semi-Senior, Junior, Frontend, DevOps)
  3. FAST (Requirements Analyst, Refinement Facilitator)
"""

import os
import json
import re
import sys
from pathlib import Path

# Windows terminal UTF-8 support
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).parent.resolve()
AGENTS_DIR = BASE_DIR / "agents"
ENV_FILE = BASE_DIR / ".env"

# Slot to agents mapping
AGENT_SLOT_MAPPING = {
    "reasoning": [
        "product_owner",
        "revisor_de_calidad_de_requerim",
        "lider_desarrollo",
        "arquitecto_software",
        "lider_qa",
        "qa_semi_senior",
    ],
    "fast": [
        "analista_de_requerimientos",
        "facilitador_refinamiento",
        "qa_junior",
    ],
    "coding": [
        "desarrollador_backend_senior",
        "desarrollador_backend_semi_senior",
        "desarrollador_backend_junior",
        "desarrollador_frontend",
        "ingeniero_devops",
        "qa_automatizacion",
    ],
}

# Preconfigured Provider Presets
PRESETS = {
    "local": {
        "description": "100% Offline con Ollama (DeepSeek R1 8B, Qwen Coder 7B, Hermes 3 8B)",
        "reasoning": "ollama/deepseek-r1:8b",
        "coding": "ollama/qwen2.5-coder:7b",
        "fast": "ollama/hermes3:8b",
    },
    "openrouter": {
        "description": "Nube OpenRouter (Nemotron 120B Free, Qwen Coder 32B, Llama 3.1 8B)",
        "reasoning": "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
        "coding": "openrouter/qwen/qwen-2.5-coder-32b-instruct",
        "fast": "ollama/hermes3:8b", #"openrouter/meta-llama/llama-3.1-8b-instruct",
    },
    "claude": {
        "description": "Anthropic Claude (Sonnet 3.5 para razonamiento y código, Haiku para tareas rápidas)",
        "reasoning": "anthropic/claude-3-5-sonnet-latest",
        "coding": "anthropic/claude-3-5-sonnet-latest",
        "fast": "anthropic/claude-3-5-haiku-latest",
    },
    "openai": {
        "description": "OpenAI (GPT-4o para razonamiento y código, GPT-4o-mini para tareas rápidas)",
        "reasoning": "openai/gpt-4o",
        "coding": "openai/gpt-4o",
        "fast": "openai/gpt-4o-mini",
    },
}


def load_env_vars():
    """Loads .env manually if dotenv is not present."""
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip("\"'")
        if key not in os.environ:
            os.environ[key] = val


def resolve_active_slots(profile_name: str | None = None) -> dict[str, str]:
    """Resolves the 3 model slots according to profile and environment overrides."""
    load_env_vars()
    selected_profile = profile_name or os.environ.get("MODEL_PROFILE", "local").lower()
    base_preset = PRESETS.get(selected_profile, PRESETS["local"])

    slots = {
        "profile": selected_profile,
        "reasoning": os.environ.get("REASONING_MODEL") or base_preset["reasoning"],
        "coding": os.environ.get("CODING_MODEL") or base_preset["coding"],
        "fast": os.environ.get("FAST_MODEL") or base_preset["fast"],
    }
    return slots


def get_agent_slot(agent_name: str) -> str:
    """Returns 'reasoning', 'coding', or 'fast' for a given agent name."""
    for slot, agents in AGENT_SLOT_MAPPING.items():
        if agent_name in agents:
            return slot
    return "reasoning"


def resolve_agent_llm(agent_name: str, profile_name: str | None = None) -> str:
    """Returns the exact LLM string for an agent based on active profile and overrides."""
    slots = resolve_active_slots(profile_name)
    slot = get_agent_slot(agent_name)
    return slots[slot]


def apply_profile_to_agents(profile_name: str | None = None) -> dict[str, str]:
    """Updates agents/*.jsonc with the models resolved from the selected profile."""
    slots = resolve_active_slots(profile_name)

    for slot, agents in AGENT_SLOT_MAPPING.items():
        model_str = slots[slot]
        for agent_name in agents:
            filepath = AGENTS_DIR / f"{agent_name}.jsonc"
            if not filepath.exists():
                continue
            content = filepath.read_text(encoding="utf-8")
            # Replace the "llm": "..." line
            updated_content = re.sub(
                r'("llm":\s*")[^"]+(")',
                rf'\g<1>{model_str}\g<2>',
                content,
            )
            filepath.write_text(updated_content, encoding="utf-8")

    return slots


def list_profiles():
    print("\n=== Perfiles de Modelos Disponibles ===")
    for name, config in PRESETS.items():
        print(f"\n[Perfil: {name}] - {config['description']}")
        print(f"  • Reasoning: {config['reasoning']}")
        print(f"  • Coding:    {config['coding']}")
        print(f"  • Fast:      {config['fast']}")
    print("\nPuedes configurar en tu .env:")
    print("  MODEL_PROFILE=openrouter  # (o local, claude, openai)")
    print("  REASONING_MODEL=...       # (override opcional del slot de razonamiento)")
    print("  CODING_MODEL=...          # (override opcional del slot de código)")
    print("  FAST_MODEL=...            # (override opcional del slot rápido)\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("list", "--list", "-l"):
        list_profiles()
    elif len(sys.argv) > 1 and sys.argv[1] in ("apply", "set"):
        target_profile = sys.argv[2] if len(sys.argv) > 2 else "local"
        res = apply_profile_to_agents(target_profile)
        print(f"Perfil '{res['profile']}' aplicado exitosamente a los 11 agentes:")
        print(f"  • Reasoning: {res['reasoning']}")
        print(f"  • Coding:    {res['coding']}")
        print(f"  • Fast:      {res['fast']}")
    else:
        active = resolve_active_slots()
        print(f"Perfil activo: '{active['profile']}'")
        print(f"  • Reasoning: {active['reasoning']}")
        print(f"  • Coding:    {active['coding']}")
        print(f"  • Fast:      {active['fast']}")
        print("Uso: python profiles.py [list | apply <nombre_perfil>]")
