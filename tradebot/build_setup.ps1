# Forward to project-root build_setup.ps1
$ErrorActionPreference = "Stop"
& (Join-Path (Split-Path $PSScriptRoot -Parent) "build_setup.ps1")
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
