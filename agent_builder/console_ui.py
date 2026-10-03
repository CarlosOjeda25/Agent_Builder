#!/usr/bin/env python3
"""
Agent Builder — Console UI & Visual Presentation System
Inspirado en la interfaz moderna, minimalista y elegante de Claude Code:
- Bordes redondeados sutiles (box.ROUNDED)
- Paleta refinada (Acento Terracota/Coral ✻, Slate, Sky Cyan, Emerald)
- Indicadores y animaciones de 'Pensando...' (Spinners con Live status)
- Tarjetas de ejecución de agentes y menús interactivos limpios
"""

import sys
import re
import time
from pathlib import Path
from contextlib import contextmanager
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.theme import Theme
from rich import box

# Paleta y tema refinado estilo Claude Code
CLAUDE_THEME = Theme({
    "accent": "bold color(208)",       # Acento coral/terracota Claude
    "info": "bold color(75)",          # Sky cyan elegante
    "dim_text": "color(245)",          # Gris pizarra suave
    "muted_border": "color(239)",      # Borde sutil grafito
    "warning": "bold color(214)",      # Ámbar suave
    "danger": "bold color(203)",       # Coral rojizo
    "success": "bold color(42)",       # Verde esmeralda
})

console = Console(theme=CLAUDE_THEME)


# ── Animación y Estado de 'Pensando' (Estilo Claude Code) ─────────────────────

@contextmanager
def animacion_pensando(mensaje: str = "Pensando...", detalle: str = "analizando con agentes"):
    """Muestra un spinner animado elegante estilo Claude Code ('Thinking...') mientras los agentes procesan."""
    texto_estado = (
        f"[bold color(208)]✻[/] [bold white]{mensaje}[/] "
        f"[color(245)]·[/] [dim color(245)]{detalle}[/]"
    )
    with console.status(
        texto_estado,
        spinner="dots",
        spinner_style="bold color(208)",
    ) as status:
        yield status


def render_agent_step(agente: str, accion: str, estado: str = "done"):
    """Muestra un paso atómico de agente estilo checklist de Claude Code."""
    if estado == "done":
        console.print(f"  [bold color(42)]✓[/] [bold white]{agente}[/] [dim color(245)]— {accion}[/]")
    elif estado == "running":
        console.print(f"  [bold color(208)]✻[/] [bold white]{agente}[/] [color(75)]{accion}...[/]")
    elif estado == "warn":
        console.print(f"  [bold color(214)]![/] [bold white]{agente}[/] [yellow]{accion}[/]")
    else:
        console.print(f"  [dim]•[/] [white]{agente}[/] [dim]{accion}[/]")


# ── Banners y Cabeceras Modernas ─────────────────────────────────────────────

def render_banner(titulo: str, subtitulo: str = "", icono: str = "✻"):
    """Muestra un encabezado minimalista y elegante con bordes redondeados."""
    grid = Table.grid(expand=True)
    grid.add_column(justify="left", ratio=1)
    grid.add_row(f"[bold color(208)]{icono}[/]  [bold white]{titulo.upper()}[/]")
    if subtitulo:
        grid.add_row(f"   [dim color(245)]{subtitulo}[/]")

    console.print()
    console.print(Panel(
        grid,
        border_style="color(239)",
        box=box.ROUNDED,
        padding=(0, 2),
    ))
    console.print()


def get_decision_badge(texto: str) -> Text:
    """Extrae y formatea el estado de la decisión del Product Owner con insignias estilo Claude."""
    t_lower = texto.lower()
    if "aceptado con reservas" in t_lower:
        return Text("● ACEPTADO CON RESERVAS", style="bold color(214)")
    elif "aceptado" in t_lower and "devuelto" not in t_lower:
        return Text("● ACEPTADO", style="bold color(42)")
    elif "devuelto" in t_lower:
        return Text("● DEVUELTO (Requiere aclaración)", style="bold color(203)")
    return Text("○ EN EVALUACIÓN", style="dim color(245)")


