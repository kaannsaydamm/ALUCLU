param(
    [string]$TectonicPath = "tectonic"
)

$ErrorActionPreference = "Stop"
$paperDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$outputDirectory = Join-Path $paperDirectory "build"
$sourcePath = Join-Path $paperDirectory "ALUCLU_paper.tex"
$compiledPath = Join-Path $outputDirectory "ALUCLU_paper.pdf"
$releasePath = Join-Path $paperDirectory "ALUCLU_paper.pdf"

if (-not (Get-Command $TectonicPath -ErrorAction SilentlyContinue)) {
    throw "Tectonic was not found. Install Tectonic 0.17+ or pass -TectonicPath."
}

New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null

Push-Location $paperDirectory
try {
    & $TectonicPath "ALUCLU_paper.tex" `
        "--outdir" "build" `
        "--keep-logs" `
        "--keep-intermediates"
    if ($LASTEXITCODE -ne 0) {
        throw "Tectonic compilation failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}

if (-not (Test-Path -LiteralPath $compiledPath -PathType Leaf)) {
    throw "Compilation completed without producing $compiledPath."
}

Copy-Item -LiteralPath $compiledPath -Destination $releasePath -Force
Write-Output "Built $releasePath"
