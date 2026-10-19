param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-f]{40}$')]
    [string]$ExpectedCommit
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$taskCheckout = 'C:\Users\kaann\Desktop\03_Projeler_Arge\ALUCLU\.worktrees\alc-r0-edit-visibility-reference'
$taskResearch = 'C:\Users\kaann\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\ALUCLU\research\alc-r0-smollm2-135m-v1'
$taskEvidence = $PSScriptRoot
$taskPython = Join-Path $taskResearch 'windows-training\.venv\Scripts\python.exe'
$taskSource = Join-Path $taskResearch 'datasets\primevul-original\authors-drive-19iLaNDS0z99N8kB_jBRTmDLehwZBolMY'
$taskPairs = Join-Path $taskResearch 'datasets\primevul-original-paired'
$taskModel = Join-Path $taskResearch 'model\SmolLM2-135M-93efa2f'

# Refuse to overwrite evidence of an earlier attempt, including a partial one.
foreach ($taskName in @('stdout.log', 'stderr.log', 'launch.log', 'launcher.log', 'exit.log')) {
    if (Test-Path -LiteralPath (Join-Path $taskEvidence $taskName)) {
        throw "Attempt evidence already exists: $taskName"
    }
}

$taskStarted = (Get-Date).ToUniversalTime().ToString('o')
$taskExitCode = 125
$taskPythonExitCode = 'not-started'
$taskReceiptCommit = 'not-verified'
$taskStatus = 'launcher-error'
try {
    foreach ($taskPath in @($taskCheckout, $taskPython, $taskSource, $taskPairs, $taskModel)) {
        if (-not (Test-Path -LiteralPath $taskPath)) { throw "Required path missing: $taskPath" }
    }
    $taskHead = (& git -C $taskCheckout rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $taskHead -ne $ExpectedCommit) { throw 'Source commit changed' }
    $taskChanges = @(& git -C $taskCheckout status --porcelain=v1 --untracked-files=all)
    if ($LASTEXITCODE -ne 0 -or $taskChanges.Count -ne 0) { throw 'Source checkout is not clean' }
    $env:PYTHONPATH = 'src'
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $env:PYTHONUNBUFFERED = '1'
    $env:HF_HUB_OFFLINE = '1'
    $env:TRANSFORMERS_OFFLINE = '1'
    $env:HF_DATASETS_OFFLINE = '1'
    $env:TOKENIZERS_PARALLELISM = 'false'
    $taskArguments = @('-m', 'aluclu.alc_r0.retained_pair_resource_census', ('"' + $taskSource + '"'), ('"' + $taskPairs + '"'), ('"' + $taskModel + '"'))
    $taskWorker = Start-Process -FilePath $taskPython -ArgumentList $taskArguments -WorkingDirectory $taskCheckout -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskEvidence 'stdout.log') -RedirectStandardError (Join-Path $taskEvidence 'stderr.log') -PassThru
    $taskHandle = $taskWorker.Handle
    [System.IO.File]::WriteAllText((Join-Path $taskEvidence 'launch.log'), "started_utc=$taskStarted`nlauncher_pid=$PID`npython_launcher_pid=$($taskWorker.Id)`nrequested_source_commit=$ExpectedCommit`nmodule=aluclu.alc_r0.retained_pair_resource_census`n")
    $taskWorker.WaitForExit()
    $taskWorker.Refresh()
    $taskExitCode = $taskWorker.ExitCode
    $taskPythonExitCode = $taskExitCode
    $taskStatus = 'python-exited'
    if ($taskPythonExitCode -eq 0) {
        $taskReceipt = Get-Content -LiteralPath (Join-Path $taskEvidence 'stdout.log') -Raw | ConvertFrom-Json
        $taskReceiptCommit = $taskReceipt.source_checkout.source_commit
        if ($taskReceiptCommit -ne $ExpectedCommit) { throw 'Successful Python receipt has a different source commit' }
        $taskTerminalHead = (& git -C $taskCheckout rev-parse HEAD).Trim()
        if ($LASTEXITCODE -ne 0 -or $taskTerminalHead -ne $ExpectedCommit) { throw 'Source commit changed before launcher completion' }
        $taskTerminalChanges = @(& git -C $taskCheckout status --porcelain=v1 --untracked-files=all)
        if ($LASTEXITCODE -ne 0 -or $taskTerminalChanges.Count -ne 0) { throw 'Source checkout changed before launcher completion' }
    }
}
catch {
    $taskExitCode = 125
    $taskStatus = 'launcher-error'
    [System.IO.File]::WriteAllText((Join-Path $taskEvidence 'launcher.log'), ($_ | Out-String))
}
finally {
    $taskFinished = (Get-Date).ToUniversalTime().ToString('o')
    [System.IO.File]::WriteAllText((Join-Path $taskEvidence 'exit.log'), "started_utc=$taskStarted`nfinished_utc=$taskFinished`nlauncher_pid=$PID`nrequested_source_commit=$ExpectedCommit`nreceipt_source_commit=$taskReceiptCommit`nstatus=$taskStatus`npython_exit_code=$taskPythonExitCode`nlauncher_exit_code=$taskExitCode`n")
}
exit $taskExitCode