def render_decision_panel(decision_text: str, resumen_md: str = ""):
    """Renderiza el veredicto del PO en una tarjeta compacta y moderna."""
    badge = get_decision_badge(decision_text)

    grid = Table.grid(expand=True)
    grid.add_column(ratio=1)
    grid.add_row(Text("Dictamen del Product Owner:", style="dim color(245)"))
    grid.add_row(badge)

    border_color = "color(203)" if "DEVUELTO" in badge.plain else ("color(214)" if "RESERVAS" in badge.plain else "color(42)")

    console.print(Panel(
        grid,
        title="[bold white]DECISIÓN DE FASE[/]",
        border_style=border_color,
        box=box.ROUNDED,
        padding=(1, 2),
    ))


def render_markdown_content(contenido: str, titulo: str = "Detalle del Documento"):
    """Renderiza contenido markdown con tipografía cuidada y bordes sutiles."""
    md = Markdown(contenido)
    console.print(Panel(
        md,
        title=f"[bold color(75)]{titulo}[/]",
        border_style="color(239)",
        box=box.ROUNDED,
        padding=(1, 2),
    ))


# ── Extracción y Análisis de Preguntas ────────────────────────────────────────

def extraer_preguntas_pendientes(texto: str) -> list[str]:
    """Extrae las preguntas abiertas que quedaron marcadas como pendientes."""
    preguntas = []
    lineas = texto.splitlines()
    i = 0
    while i < len(lineas):
        linea = lineas[i].strip()
        if "¿" in linea and "?" in linea:
            inicio = linea.find("¿")
            fin = linea.rfind("?") + 1
            pregunta = linea[inicio:fin].strip()
            if len(pregunta) > 10:
                preguntas.append(pregunta)
        elif "pendiente de confirmación" in linea.lower() and i > 0:
            prev = lineas[i - 1].strip().lstrip("- *").strip()
            if prev.startswith("¿") or prev.endswith("?"):
                preguntas.append(prev)
        i += 1

    vistas = set()
    unicas = []
    for p in preguntas:
        if p not in vistas:
            vistas.add(p)
            unicas.append(p)
    return unicas


