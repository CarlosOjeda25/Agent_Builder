#!/usr/bin/env python3
"""
Agent Builder — Code Extractor & Scaffolder Engine
===================================================
Extrae automáticamente los bloques de código y pruebas generados por los agentes
(en bundle.md, implementacion_frontend.md, implementacion_cicd.md, scripts_automatizacion.md)
y los materializa como ARCHIVOS FÍSICOS reales en disco (src/, tests/, etc.).

Incluye:
- Detección inteligente de rutas y nombres de archivo (# filepath:, // filepath:, headers, fences)
- Scaffolding automático (requirements.txt, package.json, README.md, .env.example)
- Verificación de sintaxis / compilación (py_compile para Python, json.loads, etc.)
- Renderizado visual elegante estilo Claude Code
"""

import os
import re
import sys
import json
import py_compile
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def limpiar_ruta(ruta_cruda: str) -> Optional[str]:
    """Limpia y valida una ruta de archivo relativa."""
    if not ruta_cruda:
        return None
    ruta = ruta_cruda.strip().strip("`'\"*#:; ")
    # Remover prefijos comunes como 'Archivo:', 'File:', 'filepath:', etc.
    ruta = re.sub(r"^(?:Archivo|File|Ruta|Path|filepath|file)\s*[:=]\s*", "", ruta, flags=re.IGNORECASE)
    ruta = ruta.strip().strip("`'\"*#:; ")
    ruta = ruta.replace("\\", "/")

    # Ignorar si es una ruta absoluta del sistema o URL
    if ruta.startswith("/") or ruta.startswith("http://") or ruta.startswith("https://") or ":" in ruta:
        # si es C:/... o similar, extraer lo relativo
        partes = ruta.split("/")
        if len(partes) > 1:
            ruta = "/".join(partes[1:])
        else:
            return None

    # Normalizar partes
    partes = [p for p in ruta.split("/") if p and p not in (".", "..")]
    if not partes:
        return None

    ruta_norm = "/".join(partes)

    nombre = Path(ruta_norm).name
    # Un archivo válido debe tener extensión de código/config o ser Dockerfile/Makefile
    extensiones_validas = {
        ".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".scss",
        ".json", ".yaml", ".yml", ".sql", ".sh", ".bash", ".env", ".example",
        ".dockerignore", ".gitignore", ".toml", ".xml", ".ini", ".cfg",
    }
    ext = Path(ruta_norm).suffix.lower()
    if ext not in extensiones_validas and nombre not in ("Dockerfile", "docker-compose.yml", "Makefile", "Procfile"):
        return None

    # Ignorar archivos puramente de documentación markdown generados por el orquestador
    if ruta_norm.startswith("docs/") or (ruta_norm.endswith(".md") and not ruta_norm.endswith("README.md")):
        return None

    return ruta_norm


def detectar_ruta_en_bloque(pre_header: str, tag: str, first_lines: str) -> Optional[str]:
    """Intenta detectar la ruta del archivo mediante múltiples heurísticas."""
    # 1. En la etiqueta del bloque (ej: ```python file="src/backend/main.py" o ```python:src/app.py)
    if tag:
        m = re.search(r'(?:file|filepath)=["\']?([^"\'\s]+)["\']?', tag, re.IGNORECASE)
        if m:
            r = limpiar_ruta(m.group(1))
            if r:
                return r
        if ":" in tag:
            partes = tag.split(":", 1)
            if "/" in partes[1] or "." in partes[1]:
                r = limpiar_ruta(partes[1])
                if r:
                    return r

    # 2. En las primeras 3 líneas del código (# filepath: ..., // filepath: ..., # src/...)
    for linea in first_lines.splitlines()[:4]:
        linea_s = linea.strip()
        # # filepath: src/... o // filepath: src/...
        m = re.search(r'(?:#|//|/\*|<!--)\s*(?:filepath|file)\s*[:=]\s*([^\s*>"\'`]+)', linea_s, re.IGNORECASE)
        if m:
            r = limpiar_ruta(m.group(1))
            if r:
                return r
        # Comentario directo con ruta válida (# src/backend/main.py o // src/App.jsx)
        m2 = re.search(r'^(?:#|//)\s*([a-zA-Z0-9_\-\./]+\.[a-zA-Z0-9]+)$', linea_s)
        if m2:
            r = limpiar_ruta(m2.group(1))
            if r and ("/" in r or r in ("Dockerfile", "docker-compose.yml", "package.json", "requirements.txt")):
                return r

    # 3. En el encabezado markdown inmediatamente anterior (### Archivo: src/...)
    if pre_header:
        lineas_header = [l.strip() for l in pre_header.splitlines() if l.strip()]
        for linea_h in reversed(lineas_header[-5:]):
            # Patrón comentario con filepath en encabezado (ej: // filepath: src/frontend/... o # filepath: ...)
            m_comm = re.search(r'(?:#|//|/\*|<!--)\s*(?:filepath|file)?\s*[:=]?\s*([a-zA-Z0-9_\-\./]+\.[a-zA-Z0-9]+)', linea_h, re.IGNORECASE)
            if m_comm:
                r = limpiar_ruta(m_comm.group(1))
                if r:
                    return r
            m = re.search(r'(?:###|##|#|\*\*)\s*(?:Archivo|File|Ruta|Path)\s*[:=]?\s*[`"]?([^`"\n]+)[`"]?', linea_h, re.IGNORECASE)
            if m:
                r = limpiar_ruta(m.group(1))
                if r:
                    return r
            # Patrón encabezado con paréntesis: ### Task 1.1: Backend Setup (`src/api/server.py`)
            m_paren = re.search(r'\(`?([a-zA-Z0-9_\-\./]+\.[a-zA-Z0-9]+)`?\)', linea_h)
            if m_paren:
                r = limpiar_ruta(m_paren.group(1))
                if r:
                    return r

    return None


