param(
    [string]$Workspace = $env:PAPER_READER_WORKSPACE,
    [int]$Port = 8765,
    [string]$BindHost = "127.0.0.1",
    [switch]$NoOpen
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$envPath = Join-Path $scriptDir ".env"
if (Test-Path -LiteralPath $envPath) {
    [System.IO.File]::ReadLines($envPath, [System.Text.Encoding]::UTF8) | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) { return }
        if ($line -match '^export\s+(.+)$') { $line = $Matches[1].Trim() }
        if ($line -notmatch '^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') { return }
        $key = $Matches[1]
        $value = $Matches[2].Trim()
        if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        if (-not [Environment]::GetEnvironmentVariable($key, "Process")) {
            Set-Item -Path "Env:$key" -Value $value
        }
    }
}
if (-not $Workspace) {
    $Workspace = $env:PAPER_READER_WORKSPACE
}
if (-not $Workspace) {
    $Workspace = Join-Path $scriptDir "paper_reading_workspace"
}
$workspacePath = [System.IO.Path]::GetFullPath($Workspace)
$agent = Join-Path $scriptDir "paper_reader_agent.py"
$url = "http://$BindHost`:$Port/"

function Test-ReaderServer {
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 1
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

if (-not (Test-ReaderServer)) {
    $arguments = @("-3", "`"$agent`"", "--workspace", "`"$workspacePath`"", "serve", "--host", $BindHost, "--port", "$Port")
    if (-not $NoOpen) {
        $arguments += "--open"
    }
    Start-Process -FilePath "py" -ArgumentList $arguments -WindowStyle Minimized
} elseif (-not $NoOpen) {
    Start-Process $url
}
