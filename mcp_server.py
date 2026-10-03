#!/usr/bin/env python3
"""
Agent Builder MCP Server
Exposes CrewAI Agent Builder requirements generation orchestrator via Model Context Protocol (MCP) over stdio.
Runs execution inside Docker container with GPU passthrough to host Ollama.
Compatible with Claude Code, OpenCode, Antigravity, Cursor, Gemini CLI, Codex CLI, etc.
"""

import sys
import json
import os
import shutil
import subprocess
import urllib.request
import time

SERVER_NAME = "agent-builder-mcp"
SERVER_VERSION = "2.0.0"

# ── Docker / Ollama detection ──────────────────────────────────────────────

def _find_ollama_endpoint():
    """Returns (ollama_url, extra_docker_flags) for the best available Ollama."""
    # 1. Native Ollama on Windows host (fastest — direct GPU access)
    for port in [11434, 11435]:
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/tags",
                headers={"User-Agent": "MCP"}
            )
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    return f"http://host.docker.internal:{port}", [
                        "--add-host", "host.docker.internal:host-gateway"
                    ]
        except Exception:
            pass

    # 2. Docker Compose Ollama service (container network)
    try:
        result = subprocess.run(
            ["docker", "ps", "-q", "-f", "name=agent_builder_ollama"],
            capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip():
            return "http://agent_builder_ollama:11434", [
                "--network", "agent_builder_net"
            ]
    except Exception:
        pass

    # 3. Last resort — assume host Ollama on default port
    return "http://host.docker.internal:11434", [
        "--add-host", "host.docker.internal:host-gateway"
    ]


def _pull_ollama_model(model_name: str):
    """Ensure the model is pulled in the Ollama container/service (fire-and-forget)."""
    try:
        subprocess.run(
            ["docker", "exec", "agent_builder_ollama", "ollama", "pull", model_name],
            capture_output=True, text=True, timeout=120
        )
    except Exception:
        pass  # Non-blocking — model might already exist or be pulled manually


# ── Core execution ─────────────────────────────────────────────────────────

def get_agent_builder_dir():
    """Locate the agent_builder project root (with crew.jsonc)."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(current_dir, "crew.jsonc")):
        return current_dir
    subdir = os.path.join(current_dir, "agent_builder")
    if os.path.exists(os.path.join(subdir, "crew.jsonc")):
        return subdir
    return current_dir


def run_agent_builder(solicitud_usuario, target_output_dir=None):
    base_dir = get_agent_builder_dir()
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    inputs_json = json.dumps({"solicitud_usuario": solicitud_usuario})
    ollama_host, extra_flags = _find_ollama_endpoint()

    sys.stderr.write(f"[agent-builder-mcp] Ollama endpoint: {ollama_host}\n")

    # Build Docker command (no shell=True — safer, faster on Windows)
    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{output_dir}:/app/output",
        "-e", f"OLLAMA_HOST={ollama_host}",
        "-e", f"API_BASE={ollama_host}",
        "-e", f"OPENAI_API_BASE={ollama_host}/v1",
        "-e", "OPENAI_API_KEY=ollama",
        *extra_flags,
        "agent_builder-agent_builder",
        "crewai", "run", "--inputs", inputs_json
    ]

    sys.stderr.write(f"[agent-builder-mcp] Running CrewAI in Docker...\n")
    sys.stderr.flush()

    process = subprocess.run(
        docker_cmd,
        cwd=base_dir,
        capture_output=True,
        text=True,
        timeout=900  # 15 min max
    )

    # Fallback to local crewai run if Docker fails
    if process.returncode != 0:
        sys.stderr.write(
            f"[agent-builder-mcp] Docker failed (code {process.returncode}), "
            f"falling back to local crewai...\n"
        )
        sys.stderr.flush()

        cmd = ["crewai", "run", "--inputs", inputs_json]
        process = subprocess.run(
            cmd,
            cwd=base_dir,
            capture_output=True,
            text=True,
            timeout=900
        )
        if process.returncode != 0:
            return {
                "success": False,
                "error": process.stderr or process.stdout or "CrewAI run failed",
                "logs": process.stdout
            }

    # Collect generated artifacts
    generated_files = {}
    if os.path.exists(output_dir):
        for filename in sorted(os.listdir(output_dir)):
            if filename.endswith(".md") or filename.endswith(".json"):
                src = os.path.join(output_dir, filename)
                if os.path.isfile(src):
                    with open(src, "r", encoding="utf-8") as f:
                        generated_files[filename] = f.read()
                    if target_output_dir:
                        os.makedirs(target_output_dir, exist_ok=True)
                        shutil.copy2(src, os.path.join(target_output_dir, filename))

    return {
        "success": True,
        "message": (
            f"Pipeline completado para '{solicitud_usuario}'. "
            f"Generados: {list(generated_files.keys())}"
        ),
        "output_directory": target_output_dir or output_dir,
        "files_generated": list(generated_files.keys()),
        "contents": generated_files
    }


# ── MCP JSON-RPC server (stdio) ────────────────────────────────────────────

def send_response(response):
    body = json.dumps(response, ensure_ascii=False)
    sys.stdout.write(body + "\n")
    sys.stdout.flush()


def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        try:
            req = json.loads(line)
        except Exception:
            continue

        method = req.get("method")
        msg_id = req.get("id")

        if method == "initialize":
            send_response({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "version": SERVER_VERSION
                    }
                }
            })
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            send_response({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [{
                        "name": "generate_requirements",
                        "description": (
                            "Orchestrates CrewAI Multi-Agent pipeline (PO → Analyst → QA → Backlog → "
                            "Refinement) to generate PRD, Gherkin User Stories, QA Audit, and Sprint "
                            "Refinement package. Runs in Docker with GPU passthrough to Ollama."
                        ),
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "solicitud_usuario": {
                                    "type": "string",
                                    "description": "Raw software idea, feature request, or user prompt."
                                },
                                "target_output_dir": {
                                    "type": "string",
                                    "description": "Absolute path where output files should be saved."
                                }
                            },
                            "required": ["solicitud_usuario"]
                        }
                    }]
                }
            })
        elif method == "tools/call":
            params = req.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {})

            if name == "generate_requirements":
                solicitud = args.get("solicitud_usuario", "")
                target_dir = args.get("target_output_dir")
                result = run_agent_builder(solicitud, target_dir)
                send_response({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{
                            "type": "text",
                            "text": json.dumps(result, indent=2, ensure_ascii=False)
                        }]
                    }
                })
            else:
                send_response({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool '{name}' not found"
                    }
                })
        else:
            if msg_id is not None:
                send_response({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method '{method}' not supported"
                    }
                })


if __name__ == "__main__":
    main()