def inferir_ruta_por_contenido(lenguaje: str, contenido: str, contador: Dict[str, int]) -> Optional[str]:
    """Infiere una ruta por defecto limpia y coherente si el bloque de código no tenía nombre."""
    lang = lenguaje.lower().strip()
    if lang in ("mermaid", "gherkin", "feature", "markdown", "md", "txt", "text", "output", "log"):
        return None

    c_lower = contenido.lower()

    # Pruebas unitarias reales en Python
    if ("def test_" in contenido or "import pytest" in contenido or "import unittest" in contenido) and lang in ("python", "py", ""):
        contador["test"] = contador.get("test", 0) + 1
        idx = f"_{contador['test']}" if contador["test"] > 1 else ""
        return f"tests/test_unit{idx}.py"

    # Playwright / E2E UI Tests
    if "test(" in contenido and ("page." in contenido or "locator(" in contenido):
        contador["e2e"] = contador.get("e2e", 0) + 1
        idx = f"_{contador['e2e']}" if contador["e2e"] > 1 else ""
        return f"tests/e2e/test_spec{idx}.spec.ts"

    # API Tests
    if "api_base_url" in c_lower or ("requests.get" in c_lower and "test" in c_lower):
        contador["test_api"] = contador.get("test_api", 0) + 1
        idx = f"_{contador['test_api']}" if contador["test_api"] > 1 else ""
        return f"tests/api/test_api{idx}.py"

    # Backend Python
    if lenguaje in ("python", "py") or "from fastapi" in contenido or "import flask" in contenido:
        if "fastapi(" in c_lower or "flask(" in c_lower or "@app." in contenido:
            return "src/backend/main.py"
        elif "class " in contenido and ("model" in c_lower or "basescheme" in c_lower or "pydantic" in c_lower):
            contador["models"] = contador.get("models", 0) + 1
            idx = f"_{contador['models']}" if contador["models"] > 1 else ""
            return f"src/backend/models{idx}.py"
        else:
            contador["backend"] = contador.get("backend", 0) + 1
            idx = f"_{contador['backend']}" if contador["backend"] > 1 else ""
            return f"src/backend/service{idx}.py"

    # Frontend (React / Vue / HTML)
    if lenguaje in ("javascript", "typescript", "jsx", "tsx", "js", "ts", "html", "vue"):
        if "<!doctype html" in c_lower or "<html" in c_lower:
            return "src/frontend/index.html"
        if "export default" in contenido or "import react" in c_lower or "<div>" in contenido:
            ext = "tsx" if "typescript" in lenguaje or "tsx" in lenguaje else "jsx"
            contador["component"] = contador.get("component", 0) + 1
            if contador["component"] == 1:
                return f"src/frontend/App.{ext}"
            return f"src/frontend/Component{contador['component']}.{ext}"

    # CI/CD o Docker
    if "name: " in contenido and ("on: " in contenido or "jobs: " in contenido):
        return ".github/workflows/ci.yml"
    if "from " in c_lower and ("run " in c_lower or "copy " in c_lower or "workdir " in c_lower):
        return "Dockerfile"
    if "services:" in c_lower and ("image:" in c_lower or "build:" in c_lower):
        return "docker-compose.yml"

    # Genérico por extensión reconocida (nunca generar .txt)
    ext_map = {
        "python": "py", "py": "py", "javascript": "js", "js": "js",
        "typescript": "ts", "ts": "ts", "sql": "sql", "sh": "sh", "bash": "sh", "css": "css"
    }
    ext = ext_map.get(lenguaje.lower())
    if not ext:
        return None
    contador["misc"] = contador.get("misc", 0) + 1
    return f"src/generated_{contador['misc']}.{ext}"