def render_preguntas_pendientes(preguntas: list[str]):
    """Muestra una lista estilizada de preguntas abiertas pendientes."""
    if not preguntas:
        return

    table = Table(
        show_header=True,
        header_style="bold color(214)",
        expand=True,
        box=box.ROUNDED,
        border_style="color(239)",
    )
    table.add_column("#", width=4, justify="center", style="bold color(214)")
    table.add_column("Pregunta Abierta / Definición Necesaria", style="white")

    for idx, p in enumerate(preguntas, 1):
        table.add_row(str(idx), f"[color(214)]{p}[/]")

    panel = Panel(
        table,
        title="[bold color(214)]✻ PREGUNTAS ABIERTAS PENDIENTES[/]",
        subtitle="[dim color(245)]El equipo necesita estas definiciones para cerrar el alcance[/]",
        border_style="color(214)",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print(panel)


def interactuar_preguntas_cliente(preguntas: list[str]) -> dict[str, str]:
    """Solicita interactivamente al usuario responder cada pregunta con prompt estilo Claude."""
    console.print("\n[bold color(208)]✻ Respuestas del Cliente (Human-in-the-Loop):[/]")
    console.print("[dim color(245)]Ingresá tu respuesta para cada punto. Podés escribir con tus palabras naturales.[/]\n")

    respuestas = {}
    for idx, p in enumerate(preguntas, 1):
        console.print(f"[bold color(214)]╭─ Pregunta {idx}/{len(preguntas)}[/]")
        console.print(f"[white]│  {p}[/]")
        resp = Prompt.ask("[bold color(208)]╰─❯ Tu respuesta[/]")
        while not resp.strip():
            resp = Prompt.ask("[yellow]╰─❯ Ingresá una respuesta válida[/]")
        respuestas[p] = resp.strip()
        console.print()

    return respuestas


# ── Renderizado de Archivos Guardados ─────────────────────────────────────────

def render_archivos_guardados(archivos: list[Path]):
    """Muestra una tabla elegante y limpia con los archivos generados en el proyecto."""
    table = Table(
        show_header=True,
        header_style="bold color(75)",
        box=box.ROUNDED,
        border_style="color(239)",
        expand=True,
    )
    table.add_column("Entregable Generado", style="bold white")
    table.add_column("Tamaño", justify="right", style="dim color(245)")
    table.add_column("Ubicación en tu Proyecto", style="color(75)")

    for path in archivos:
        target = Path(path)
        if not target.exists() and target.parent.exists():
            matches = list(target.parent.rglob(target.name))
            if matches:
                target = matches[0]

        if target.exists():
            size_kb = f"{target.stat().st_size / 1024:.1f} KB"
            ubicacion = str(target.parent.name)
            ubicacion_str = f"docs/{ubicacion}" if ubicacion not in ("docs", "workspace") else "docs"
            table.add_row(f"[color(208)]📄[/] {target.name}", size_kb, ubicacion_str)

    console.print(Panel(
        table,
        title="[bold color(42)]✻ ARTEFACTOS GENERADOS[/]",
        border_style="color(239)",
        box=box.ROUNDED,
    ))


# ── Resumen Ejecutivo & Validación de Propuesta (Claude Code Style) ───────────

def extraer_seccion_markdown(texto: str, encabezados: list[str], max_lineas: int = 15) -> str:
    """Extrae líneas correspondientes a una sección markdown dado uno o varios títulos posibles."""
    if not texto:
        return ""
    lineas = texto.splitlines()
    capturando = False
    resultado = []
    encabezados_lower = [e.lower() for e in encabezados]

    for l in lineas:
        l_str = l.strip()
        if any(h in l_str.lower() for h in encabezados_lower) and l_str.startswith("#"):
            capturando = True
            continue
        elif capturando and l_str.startswith("#"):
            break
        elif capturando:
            if l_str:
                resultado.append(l_str)
            if len(resultado) >= max_lineas:
                break

    return "\n".join(resultado)


def render_resumen_ejecutivo_propuesta(prd_text: str, backlog_text: str):
    """Muestra un dashboard ejecutivo con los puntos clave y decisiones de la propuesta inicial."""
    render_banner("RESUMEN EJECUTIVO DE LA PROPUESTA INICIAL", "Validación y Aprobación de Alcance", icono="✻")

    badge = get_decision_badge(backlog_text)
    border_color = "color(203)" if "DEVUELTO" in badge.plain else ("color(214)" if "RESERVAS" in badge.plain else "color(42)")

    # 1. Objetivo Principal
    objetivo = extraer_seccion_markdown(prd_text, ["objetivo", "problema", "visión", "vision", "propósito"])
    if not objetivo:
        parrafos = [p.strip() for p in prd_text.split("\n\n") if len(p.strip()) > 30 and not p.strip().startswith("#")]
        objetivo = parrafos[0] if parrafos else "Definición y alcance del sistema estructurados en PRD."

    # 2. Alcance y Funcionalidades
    alcance = extraer_seccion_markdown(prd_text, ["funcionalidades", "alcance", "core", "moscow", "must"])
    if not alcance:
        alcance = extraer_seccion_markdown(backlog_text, ["backlog priorizado", "historias", "prioridad"])

    # 3. Decisiones Clave y Supuestos
    decisiones = extraer_seccion_markdown(backlog_text, ["decisiones", "respuestas", "supuestos", "riesgos"])
    if not decisiones:
        decisiones = extraer_seccion_markdown(prd_text, ["decisiones", "restricciones", "supuestos"])
    if not decisiones:
        decisiones = "Alcance estándar definido sin restricciones bloqueantes."

    table = Table(
        show_header=True,
        header_style="bold color(75)",
        box=box.ROUNDED,
        border_style="color(239)",
        expand=True,
    )
    table.add_column("Aspecto Clave", width=26, style="bold white")
    table.add_column("Detalle Ejecutivo de la Propuesta", style="dim color(250)")

    table.add_row("🎯 Propósito y Visión", objetivo[:450] + ("..." if len(objetivo) > 450 else ""))
    table.add_row("📋 Funcionalidades Core", alcance[:550] + ("..." if len(alcance) > 550 else "") if alcance else "Ver detalle completo en docs/producto/prd.md")
    table.add_row("⚖️ Decisiones y Supuestos", decisiones[:450] + ("..." if len(decisiones) > 450 else ""))
    table.add_row("🚦 Estado del Backlog", badge.plain)

    console.print(Panel(
        table,
        title="[bold color(208)]✻ PUNTOS DESTACADOS DE LA PROPUESTA[/]",
        border_style=border_color,
        box=box.ROUNDED,
        padding=(1, 1),
    ))


def gestionar_aprobacion_propuesta(
    prd_text: str,
    backlog_text: str,
    on_aceptar,
    on_modificar,
    on_responder_preguntas,
):
    """Permite al usuario validar la propuesta: aceptar, solicitar cambios para replantear, o responder dudas."""
    preguntas = extraer_preguntas_pendientes(backlog_text)
    if not preguntas:
        preguntas = extraer_preguntas_pendientes(prd_text)

    menu_grid = Table.grid(expand=True)
    menu_grid.add_column(ratio=1)
    menu_grid.add_row("[bold white]¿Cómo deseas proceder con esta propuesta inicial?[/]\n")
    menu_grid.add_row("  [bold color(42)][1] Aceptar propuesta[/]       [dim color(245)]— Me gusta el enfoque, continuar al refinamiento técnico[/]")
    menu_grid.add_row("  [bold color(214)][2] Modificar / Cambiar[/]     [dim color(245)]— No me cuadran detalles, replantear la propuesta de otra forma[/]")
    if preguntas:
        menu_grid.add_row(f"  [bold color(208)][3] Resolver dudas ({len(preguntas)})[/]     [dim color(245)]— Responder preguntas abiertas pendientes del equipo[/]")

    console.print(Panel(
        menu_grid,
        border_style="color(239)",
        box=box.ROUNDED,
        padding=(1, 2),
    ))

    opciones_validas = ["1", "2"]
    if preguntas:
        opciones_validas.append("3")

    default_opc = "3" if preguntas else "1"

    try:
        console.print("[dim color(245)]╭─ ✻ agent-builder[/]")
        opc = Prompt.ask(
            f"[bold color(208)]╰─❯ Seleccioná una opción ({'/'.join(opciones_validas)})[/]",
            choices=opciones_validas,
            default=default_opc,
        )
    except Exception:
        opc = default_opc

    if opc == "1":
        console.print("\n[bold color(42)]✓ Propuesta inicial aprobada por el usuario.[/]")
        console.print("[dim color(245)]El backlog y las especificaciones están confirmadas y listas para refinar.[/]\n")
        try:
            if Confirm.ask("[bold color(208)]¿Deseas ejecutar el refinamiento técnico ahora mismo (PO ➔ Dev ➔ QA ➔ Consolidar)?[/]", default=True):
                return "refinar_ahora"
        except Exception:
            pass
        return on_aceptar()

    elif opc == "2":
        console.print("\n[bold color(214)]╭─ ✻ Solicitud de Cambios / Re-planificación[/]")
        console.print("[dim color(245)]│  Explicá qué no te gusta, qué falta, o cómo querés que se plantee la solución:[/] ")
        cambios = Prompt.ask("[bold color(208)]╰─❯ Tus observaciones o cambios requeridos[/]")
        while not cambios.strip():
            cambios = Prompt.ask("[yellow]╰─❯ Por favor ingresá qué cambios te gustaría realizar[/]")
        return on_modificar(cambios.strip())

    elif opc == "3" and preguntas:
        render_preguntas_pendientes(preguntas)
        resps = interactuar_preguntas_cliente(preguntas)
        return on_responder_preguntas(resps)
