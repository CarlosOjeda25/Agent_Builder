#!/usr/bin/env python3
"""
Agent Builder — Phase-Based Multi-Team Orchestrator
====================================================
Ejecuta el pipeline completo de ingeniería de software por fases Scrum,
respetando pausas entre Definición → Refinamiento → Diseño → Implementación.

Uso:
  python orchestrator.py po definicion     # PRD + User Stories + QA + Backlog
  python orchestrator.py po responder      # Responder preguntas abiertas del cliente
  python orchestrator.py po preparar       # Paquete de preguntas para Dev/QA/Infra
  python orchestrator.py po consolidar     # Consolidar respuestas y decidir
  python orchestrator.py dev refinamiento  # Viabilidad técnica + estimaciones
  python orchestrator.py dev disenar       # Arquitectura + CI/CD + solicitud Infra
  python orchestrator.py dev implementar   # Asignación + código + revisión + entrega
  python orchestrator.py dev corregir      # Triage de defectos QA + correcciones
  python orchestrator.py full "Mi idea"    # Pipeline completo con pausas
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

# Windows terminal UTF-8 support
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()
AGENTS_DIR = BASE_DIR / "agents"
BASE_OUTPUT_DIR = Path(os.environ.get("AGENT_BUILDER_OUTPUT_DIR", BASE_DIR / "output")).resolve()
BASE_INTERCAMBIO_DIR = Path(os.environ.get("AGENT_BUILDER_INTERCAMBIO_DIR", BASE_DIR / "intercambio")).resolve()
OUTPUT_DIR = BASE_OUTPUT_DIR
INTERCAMBIO_DIR = BASE_INTERCAMBIO_DIR

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
INTERCAMBIO_DIR.mkdir(parents=True, exist_ok=True)

# ── Dynamic Project & Profile State ────────────────────────────────────────
ACTIVE_PROJECT = "default"
ACTIVE_PROFILE = None


def set_project(name: str):
    """Sets active project directory to isolate outputs and exchanges."""
    global OUTPUT_DIR, INTERCAMBIO_DIR, ACTIVE_PROJECT
    sanitized = re.sub(r"[^a-zA-Z0-9_\-]", "_", name.strip()) or "default"
    ACTIVE_PROJECT = sanitized
    if os.environ.get("AGENT_BUILDER_FLAT_OUTPUT") == "1":
        OUTPUT_DIR = BASE_OUTPUT_DIR
        INTERCAMBIO_DIR = BASE_INTERCAMBIO_DIR
    else:
        OUTPUT_DIR = BASE_OUTPUT_DIR if ACTIVE_PROJECT == "default" else BASE_OUTPUT_DIR / ACTIVE_PROJECT
        INTERCAMBIO_DIR = BASE_INTERCAMBIO_DIR if ACTIVE_PROJECT == "default" else BASE_INTERCAMBIO_DIR / ACTIVE_PROJECT
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    INTERCAMBIO_DIR.mkdir(parents=True, exist_ok=True)


def set_profile(name: str):
    """Sets active model profile (e.g. 'local', 'openrouter', 'claude', 'openai')."""
    global ACTIVE_PROFILE
    ACTIVE_PROFILE = name.strip().lower()


# ── JSONC loader ───────────────────────────────────────────────────────────
def strip_jsonc_comments(content: str) -> str:
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    content = re.sub(r"//.*", "", content)
    return content


def load_agent_config(name: str) -> dict:
    path = AGENTS_DIR / f"{name}.jsonc"
    if not path.exists():
        raise FileNotFoundError(f"Agent config not found: {path}")
    return json.loads(strip_jsonc_comments(path.read_text(encoding="utf-8")))


# ── Mapeo de Subcarpetas para Organización Limpia ─────────────────────────
SUBFOLDER_MAP = {
    # docs/producto
    "prd.md": "docs/producto",
    "historias_de_usuario.md": "docs/producto",
    "auditoria_calidad.md": "docs/producto",
    "backlog_final.md": "docs/producto",
    "paquete_refinamiento.md": "docs/producto",
    "historias_refinadas.md": "docs/producto",
    "feedback_consolidado.md": "docs/producto",
    "backlog_refinado.md": "docs/producto",
    "acta_refinamiento.md": "docs/producto",
    # docs/specs (canónicos SDD)
    "proposal.md": "docs/specs",
    "specs.md": "docs/specs",
    "design.md": "docs/specs",
    "tasks.md": "docs/specs",
    # docs/arquitectura
    "respuesta_desarrollo.md": "docs/arquitectura",
    "arquitectura.md": "docs/arquitectura",
    "arquitectura_vigente.md": "docs/arquitectura",
    "plan_asignacion.md": "docs/arquitectura",
    "gate_calidad_dev.md": "docs/arquitectura",
    "estrategia_cicd.md": "docs/arquitectura",
    "solicitud_infraestructura.md": "docs/arquitectura",
    "implementacion_backend_senior.md": "docs/arquitectura",
    "implementacion_backend_semi.md": "docs/arquitectura",
    "implementacion_backend_junior.md": "docs/arquitectura",
    "implementacion_frontend.md": "docs/arquitectura",
    "implementacion_cicd.md": "docs/arquitectura",
    "entrega_qa.md": "docs/arquitectura",
    "reentrega_qa.md": "docs/arquitectura",
    # docs/qa
    "respuestas_qa.md": "docs/qa",
    "qa_analisis_riesgos.md": "docs/qa",
    "qa_testabilidad.md": "docs/qa",
    "qa_evaluacion_automatizacion.md": "docs/qa",
    "qa_auditoria_unitests.md": "docs/qa",
    "plan_pruebas.md": "docs/qa",
    "revision_casos.md": "docs/qa",
    "estrategia_automatizacion.md": "docs/qa",
    "casos_semi_senior.md": "docs/qa",
    "casos_junior.md": "docs/qa",
    "hoja_ejecucion.md": "docs/qa",
    "scripts_automatizacion.md": "docs/qa",
    "reporte_qa.md": "docs/qa",
    "dictamen_qa.md": "docs/qa",
    "hoja_reverificacion.md": "docs/qa",
    "automatizacion_regresion.md": "docs/qa",
    "analisis_reverificacion.md": "docs/qa",
    "dictamen_final_qa.md": "docs/qa",
    # docs
    "bundle.md": "docs",
    "bundle_dev.md": "docs",
    "bundle_qa.md": "docs",
    "bundle.json": "docs",
}


def buscar_archivo(nombre_o_ruta: Path | str) -> Path:
    """Encuentra un archivo tanto si está en la raíz, en docs/ o en una subcarpeta."""
    if isinstance(nombre_o_ruta, Path) and nombre_o_ruta.exists():
        return nombre_o_ruta
    nombre = Path(nombre_o_ruta).name
    # 1. Verificar si está en la subcarpeta mapeada esperada
    sub = SUBFOLDER_MAP.get(nombre)
    if sub and (OUTPUT_DIR / sub / nombre).exists():
        return OUTPUT_DIR / sub / nombre
    # 2. Verificar directo en OUTPUT_DIR
    if (OUTPUT_DIR / nombre).exists():
        return OUTPUT_DIR / nombre
    # 3. Búsqueda recursiva en OUTPUT_DIR
    for match in OUTPUT_DIR.rglob(nombre):
        if match.is_file():
            return match
    # Fallback predeterminado según mapa o directo
    if sub:
        return OUTPUT_DIR / sub / nombre
    return OUTPUT_DIR / nombre


def leer_archivo(ruta: Path | str, defecto: str = "SIN DATO") -> str:
    path = buscar_archivo(ruta)
    return path.read_text(encoding="utf-8") if path.exists() else defecto


# ── Agent factory ──────────────────────────────────────────────────────────
def crear_agente(name: str):
    """Build a CrewAI Agent from its .jsonc config, dynamically resolving the model profile."""
    from crewai import Agent

    cfg = load_agent_config(name)
    settings = cfg.get("settings", {})

    try:
        from profiles import resolve_agent_llm
        llm_raw = resolve_agent_llm(name, ACTIVE_PROFILE)
    except Exception:
        llm_raw = cfg.get("llm", "ollama/llama3.2:3b")

    tools = []  # Tools se configuran per-task, no per-agent en este orquestador

    return Agent(
        role=cfg["role"],
        goal=cfg["goal"],
        backstory=cfg["backstory"],
        llm=llm_raw,
        tools=tools,
        verbose=settings.get("verbose", True),
        allow_delegation=settings.get("allow_delegation", False),
        max_iter=settings.get("max_iter", 4),
    )


# ── File I/O & Bundle helpers ──────────────────────────────────────────────
def resolver_ruta_salida(nombre: str) -> Path:
    sub = SUBFOLDER_MAP.get(Path(nombre).name, "docs")
    target_dir = OUTPUT_DIR / sub
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / Path(nombre).name


def guardar_salida(nombre: str, contenido: str) -> Path:
    path = resolver_ruta_salida(nombre)
    path.write_text(contenido, encoding="utf-8")
    print(f"  📄 {path}")
    guardar_bundle()
    return path


def guardar_intercambio(nombre: str, contenido: str) -> Path:
    path = INTERCAMBIO_DIR / nombre
    path.write_text(contenido, encoding="utf-8")
    print(f"  🔄 {path}")
    return path


def guardar_bundle(extra_metadata: dict | None = None) -> dict:
    """Consolida todos los archivos generados en docs/ en un único bundle.json para consumo de UI/API."""
    docs_dir = OUTPUT_DIR / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = docs_dir / "bundle.json"
    artifacts = {}
    for md_file in sorted(OUTPUT_DIR.rglob("*.md")):
        if md_file.name == "bundle.md":
            continue
        rel = md_file.relative_to(OUTPUT_DIR)
        artifacts[str(rel).replace("\\", "/")] = md_file.read_text(encoding="utf-8")

    bundle_data = {
        "project": ACTIVE_PROJECT,
        "profile": ACTIVE_PROFILE or os.environ.get("MODEL_PROFILE", "local"),
        "updated_at": datetime.now().isoformat(),
        "total_artifacts": len(artifacts),
        "artifacts": artifacts,
    }
    if extra_metadata:
        bundle_data.update(extra_metadata)

    bundle_path.write_text(json.dumps(bundle_data, indent=2, ensure_ascii=False), encoding="utf-8")
    return bundle_data


def persistir_salidas_crew(crew, result):
    """Garantiza que todas las salidas de las tareas de CrewAI se guarden en OUTPUT_DIR (host),
    evitando el bug de CrewAI que elimina el slash inicial de output_file y guarda en /app/workspace."""
    if not hasattr(result, "tasks_output"):
        return
    for task, out in zip(crew.tasks, result.tasks_output):
        nombre_salida = getattr(task, "output_file", None)
        raw_content = getattr(out, "raw", None)
        if nombre_salida and raw_content:
            filename = Path(nombre_salida).name
            guardar_salida(filename, raw_content)


def recuperar_desde_bundle_si_necesario():
    """Si bundle.md existe pero faltan los archivos individuales de definición,
    los recupera y extrae automáticamente en su subcarpeta de docs/."""
    bundle_file = buscar_archivo("bundle.md")
    if not bundle_file.exists():
        return

    contenido = bundle_file.read_text(encoding="utf-8")
    partes = contenido.split("\n---\n\n")

    mapeo = [
        ("prd.md", ["# PRD"]),
        ("historias_de_usuario.md", ["# Historias de Usuario"]),
        ("auditoria_calidad.md", ["# Reporte de Auditoría", "# Reporte de Auditoria"]),
        ("backlog_final.md", ["# Backlog Final"]),
    ]

    for filename, headers in mapeo:
        target_path = buscar_archivo(filename)
        if not target_path.exists() or target_path.stat().st_size == 0:
            for parte in partes:
                matched_header = next((h for h in headers if h in parte), None)
                if matched_header:
                    idx = parte.find(matched_header)
                    bloque = parte[idx:].strip() if idx != -1 else parte.strip()
                    guardar_salida(filename, bloque + "\n")
                    break


# ═══════════════════════════════════════════════════════════════════════════
# TEAM PO — Fase 1: Definición (PRD + Historias + QA + Backlog)
# ═══════════════════════════════════════════════════════════════════════════

def fase_po_definicion(solicitud_usuario: str):
    """Ejecuta el pipeline completo del Team PO: desde la idea hasta el backlog aceptado."""
    try:
        import console_ui
        console_ui.render_banner("TEAM PO — FASE 1: DEFINICIÓN", f"Solicitud: {solicitud_usuario}", icono="🐶")
    except Exception:
        print("\n" + "=" * 70)
        print("🐶 TEAM PO — FASE 1: DEFINICIÓN")
        print("=" * 70)

    from crewai import Task, Crew, Process

    po = crear_agente("product_owner")
    analista = crear_agente("analista_de_requerimientos")
    revisor = crear_agente("revisor_de_calidad_de_requerim")

    # ── Task 1: Analizar solicitud y redactar PRD ──
    t_prd = Task(
        description=(
            f"Analiza la solicitud del usuario: [{solicitud_usuario}].\n"
            "Extrae SOLO lo que aparece en ella. Identifica el problema, los usuarios, "
            "los objetivos (máximo 5) y las restricciones. Registra supuestos y preguntas "
            "abiertas en lugar de inventar información.\n\n"
            "Define máximo 10 funcionalidades core con ID (F-01, F-02...), nombre, "
            "descripción de una línea (qué hace, no cómo), valor de negocio y prioridad "
            "MoSCoW (al menos una Must). Lista qué queda fuera del alcance (mínimo 3 ítems). "
            "Añade entre 2 y 4 métricas de éxito medibles. No menciones tecnologías."
        ),
        expected_output=(
            "# PRD\n"
            "## 1. Objetivo del producto\n"
            "## 2. Problema que resuelve\n"
            "## 3. Público objetivo\n"
            "## 4. Alcance (incluido y fuera de alcance)\n"
            "## 5. Funcionalidades core (tabla: ID | Funcionalidad | Descripción | "
            "Valor de negocio | Prioridad MoSCoW)\n"
            "## 6. Métricas de éxito (2 a 4 medibles)\n"
            "## 7. Supuestos y preguntas abiertas"
        ),
        agent=po,
        output_file=str(OUTPUT_DIR / "prd.md"),
    )

    # ── Task 2: Épicas + Historias + Gherkin ──
    t_historias = Task(
        description=(
            "Lee el PRD generado. Identifica los actores y agrupa las funcionalidades F-xx "
            "en máximo 6 épicas. Para cada épica desglosa historias de usuario "
            "atómicas con formato [ID-001] (prefijo numérico, no HU-xxx). Cada historia "
            "debe ser independiente, pequeña y verificable (INVEST).\n\n"
            "Cada historia incluye:\n"
            "- **Sección 1 — Perspectiva de Negocio:** Como/Quiero/Para + Métricas de éxito "
            "medibles (ej. 'reducir el tiempo de respuesta en un 20%').\n"
            "- **Sección 4 — Estrategia de Testing:** Criterios Gherkin con mínimo 3 escenarios "
            "(feliz, alterno, error/borde). Dado/Cuando/Entonces con un solo 'Cuando' por "
            "escenario. Valores medibles. Prohibido términos vagos.\n\n"
            "Las secciones 2 (Arquitectura C4), 3 (Contratos API) y 5 (DoD) quedan como "
            "'Pendiente de refinamiento técnico' — se completan en fases posteriores."
        ),
        expected_output=(
            "# Historias de Usuario y Criterios de Aceptación\n"
            "## Actores del Sistema (tabla: Actor | Descripción)\n"
            "## Épicas (tabla: ID E-xx | Nombre | Funcionalidades F-xx | Prioridad)\n\n"
            "Para cada historia:\n"
            "### [ID-001] — Título de la Historia\n"
            "**Épica:** E-xx | **Prioridad:** [MoSCoW] | **Story Points:** Pendiente\n\n"
            "**1. Perspectiva de Negocio**\n"
            "Como [rol], Quiero [acción], Para [valor de negocio]\n"
            "Métricas de Éxito: [2-3 métricas medibles con números concretos]\n\n"
            "**2. Arquitectura y Componentes**\n"
            "Pendiente de refinamiento técnico (fase dev disenar)\n\n"
            "**3. Contratos de Integración**\n"
            "Pendiente de refinamiento técnico (fase dev disenar)\n\n"
            "**4. Estrategia de Testing**\n"
            "Escenario 1 [feliz]:\n"
            "  Dado [contexto inicial]\n"
            "  Cuando [acción concreta]\n"
            "  Entonces [resultado verificable]\n"
            "Escenario 2 [alterno]:\n"
            "  Dado ...\n"
            "  Cuando ...\n"
            "  Entonces ...\n"
            "Escenario 3 [error/borde]:\n"
            "  Dado ...\n"
            "  Cuando ...\n"
            "  Entonces ...\n\n"
            "Datos de Prueba: Pendiente (fase dev implementar)\n"
            "Selectores UI (data-testid): Pendiente (fase dev implementar)\n\n"
            "**5. Definition of Done**\n"
            "Pendiente (fase dev implementar)\n\n"
            "---\n\n"
            "## Preguntas para el PO (lista o 'Ninguna')"
        ),
        agent=analista,
        context=[t_prd],
        output_file=str(OUTPUT_DIR / "historias_de_usuario.md"),
    )

    # ── Task 3: Auditoría de calidad ──
    t_auditoria = Task(
        description=(
            "Audita las Historias de Usuario contra el PRD. Valida: "
            "(1) cada funcionalidad F-xx tenga al menos una historia, "
            "(2) cada historia referencie una F-xx que exista. "
            "Para cada historia aplica checklist INVEST respondiendo Sí/No: "
            "(a) Formato Como/quiero/para correcto, (b) INVEST, "
            "(c) Mínimo 3 escenarios (feliz, alterno, error), "
            "(d) Valores medibles sin términos vagos, (e) Gherkin bien formado. "
            "Emite veredicto: 'Listo para Desarrollo' o 'Requiere otra iteración'."
        ),
        expected_output=(
            "# Reporte de Auditoría y Calidad de Requerimientos\n"
            "## 1. Veredicto Final\n"
            "## 2. Resumen General\n"
            "## 3. Cobertura y Trazabilidad (Tabla: F-xx | Historias asociadas | Estado)\n"
            "## 4. Auditoría INVEST por Historia (Tabla con Sí/No)\n"
            "## 5. Correcciones Obligatorias Numeradas"
        ),
        agent=revisor,
        context=[t_prd, t_historias],
        output_file=str(OUTPUT_DIR / "auditoria_calidad.md"),
    )

    # ── Task 4: Aceptar backlog ──
    t_backlog = Task(
        description=(
            "Verifica que las historias finales respondan a los objetivos y funcionalidades "
            "Must del PRD. Responde cada 'Pregunta para el PO' con una decisión concreta o "
            "'Pendiente de confirmación del usuario'. Emite la decisión de aceptación del "
            "backlog (Aceptado / Aceptado con reservas / Devuelto) y ordena el backlog final "
            "por prioridad MoSCoW y valor de negocio."
        ),
        expected_output=(
            "# Backlog Final Aceptado\n"
            "## 1. Decisión del Product Owner (Aceptado / Aceptado con reservas / Devuelto)\n"
            "## 2. Respuestas a Preguntas del Analista\n"
            "## 3. Backlog Priorizado (Tabla: Orden | HU | Prioridad | Justificación)\n"
            "## 4. Riesgos y Supuestos Pendientes"
        ),
        agent=po,
        context=[t_prd, t_auditoria, t_historias],
        output_file=str(OUTPUT_DIR / "backlog_final.md"),
    )

    crew = Crew(
        agents=[po, analista, revisor],
        tasks=[t_prd, t_historias, t_auditoria, t_backlog],
        process=Process.sequential,
        verbose=True,
    )

    try:
        import console_ui
        with console_ui.animacion_pensando("Célula de Producto colaborando...", "PO, Analista y Revisor INVEST"):
            result = crew.kickoff(inputs={"solicitud_usuario": solicitud_usuario})
    except Exception:
        result = crew.kickoff(inputs={"solicitud_usuario": solicitud_usuario})

    persistir_salidas_crew(crew, result)

    # Espejo de artefactos canónicos SDD
    if (OUTPUT_DIR / "prd.md").exists():
        guardar_salida("proposal.md", (OUTPUT_DIR / "prd.md").read_text(encoding="utf-8"))
    if (OUTPUT_DIR / "historias_de_usuario.md").exists():
        guardar_salida("specs.md", (OUTPUT_DIR / "historias_de_usuario.md").read_text(encoding="utf-8"))

    # Consolidate all phase outputs into bundle.md
    _bundle_parts = []
    for _t in result.tasks_output:
        if _t.raw:
            _bundle_parts.append(f"## {_t.name}\n\n{_t.raw}\n")
    _bundle = "\n---\n\n".join(_bundle_parts)
    guardar_salida("bundle.md", _bundle)

    # ── Renderizado visual con Rich y Human-in-the-Loop ──────────────────────
    backlog_text = leer_archivo(OUTPUT_DIR / "backlog_final.md", str(result))
    prd_text = leer_archivo(OUTPUT_DIR / "prd.md", "")
    try:
        import console_ui
        console_ui.render_resumen_ejecutivo_propuesta(prd_text, backlog_text)

        decision = console_ui.gestionar_aprobacion_propuesta(
            prd_text=prd_text,
            backlog_text=backlog_text,
            on_aceptar=lambda: None,
            on_modificar=lambda cambios: fase_po_responder(feedback_libre=cambios),
            on_responder_preguntas=lambda resps: fase_po_responder(respuestas_usuario=resps),
        )

        if decision == "refinar_ahora":
            return pipeline_refinamiento_completo()

        archivos = [
            buscar_archivo("prd.md"),
            buscar_archivo("historias_de_usuario.md"),
            buscar_archivo("auditoria_calidad.md"),
            buscar_archivo("backlog_final.md"),
            buscar_archivo("bundle.md"),
        ]
        console_ui.render_archivos_guardados(archivos)
    except Exception as e:
        print(f"\n✅ Fase Definición completada — {result}")

    return result


def fase_po_responder(respuestas_usuario: dict | None = None, feedback_libre: str | None = None):
    """Permite al cliente responder preguntas abiertas o dar feedback para reestructurar el PRD, Historias y Backlog."""
    recuperar_desde_bundle_si_necesario()
    try:
        import console_ui
        console_ui.render_banner("TEAM PO — RESOLUCIÓN DE PREGUNTAS Y FEEDBACK DEL CLIENTE", "Human-in-the-Loop", icono="📝")
    except Exception:
        print("\n" + "=" * 70)
        print("📝 TEAM PO — RESOLUCIÓN DE PREGUNTAS Y FEEDBACK DEL CLIENTE")
        print("=" * 70)

    backlog_actual = leer_archivo(OUTPUT_DIR / "backlog_final.md")
    prd_actual = leer_archivo(OUTPUT_DIR / "prd.md")
    historias_actuales = leer_archivo(OUTPUT_DIR / "historias_de_usuario.md")

    if not respuestas_usuario and not feedback_libre:
        try:
            import console_ui
            preguntas = console_ui.extraer_preguntas_pendientes(backlog_actual)
            if not preguntas:
                preguntas = console_ui.extraer_preguntas_pendientes(prd_actual)

            if preguntas:
                console_ui.render_preguntas_pendientes(preguntas)
                respuestas_usuario = console_ui.interactuar_preguntas_cliente(preguntas)
            else:
                from rich.prompt import Prompt
                console_ui.console.print("\n[bold cyan]💡 No hay preguntas técnicas bloqueantes. Podés ingresar tus cambios, correcciones o detalles que no te cuadran:[/]")
                ajuste = Prompt.ask("[bold green]Tus ajustes o correcciones (o Enter para aceptar la propuesta tal cual)[/]")
                if ajuste.strip():
                    feedback_libre = ajuste.strip()
                else:
                    console_ui.console.print("[green]✅ Propuesta aceptada sin modificaciones adicionales.[/]")
                    return
        except Exception as e:
            print(f"Error extrayendo preguntas: {e}")
            return

    # Formatear las respuestas del cliente en un bloque markdown
    lineas = []
    if respuestas_usuario:
        for preg, resp in respuestas_usuario.items():
            lineas.append(f"- **Pregunta:** {preg}\n  **Decisión del Cliente:** {resp}")
    if feedback_libre:
        lineas.append(f"- **Ajustes y Correcciones Solicitadas por el Cliente:**\n  {feedback_libre}")
    bloque_respuestas = "\n".join(lineas)

    try:
        import console_ui
        console_ui.console.print("\n[bold cyan]🔄 Reestructurando especificaciones con las decisiones del cliente...[/]")
    except Exception:
        print("\n🔄 Reestructurando especificaciones con las decisiones del cliente...")

    from crewai import Task, Crew, Process

    analista = crear_agente("analista_de_requerimientos")
    po = crear_agente("product_owner")

    t_ajustar_prd = Task(
        description=(
            f"El cliente (usuario final) ha proporcionado aclaraciones, respuestas y/o modificaciones a la propuesta:\n\n"
            f"{bloque_respuestas}\n\n"
            f"PRD actual:\n{prd_actual[:2500]}\n\n"
            "INSTRUCCIONES:\n"
            "1. Si el cliente solicitó modificaciones o cambios de rumbo, replantea el PRD para cumplir exactamente con sus nuevos requisitos y descartar lo que no le cuadre.\n"
            "2. Incorpora cada respuesta/ajuste del cliente: actualiza objetivos, usuarios, funcionalidades MoSCoW y restricciones.\n"
            "3. En la sección de preguntas abiertas, reemplaza las dudas con una sección 'Decisiones Confirmadas del Cliente'.\n"
            "4. Entrega el PRD completo, coherente y definitivo."
        ),
        expected_output=(
            "# PRD Actualizado con Feedback del Cliente\n"
            "## 1. Problema y Usuarios\n"
            "## 2. Objetivos y Restricciones (Actualizados)\n"
            "## 3. Decisiones del Cliente Confirmadas\n"
            "## 4. Funcionalidades Core (MoSCoW)\n"
            "## 5. Métricas de Éxito"
        ),
        agent=analista,
        output_file=str(OUTPUT_DIR / "prd.md"),
    )

    t_actualizar_historias = Task(
        description=(
            "Toma el PRD actualizado con las respuestas y cambios solicitados por el cliente y reestructura el documento de Historias de Usuario. "
            "Asegúrate de que las historias reflejen con exactitud las nuevas decisiones y cambios del cliente, eliminando lo descartado y agregando las nuevas funcionalidades con criterios Given-When-Then."
        ),
        expected_output=(
            "# Historias de Usuario Actualizadas\n"
            "Historias con formato 'Como... Quiero... Para...', criterios Given-When-Then alineados con el feedback del cliente."
        ),
        agent=analista,
        context=[t_ajustar_prd],
        output_file=str(OUTPUT_DIR / "historias_de_usuario.md"),
    )

    t_aceptar_backlog = Task(
        description=(
            "Como Product Owner, revisa el PRD y las Historias de Usuario actualizadas tras las correcciones y aclaraciones del cliente. "
            "Dado que las dudas y cambios han sido incorporados oficialmente según lo pedido por el cliente, emite la decisión de ACEPTADO. "
            "Presenta el Backlog Final priorizado y confirma que está listo para el Sprint Planning."
        ),
        expected_output=(
            "# Backlog Final Aceptado\n"
            "## 1. Decisión del Product Owner\n"
            "Aceptado\n\n"
            "## 2. Decisiones Clave Validadas con el Cliente\n"
            "## 3. Backlog Priorizado (Tabla: Orden | HU | Prioridad | Justificación)\n"
            "## 4. Criterios de Aceptación Globales para Refinamiento"
        ),
        agent=po,
        context=[t_ajustar_prd, t_actualizar_historias],
        output_file=str(OUTPUT_DIR / "backlog_final.md"),
    )

    crew_reestructurar = Crew(
        agents=[analista, po],
        tasks=[t_ajustar_prd, t_actualizar_historias, t_aceptar_backlog],
        process=Process.sequential,
        verbose=True,
    )

    try:
        import console_ui
        with console_ui.animacion_pensando("Reestructurando especificaciones...", "Analista y PO aplicando tu feedback"):
            resultado = crew_reestructurar.kickoff()
    except Exception:
        resultado = crew_reestructurar.kickoff()

    persistir_salidas_crew(crew_reestructurar, resultado)

    # Actualizar espejos SDD
    if (OUTPUT_DIR / "prd.md").exists():
        guardar_salida("proposal.md", (OUTPUT_DIR / "prd.md").read_text(encoding="utf-8"))
    if (OUTPUT_DIR / "historias_de_usuario.md").exists():
        guardar_salida("specs.md", (OUTPUT_DIR / "historias_de_usuario.md").read_text(encoding="utf-8"))

    # Actualizar bundle
    _bundle_parts = []
    for _t in resultado.tasks_output:
        if _t.raw:
            _bundle_parts.append(f"## {_t.name}\n\n{_t.raw}\n")
    guardar_salida("bundle.md", "\n---\n\n".join(_bundle_parts))

    # Renderizar resultado enriquecido
    backlog_nuevo = leer_archivo(OUTPUT_DIR / "backlog_final.md", str(resultado))
    prd_nuevo = leer_archivo(OUTPUT_DIR / "prd.md", "")
    try:
        import console_ui
        console_ui.render_resumen_ejecutivo_propuesta(prd_nuevo, backlog_nuevo)
        console_ui.console.print("\n[bold green]🏆 ¡Propuesta replanteada y aceptada con éxito![/]")
        console_ui.console.print("[dim]Las especificaciones se han actualizado según tu visión. Ya podés ejecutar [bold cyan]ab refinar[/bold cyan] cuando quieras.[/]\n")
        archivos = [
            buscar_archivo("prd.md"),
            buscar_archivo("historias_de_usuario.md"),
            buscar_archivo("backlog_final.md"),
            buscar_archivo("bundle.md"),
        ]
        console_ui.render_archivos_guardados(archivos)
    except Exception:
        print(f"\n✅ Backlog reestructurado y aceptado.")

    return resultado


# ═══════════════════════════════════════════════════════════════════════════
# TEAM PO — Fase 2A: Preparar Refinamiento
# ═══════════════════════════════════════════════════════════════════════════

def fase_po_preparar():
    """Genera el paquete de preguntas para los teams de Desarrollo, QA e Infraestructura."""
    try:
        import console_ui
        console_ui.render_banner("TEAM PO — FASE 2A: PREPARAR REFINAMIENTO", "Paquete de preguntas técnicas para Dev, QA e Infra", icono="📦")
    except Exception:
        print("\n" + "=" * 70)
        print("🐶 TEAM PO — FASE 2A: PREPARAR REFINAMIENTO")
        print("=" * 70)

    from crewai import Task, Crew, Process

    facilitador = crear_agente("facilitador_refinamiento")

    backlog = leer_archivo(OUTPUT_DIR / "backlog_final.md")
    historias = leer_archivo(OUTPUT_DIR / "historias_de_usuario.md")
    specs = leer_archivo(OUTPUT_DIR / "specs.md", historias)

    t_paquete = Task(
        description=(
            f"Lee el backlog final y las especificaciones formales SDD generadas:\n\n"
            f"BACKLOG:\n{backlog[:2500]}\n\n"
            f"ESPECIFICACIONES SDD (specs.md / Historias):\n{specs[:4500]}\n\n"
            "Selecciona las historias del tope del backlog priorizado que entrarán al próximo ciclo. "
            "Para cada una prepara un paquete de refinamiento técnico enfocado en validar specs y tareas:\n"
            "1. Desarrollo: viabilidad de implementación, dependencias técnicas, stack y desglose de tareas técnicas.\n"
            "2. QA: auditoría de la especificación (specs.md), escenarios de borde faltantes en Gherkin, "
            "requisitos de testabilidad (mocks, contratos API), selectores data-testid para Playwright "
            "y definición de tareas de prueba automatizada.\n"
            "3. Infraestructura: entornos, URLs base (API_BASE_URL, FRONTEND_BASE_URL), accesos y despliegue.\n\n"
            "Máximo 3 preguntas concretas por historia y por team."
        ),
        expected_output=(
            "# Paquete de Refinamiento Técnico\n"
            "## 1. Historias y Especificaciones a Refinar (Tabla: Orden | HU | Título | Prioridad)\n"
            "## 2. Especificaciones BDD bajo Revisión (Gherkin de cada HU)\n"
            "## 3. Preguntas y Desafíos para Desarrollo (Viabilidad y Desglose técnico)\n"
            "## 4. Preguntas y Auditoría para QA (Testabilidad de specs, escenarios borde y tareas de testing)\n"
            "## 5. Preguntas para Infraestructura (Entornos y URLs base)\n"
            "## 6. Instrucciones de Intercambio (archivos esperados en carpeta intercambio/)"
        ),
        agent=facilitador,
        output_file=str(OUTPUT_DIR / "paquete_refinamiento.md"),
    )

    crew = Crew(
        agents=[facilitador],
        tasks=[t_paquete],
        process=Process.sequential,
        verbose=True,
    )

    try:
        import console_ui
        with console_ui.animacion_pensando("Preparando paquete de refinamiento...", "Facilitador estructurando preguntas para ingeniería"):
            result = crew.kickoff()
    except Exception:
        result = crew.kickoff()
    persistir_salidas_crew(crew, result)
    # Guardar copia en intercambio para los otros teams
    contenido = leer_archivo(OUTPUT_DIR / "paquete_refinamiento.md")
    guardar_intercambio("paquete_refinamiento.md", contenido)

    print(f"\n✅ Paquete de refinamiento generado en output/ e intercambio/")
    print("   ⏸️  Entrega este paquete a Dev, QA e Infraestructura.")
    print("   ⏸️  Cuando respondan, guarda sus archivos en intercambio/ y ejecutá:")
    print("        python orchestrator.py po consolidar")
    # Consolidate all phase outputs into bundle.md
    _ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    _bundle_parts = []
    for _t in result.tasks_output:
        if _t.raw:
            _bundle_parts.append(f"## {_t.name}\n\n{_t.raw}\n")
    _bundle = "\n---\n\n".join(_bundle_parts)
    guardar_salida("bundle.md", _bundle)

    try:
        import console_ui
        console_ui.render_markdown_content(contenido, titulo="Paquete de Refinamiento Preparado")
        archivos = [
            buscar_archivo("paquete_refinamiento.md"),
            buscar_archivo("bundle.md"),
        ]
        console_ui.render_archivos_guardados(archivos)
    except Exception:
        pass

    return result


# ═══════════════════════════════════════════════════════════════════════════
# TEAM PO — Fase 2B: Consolidar Refinamiento
# ═══════════════════════════════════════════════════════════════════════════

def fase_po_consolidar():
    """Consolida respuestas de los teams y emite decisiones finales del PO."""
    print("\n" + "=" * 70)
    print("🐶 TEAM PO — FASE 2B: CONSOLIDAR REFINAMIENTO")
    print("=" * 70)

    from crewai import Task, Crew, Process

    facilitador = crear_agente("facilitador_refinamiento")
    analista = crear_agente("analista_de_requerimientos")
    revisor = crear_agente("revisor_de_calidad_de_requerim")
    po = crear_agente("product_owner")

    paquete = leer_archivo(OUTPUT_DIR / "paquete_refinamiento.md")
    historias = leer_archivo(OUTPUT_DIR / "historias_de_usuario.md")
    prd = leer_archivo(OUTPUT_DIR / "prd.md")
    resp_dev = leer_archivo(INTERCAMBIO_DIR / "respuestas_desarrollo.md")
    resp_qa = leer_archivo(INTERCAMBIO_DIR / "respuestas_qa.md")
    resp_infra = leer_archivo(INTERCAMBIO_DIR / "respuestas_infraestructura.md")

    t_consolidar = Task(
        description=(
            f"Paquete enviado: {paquete[:2000]}\n\n"
            f"Respuestas de Desarrollo: {resp_dev[:2000]}\n"
            f"Respuestas de QA: {resp_qa[:2000]}\n"
            f"Respuestas de Infraestructura: {resp_infra[:2000]}\n\n"
            "Consolida las respuestas por historia sin alterarlas. Si un team no respondió, "
            "escribe 'Sin respuesta'. Clasifica cada hallazgo como: Bloqueo, Riesgo, "
            "Pregunta para el PO, Ajuste a historia o Información. "
            "Si dos teams se contradicen, repórtalo como 'Desacuerdo' sin resolverlo."
        ),
        expected_output=(
            "# Feedback Consolidado\n"
            "## Resumen por historia (Tabla: HU | Desarrollo | QA | Infra | Hallazgos)\n"
            "## Bloqueos\n## Riesgos\n## Preguntas para el PO\n"
            "## Ajustes sugeridos a historias\n## Desacuerdos entre teams"
        ),
        agent=facilitador,
        output_file=str(OUTPUT_DIR / "feedback_consolidado.md"),
    )

    t_ajustar = Task(
        description=(
            f"Historias actuales: {historias[:3000]}\n\n"
            "Trabaja SOLO con las historias que aparecen en el feedback consolidado. "
            "Aplica los ajustes sugeridos incorporando el feedback de Desarrollo, QA e "
            "Infraestructura. Produce el formato COMPLETO de Historia de Usuario Refinada "
            "con las 5 secciones. Si una sección no tiene datos (porque el team no respondió), "
            "márcala como 'Pendiente de [team]'. Marca con '(Refinada)' el título.\n\n"
            "FORMATO EXACTO requerido por historia:\n"
            "### [ID-001] Título de la Historia de Usuario (Refinada)\n"
            "Épica: [Módulo] | Prioridad: [Must/Should/Could] | Story Points: [Fibonacci]\n\n"
            "1. Perspectiva de Negocio (Product Owner & Scrum Master)\n"
            "Como [Rol], Quiero [Acción], Para [Valor de negocio]\n"
            "Métricas de Éxito: [1-3 métricas medibles con números]\n\n"
            "2. Arquitectura y Componentes (Tech Lead / Dev)\n"
            "Diagrama C4 — Nivel Contenedores en sintaxis MERMAID:\n"
            "```mermaid\nC4Context\n  title [Nombre]\n  Person(user, \"Usuario\", \"...\")\n  System_Boundary(sys, \"...\") { ... }\n```\n\n"
            "3. Contratos de Integración (Dev)\n"
            "Endpoint: [MÉTODO] /api/v1/[recurso]\n"
            "Request (JSON Schema) + Response exitoso (JSON payload)\n\n"
            "4. Estrategia de Testing (QA)\n"
            "Escenarios BDD + Selectores data-testid + Datos de prueba mock\n\n"
            "5. Definition of Done (Scrum Master)\n"
            "Checklist con mínimo 5 items verificables"
        ),
        expected_output=(
            "# Historias de Usuario Refinadas\n\n"
            "Para cada historia, este formato EXACTO:\n\n"
            "### [ID-001] Título de la Historia de Usuario (Refinada)\n"
            "**Épica:** [Módulo] | **Prioridad:** [Must/Should/Could] | **Story Points:** [Fibonacci]\n\n"
            "**1. Perspectiva de Negocio (Product Owner & Scrum Master)**\n"
            "Como [Rol], Quiero [Acción], Para [Valor de negocio]\n"
            "Métricas de Éxito: [1-3 métricas medibles]\n\n"
            "**2. Arquitectura y Componentes (Tech Lead / Dev)**\n"
            "Diagrama C4 (Nivel 2 — Contenedores) en Mermaid:\n"
            "```mermaid\nC4Context\n  ...\n```\n\n"
            "**3. Contratos de Integración (Dev)**\n"
            "Endpoint: [MÉTODO] /api/v1/[recurso]\n"
            "Headers: [Authorization, Content-Type]\n"
            "Request JSON Schema:\n"
            "```json\n{ ... }\n```\n"
            "Response (éxito):\n"
            "```json\n{ ... }\n```\n\n"
            "**4. Estrategia de Testing (QA Automation & Manual)**\n"
            "Escenario 1 [Feliz]: Dado/Cuando/Entonces\n"
            "Escenario 2 [Alterno]: Dado/Cuando/Entonces\n"
            "Escenario 3 [Error]: Dado/Cuando/Entonces\n"
            "Selectores UI (data-testid):\n"
            "- Input: data-testid=\"input-[nombre]\"\n"
            "- Botón: data-testid=\"btn-[nombre]\"\n"
            "Datos de Prueba Mock: [usuarios, tarjetas, tokens...]\n\n"
            "**5. Definition of Done (Checklist del Scrum Master)**\n"
            "- [ ] Código en rama feature/[ID-001] con PR mergeado\n"
            "- [ ] Pruebas unitarias ≥ 80% cobertura\n"
            "- [ ] Diagramas C4 actualizados en documentación\n"
            "- [ ] Colección Postman/Swagger actualizada\n"
            "- [ ] Scripts E2E (Playwright/Cypress) en CI/CD sin errores\n\n"
            "---\n\n"
            "## Registro de cambios (ID | qué se cambió)"
        ),
        agent=analista,
        context=[t_consolidar],
        output_file=str(OUTPUT_DIR / "historias_refinadas.md"),
    )

    # ── Task SDD: Desglose Canónico de Tareas Atómicas para Dev y QA ──
    t_sdd_tasks = Task(
        description=(
            "A partir de las Historias de Usuario Refinadas, genera el desglose canónico de "
            "Tareas Atómicas de Ingeniería bajo la metodología SDD (Spec-Driven Development).\n\n"
            "Cada tarea debe ser un bloque de trabajo atómico, ordenado por dependencias e "
            "identificado claramente para el rol ejecutor y su criterio de verificación:\n"
            "- Identificador secuencial atómico (ej: [ ] Task 1.1: Inicializar entidades de dominio)\n"
            "- Historia y funcionalidad asociada: [ID-001] / F-xx\n"
            "- Track asignado: [Backend Senior / Frontend / DevOps / QA Automation]\n"
            "- Dependencias: Tareas previas requeridas (ej: Task 1.1)\n"
            "- Archivos y componentes afectados esperados (ej: src/domain/models/)\n"
            "- Criterio de Verificación DoD (para Dev y QA): contrato de API, test unitario esperado o selector Playwright."
        ),
        expected_output=(
            "# Desglose Canónico de Tareas SDD (tasks.md)\n"
            "## 1. Grafo de Dependencias y Orden de Ejecución\n"
            "## 2. Tareas Atómicas por Historia Refinada\n"
            "### [ID-001] Título de la Historia\n"
            "- [ ] **Task 1.1** [Track: Backend]: Descripción concreta | Deps: ninguna | Verificación: Test unitario entidad\n"
            "- [ ] **Task 1.2** [Track: Backend]: Endpoint y DTO | Deps: Task 1.1 | Verificación: Endpoint HTTP status y schema\n"
            "- [ ] **Task 1.3** [Track: Frontend]: Vista y data-testid | Deps: Task 1.2 | Verificación: Render y data-testid presentes\n"
            "- [ ] **Task 1.4** [Track: QA]: Test API y Playwright E2E | Deps: Task 1.2, Task 1.3 | Verificación: Suite Playwright verde\n"
            "## 3. Matriz de Cobertura y Trazabilidad (HU -> Tasks -> Specs)"
        ),
        agent=analista,
        context=[t_ajustar],
        output_file=str(OUTPUT_DIR / "tasks.md"),
    )

    t_verificar = Task(
        description=(
            "Verifica qué historias refinadas quedan listas para entrar a un sprint. "
            "Emite veredicto por historia (Lista / Pendiente) con justificación."
        ),
        expected_output=(
            "## Veredicto por historia (Tabla: HU | Estado | Justificación)\n"
            "## Resumen: X de Y historias listas para sprint"
        ),
        agent=revisor,
        context=[t_ajustar, t_consolidar],
        output_file=str(OUTPUT_DIR / "veredicto_historias.md"),
    )

    t_decidir = Task(
        description=(
            f"PRD original: {prd[:2000]}\n\n"
            "Con el feedback consolidado y las historias ajustadas, emite la decisión final "
            "del refinamiento: ordena el backlog refinado, resuelve las preguntas pendientes "
            "y registra riesgos."
        ),
        expected_output=(
            "# Backlog Refinado\n"
            "## 1. Decisión final\n"
            "## 2. Respuestas a preguntas del PO\n"
            "## 3. Backlog Priorizado (Tabla: Orden | HU | Prioridad | Justificación)\n"
            "## 4. Riesgos y Supuestos"
        ),
        agent=po,
        context=[t_consolidar, t_ajustar, t_verificar],
        output_file=str(OUTPUT_DIR / "backlog_refinado.md"),
    )

    t_acta = Task(
        description=(
            "Registra el acta del refinamiento: decisiones tomadas, acuerdos alcanzados, "
            "pendientes por team y próximos pasos."
        ),
        expected_output=(
            "# Acta de Refinamiento\n"
            "## 1. Decisiones tomadas\n## 2. Acuerdos\n## 3. Pendientes por team\n"
            "## 4. Próximos pasos"
        ),
        agent=facilitador,
        context=[t_consolidar, t_verificar, t_decidir],
        output_file=str(OUTPUT_DIR / "acta_refinamiento.md"),
    )

    crew = Crew(
        agents=[facilitador, analista, revisor, po],
        tasks=[t_consolidar, t_ajustar, t_sdd_tasks, t_verificar, t_decidir, t_acta],
        process=Process.sequential,
        verbose=True,
    )

    try:
        import console_ui
        with console_ui.animacion_pensando("Consolidando propuesta técnica definitiva...", "PO y Facilitador cerrando backlog"):
            result = crew.kickoff()
    except Exception:
        result = crew.kickoff()
    persistir_salidas_crew(crew, result)
    print(f"\n✅ Refinamiento consolidado — backlog listo para Sprint Planning")

    # Espejo de especificación canónica SDD (specs.md)
    if buscar_archivo("historias_refinadas.md").exists():
        guardar_salida("specs.md", buscar_archivo("historias_refinadas.md").read_text(encoding="utf-8"))

    # Consolidate all phase outputs into bundle.md
    _bundle_parts = []
    for _t in result.tasks_output:
        if _t.raw:
            _bundle_parts.append(f"## {_t.name}\n\n{_t.raw}\n")
    _bundle = "\n---\n\n".join(_bundle_parts)
    guardar_salida("bundle.md", _bundle)

    try:
        import console_ui
        acta_txt = leer_archivo("acta_refinamiento.md", str(result))
        console_ui.render_markdown_content(acta_txt, titulo="Acta de Refinamiento Consolidada")
        archivos = [
            buscar_archivo("feedback_consolidado.md"),
            buscar_archivo("historias_refinadas.md"),
            buscar_archivo("tasks.md"),
            buscar_archivo("backlog_refinado.md"),
            buscar_archivo("acta_refinamiento.md"),
            buscar_archivo("bundle.md"),
        ]
        console_ui.render_archivos_guardados(archivos)
    except Exception:
        pass

    return result


# ═══════════════════════════════════════════════════════════════════════════
# PIPELINE DE REFINAMIENTO COMPLETO (PO ➔ DEV ➔ QA ➔ CONSOLIDACIÓN)
# ═══════════════════════════════════════════════════════════════════════════

def pipeline_refinamiento_completo():
    """Ejecuta el ciclo de refinamiento autónomo en cadena sin intervención manual intermedia:
    1. PO prepara el paquete técnico.
    2. Dev evalúa viabilidad, dependencias y story points.
    3. QA analiza riesgos, testabilidad y automatización.
    4. PO consolida feedback, actualiza historias y emite tareas SDD.
    """
    try:
        import console_ui
        console_ui.render_banner(
            "PIPELINE DE REFINAMIENTO COMPLETO",
            "PO (Preparar) ➔ DEV (Estimar) ➔ QA (Riesgos) ➔ PO (Consolidar)",
            icono="🔄",
        )
    except Exception:
        print("\n" + "═" * 70)
        print("🔄 PIPELINE DE REFINAMIENTO COMPLETO (PO ➔ DEV ➔ QA ➔ CONSOLIDACIÓN)")
        print("═" * 70)

    fase_po_preparar()
    fase_dev_refinamiento()
    fase_qa_refinamiento()
    res = fase_po_consolidar()

    try:
        import console_ui
        console_ui.render_banner(
            "FASE 1 COMPLETADA CON ÉXITO",
            "Propuesta técnica definitiva lista. Siguiente paso: Fase 2 (ab dev disenar / ab qa preparar)",
            icono="🏆",
        )
    except Exception:
        print("\n" + "═" * 70)
        print("🏆 FASE 1 COMPLETADA CON ÉXITO — PROPUESTA DEFINITIVA LISTA")
        print("═" * 70)

    return res


# ═══════════════════════════════════════════════════════════════════════════
# TEAM DEV — Fase 1: Refinamiento Técnico
# ═══════════════════════════════════════════════════════════════════════════

def fase_dev_refinamiento():
    """Viabilidad técnica + estimaciones de backend, frontend y DevOps."""
    print("\n" + "=" * 70)
    print("💻 TEAM DEV — FASE 1: REFINAMIENTO TÉCNICO")
    print("=" * 70)

    from crewai import Task, Crew, Process

    arquitecto = crear_agente("arquitecto_software")
    back_senior = crear_agente("desarrollador_backend_senior")
    frontend = crear_agente("desarrollador_frontend")
    devops = crear_agente("ingeniero_devops")
    lider = crear_agente("lider_desarrollo")

    paquete = leer_archivo(INTERCAMBIO_DIR / "paquete_refinamiento.md")
    historias = leer_archivo(OUTPUT_DIR / "historias_refinadas.md",
                             leer_archivo(OUTPUT_DIR / "historias_de_usuario.md"))

    t_viabilidad = Task(
        description=(
            f"Paquete de refinamiento: {paquete[:3000]}\n"
            f"Historias: {historias[:3000]}\n\n"
            "Para cada historia identifica: componentes afectados (Backend, Frontend, DevOps), "
            "si requiere decisión arquitectónica (Sí/No y cuál), dependencias, riesgos técnicos "
            "y requisitos no funcionales. Usa supuestos explícitos si el stack no está definido."
        ),
        expected_output=(
            "Por cada historia:\n"
            "### HU-xxx\n"
            "- Componentes: [Backend / Frontend / DevOps]\n"
            "- Decisión arquitectónica: [Sí + cuál / No]\n"
            "- Dependencias: [lista o 'Ninguna']\n"
            "- Riesgos: [lista o 'Ninguno']\n"
            "- Requisitos no funcionales: [lista]\n"
            "- Supuestos: [lista]\n"
            "## Supuestos globales"
        ),
        agent=arquitecto,
    )

    t_estimacion_back = Task(
        description=(
            f"Paquete: {paquete[:2000]}\n\n"
            "Para cada historia estima SOLO el trabajo de backend (endpoints, lógica, "
            "persistencia, integraciones). Escala Fibonacci (1,2,3,5,8,13,21). "
            "0 si no hay trabajo backend. 'No estimable' con motivo si falta info. "
            "Marca ítems de riesgo (seguridad, concurrencia, integración externa, migración)."
        ),
        expected_output=(
            "Por cada historia:\n### HU-xxx\n- Tamaño backend: [puntos / 0 / No estimable]\n"
            "- Tareas técnicas: [lista, marcando riesgos]\n- Dependencias\n- Riesgos"
        ),
        agent=back_senior,
        context=[t_viabilidad],
    )

    t_estimacion_front = Task(
        description=(
            f"Paquete: {paquete[:2000]}\n\n"
            "Para cada historia estima SOLO trabajo de frontend (pantallas, componentes, "
            "estados, integración API). Fibonacci. 0 si no hay. 'No estimable' con motivo."
        ),
        expected_output=(
            "Por cada historia:\n### HU-xxx\n- Tamaño frontend: [puntos / 0 / No estimable]\n"
            "- Tareas técnicas\n- Dependencias\n- Riesgos"
        ),
        agent=frontend,
        context=[t_viabilidad],
    )

    t_estimacion_devops = Task(
        description=(
            f"Paquete: {paquete[:2000]}\n\n"
            "Para cada historia estima SOLO trabajo DevOps (pipelines, despliegue, "
            "configuración, secretos). Fibonacci. Indica necesidades hacia Infraestructura."
        ),
        expected_output=(
            "Por cada historia:\n### HU-xxx\n- Tamaño DevOps: [puntos / 0 / No estimable]\n"
            "- Tareas técnicas\n- Necesidades Infraestructura\n- Riesgos"
        ),
        agent=devops,
        context=[t_viabilidad],
    )

    t_respuesta = Task(
        description=(
            "Consolida el análisis de viabilidad y las tres estimaciones en la respuesta "
            "oficial de Desarrollo al Team PO. Responde cada pregunta del paquete. "
            "Si un ítem no es estimable, explica por qué. Usa el formato de plantilla acordado."
        ),
        expected_output=(
            "# Respuestas del Team Desarrollo\n"
            "## Resumen por historia (Tabla: HU | Viabilidad | Backend | Frontend | DevOps | Total)\n"
            "## Respuestas a preguntas del PO\n"
            "## Riesgos identificados\n## Supuestos"
        ),
        agent=lider,
        context=[t_viabilidad, t_estimacion_back, t_estimacion_front, t_estimacion_devops],
        output_file=str(OUTPUT_DIR / "respuesta_desarrollo.md"),
    )

    crew = Crew(
        agents=[arquitecto, back_senior, frontend, devops, lider],
        tasks=[t_viabilidad, t_estimacion_back, t_estimacion_front,
               t_estimacion_devops, t_respuesta],
        process=Process.sequential,
        verbose=True,
    )

    try:
        import console_ui
        with console_ui.animacion_pensando("Team Dev analizando viabilidad y esfuerzo...", "Arquitecto, Backend, Frontend y DevOps"):
            result = crew.kickoff()
    except Exception:
        result = crew.kickoff()
    persistir_salidas_crew(crew, result)
    contenido = leer_archivo("respuesta_desarrollo.md", str(result))
    guardar_salida("respuesta_desarrollo.md", contenido)
    guardar_intercambio("respuestas_desarrollo.md", contenido)
    print(f"\n✅ Refinamiento técnico completado — respuesta en intercambio/")
    # Consolidate all phase outputs into bundle.md
    _ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    _bundle_parts = []
    for _t in result.tasks_output:
        if _t.raw:
            _bundle_parts.append(f"## {_t.name}\n\n{_t.raw}\n")
    _bundle = "\n---\n\n".join(_bundle_parts)
    guardar_salida("bundle.md", _bundle)

    try:
        import console_ui
        console_ui.render_markdown_content(contenido, titulo="Respuestas Técnicas de Desarrollo")
        archivos = [
            buscar_archivo("respuesta_desarrollo.md"),
            buscar_archivo("bundle.md"),
        ]
        console_ui.render_archivos_guardados(archivos)
    except Exception:
        pass

    return result


# ═══════════════════════════════════════════════════════════════════════════
# TEAM DEV — Fase 2: Diseño Técnico
# ═══════════════════════════════════════════════════════════════════════════

def fase_dev_disenar():
    """Arquitectura + estrategia CI/CD + solicitud a Infraestructura."""
    print("\n" + "=" * 70)
    print("💻 TEAM DEV — FASE 2: DISEÑO TÉCNICO")
    print("=" * 70)

    from crewai import Task, Crew, Process

    arquitecto = crear_agente("arquitecto_software")
    devops = crear_agente("ingeniero_devops")

    historias = leer_archivo(OUTPUT_DIR / "historias_refinadas.md",
                             leer_archivo(OUTPUT_DIR / "historias_de_usuario.md"))
    backlog = leer_archivo(OUTPUT_DIR / "backlog_refinado.md",
                           leer_archivo(OUTPUT_DIR / "backlog_final.md"))

    t_arquitectura = Task(
        description=(
            f"Historias refinadas: {historias[:3000]}\n"
            f"Backlog: {backlog[:2000]}\n\n"
            "Define la arquitectura y el stack tecnológico usando el MODELO C4 como guía. "
            "Documenta los 4 niveles: Contexto (sistema y actores externos), Contenedores "
            "(servicios, APIs, bases de datos, colas), Componentes (módulos internos de cada "
            "contenedor) y Código (estructura de paquetes). Incluye: estilo arquitectónico "
            "(Clean Architecture, microservicios, etc.), stack (lenguajes, frameworks, bases "
            "de datos), modelo de datos conceptual, contrato de API (recursos, endpoints, "
            "métodos), y requisitos no funcionales con valores medibles. "
            "Toda decisión incluye la alternativa descartada y la razón. "
            "Respeta las restricciones del PRD. Si no existen, regístralas como 'Supuesto'."
        ),
        expected_output=(
            "# Arquitectura y Stack Tecnológico (Modelo C4)\n"
            "## 1. C4 — Nivel Contexto (diagrama textual: sistema, actores, sistemas externos)\n"
            "## 2. C4 — Nivel Contenedores (tabla: Contenedor | Tecnología | Responsabilidad)\n"
            "## 3. C4 — Nivel Componentes (por contenedor: componentes internos)\n"
            "## 4. C4 — Nivel Código (estructura de paquetes/módulos)\n"
            "## 5. Estilo Arquitectónico (decisión + alternativas descartadas)\n"
            "## 6. Stack Tecnológico (tabla: Capa | Tecnología | Justificación)\n"
            "## 7. Modelo de Datos Conceptual\n"
            "## 8. Contrato de API (recursos y endpoints principales)\n"
            "## 9. Requisitos No Funcionales (con valores medibles)\n"
            "## 10. Decisiones documentadas (ADR)\n"
            "## 11. Supuestos"
        ),
        agent=arquitecto,
        output_file=str(OUTPUT_DIR / "arquitectura.md"),
    )

    t_cicd = Task(
        description=(
            "Con base en la arquitectura definida, diseña la estrategia CI/CD: "
            "pipelines (build, test, deploy), estrategia de ramas, entornos "
            "(dev, staging, prod), gates de calidad, versionado, rollback."
        ),
        expected_output=(
            "# Estrategia CI/CD\n"
            "## 1. Pipelines (diagrama de etapas)\n"
            "## 2. Estrategia de Ramas\n"
            "## 3. Entornos\n"
            "## 4. Gates de Calidad\n"
            "## 5. Versionado y Rollback"
        ),
        agent=devops,
        context=[t_arquitectura],
        output_file=str(OUTPUT_DIR / "estrategia_cicd.md"),
    )

    t_solicitud_infra = Task(
        description=(
            "Prepara la solicitud formal a Infraestructura con lo que el proyecto necesita: "
            "entornos, bases de datos, storage, networking, seguridad, secretos, capacidad. "
            "No decidas por Infraestructura: preguntá y especificá."
        ),
        expected_output=(
            "# Solicitud a Infraestructura\n"
            "## 1. Entornos requeridos\n## 2. Bases de datos\n## 3. Storage\n"
            "## 4. Networking\n## 5. Seguridad y secretos\n## 6. Capacidad estimada\n"
            "## 7. Restricciones"
        ),
        agent=arquitecto,
        context=[t_arquitectura, t_cicd],
        output_file=str(OUTPUT_DIR / "solicitud_infraestructura.md"),
    )

    crew = Crew(
        agents=[arquitecto, devops],
        tasks=[t_arquitectura, t_cicd, t_solicitud_infra],
        process=Process.sequential,
        verbose=True,
    )

    try:
        import console_ui
        with console_ui.animacion_pensando("Arquitecto y DevOps diseñando arquitectura C4 y CI/CD...", "Modelo C4, Contratos API y Solicitud de Infra"):
            result = crew.kickoff()
    except Exception:
        result = crew.kickoff()

    persistir_salidas_crew(crew, result)

    # Espejo de diseño técnico canónico SDD (design.md)
    if (OUTPUT_DIR / "arquitectura.md").exists():
        guardar_salida("design.md", (OUTPUT_DIR / "arquitectura.md").read_text(encoding="utf-8"))

    contenido = leer_archivo(OUTPUT_DIR / "solicitud_infraestructura.md")
    guardar_intercambio("solicitud_infraestructura.md", contenido)

    # Consolidate all phase outputs into bundle.md
    _bundle_parts = []
    for _t in result.tasks_output:
        if _t.raw:
            _bundle_parts.append(f"## {_t.name}\n\n{_t.raw}\n")
    _bundle = "\n---\n\n".join(_bundle_parts)
    guardar_salida("bundle.md", _bundle)

    try:
        import console_ui
        console_ui.render_banner("DISEÑO TÉCNICO COMPLETADO", "Arquitectura C4, Contratos API y Estrategia CI/CD", icono="🏛️")
        archivos = [
            buscar_archivo("arquitectura.md"),
            buscar_archivo("estrategia_cicd.md"),
            buscar_archivo("solicitud_infraestructura.md"),
            buscar_archivo("bundle.md"),
        ]
        console_ui.render_archivos_guardados(archivos)
        console_ui.console.print("\n[bold color(42)]✓ Los planos de arquitectura y contratos quedaron listos en docs/arquitectura/[/]")
        console_ui.console.print("[dim color(245)]Siguiente paso recomendado: [bold color(75)]ab qa preparar[/bold color(75)] (Diseñar plan y casos de prueba) o [bold color(75)]ab dev implementar[/bold color(75)] (Construir código fuente)[/]\n")
    except Exception:
        print(f"\n✅ Diseño técnico completado — planos listos en docs/arquitectura/")

    return result


    # ═══════════════════════════════════════════════════════════════════════════
# TEAM DEV — Fase 3: Implementación
# ═══════════════════════════════════════════════════════════════════════════

def fase_dev_implementar():
    """Planificación + asignación + implementación + revisión + entrega a QA."""
    print("\n" + "=" * 70)
    print("💻 TEAM DEV — FASE 3: IMPLEMENTACIÓN")
    print("=" * 70)

    from crewai import Task, Crew, Process

    arquitecto = crear_agente("arquitecto_software")
    lider = crear_agente("lider_desarrollo")
    back_senior = crear_agente("desarrollador_backend_senior")
    back_semi = crear_agente("desarrollador_backend_semi_senior")
    back_junior = crear_agente("desarrollador_backend_junior")
    frontend = crear_agente("desarrollador_frontend")
    devops = crear_agente("ingeniero_devops")

    arquitectura = leer_archivo(OUTPUT_DIR / "arquitectura.md", leer_archivo(OUTPUT_DIR / "design.md"))
    resp_infra = leer_archivo(INTERCAMBIO_DIR / "respuesta_infraestructura.md")
    historias = leer_archivo(OUTPUT_DIR / "historias_refinadas.md",
                             leer_archivo(OUTPUT_DIR / "historias_de_usuario.md"))
    specs = leer_archivo(OUTPUT_DIR / "specs.md", historias)
    tasks_sdd = leer_archivo(OUTPUT_DIR / "tasks.md")
    backlog = leer_archivo(OUTPUT_DIR / "backlog_refinado.md",
                           leer_archivo(OUTPUT_DIR / "backlog_final.md"))

    t_incorporar = Task(
        description=(
            f"Arquitectura propuesta: {arquitectura[:2000]}\n"
            f"Respuesta de Infraestructura: {resp_infra[:2000]}\n\n"
            "Ajusta la arquitectura según la respuesta de Infraestructura. "
            "Incorpora restricciones, cambia decisiones si es necesario y produce "
            "la arquitectura VIGENTE (la que el equipo debe seguir para implementar). "
            "Mantén el MODELO C4 completo: Contexto, Contenedores, Componentes y Código."
        ),
        expected_output=(
            "# Arquitectura Vigente (Modelo C4)\n"
            "## 1. Cambios respecto a la versión original\n"
            "## 2. C4 — Contexto (definitivo)\n"
            "## 3. C4 — Contenedores (tabla definitiva)\n"
            "## 4. C4 — Componentes por contenedor (definitivo)\n"
            "## 5. Stack tecnológico definitivo\n"
            "## 6. Contrato de API definitivo\n"
            "## 7. Modelo de datos definitivo\n"
            "## 8. Patrones de código (estructura de proyecto, naming, manejo de errores)"
        ),
        agent=arquitecto,
        output_file=str(OUTPUT_DIR / "arquitectura_vigente.md"),
    )

    t_plan = Task(
        description=(
            f"Arquitectura vigente: {arquitectura[:2000]}\n"
            f"Desglose Canónico de Tareas SDD (tasks.md):\n{tasks_sdd[:3000]}\n"
            f"Especificaciones SDD (specs.md):\n{specs[:2500]}\n\n"
            "Toma las tareas atómicas definidas en tasks.md (Task 1.1, Task 1.2, etc.) y genera "
            "el plan de asignación técnica para el equipo de desarrollo respetando la trazabilidad SDD. "
            "Cada tarea: complejidad (Baja/Media/Alta), desarrollador asignado (Backend Senior / "
            "Semi Senior / Junior / Frontend / DevOps), contenedor y componente C4 asignado, dependencias y revisor.\n\n"
            "Reglas Gentle-AI:\n"
            "- Tareas con riesgo (seguridad, autenticación, concurrencia, integración externa) van al Senior.\n"
            "- Tareas de frontend deben incluir explícitamente la inyección de data-testid exigida por QA.\n"
            "- Cada tarea de backend debe mapearse a su capa Clean Architecture (dominio, aplicación, infraestructura).\n"
            "- Ninguna tarea sin responsable ni sin DoD claro."
        ),
        expected_output=(
            "# Plan de Asignación SDD (con trazabilidad C4)\n"
            "## 1. Mapeo de Tareas SDD a Desarrolladores (Tabla: Task ID | Descripción | "
            "Complejidad | Responsable | Capa Clean Arch / Contenedor C4 | Dependencias | Revisor)\n"
            "## 2. Orden de ejecución y dependencias críticas\n"
            "## 3. Criterios de aceptación y DoD por tarea"
        ),
        agent=lider,
        context=[t_incorporar],
        output_file=str(OUTPUT_DIR / "plan_asignacion.md"),
    )

    t_back_senior = Task(
        description=(
            "Implementa SOLO los ítems asignados a Backend Senior en el plan. "
            "Define y documenta los 'Patrones establecidos' (estructura, nombres, "
            "manejo de errores, forma de las pruebas) antes de implementar. "
            "Cada escenario Gherkin con al menos una prueba unitaria.\n"
            "OBLIGATORIO: Todo código DEBE incluir la ruta de archivo relativa exacta en la primera línea dentro del bloque markdown, por ejemplo:\n"
            "```python\n"
            "# filepath: src/backend/main.py\n"
            "... código completo ejecutable ...\n"
            "```\n"
            "Código 100% completo, ejecutable y sin omitir partes. "
            "Si no tenés ítems asignados, respondé 'Sin asignaciones'."
        ),
        expected_output=(
            "# Implementación Backend Senior\n"
            "## Patrones establecidos\n## Ítems implementados (IT-xx → código + pruebas)\n"
            "## Cambios de contrato propuestos"
        ),
        agent=back_senior,
        context=[t_plan],
        output_file=str(OUTPUT_DIR / "implementacion_backend_senior.md"),
    )

    t_back_semi = Task(
        description=(
            "Implementa SOLO los ítems asignados a Backend Semi Senior siguiendo los "
            "patrones del Senior. Cada escenario Gherkin con prueba unitaria.\n"
            "OBLIGATORIO: Todo código DEBE incluir la ruta de archivo relativa exacta en la primera línea dentro del bloque markdown (# filepath: src/backend/...).\n"
            "Si no tenés ítems, respondé 'Sin asignaciones'. "
            "Dudas → 'Duda para el Senior'."
        ),
        expected_output=(
            "# Implementación Backend Semi Senior\n"
            "## Ítems implementados (IT-xx → código + pruebas)\n"
            "## Dudas para el Senior"
        ),
        agent=back_semi,
        context=[t_plan, t_back_senior],
        output_file=str(OUTPUT_DIR / "implementacion_backend_semi.md"),
    )

    t_back_junior = Task(
        description=(
            "Implementa SOLO los ítems asignados a Backend Junior siguiendo exactamente "
            "los patrones del Senior.\n"
            "OBLIGATORIO: Todo código DEBE incluir la ruta de archivo relativa exacta en la primera línea dentro del bloque markdown (# filepath: src/backend/...).\n"
            "Si no tenés ítems, respondé 'Sin asignaciones'. "
            "No adivines: 'Duda para el Senior'."
        ),
        expected_output=(
            "# Implementación Backend Junior\n"
            "## Ítems implementados (IT-xx → código + pruebas)\n"
            "## Dudas para el Senior"
        ),
        agent=back_junior,
        context=[t_plan, t_back_senior],
        output_file=str(OUTPUT_DIR / "implementacion_backend_junior.md"),
    )

    t_revision = Task(
        description=(
            "Revisa el código del Semi Senior y del Junior. Verifica que sigan los "
            "patrones establecidos, el contrato de API y que cada escenario Gherkin "
            "tenga su prueba. Indicá qué falla y cómo corregirlo. No reescribas."
        ),
        expected_output=(
            "# Revisión de Código Backend\n"
            "## Semi Senior: [Aprobado / Con observaciones] — detalle por ítem\n"
            "## Junior: [Aprobado / Con observaciones] — detalle por ítem\n"
            "## Correcciones solicitadas"
        ),
        agent=back_senior,
        context=[t_back_senior, t_back_semi, t_back_junior],
    )

    t_frontend_impl = Task(
        description=(
            "Implementa SOLO las tareas asignadas a Frontend en el plan de tasks.md. "
            "Consume el contrato de API vigente. Estados de carga, error y vacío en cada pantalla. "
            "REQUISITO OBLIGATORIO DE QA: Inyecta atributos data-testid=\"...\" en todos los inputs, "
            "botones, modales y mensajes de error para que la suite Playwright pueda ejecutarse "
            "de forma determinista sin depender de clases CSS volátiles.\n"
            "OBLIGATORIO: Todo código DEBE incluir la ruta de archivo relativa exacta en la primera línea dentro del bloque markdown (ej: // filepath: src/frontend/App.tsx o src/frontend/index.html).\n"
            "Si no tenés tareas asignadas, respondé 'Sin asignaciones'."
        ),
        expected_output=(
            "# Implementación Frontend\n"
            "## Tareas implementadas (Task ID → componentes + data-testid + pruebas unitarias)\n"
            "## Catálogo de Selectores data-testid generados para QA\n"
            "## Dudas de contrato"
        ),
        agent=frontend,
        context=[t_plan],
        output_file=str(OUTPUT_DIR / "implementacion_frontend.md"),
    )

    t_cicd_impl = Task(
        description=(
            "Implementa la configuración CI/CD: pipelines como código, scripts de build "
            "y despliegue, configuración por entorno. No aprovisiones infraestructura. "
            "Todo despliegue reversible con paso de verificación.\n"
            "OBLIGATORIO: Todo código DEBE incluir la ruta de archivo relativa exacta en la primera línea dentro del bloque markdown (ej: # filepath: .github/workflows/ci.yml o Dockerfile).\n"
        ),
        expected_output=(
            "# Configuración CI/CD\n"
            "## Pipelines implementados\n## Scripts de despliegue\n"
            "## Configuración por entorno\n## Instrucciones de verificación"
        ),
        agent=devops,
        context=[t_plan],
        output_file=str(OUTPUT_DIR / "implementacion_cicd.md"),
    )

    t_gate = Task(
        description=(
            "Gate de Calidad y DoD de Gentle-AI previo a QA: Revisa que todo lo implementado cumpla: "
            "(1) cobertura de pruebas unitarias por escenario Gherkin de specs.md, "
            "(2) contratos de API y capas Clean Architecture respetadas, "
            "(3) selectores data-testid presentes en Frontend, "
            "(4) CI/CD configurado sin secretos en código, "
            "(5) trazabilidad 1:1 con las tareas de tasks.md. "
            "Emite veredicto: 'Listo para QA' o 'Pendiente'."
        ),
        expected_output=(
            "# Gate de Calidad — Revisión de Implementación (DoD Gentle-AI)\n"
            "## 1. Veredicto: [Listo para QA / Pendiente]\n"
            "## 2. Checklist por Tarea SDD (tasks.md)\n## 3. Pendientes"
        ),
        agent=lider,
        context=[t_plan, t_back_senior, t_revision, t_frontend_impl, t_cicd_impl],
        output_file=str(OUTPUT_DIR / "gate_calidad_dev.md"),
    )

    t_entrega_qa = Task(
        description=(
            "Prepara la entrega formal a QA: versión, URLs base (API_BASE_URL, FRONTEND_BASE_URL), "
            "instrucciones de despliegue, catálogo de endpoints, catálogo de data-testid, datos mock de prueba "
            "y criterios de aceptación por HU y tarea de tasks.md. Todo reproducible."
        ),
        expected_output=(
            "# Entrega a QA (Paquete Ejecutable)\n"
            "## 1. Versión y URLs base (API_BASE_URL, FRONTEND_BASE_URL)\n"
            "## 2. Instrucciones de despliegue y healthcheck\n"
            "## 3. Endpoints / Contratos API para test de API\n"
            "## 4. Catálogo de data-testid para Playwright E2E\n"
            "## 5. Datos de prueba y Mocks\n"
            "## 6. Mapeo de verificación por Tarea SDD"
        ),
        agent=devops,
        context=[t_gate, t_cicd_impl],
        output_file=str(OUTPUT_DIR / "entrega_qa.md"),
    )

    crew = Crew(
        agents=[arquitecto, lider, back_senior, back_semi, back_junior, frontend, devops],
        tasks=[t_incorporar, t_plan, t_back_senior, t_back_semi, t_back_junior,
               t_revision, t_frontend_impl, t_cicd_impl, t_gate, t_entrega_qa],
        process=Process.sequential,
        verbose=True,
    )

    try:
        import console_ui
        with console_ui.animacion_pensando("Team Dev construyendo código fuente...", "Líder, Senior, Semi, Junior, Frontend y DevOps"):
            result = crew.kickoff()
    except Exception:
        result = crew.kickoff()

    persistir_salidas_crew(crew, result)
    contenido = leer_archivo(OUTPUT_DIR / "entrega_qa.md")
    guardar_intercambio("entrega_a_qa.md", contenido)

    # Consolidate all phase outputs into bundle_dev.md and accumulate in bundle.md
    _bundle_parts = []
    for _t in result.tasks_output:
        if _t.raw:
            _bundle_parts.append(f"## {_t.name}\n\n{_t.raw}\n")
    _bundle = "\n---\n\n".join(_bundle_parts)
    guardar_salida("bundle_dev.md", _bundle)

    bundle_actual = leer_archivo(OUTPUT_DIR / "bundle.md", "")
    if bundle_actual and "# TEAM DEV IMPLEMENTACIÓN" not in bundle_actual:
        _bundle_total = bundle_actual.strip() + "\n\n---\n\n# TEAM DEV IMPLEMENTACIÓN\n\n" + _bundle
    else:
        _bundle_total = "# TEAM DEV IMPLEMENTACIÓN\n\n" + _bundle
    guardar_salida("bundle.md", _bundle_total)

    # Materializar código fuente en disco físico (src/, tests/, etc.)
    try:
        import code_extractor
        archivos_codigo = code_extractor.materializar_codigo(OUTPUT_DIR)
        code_extractor.render_reporte_extraccion(archivos_codigo)
    except Exception as _e_extract:
        print(f"  ⚠ Materialización de código: {_e_extract}")

    try:
        import console_ui
        console_ui.render_banner("IMPLEMENTACIÓN COMPLETADA", "Código fuente, Unit Tests y Paquete de Entrega a QA", icono="💻")
        archivos = [
            buscar_archivo("arquitectura_vigente.md"),
            buscar_archivo("plan_asignacion.md"),
            buscar_archivo("gate_calidad_dev.md"),
            buscar_archivo("entrega_qa.md"),
            buscar_archivo("bundle.md"),
        ]
        console_ui.render_archivos_guardados(archivos)
        console_ui.console.print("\n[bold color(42)]✓ Código fuente materializado y empaquetado para validación de QA[/]")
        console_ui.console.print("[dim color(245)]Siguiente paso: [bold color(75)]ab qa preparar_ejecucion[/bold color(75)] (Generar scripts automáticos) o [bold color(75)]ab qa validar[/bold color(75)] (Certificar calidad)[/]\n")
    except Exception:
        print(f"\n✅ Implementación completada — entrega a QA en intercambio/")

    return result


def fase_dev_extraer():
    """Extrae y materializa todos los bloques de código fuente en disco físico (src/, tests/, etc.)."""
    import code_extractor
    try:
        import console_ui
        console_ui.render_banner("MATERIALIZAR CÓDIGO FUENTE", "Extracción física de archivos, pruebas y dependencias", icono="📦")
    except Exception:
        print("\n" + "=" * 70)
        print("📦 MATERIALIZAR CÓDIGO FUENTE EN DISCO")
        print("=" * 70)

    archivos = code_extractor.materializar_codigo(OUTPUT_DIR)
    code_extractor.render_reporte_extraccion(archivos)
    return archivos


# ═══════════════════════════════════════════════════════════════════════════
# TEAM DEV — Fase 4: Corrección de Defectos
# ═══════════════════════════════════════════════════════════════════════════

def fase_dev_corregir():
    """Triage de defectos QA + correcciones + re-entrega."""
    print("\n" + "=" * 70)
    print("💻 TEAM DEV — FASE 4: CORRECCIÓN DE DEFECTOS")
    print("=" * 70)

    from crewai import Task, Crew, Process

    lider = crear_agente("lider_desarrollo")
    back_senior = crear_agente("desarrollador_backend_senior")
    back_semi = crear_agente("desarrollador_backend_semi_senior")
    back_junior = crear_agente("desarrollador_backend_junior")
    frontend = crear_agente("desarrollador_frontend")
    devops = crear_agente("ingeniero_devops")

    reporte_qa = leer_archivo(INTERCAMBIO_DIR / "reporte_qa.md")
    plan = leer_archivo(OUTPUT_DIR / "plan_asignacion.md")

    t_triage = Task(
        description=(
            f"Reporte de QA: {reporte_qa[:3000]}\n"
            f"Plan de asignación: {plan[:2000]}\n\n"
            "Analiza el reporte de QA. Clasifica cada defecto por severidad y asígnalo "
            "al responsable que implementó el ítem original. Si un defecto es de diseño, "
            "derivalo al Arquitecto."
        ),
        expected_output=(
            "# Triage de Defectos\n"
            "## 1. Resumen (Total defectos, por severidad, por responsable)\n"
            "## 2. Asignación (Tabla: Defecto | Severidad | HU | Responsable | Acción)\n"
            "## 3. Defectos de diseño → Arquitecto"
        ),
        agent=lider,
    )

    t_corr_senior = Task(
        description=(
            "Corregí SOLO los defectos asignados a Backend Senior en el triage. "
            "Cada fix con su prueba unitaria. Si no tenés defectos, 'Sin asignaciones'."
        ),
        expected_output=(
            "# Correcciones Backend Senior\n"
            "## Defectos corregidos (ID → fix + prueba)"
        ),
        agent=back_senior,
        context=[t_triage],
    )

    t_corr_semi = Task(
        description="Corregí SOLO los defectos asignados a Backend Semi Senior.",
        expected_output="# Correcciones Backend Semi Senior\n## Defectos corregidos",
        agent=back_semi,
        context=[t_triage],
    )

    t_corr_junior = Task(
        description="Corregí SOLO los defectos asignados a Backend Junior.",
        expected_output="# Correcciones Backend Junior\n## Defectos corregidos",
        agent=back_junior,
        context=[t_triage],
    )

    t_corr_front = Task(
        description="Corregí SOLO los defectos asignados a Frontend.",
        expected_output="# Correcciones Frontend\n## Defectos corregidos",
        agent=frontend,
        context=[t_triage],
    )

    t_reentrega = Task(
        description=(
            "Prepara la re-entrega a QA con los defectos corregidos: nueva versión, "
            "lista de defectos cerrados, instrucciones de verificación."
        ),
        expected_output=(
            "# Re-entrega a QA\n"
            "## 1. Nueva versión\n## 2. Defectos cerrados\n## 3. Instrucciones de verificación"
        ),
        agent=devops,
        context=[t_triage, t_corr_senior, t_corr_semi, t_corr_junior, t_corr_front],
    )

    crew = Crew(
        agents=[lider, back_senior, back_semi, back_junior, frontend, devops],
        tasks=[t_triage, t_corr_senior, t_corr_semi, t_corr_junior,
               t_corr_front, t_reentrega],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    persistir_salidas_crew(crew, result)
    contenido = leer_archivo(OUTPUT_DIR / "reentrega_qa.md")
    guardar_intercambio("reentrega_a_qa.md", contenido)
    print(f"\n✅ Correcciones completadas — re-entrega en intercambio/")
    return result



# ═══════════════════════════════════════════════════════════════════════════
# TEAM QA — Fase 1: Refinamiento (Riesgos + Testabilidad + Automatización)
# ═══════════════════════════════════════════════════════════════════════════

def fase_qa_refinamiento():
    """Ejecuta los aportes de calidad para responder al paquete de refinamiento del Team PO."""
    print("\n" + "=" * 70)
    print("🧪 TEAM QA — FASE 1: REFINAMIENTO")
    print("=" * 70)

    from crewai import Task, Crew, Process

    lider_qa = crear_agente("lider_qa")
    qa_semi = crear_agente("qa_semi_senior")
    qa_jun = crear_agente("qa_junior")
    qa_auto = crear_agente("qa_automatizacion")

    paquete = leer_archivo(INTERCAMBIO_DIR / "paquete_refinamiento.md",
                           leer_archivo(OUTPUT_DIR / "paquete_refinamiento.md"))
    historias = leer_archivo(OUTPUT_DIR / "historias_refinadas.md",
                             leer_archivo(OUTPUT_DIR / "historias_de_usuario.md"))
    specs = leer_archivo(OUTPUT_DIR / "specs.md", historias)

    t_riesgos = Task(
        description=(
            f"Paquete de refinamiento: {paquete[:2500]}\n"
            f"Especificaciones SDD (specs.md / Historias):\n{specs[:4000]}\n\n"
            "Analiza las especificaciones con pensamiento adversarial e independiente. "
            "Aplica heurísticas (límites, particiones, concurrencia, fallo de red, impacto). "
            "Identifica vacíos en los criterios de aceptación y formula los escenarios BDD/Gherkin "
            "faltantes que deben agregarse a specs.md. Evalúa el riesgo de regresión."
        ),
        expected_output=(
            "### HU-xxx\n"
            "Tabla de aportes: ID | Clasificación | Aporte | Riesgo (Alto/Medio/Bajo) | Técnica\n"
            "- Riesgo de regresión: [Alto/Medio/Bajo + módulo]\n"
            "- Escenarios Gherkin faltantes para specs.md: [Dado/Cuando/Entonces concretos]\n"
            "- Respuestas a preguntas del paquete: [lista]"
        ),
        agent=qa_semi,
        output_file=str(OUTPUT_DIR / "qa_analisis_riesgos.md"),
    )

    t_testabilidad = Task(
        description=(
            f"Paquete de refinamiento: {paquete[:2500]}\n"
            f"Especificaciones SDD (specs.md):\n{specs[:4000]}\n\n"
            "Audita cada escenario Gherkin en specs.md evaluando Sí o No: "
            "(a) verificable, (b) medible, (c) datos mock definidos, (d) precondición clara. "
            "Si hay 'No', detalla la corrección obligatoria para que el Analista ajuste la spec. "
            "Lista datos y entorno requeridos."
        ),
        expected_output=(
            "### HU-xxx\n"
            "Tabla: Escenario | Verificable | Medible | Datos definidos | Precondición | Motivo\n"
            "- ¿Criterios testables?: [Sí/No]\n"
            "- Correcciones obligatorias a specs.md: [lista]\n"
            "- Datos de prueba mock requeridos: [lista]\n"
            "- Entorno requerido: [lista]"
        ),
        agent=qa_jun,
        output_file=str(OUTPUT_DIR / "qa_testabilidad.md"),
    )

    t_eval_auto = Task(
        description=(
            f"Paquete de refinamiento: {paquete[:2500]}\n"
            f"Especificaciones SDD (specs.md):\n{specs[:4000]}\n\n"
            "Evalúa la estrategia de automatización dual: (1) pruebas de API desplegada (API_BASE_URL) "
            "y (2) pruebas UI Playwright con selectores data-testid (FRONTEND_BASE_URL).\n\n"
            "Define las TAREAS que deben existir en tasks.md:\n"
            "- Requisitos para tareas de Dev: qué data-testid exige Frontend y qué contrato/status codes exige Backend.\n"
            "- Tareas propias de QA: desglose de tareas [Track: QA Automatización] para implementar "
            "suites de API y Playwright E2E con sus criterios de verificación."
        ),
        expected_output=(
            "### HU-xxx\n"
            "- Automatizable: [Sí / Parcial / No]\n"
            "- Nivel: [API / Playwright UI / Ambos]\n"
            "- Tareas requeridas para Dev en tasks.md: [data-testid necesarios, contratos HTTP]\n"
            "- Tareas propuestas para QA en tasks.md:\n"
            "  * [ ] Task X.Y [Track: QA]: Test API desplegada (endpoints y schemas)\n"
            "  * [ ] Task X.Z [Track: QA]: Test E2E Playwright con selectores data-testid\n"
            "- Esfuerzo de automatización estimado: [Bajo / Medio / Alto]"
        ),
        agent=qa_auto,
        output_file=str(OUTPUT_DIR / "qa_evaluacion_automatizacion.md"),
    )

    t_consolida_qa = Task(
        description=(
            f"Paquete de refinamiento: {paquete[:2500]}\n\n"
            "Consolida los análisis de riesgos, testabilidad y automatización en la respuesta "
            "oficial del Team QA hacia el Team PO y Team Dev. Asegúrate de incluir:\n"
            "1. Desafíos y ajustes obligatorios a specs.md (escenarios Gherkin adicionales).\n"
            "2. Requisitos y tareas que deben quedar en tasks.md para Dev y para QA.\n"
            "3. Veredicto de testabilidad y preguntas que requieren decisión del PO."
        ),
        expected_output=(
            "# Respuestas Oficiales del Team QA (Refinamiento SDD)\n\n"
            "## HU-xxx\n"
            "### 1. Auditoría de Especificaciones (specs.md)\n"
            "- ¿Criterios testables?: [Sí / No + motivo]\n"
            "- Escenarios Gherkin adicionales recomendados: [Dado/Cuando/Entonces]\n"
            "### 2. Aportes al Desglose de Tareas (tasks.md)\n"
            "- Requisitos para Dev: [selectores data-testid, endpoints requeridos]\n"
            "- Tareas de automatización asignadas a QA: [Task X.Y con criterios de éxito]\n"
            "### 3. Riesgos y Testabilidad\n"
            "- Riesgo de regresión: [Alto / Medio / Bajo + módulo]\n"
            "- Datos mock y entorno requeridos: [lista]\n"
            "- Preguntas / Decisiones pendientes para el PO: [lista o 'Ninguna']"
        ),
        agent=lider_qa,
        context=[t_riesgos, t_testabilidad, t_eval_auto],
        output_file=str(OUTPUT_DIR / "respuestas_qa.md"),
    )

    crew = Crew(
        agents=[qa_semi, qa_jun, qa_auto, lider_qa],
        tasks=[t_riesgos, t_testabilidad, t_eval_auto, t_consolida_qa],
        process=Process.sequential,
        verbose=True,
    )

    try:
        import console_ui
        with console_ui.animacion_pensando("Team QA evaluando riesgos y cobertura...", "Líder de QA, Automation y Manual QAs"):
            result = crew.kickoff()
    except Exception:
        result = crew.kickoff()
    persistir_salidas_crew(crew, result)
    contenido = leer_archivo(OUTPUT_DIR / "respuestas_qa.md")
    guardar_intercambio("respuestas_qa.md", contenido)
    print("\n✅ Refinamiento de QA completado — respuesta guardada en intercambio/respuestas_qa.md")
    return result


# ═══════════════════════════════════════════════════════════════════════════
# TEAM QA — Fase 2: Preparar Pruebas (Plan + Casos + Estrategia Auto)
# ═══════════════════════════════════════════════════════════════════════════

def fase_qa_preparar():
    """Genera el plan de pruebas por riesgo, diseña casos y estrategia de automatización."""
    print("\n" + "=" * 70)
    print("🧪 TEAM QA — FASE 2: PREPARAR PRUEBAS")
    print("=" * 70)

    from crewai import Task, Crew, Process

    lider_qa = crear_agente("lider_qa")
    qa_semi = crear_agente("qa_semi_senior")
    qa_jun = crear_agente("qa_junior")
    qa_auto = crear_agente("qa_automatizacion")

    historias = leer_archivo(OUTPUT_DIR / "historias_refinadas.md",
                             leer_archivo(OUTPUT_DIR / "historias_de_usuario.md"))
    backlog = leer_archivo(OUTPUT_DIR / "backlog_refinado.md",
                           leer_archivo(OUTPUT_DIR / "backlog_final.md"))
    respuestas_qa = leer_archivo(INTERCAMBIO_DIR / "respuestas_qa.md")
    entrega_dev = leer_archivo(OUTPUT_DIR / "entrega_qa.md",
                               leer_archivo(INTERCAMBIO_DIR / "entrega_a_qa.md"))
    gate_dev = leer_archivo(OUTPUT_DIR / "gate_calidad_dev.md")

    # ── Task 0: Auditoría Grey-Box de Unit Tests y Mutation Testing (QA Semi Senior) ──
    t_auditoria_unitest = Task(
        description=(
            f"Entrega y código de Desarrollo: {entrega_dev[:2000]}\n"
            f"Gate de Calidad Dev: {gate_dev[:1500]}\n"
            f"Historias y Criterios Gherkin: {historias[:2500]}\n\n"
            "Como QA con dominio técnico de código y del negocio, audita rigurosamente las pruebas unitarias "
            "escritas por los desarrolladores antes de certificar la calidad.\n\n"
            "Aplica los estándares de Gentle-AI (Sección 5):\n"
            "1. Patrón AAA: Verifica que cada unit test esté estructurado explícitamente en Arrange, Act y Assert.\n"
            "2. Detección de Test Padding / Pruebas Basura: Identifica pruebas sin asserts reales, "
            "asserts triviales (ej. assert True), o pruebas sobre-mockeadas que no verifiquen reglas de negocio.\n"
            "3. Calificación por Mutation Testing (Mutation Score conceptual):\n"
            "   - Plantea mutaciones lógicas a las reglas de negocio (inversión de condicionales, límites < vs <=, omisiones).\n"
            "   - Evalúa: ¿la prueba unitaria actual mataría al mutante o pasaría en verde?\n"
            "   - Si la prueba pasa en verde con el código roto, clasifícala como 'MUTANTE SOBREVIVIENTE (Test sin valor)'.\n\n"
            "Emite veredicto: 'Aprobado: Unit Tests de Alto Valor' o 'Devuelto: Pruebas Basura/Cosméticas Detectadas' con correcciones obligatorias."
        ),
        expected_output=(
            "# Reporte de Auditoría de Unit Tests y Mutation Testing (QA Semi Senior)\n"
            "## 1. Veredicto Final: [Aprobado: Unit Tests de Alto Valor / Devuelto: Pruebas Basura Detectadas]\n"
            "## 2. Resumen de Calidad (Total pruebas evaluadas, % Cumplimiento AAA, Mutation Score estimado %)\n"
            "## 3. Matriz de Auditoría por Prueba:\n"
            "   Tabla: Test ID | Módulo/Caso | Patrón AAA (Sí/No) | Aserciones de Valor (Sí/No) | Mutante Evaluado | ¿Mata al Mutante? | Veredicto\n"
            "## 4. Pruebas Basura Detectadas (detalle y motivo del rechazo)\n"
            "## 5. Correcciones Obligatorias para Desarrollo"
        ),
        agent=qa_semi,
        output_file=str(OUTPUT_DIR / "qa_auditoria_unitests.md"),
    )

    t_plan = Task(
        description=(
            f"Historias refinadas: {historias[:2500]}\n"
            f"Backlog: {backlog[:2000]}\n"
            f"Respuestas de QA: {respuestas_qa[:2000]}\n\n"
            "Diseña el Plan de Pruebas con enfoque en riesgo. El plan debe cubrir OBLIGATORIAMENTE dos vías de prueba:\n"
            "1. Pruebas de API Desplegada: Validación de contratos REST, códigos HTTP (200, 201, 400, 401, 403, 404, 422, 500), payload, esquemas y límites.\n"
            "2. Pruebas con Playwright: Validación E2E de flujos de usuario sobre la UI web con selectores estables data-testid.\n"
            "Cada escenario Gherkin debe tener al menos un ítem de prueba (TP-01, TP-02...). "
            "Asigna: complejidad Básica (humo, camino feliz, validaciones simples) al QA Junior; "
            "Compleja (negativos, límites, integración, exploratorios, regresión y riesgo Alto) al QA Semi Senior. "
            "Marca 'Automatizar = Sí' para ítems deterministas y repetitivos. Define criterios de entrada y salida."
        ),
        expected_output=(
            "# Plan de pruebas\n"
            "## Alcance (tabla: Orden | HU | Título)\n"
            "## Estrategia por vía de prueba:\n"
            "### 1. Pruebas sobre la API Desplegada\n"
            "### 2. Pruebas E2E con Playwright\n"
            "## Riesgos priorizados\n"
            "## Criterios de entrada y salida\n"
            "## Entorno y datos necesarios (API_BASE_URL y FRONTEND_BASE_URL)\n"
            "## Necesidades hacia Desarrollo e Infraestructura (data-testid y endpoints)\n"
            "## Plantilla de caso de prueba\n"
            "## Ítems de prueba (Tabla: ID | HU | Vía (API / Playwright UI) | Escenario | Tipo | Prioridad | Complejidad | Diseña | Automatizar | Revisor)\n"
            "## Carga por agente"
        ),
        agent=lider_qa,
        context=[t_auditoria_unitest],
        output_file=str(OUTPUT_DIR / "plan_pruebas.md"),
    )

    t_casos_semi = Task(
        description=(
            f"Historias: {historias[:2500]}\n\n"
            "Diseña SOLO los casos de los ítems asignados a QA Semi Senior en el plan. "
            "Para los ítems de API: valida status HTTP, errores (4xx/5xx), esquemas y valores límite. "
            "Para los ítems de Playwright UI: valida flujos complejos, estados de carga y feedback de error en el DOM. "
            "Aplica técnicas de diseño (valores límite, particiones, tablas de decisión) y nómbralas. "
            "Resultados esperados medibles con valores exactos. Si no tienes ítems, responde: Sin asignaciones."
        ),
        expected_output=(
            "### CP-xxx (TP-xx)\n"
            "- Historia | Vía (API / Playwright UI) | Escenario Gherkin\n"
            "- Tipo | Prioridad | Técnica de diseño\n"
            "- Precondiciones y datos\n"
            "- Pasos numerados\n"
            "- Resultado esperado medible\n"
            "- Automatizar: [Sí/No]"
        ),
        agent=qa_semi,
        context=[t_plan],
        output_file=str(OUTPUT_DIR / "casos_semi_senior.md"),
    )

    t_casos_jun = Task(
        description=(
            f"Historias: {historias[:2500]}\n\n"
            "Diseña SOLO los casos de los ítems asignados a QA Junior en el plan. "
            "Cubre caminos felices y validaciones simples tanto para API (smoke HTTP 200/201) "
            "como para Playwright UI (carga de página, envío con datos válidos). "
            "Sigue exactamente la plantilla. Si algo no está claro, regístralo como 'Duda para el Semi Senior'. "
            "Si no tienes ítems, responde: Sin asignaciones."
        ),
        expected_output=(
            "### CP-xxx (TP-xx)\n"
            "- Historia | Vía (API / Playwright UI) | Escenario Gherkin\n"
            "- Tipo | Prioridad | Técnica\n"
            "- Precondiciones y datos\n"
            "- Pasos numerados\n"
            "- Resultado esperado medible\n"
            "- Automatizar: [Sí/No]\n"
            "- Dudas para el Semi Senior: [lista o 'Ninguna']"
        ),
        agent=qa_jun,
        context=[t_plan, t_casos_semi],
        output_file=str(OUTPUT_DIR / "casos_junior.md"),
    )

    t_revision = Task(
        description=(
            "Revisa los casos del QA Junior contra el plan. Para cada caso evalúa: "
            "(a) trazable a Gherkin, (b) reproducible, (c) medible, (d) precondiciones y datos, (e) plantilla. "
            "Veredicto: Aprobado o Devuelto (indicando corrección exacta). Responde las dudas del Junior."
        ),
        expected_output=(
            "Tabla: Caso | Vía | Trazable | Reproducible | Medible | Datos | Plantilla | Veredicto | Corrección\n"
            "## Respuestas a dudas\n"
            "## Resumen: X de Y casos aprobados"
        ),
        agent=qa_semi,
        context=[t_plan, t_casos_semi, t_casos_jun],
        output_file=str(OUTPUT_DIR / "revision_casos.md"),
    )

    t_estrategia_auto = Task(
        description=(
            "Trabaja SOLO con los ítems marcados 'Automatizar = Sí' en el plan. "
            "Define la estrategia de automatización en DOS SUITES OBLIGATORIAS:\n"
            "1. Suite API: Pruebas de integración sobre la API desplegada (endpoints REST, headers, status codes) "
            "utilizando Playwright API (`request`) o biblioteca de pruebas contra API_BASE_URL.\n"
            "2. Suite Playwright UI: Pruebas E2E en navegador sobre la interfaz web con Playwright "
            "utilizando exclusivamente selectores `data-testid` contra FRONTEND_BASE_URL.\n"
            "Estructura de carpetas, manejo de datos, cero secretos en código y necesidades hacia Desarrollo."
        ),
        expected_output=(
            "# Estrategia de automatización\n"
            "## 1. Suite de Pruebas de API Desplegada (Herramientas, estructura, variables de entorno)\n"
            "## 2. Suite E2E con Playwright (Selectores data-testid, flujos soportados, variables de entorno)\n"
            "## Ítems a automatizar (tabla: TP | Vía (API / Playwright UI) | Razón)\n"
            "## Convenciones y manejo de datos\n"
            "## Integración CI/CD y comandos de ejecución\n"
            "## Necesidades hacia Desarrollo y DevOps"
        ),
        agent=qa_auto,
        context=[t_plan],
        output_file=str(OUTPUT_DIR / "estrategia_automatizacion.md"),
    )

    tasks_qa = [t_plan, t_casos_semi, t_casos_jun, t_revision, t_estrategia_auto]
    if entrega_dev != "SIN DATO":
        tasks_qa.insert(0, t_auditoria_unitest)

    crew = Crew(
        agents=[lider_qa, qa_semi, qa_jun, qa_auto],
        tasks=tasks_qa,
        process=Process.sequential,
        verbose=True,
    )

    try:
        import console_ui
        with console_ui.animacion_pensando("Team QA diseñando Plan de Pruebas y Casos...", "Líder de QA, Semi Senior, Junior y Automation"):
            result = crew.kickoff()
    except Exception:
        result = crew.kickoff()

    persistir_salidas_crew(crew, result)
    contenido_plan = leer_archivo(OUTPUT_DIR / "plan_pruebas.md")
    guardar_intercambio("plan_pruebas.md", contenido_plan)

    try:
        import console_ui
        console_ui.render_banner("PREPARACIÓN DE PRUEBAS COMPLETADA", "Plan de Pruebas, Casos por Riesgo y Estrategia Auto", icono="🧪")
        archivos = [
            buscar_archivo("plan_pruebas.md"),
            buscar_archivo("revision_casos.md"),
            buscar_archivo("estrategia_automatizacion.md"),
            buscar_archivo("casos_semi_senior.md"),
            buscar_archivo("casos_junior.md"),
            buscar_archivo("bundle.md"),
        ]
        console_ui.render_archivos_guardados(archivos)
        console_ui.console.print("\n[bold color(42)]✓ Casos de prueba y estrategia de calidad listos en docs/qa/[/]")
        console_ui.console.print("[dim color(245)]Siguiente paso: [bold color(75)]ab dev implementar[/bold color(75)] (Construir código fuente del software)[/]\n")
    except Exception:
        print("\n✅ Preparación de pruebas completada — plan guardado en intercambio/plan_pruebas.md")

    return result


# ═══════════════════════════════════════════════════════════════════════════
# TEAM QA — Fase 3: Preparar Ejecución (Hoja de ejecución + Scripts)
# ═══════════════════════════════════════════════════════════════════════════

def fase_qa_preparar_ejecucion():
    """Genera la hoja de ejecución tras recibir la entrega de Desarrollo y genera scripts."""
    print("\n" + "=" * 70)
    print("🧪 TEAM QA — FASE 3: PREPARAR EJECUCIÓN")
    print("=" * 70)

    from crewai import Task, Crew, Process

    lider_qa = crear_agente("lider_qa")
    qa_auto = crear_agente("qa_automatizacion")

    entrega = leer_archivo(INTERCAMBIO_DIR / "entrega_a_qa.md",
                           leer_archivo(OUTPUT_DIR / "entrega_qa.md"))
    plan = leer_archivo(OUTPUT_DIR / "plan_pruebas.md")
    revision = leer_archivo(OUTPUT_DIR / "revision_casos.md")
    estrategia = leer_archivo(OUTPUT_DIR / "estrategia_automatizacion.md")
    casos_semi = leer_archivo(OUTPUT_DIR / "casos_semi_senior.md")
    casos_jun = leer_archivo(OUTPUT_DIR / "casos_junior.md")

    t_hoja = Task(
        description=(
            f"Entrega de Desarrollo: {entrega[:2500]}\n"
            f"Plan de pruebas: {plan[:2000]}\n"
            f"Revisión de casos: {revision[:1500]}\n\n"
            "Verifica los criterios de entrada: versión, historias incluidas, pasos de despliegue, URLs/endpoints. "
            "Veredicto: Aceptada o Rechazada. Si es Aceptada, arma la hoja de ejecución clasificando cada caso "
            "en su vía (API Desplegada o Playwright UI), priorizando humo y luego prioridad Alta a Baja. "
            "Excluye casos devueltos. Asigna el modo (Manual o Automatizado) y quién registra."
        ),
        expected_output=(
            "# Hoja de ejecución\n"
            "## Veredicto de la entrega: Aceptada o Rechazada (+ faltantes si aplica)\n"
            "## Versión probada y URLs de entorno\n"
            "## Hoja (Tabla: Orden | CP | HU | Vía (API / Playwright UI) | Prioridad | Modo | Registra)\n"
            "## Casos excluidos"
        ),
        agent=lider_qa,
        output_file=str(OUTPUT_DIR / "hoja_ejecucion.md"),
    )

    t_auto = Task(
        description=(
            f"Entrega de Desarrollo: {entrega[:2000]}\n"
            f"Estrategia de automatización: {estrategia[:2000]}\n"
            f"Casos Semi: {casos_semi[:2000]}\n"
            f"Casos Junior: {casos_jun[:2000]}\n\n"
            "Escribe los scripts de automatización para los ítems marcados 'Automatizar = Sí' en la hoja de ejecución, "
            "generando las dos suites completas en inglés técnico:\n"
            "1. Suite API (tests/api/...): Scripts que atacan la API desplegada usando variables de entorno (API_BASE_URL), "
            "validando endpoints, status codes, headers y esquemas JSON.\n"
            "2. Suite Playwright UI (tests/e2e/...): Scripts Playwright para navegador usando selectores data-testid "
            "contra FRONTEND_BASE_URL, con esperas por condición.\n"
            "Código completo y limpio por archivo, sin secretos. Comandos de ejecución para CI/CD. Estado: 'Sin ejecutar'."
        ),
        expected_output=(
            "## 1. Suite de Pruebas de API Desplegada\n"
            "Archivos con su ruta y código completo en inglés.\n"
            "## 2. Suite E2E con Playwright\n"
            "Archivos con su ruta y código completo en inglés.\n"
            "## Mapeo caso a script\n"
            "## Comandos de ejecución para el pipeline\n"
            "## Variables de entorno necesarias\n"
            "## Estado: Sin ejecutar"
        ),
        agent=qa_auto,
        context=[t_hoja],
        output_file=str(OUTPUT_DIR / "scripts_automatizacion.md"),
    )

    crew = Crew(
        agents=[lider_qa, qa_auto],
        tasks=[t_hoja, t_auto],
        process=Process.sequential,
        verbose=True,
    )

    try:
        import console_ui
        with console_ui.animacion_pensando("Team QA preparando scripts de automatización...", "Líder de QA y QA Automation generando Playwright y API tests"):
            result = crew.kickoff()
    except Exception:
        result = crew.kickoff()

    persistir_salidas_crew(crew, result)

    # Consolidate all phase outputs into bundle.md
    _bundle_parts = []
    for _t in result.tasks_output:
        if _t.raw:
            _bundle_parts.append(f"## {_t.name}\n\n{_t.raw}\n")
    _bundle = "\n---\n\n".join(_bundle_parts)
    guardar_salida("bundle_qa.md", _bundle)

    bundle_actual = leer_archivo(OUTPUT_DIR / "bundle.md", "")
    if bundle_actual and "# TEAM QA PREPARACIÓN EJECUCIÓN" not in bundle_actual:
        _bundle_total = bundle_actual.strip() + "\n\n---\n\n# TEAM QA PREPARACIÓN EJECUCIÓN\n\n" + _bundle
    else:
        _bundle_total = "# TEAM QA PREPARACIÓN EJECUCIÓN\n\n" + _bundle
    guardar_salida("bundle.md", _bundle_total)

    # Materializar scripts de pruebas (tests/api/, tests/e2e/, etc.)
    try:
        import code_extractor
        archivos_codigo = code_extractor.materializar_codigo(OUTPUT_DIR)
        code_extractor.render_reporte_extraccion(archivos_codigo)
    except Exception as _e_extract:
        print(f"  ⚠ Materialización de scripts QA: {_e_extract}")

    try:
        import console_ui
        console_ui.render_banner("PREPARACIÓN DE EJECUCIÓN LISTA", "Hoja de Ejecución y Suites de Automatización", icono="⚡")
        archivos = [
            buscar_archivo("hoja_ejecucion.md"),
            buscar_archivo("scripts_automatizacion.md"),
            buscar_archivo("bundle.md"),
        ]
        console_ui.render_archivos_guardados(archivos)
        console_ui.console.print("\n[bold color(42)]✓ Scripts de Playwright y pruebas de API generados con éxito[/]")
        console_ui.console.print("[dim color(245)]Siguiente paso: [bold color(75)]ab qa validar[/bold color(75)] (Certificar calidad y emitir dictamen de release)[/]\n")
    except Exception:
        print("\n✅ Hoja de ejecución y scripts preparados.")

    return result


# ═══════════════════════════════════════════════════════════════════════════
# TEAM QA — Fase 4: Validar (Registro + Defectos + Dictamen de Calidad)
# ═══════════════════════════════════════════════════════════════════════════

def fase_qa_validar():
    """Analiza resultados reales de ejecución, reporta defectos y emite el dictamen de calidad."""
    print("\n" + "=" * 70)
    print("🧪 TEAM QA — FASE 4: VALIDAR RESULTADOS")
    print("=" * 70)

    from crewai import Task, Crew, Process

    lider_qa = crear_agente("lider_qa")
    qa_semi = crear_agente("qa_semi_senior")
    qa_jun = crear_agente("qa_junior")

    hoja = leer_archivo(OUTPUT_DIR / "hoja_ejecucion.md")
    resultados = leer_archivo(INTERCAMBIO_DIR / "resultados_ejecucion.md")
    plan = leer_archivo(OUTPUT_DIR / "plan_pruebas.md")

    t_reg_jun = Task(
        description=(
            f"Resultados de ejecución: {resultados[:3000]}\n"
            f"Hoja de ejecución: {hoja[:2000]}\n\n"
            "Registra SOLO los resultados de los casos asignados a QA Junior. "
            "Estados: Pasó, Falló, Bloqueado o No ejecutado. NUNCA inventes resultados. "
            "Cita la evidencia tal como aparece."
        ),
        expected_output=(
            "Tabla: Caso | HU | Estado | Evidencia | Observaciones\n"
            "## Resumen: X de Y casos ejecutados"
        ),
        agent=qa_jun,
        output_file=str(OUTPUT_DIR / "ejecucion_junior.md"),
    )

    t_analisis_defectos = Task(
        description=(
            f"Resultados de ejecución: {resultados[:3000]}\n"
            f"Hoja de ejecución: {hoja[:2000]}\n\n"
            "1. Registra los casos asignados a Semi Senior y automatizados.\n"
            "2. Por cada caso Falló o Bloqueado (del Junior, tuyo o automatizado), redacta el reporte "
            "de defecto con BUG-001, BUG-002... Incluye pasos reproducibles, esperado, obtenido y evidencia.\n"
            "3. Clasifica severidad (Crítica, Alta, Media, Baja). Si es requisito ambiguo, 'Pregunta para el PO'."
        ),
        expected_output=(
            "## Registro de ejecución (Semi Senior y automatizados)\n"
            "Tabla: Caso | HU | Estado | Evidencia | Observaciones\n"
            "## Defectos (BUG-001... con HU, Gherkin, Severidad, Pasos, Esperado, Obtenido, Evidencia, Versión)\n"
            "## Preguntas para el PO\n"
            "## Cobertura de ejecución"
        ),
        agent=qa_semi,
        context=[t_reg_jun],
        output_file=str(OUTPUT_DIR / "resultados_y_defectos.md"),
    )

    t_reporte_lider = Task(
        description=(
            "Audita los defectos redactados. Aprueba solo los que tengan pasos reproducibles, "
            "esperado/obtenido claros, evidencia y severidad justificada. "
            "Si no hay defectos aprobados, responde exactamente: SIN REPORTE."
        ),
        expected_output=(
            "Solo los defectos aprobados en formato ## BUG-00x o la frase 'SIN REPORTE'."
        ),
        agent=lider_qa,
        context=[t_analisis_defectos],
        output_file=str(OUTPUT_DIR / "reporte_qa.md"),
    )

    t_dictamen = Task(
        description=(
            f"Plan de pruebas y criterios de salida: {plan[:2000]}\n\n"
            "Emite el dictamen de calidad. Veredicto general: 'Apto para aceptación del PO' (si cumple criterios), "
            "'No apto' (si falló o defectos críticos/altos abiertos), o 'Pendiente de ejecución'. "
            "Detalla resultado por historia y estado de criterios de salida."
        ),
        expected_output=(
            "# Dictamen de calidad\n"
            "## Veredicto general: [Apto / No apto / Pendiente de ejecución]\n"
            "## Resultado por historia (Tabla: HU | Ejecutados | Pasaron | Fallaron | Defectos | Veredicto)\n"
            "## Criterios de salida (Tabla: Criterio | Meta | Resultado | Cumple)\n"
            "## Defectos retenidos y motivo\n"
            "## Riesgos residuales"
        ),
        agent=lider_qa,
        context=[t_reg_jun, t_analisis_defectos, t_reporte_lider],
        output_file=str(OUTPUT_DIR / "dictamen_qa.md"),
    )

    crew = Crew(
        agents=[qa_jun, qa_semi, lider_qa],
        tasks=[t_reg_jun, t_analisis_defectos, t_reporte_lider, t_dictamen],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    persistir_salidas_crew(crew, result)
    rep = leer_archivo(OUTPUT_DIR / "reporte_qa.md")
    guardar_intercambio("reporte_qa.md", rep)
    dic = leer_archivo(OUTPUT_DIR / "dictamen_qa.md")
    guardar_intercambio("dictamen_qa.md", dic)
    print("\n✅ Validación de calidad completada — reporte y dictamen en intercambio/")
    return result


# ═══════════════════════════════════════════════════════════════════════════
# TEAM QA — Fase 5: Reverificar (Repruebas tras correcciones de Desarrollo)
# ═══════════════════════════════════════════════════════════════════════════

def fase_qa_reverificar():
    """Verifica la reentrega de correcciones y emite el dictamen final de calidad."""
    print("\n" + "=" * 70)
    print("🧪 TEAM QA — FASE 5: REVERIFICACIÓN")
    print("=" * 70)

    from crewai import Task, Crew, Process

    lider_qa = crear_agente("lider_qa")
    qa_semi = crear_agente("qa_semi_senior")
    qa_jun = crear_agente("qa_junior")
    qa_auto = crear_agente("qa_automatizacion")

    reentrega = leer_archivo(INTERCAMBIO_DIR / "reentrega_a_qa.md")
    reporte_previo = leer_archivo(OUTPUT_DIR / "reporte_qa.md")
    resultados_rev = leer_archivo(INTERCAMBIO_DIR / "resultados_reverificacion.md")

    t_plan_rev = Task(
        description=(
            f"Reentrega de Desarrollo: {reentrega[:2500]}\n"
            f"Reporte previo: {reporte_previo[:2000]}\n\n"
            "Arma la hoja de reverificación: para cada defecto corregido define reprueba, "
            "y para las historias afectadas define regresión. Asigna básico al Junior, "
            "complejo al Semi Senior, automatizado al QA Automatización."
        ),
        expected_output=(
            "# Hoja de reverificación\n"
            "## Veredicto de la reentrega: Aceptada o Rechazada\n"
            "## Nueva versión\n"
            "## Defectos por estado (Tabla: BUG | Severidad | Estado | Motivo)\n"
            "## Hoja de repruebas y regresión"
        ),
        agent=lider_qa,
        output_file=str(OUTPUT_DIR / "hoja_reverificacion.md"),
    )

    t_auto_reg = Task(
        description=(
            f"Reentrega de Desarrollo: {reentrega[:2000]}\n\n"
            "Para cada defecto corregido automatizable, escribe un script de regresión que "
            "reproduzca el fix y evite reaparición. Actualiza scripts afectados."
        ),
        expected_output=(
            "## Scripts nuevos y modificados\n"
            "## Mapeo defecto a script\n"
            "## Estado: Sin ejecutar"
        ),
        agent=qa_auto,
        context=[t_plan_rev],
        output_file=str(OUTPUT_DIR / "automatizacion_regresion.md"),
    )

    t_analisis_rev = Task(
        description=(
            f"Resultados de reverificación: {resultados_rev[:3000]}\n"
            f"Reporte previo: {reporte_previo[:2000]}\n\n"
            "Clasifica cada defecto: Cerrado (reprueba pasó), Reabierto (falló), o Sin verificar. "
            "Si la regresión detecta nuevos fallos, redacta nuevos BUGs. NUNCA inventes resultados."
        ),
        expected_output=(
            "## Estado de los defectos (Tabla: BUG | Estado | Evidencia)\n"
            "## Defectos reabiertos y nuevos (o 'Ninguno')\n"
            "## Registro de ejecución"
        ),
        agent=qa_semi,
        context=[t_plan_rev, t_auto_reg],
        output_file=str(OUTPUT_DIR / "analisis_reverificacion.md"),
    )

    t_dictamen_final = Task(
        description=(
            "Emite el dictamen final tras la reverificación. Veredicto: 'Apto para aceptación del PO' "
            "o 'No apto'. Resume defectos cerrados vs reabiertos o remanentes."
        ),
        expected_output=(
            "# Dictamen final de calidad\n"
            "## Veredicto general: [Apto / No apto]\n"
            "## Resumen de defectos: Cerrados, Reabiertos, Nuevos\n"
            "## Dictamen por historia\n"
            "## Riesgos residuales"
        ),
        agent=lider_qa,
        context=[t_plan_rev, t_analisis_rev],
        output_file=str(OUTPUT_DIR / "dictamen_final_qa.md"),
    )

    crew = Crew(
        agents=[lider_qa, qa_auto, qa_semi],
        tasks=[t_plan_rev, t_auto_reg, t_analisis_rev, t_dictamen_final],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    persistir_salidas_crew(crew, result)
    dic_final = leer_archivo(OUTPUT_DIR / "dictamen_final_qa.md")
    guardar_intercambio("dictamen_qa.md", dic_final)
    print("\n✅ Reverificación completada — dictamen final guardado en intercambio/dictamen_qa.md")
    return result


# ═══════════════════════════════════════════════════════════════════════════
# Pipeline completo
# ═══════════════════════════════════════════════════════════════════════════

def pipeline_completo(solicitud: str):
    """Ejecuta todas las fases en orden, con pausas lógicas."""
    fases = [
        ("PO — Definición", lambda: fase_po_definicion(solicitud)),
        ("PO — Preparar Refinamiento", fase_po_preparar),
    ]

    for nombre, fn in fases:
        print(f"\n{'▣' * 35}")
        print(f"  {nombre}")
        print(f"{'▣' * 35}")
        fn()

    print("\n" + "─" * 70)
    print("⏸️  Entregá el paquete de refinamiento a Dev, QA e Infra.")
    print("   Guardá sus respuestas en intercambio/ y ejecutá:")
    print("     python orchestrator.py po consolidar")
    print("     python orchestrator.py dev refinamiento")
    print("     python orchestrator.py dev disenar")
    print("     python orchestrator.py dev implementar")
    print("     python orchestrator.py dev corregir")
    print("─" * 70)


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

USO = """
Agent Builder — Phase-Based Orchestrator
=========================================