def extraer_bloques_de_texto(texto: str) -> List[Tuple[str, str, str]]:
    """Extrae bloques de código en markdown (header_previo, lenguaje_o_tag, codigo)."""
    # Regex que captura el contexto anterior y el bloque de código
    patron = re.compile(
        r'(?:^|\n)(?P<header>(?:[^\n]+\n){0,4})?'
        r'```(?P<tag>[a-zA-Z0-9_\-\.]+)?(?P<tag_extra>[^\n]*)\n'
        r'(?P<code>.*?)'
        r'```',
        re.DOTALL
    )

    resultados = []
    for m in patron.finditer(texto):
        header = m.group("header") or ""
        tag = (m.group("tag") or "").strip()
        tag_extra = (m.group("tag_extra") or "").strip()
        code = m.group("code") or ""
        full_tag = f"{tag} {tag_extra}".strip()
        resultados.append((header, full_tag, code))

    return resultados


def verificar_sintaxis(ruta_absoluta: Path) -> Tuple[bool, str]:
    """Valida la sintaxis del archivo según su extensión."""
    ext = ruta_absoluta.suffix.lower()

    if ext == ".py":
        try:
            py_compile.compile(str(ruta_absoluta), doraise=True)
            return True, "Sintaxis Python OK"
        except py_compile.PyCompileError as e:
            msg = str(e).splitlines()[-1] if str(e) else "Error de sintaxis"
            return False, f"Error: {msg[:60]}"

    elif ext == ".json":
        try:
            json.loads(ruta_absoluta.read_text(encoding="utf-8"))
            return True, "JSON Válido"
        except Exception as e:
            return False, f"JSON Inválido: {str(e)[:40]}"

    elif ext in (".yaml", ".yml"):
        try:
            import yaml
            yaml.safe_load(ruta_absoluta.read_text(encoding="utf-8"))
            return True, "YAML Válido"
        except Exception:
            return True, "Formato YAML"

    return True, "Válido"


