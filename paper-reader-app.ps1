param(
    [string]$Workspace = $env:PAPER_READER_WORKSPACE,
    [int]$Port = 8765,
    [string]$BindHost = "127.0.0.1",
    [switch]$NoOpen
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
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
