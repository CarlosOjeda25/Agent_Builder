# PowerShell Script to install Agent Builder MCP Server globally across Claude, Antigravity, Gemini CLI, Cursor, and OpenCode
$mcpScriptPath = "C:/Users/duvan/Proyectos/Agent Builder/mcp_server.py"

Write-Host "Installing Agent Builder MCP Server globally with 15min timeout..." -ForegroundColor Green

# Standard MCP configs (Claude, Antigravity, Cursor)
$standardConfigs = @(
    "$env:APPDATA\Claude\claude_desktop_config.json",
    "$env:USERPROFILE\.gemini\antigravity\mcp_config.json",
    "$env:USERPROFILE\.gemini\antigravity-cli\mcp_config.json",
    "$env:USERPROFILE\.gemini\antigravity-ide\mcp_config.json"
)

foreach ($configFile in $standardConfigs) {
    $dir = Split-Path -Parent $configFile
    if (!(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $configObj = @{ mcpServers = @{} }
    if (Test-Path $configFile) {
        try {
            $json = Get-Content $configFile -Raw | ConvertFrom-Json
            if ($json.mcpServers) {
                $json.mcpServers.psobject.properties | ForEach-Object { $configObj.mcpServers[$_.Name] = $_.Value }
            }
        } catch {}
    }
    $configObj.mcpServers."agent-builder" = @{
        command = "py"
        args = @("-3", $mcpScriptPath)
        disabled = $false
        timeout = 900000
    }
    $configJson = $configObj | ConvertTo-Json -Depth 10
    Set-Content -Path $configFile -Value $configJson -Encoding UTF8
    Write-Host "Registered standard MCP: $configFile" -ForegroundColor Cyan
}

# OpenCode specific configs (strictly conforming to OpenCode schema with timeout: 900000)
$opencodeConfigs = @(
    "$env:USERPROFILE\.config\opencode\opencode.json",
    "$env:APPDATA\opencode\opencode.json"
)

foreach ($configFile in $opencodeConfigs) {
    $dir = Split-Path -Parent $configFile
    if (!(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    
    $configObj = @{
        '$schema' = "https://opencode.ai/config.json"
        mcp = @{}
    }
    
    if (Test-Path $configFile) {
        try {
            $json = Get-Content $configFile -Raw | ConvertFrom-Json
            if ($json.mcp) {
                $json.mcp.psobject.properties | ForEach-Object { $configObj.mcp[$_.Name] = $_.Value }
            }
        } catch {}
    }

    # OpenCode strict McpLocalConfig schema with 15min timeout (900000 ms)
    $configObj.mcp."agent-builder" = @{
        type = "local"
        command = @("py", "-3", $mcpScriptPath)
        enabled = $true
        timeout = 900000
    }

    $configJson = $configObj | ConvertTo-Json -Depth 10
    Set-Content -Path $configFile -Value $configJson -Encoding UTF8
    Write-Host "Registered OpenCode strict MCP with 15-min timeout: $configFile" -ForegroundColor Cyan
}

Write-Host "Agent Builder MCP Server successfully updated with 15-minute timeout!" -ForegroundColor Green