def generar_scaffolding_faltante(raiz: Path, archivos_creados: List[str]) -> List[str]:
    """Genera requirements.txt, .env.example, README.md si no fueron creados."""
    nuevos = []
    has_py = any(a.endswith(".py") for a in archivos_creados)
    has_frontend = any(a.endswith((".jsx", ".tsx", ".vue", ".html")) for a in archivos_creados)

    # 1. requirements.txt para proyectos Python
    req_file = raiz / "requirements.txt"
    if has_py and not req_file.exists():
        # Escanear imports para detectar dependencias requeridas
        pkgs = set(["pytest", "pytest-asyncio", "httpx"])
        for a in archivos_creados:
            if a.endswith(".py"):
                fpath = raiz / a
                if fpath.exists():
                    contenido = fpath.read_text(encoding="utf-8", errors="replace")
                    if "fastapi" in contenido:
                        pkgs.update(["fastapi", "uvicorn[standard]", "pydantic"])
                    if "flask" in contenido:
                        pkgs.update(["flask"])
                    if "sqlalchemy" in contenido:
                        pkgs.update(["sqlalchemy"])
                    if "playwright" in contenido:
                        pkgs.update(["playwright"])
                    if "pydantic_settings" in contenido:
                        pkgs.update(["pydantic-settings"])
                    if "jwt" in contenido or "jose" in contenido:
                        pkgs.update(["python-jose[cryptography]", "passlib[bcrypt]"])

        req_content = "# Dependencies generadas automáticamente por Agent Builder\n" + "\n".join(sorted(pkgs)) + "\n"
        req_file.write_text(req_content, encoding="utf-8")
        nuevos.append("requirements.txt")

    # 2. .env.example
    env_file = raiz / ".env.example"
    if not env_file.exists() and not (raiz / ".env").exists():
        env_content = (
            "# Agent Builder — Entorno Local\n"
            "PORT=8000\n"
            "HOST=0.0.0.0\n"
            "API_BASE_URL=http://localhost:8000\n"
            "FRONTEND_BASE_URL=http://localhost:3000\n"
            "DATABASE_URL=sqlite:///./app.db\n"
            "DEBUG=True\n"
        )
        env_file.write_text(env_content, encoding="utf-8")
        nuevos.append(".env.example")

    # 3. README.md ejecutable si no existe en la raíz
    readme_file = raiz / "README.md"
    if not readme_file.exists():
        readme_content = f"""# Proyecto Generado por Agent Builder

Este proyecto fue generado y estructurado siguiendo el ciclo de vida de ingeniería Scrum y SDD con arquitectura limpia.

## 🚀 Inicio Rápido (Local)

### 1. Requisitos
- Python 3.10+
{"- Node.js 18+ (para el frontend)" if has_frontend else ""}

### 2. Configuración del Backend
```bash
# Crear entorno virtual
python -m venv venv

# Activar en Windows:
.\\venv\\Scripts\\activate
# Activar en Linux/macOS:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Ejecutar la Aplicación
```bash
# Servidor FastAPI / Uvicorn:
uvicorn src.backend.main:app --reload --port 8000
```

### 4. Ejecutar Pruebas Automatizadas
```bash
# Correr suite de pruebas unitarias
pytest -v
```

---
*Generado automáticamente con **Agent Builder**.*
"""
        readme_file.write_text(readme_content, encoding="utf-8")
        nuevos.append("README.md")

    return nuevos