🚀 Flujo Rápido Recomendado (3 Pasos):
  Paso 1: ab idea "Mi idea de software"    — PRD + Historias de Usuario + Backlog inicial
  Paso 2: ab aceptar                       — Responder dudas/feedback del cliente y aprobar
  Paso 3: ab refinar                       — Pipeline autónomo: PO (prepara) ➔ Dev (estima) ➔ QA (audita) ➔ PO (consolida)
                                             Genera la propuesta técnica definitiva (tasks.md, arquitectura, backlog)

Uso granular por fases:
  python orchestrator.py po definicion "Mi idea de software" --project mi_app --profile openrouter
  python orchestrator.py po responder --project mi_app
  python orchestrator.py po preparar --project mi_app
  python orchestrator.py dev refinamiento --project mi_app
  python orchestrator.py qa refinamiento --project mi_app
  python orchestrator.py po consolidar --project mi_app
  python orchestrator.py dev disenar --project mi_app
  python orchestrator.py qa preparar --project mi_app
  python orchestrator.py qa preparar_ejecucion --project mi_app
  python orchestrator.py dev implementar --project mi_app
  python orchestrator.py dev extraer --project mi_app   # Materializar código fuente en disco (src/, tests/)
  python orchestrator.py qa validar --project mi_app
  python orchestrator.py dev corregir --project mi_app
  python orchestrator.py qa reverificar --project mi_app
  python orchestrator.py list

