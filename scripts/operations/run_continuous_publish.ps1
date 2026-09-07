param(
    [string]$Profile = "opcenter2607-core",
    [ValidateSet("dev", "uat", "prod")]
    [string]$Environment = "dev",
    [string]$Actor = "cronjob"
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Push-Location $projectRoot
try {
    python -m src.graphstudio_sync.cli continuous-publish `
        --job camstar-full `
        --profile $Profile `
        --environment $Environment `
        --actor $Actor `
        --apply
    if ($LASTEXITCODE -ne 0) {
        throw "Continuous Graph Studio publication failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}