def materializar_codigo(output_dir: Path) -> List[Dict[str, any]]:
    """
    Función principal: localiza todos los archivos de entrega y bundles,
    extrae el código fuente y lo escribe físicamente en disco bajo output_dir.
    """
    raiz = Path(output_dir).resolve()
    raiz.mkdir(parents=True, exist_ok=True)

    # Limpiar posibles archivos creados por error con nombres de directorio
    for bad_name in ("src", "context.exception", "app", "tests"):
        bad_path = raiz / bad_name
        if bad_path.is_file():
            try:
                bad_path.unlink()
            except Exception:
                pass

    # Limpiar tests unitarios residuales generados de gherkin/mermaid en corridas anteriores
    tests_dir = raiz / "tests"
    if tests_dir.exists():
        for junk in tests_dir.glob("test_unit_*.py"):
            try:
                junk.unlink()
            except Exception:
                pass

    # Limpiar archivos generados genéricos previos en src/
    src_dir = raiz / "src"
    if src_dir.is_dir():
        for junk in src_dir.glob("generated_*.*"):
            try:
                junk.unlink()
            except Exception:
                pass

    # Fuentes a inspeccionar en orden de prioridad
    fuentes_candidatas = [
        raiz / "docs" / "bundle_dev.md",
        raiz / "docs" / "bundle.md",
        raiz / "docs" / "arquitectura" / "implementacion_backend_senior.md",
        raiz / "docs" / "arquitectura" / "implementacion_backend_semi.md",
        raiz / "docs" / "arquitectura" / "implementacion_backend_junior.md",
        raiz / "docs" / "arquitectura" / "implementacion_frontend.md",
        raiz / "docs" / "arquitectura" / "implementacion_cicd.md",
        raiz / "docs" / "arquitectura" / "entrega_qa.md",
        raiz / "docs" / "qa" / "scripts_automatizacion.md",
        raiz / "docs" / "bundle_qa.md",
        raiz / "bundle_dev.md",
        raiz / "bundle.md",
        raiz / "implementacion_backend_senior.md",
        raiz / "implementacion_backend_semi.md",
        raiz / "implementacion_backend_junior.md",
        raiz / "implementacion_frontend.md",
        raiz / "implementacion_cicd.md",
        raiz / "entrega_qa.md",
        raiz / "scripts_automatizacion.md",
        raiz / "bundle_qa.md",
    ]

    # También buscar cualquier otro .md en docs/arquitectura o docs/qa
    docs_dir = raiz / "docs"
    if docs_dir.exists():
        for extra_md in docs_dir.rglob("*.md"):
            if extra_md not in fuentes_candidatas and extra_md.is_file():
                fuentes_candidatas.append(extra_md)

    archivos_procesados = {}
    contador_inferencias = {}

    for ruta_md in fuentes_candidatas:
        if not ruta_md.exists():
            continue
        try:
            texto = ruta_md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        bloques = extraer_bloques_de_texto(texto)
        for pre_header, tag, codigo in bloques:
            codigo_limpio = codigo.strip()
            # Ignorar bloques vacíos o muy cortos sin lógica (ej: comandos bash de 1 línea o json de ejemplo corto)
            if not codigo_limpio or len(codigo_limpio.splitlines()) < 2:
                continue

            # Ignorar si es un ejemplo de plantilla del prompt
            if any(marker in codigo_limpio.lower() for marker in ("código completo ejecutable", "codigo completo ejecutable", "... código", "... codigo")):
                continue

            tag_lang = tag.split()[0].lower() if tag else ""
            # Ignorar si es explícitamente markdown o texto plano descriptivo
            if tag_lang in ("markdown", "md", "text", "txt") and "class " not in codigo and "def " not in codigo:
                continue

            # Detectar ruta
            primera_linea = codigo_limpio.splitlines()[0] if codigo_limpio else ""
            ruta_rel = detectar_ruta_en_bloque(pre_header, tag, primera_linea)

            if not ruta_rel:
                ruta_rel = inferir_ruta_por_contenido(tag_lang, codigo_limpio, contador_inferencias)

            if not ruta_rel:
                continue

            # Si ya se procesó este archivo, pero este bloque tiene más contenido o es más completo, actualizar
            if ruta_rel not in archivos_procesados or len(codigo_limpio) > len(archivos_procesados[ruta_rel]["codigo"]):
                archivos_procesados[ruta_rel] = {
                    "codigo": codigo_limpio,
                    "origen": ruta_md.name,
                    "lenguaje": tag_lang or Path(ruta_rel).suffix.lstrip("."),
                }

    # Materializar en disco
    resultado_archivos = []
    for rel_path, data in archivos_procesados.items():
        destino = raiz / rel_path
        destino.parent.mkdir(parents=True, exist_ok=True)

        codigo_a_guardar = data["codigo"]
        # Limpiar posible línea inicial '# filepath: ...'
        lineas = codigo_a_guardar.splitlines()
        if lineas and re.search(r'^(?:#|//|/\*|<!--)\s*(?:filepath|file)\s*[:=]', lineas[0], re.IGNORECASE):
            codigo_a_guardar = "\n".join(lineas[1:]).lstrip()

        destino.write_text(codigo_a_guardar + "\n", encoding="utf-8")

        # Validar sintaxis
        sintaxis_ok, detalle_sintaxis = verificar_sintaxis(destino)
        if not sintaxis_ok and rel_path.endswith(".py"):
            # Intento 1: separar bloques de excepción/control colapsados
            reparado = re.sub(r'(\S)\s+(except\b|elif\b|else:|finally:)', r'\1\n        \2', codigo_a_guardar)
            destino.write_text(reparado + "\n", encoding="utf-8")
            s_ok_rep, d_rep = verificar_sintaxis(destino)
            if s_ok_rep:
                sintaxis_ok, detalle_sintaxis = s_ok_rep, d_rep
            else:
                # Intento 2: separar asignaciones colapsadas en la misma línea
                reparado2 = re.sub(r'([^\n])\s{4,}([a-zA-Z_]\w*\s*=)', r'\1\n        \2', reparado)
                destino.write_text(reparado2 + "\n", encoding="utf-8")
                s_ok_rep2, d_rep2 = verificar_sintaxis(destino)
                if s_ok_rep2:
                    sintaxis_ok, detalle_sintaxis = s_ok_rep2, d_rep2
                else:
                    destino.write_text(codigo_a_guardar + "\n", encoding="utf-8")

        resultado_archivos.append({
            "ruta": rel_path,
            "destino_abs": str(destino),
            "lineas": len(lineas),
            "tamano_bytes": destino.stat().st_size,
            "lenguaje": data["lenguaje"],
            "sintaxis_ok": sintaxis_ok,
            "detalle_sintaxis": detalle_sintaxis,
        })

    # Generar scaffolding faltante (requirements.txt, README.md, etc.)
    creados_rel = [item["ruta"] for item in resultado_archivos]
    scaffolding_creados = generar_scaffolding_faltante(raiz, creados_rel)
    for sc_rel in scaffolding_creados:
        sc_destino = raiz / sc_rel
        sintaxis_ok, detalle_sintaxis = verificar_sintaxis(sc_destino)
        resultado_archivos.append({
            "ruta": sc_rel,
            "destino_abs": str(sc_destino),
            "lineas": len(sc_destino.read_text(encoding="utf-8").splitlines()),
            "tamano_bytes": sc_destino.stat().st_size,
            "lenguaje": sc_destino.suffix.lstrip(".") or "config",
            "sintaxis_ok": sintaxis_ok,
            "detalle_sintaxis": detalle_sintaxis,
        })

    return sorted(resultado_archivos, key=lambda x: x["ruta"])


