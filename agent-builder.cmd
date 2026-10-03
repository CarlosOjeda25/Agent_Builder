@echo off
setlocal

:: Agent Builder Global CLI Launcher
:: Permite ejecutar Agent Builder desde cualquier ruta de CMD y genera los artefactos en el directorio actual (%cd%)

set "ENV_FILE=c:\Users\duvan\Proyectos\Agent Builder\agent_builder\.env"
set "ENV_ARG="
if exist "%ENV_FILE%" (
    set ENV_ARG=--env-file "%ENV_FILE%"
)

docker run --rm -i ^
  --network agent_builder_net ^
  -v "%cd%:/workspace" ^
  -e AGENT_BUILDER_OUTPUT_DIR=/workspace ^
  -e AGENT_BUILDER_FLAT_OUTPUT=1 ^
  -e AGENT_BUILDER_INTERCAMBIO_DIR=/workspace/.intercambio ^
  -e OLLAMA_HOST=http://agent_builder_ollama:11434 ^
  -e API_BASE=http://agent_builder_ollama:11434 ^
  -e OPENAI_API_BASE=http://agent_builder_ollama:11434/v1 ^
  -e OPENAI_API_KEY=ollama ^
  -e CREWAI_REQUEST_TIMEOUT=600 ^
  %ENV_ARG% ^
  agent_builder-agent_builder python orchestrator.py %*

endlocal