Opciones:
  --project <nombre>, -p  Aísla los artefactos en output/<nombre>/ y bundle.json
  --profile <perfil>, -m  Usa un perfil de modelos (local, openrouter, claude, openai)
"""


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h", "help"):
        print(USO)
        return

    # Extraer flags globales (--project y --profile)
    filtered_args = []
    i = 0
    while i < len(args):
        if args[i] in ("--project", "-p") and i + 1 < len(args):
            set_project(args[i + 1])
            i += 2
        elif args[i] in ("--profile", "-m") and i + 1 < len(args):
            set_profile(args[i + 1])
            i += 2
        else:
            filtered_args.append(args[i])
            i += 1
    args = filtered_args

    recuperar_desde_bundle_si_necesario()

    if not args or args[0].lower() in ("cli", "interactive", "ui"):
        import cli
        cli.main()
        return

    cmd = args[0].lower()

    if cmd in ("help", "--help", "-h"):
        print(USO)
        return

    if cmd == "list":
        print(f"\nAgentes disponibles (Perfil activo: {ACTIVE_PROFILE or 'default/.env'}):")
        for f in sorted(AGENTS_DIR.glob("*.jsonc")):
            cfg = load_agent_config(f.stem)
            try:
                from profiles import resolve_agent_llm
                llm_resolved = resolve_agent_llm(f.stem, ACTIVE_PROFILE)
            except Exception:
                llm_resolved = cfg.get("llm", "N/A")
            print(f"  {f.stem:<40} → {cfg['role']}  [{llm_resolved}]")
        return

    # ── Atajo Paso 1: Decir la idea ──
    if cmd in ("idea", "nueva", "nuevo", "iniciar", "crear"):
        solicitud = " ".join(args[1:]) if len(args) > 1 else "Solicitud de software no especificada"
        fase_po_definicion(solicitud)
        return

    # ── Atajo Paso 2: Aceptar / responder feedback antes de refinar ──
    if cmd in ("aceptar", "responder", "feedback", "aclarar", "corregir", "ajustar"):
        fb_arg = " ".join(args[1:]) if len(args) > 1 else None
        fase_po_responder(feedback_libre=fb_arg)
        return

    # ── Atajo Paso 3: Refinamiento técnico (autónomo o por rol) ──
    texto_cmd = " ".join(args).lower()
    if any(k in texto_cmd for k in ("refinamiento", "refinar", "hagamos el refinamiento", "preparar refinamiento")):
        if "dev" in texto_cmd:
            fase_dev_refinamiento()
            return
        elif "qa" in texto_cmd:
            fase_qa_refinamiento()
            return
        elif "consolidar" in texto_cmd:
            fase_po_consolidar()
            return
        elif "preparar" in texto_cmd:
            fase_po_preparar()
            return
        else:
            # Ejecuta el pipeline completo de refinamiento autónomo (PO -> Dev -> QA -> Consolidar)
            pipeline_refinamiento_completo()
            return

    # ── Atajo: Materializar / Extraer código fuente en disco físico ──
    if cmd in ("extraer", "scaffold", "materializar", "codigo", "code"):
        fase_dev_extraer()
        return

    if cmd == "po":
        sub = args[1] if len(args) > 1 else None
        if sub == "definicion":
            solicitud = args[2] if len(args) > 2 else "Solicitud de software no especificada"
            fase_po_definicion(solicitud)
        elif sub in ("responder", "feedback", "aclarar", "corregir", "ajustar"):
            fb_arg = " ".join(args[2:]) if len(args) > 2 else None
            fase_po_responder(feedback_libre=fb_arg)
        elif sub in ("preparar", "refinamiento", "refinar"):
            fase_po_preparar()
        elif sub == "consolidar":
            fase_po_consolidar()
        else:
            print(f"❌ Subcomando PO desconocido: {sub}")
            print("   Usá: definicion | responder | preparar | consolidar")
        return


    if cmd == "qa":
        sub = args[1] if len(args) > 1 else None
        if sub == "refinamiento":
            fase_qa_refinamiento()
        elif sub == "preparar":
            fase_qa_preparar()
        elif sub == "preparar_ejecucion":
            fase_qa_preparar_ejecucion()
        elif sub == "validar":
            fase_qa_validar()
        elif sub == "reverificar":
            fase_qa_reverificar()
        else:
            print(f"❌ Subcomando QA desconocido: {sub}")
            print("   Usá: refinamiento | preparar | preparar_ejecucion | validar | reverificar")
        return

    if cmd == "dev":
        sub = args[1] if len(args) > 1 else None
        if sub == "refinamiento":
            fase_dev_refinamiento()
        elif sub == "disenar":
            fase_dev_disenar()
        elif sub in ("implementar", "impl"):
            fase_dev_implementar()
        elif sub in ("extraer", "scaffold", "materializar", "codigo", "code"):
            fase_dev_extraer()
        elif sub == "corregir":
            fase_dev_corregir()
        else:
            print(f"❌ Subcomando DEV desconocido: {sub}")
            print("   Usá: refinamiento | disenar | implementar | extraer | corregir")
        return

    if cmd == "full":
        solicitud = args[1] if len(args) > 1 else "Solicitud de software no especificada"
        pipeline_completo(solicitud)
        return

    print(f"❌ Comando desconocido: {cmd}")
    print(USO)


if __name__ == "__main__":
    main()