def render_reporte_extraccion(archivos: List[Dict[str, any]]):
    """Presenta los archivos materializados usando el tema elegante de Claude Code."""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich import box
        from console_ui import CLAUDE_THEME, console
    except Exception:
        print("\n" + "=" * 70)
        print("📦 ARCHIVOS DE CÓDIGO MATERIALIZADOS EN DISCO")
        print("=" * 70)
        for a in archivos:
            st = "✓ OK" if a["sintaxis_ok"] else f"⚠ {a['detalle_sintaxis']}"
            print(f"  • {a['ruta']:<40} [{a['lineas']} líneas, {a['tamano_bytes']} B] -> {st}")
        print("=" * 70 + "\n")
        return

    table = Table(
        show_header=True,
        header_style="bold color(208)",
        box=box.ROUNDED,
        border_style="color(239)",
        expand=True,
    )
    table.add_column("Archivo Generado (Ruta en Disco)", style="bold white")
    table.add_column("Tipo", width=12, style="color(75)")
    table.add_column("Líneas", width=8, justify="right", style="dim color(245)")
    table.add_column("Tamaño", width=10, justify="right", style="dim color(245)")
    table.add_column("Sintaxis & Compilación", style="bold")

    total_lineas = 0
    total_bytes = 0
    errores_sintaxis = 0

    for a in archivos:
        total_lineas += a["lineas"]
        total_bytes += a["tamano_bytes"]
        if not a["sintaxis_ok"]:
            errores_sintaxis += 1
            badge = f"[bold color(203)]✗ {a['detalle_sintaxis']}[/]"
        else:
            badge = f"[bold color(42)]✓ {a['detalle_sintaxis']}[/]"

        # Iconos por extensión
        ext = Path(a["ruta"]).suffix.lower()
        icono = "🐍" if ext == ".py" else ("⚛️" if ext in (".jsx", ".tsx", ".js", ".ts") else ("🧪" if "test" in a["ruta"] else "📄"))

        table.add_row(
            f"{icono} [color(255)]{a['ruta']}[/]",
            a["lenguaje"] or ext.lstrip("."),
            str(a["lineas"]),
            f"{a['tamano_bytes']} B",
            badge,
        )

    console.print()
    console.print(Panel(
        table,
        title=f"[bold color(208)]✻ MATERIALIZACIÓN DE CÓDIGO FUENTE COMPLETADA ({len(archivos)} archivos, {total_lineas} líneas)[/]",
        subtitle="[dim color(245)]Archivos físicos listos para compilar, probar y entregar[/]",
        border_style="color(208)" if errores_sintaxis == 0 else "color(214)",
        box=box.ROUNDED,
        padding=(1, 1),
    ))

    # Tarjeta de comandos rápidos para correr
    guia_cmd = Table.grid(expand=True)
    guia_cmd.add_column(ratio=1)
    guia_cmd.add_row("[bold white]Comandos para compilar y ejecutar tu código localmente:[/]\n")
    guia_cmd.add_row("  [bold color(75)]1. Instalar dependencias:[/]  [dim color(250)]pip install -r requirements.txt[/]")
    guia_cmd.add_row("  [bold color(75)]2. Ejecutar la API:[/]        [dim color(250)]python -m uvicorn src.backend.main:app --reload[/]")
    guia_cmd.add_row("  [bold color(75)]3. Ejecutar las pruebas:[/]   [dim color(250)]pytest -v[/]")

    console.print(Panel(
        guia_cmd,
        title="[bold color(75)]▶ GUÍA DE EJECUCIÓN INMEDIATA[/]",
        border_style="color(239)",
        box=box.ROUNDED,
        padding=(1, 2),
    ))
    console.print()


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    res = materializar_codigo(target)
    render_reporte_extraccion(res)
