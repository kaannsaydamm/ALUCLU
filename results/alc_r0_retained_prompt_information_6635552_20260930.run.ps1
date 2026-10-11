$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$checkout = 'C:\Users\kaann\Desktop\03_Projeler_Arge\ALUCLU\.worktrees\unified-lifelong-cognition-local'
$research = 'C:\Users\kaann\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\ALUCLU\research\alc-r0-smollm2-135m-v1'
$evidence = 'C:\Users\kaann\Desktop\03_Projeler_Arge\ALUCLU\.research-evidence\alc_r0_retained_prompt_info_6635552_detached_v3_20260930'
$python = Join-Path $research 'windows-training\.venv\Scripts\python.exe'
$source = Join-Path $research 'datasets\primevul-original\authors-drive-19iLaNDS0z99N8kB_jBRTmDLehwZBolMY'
$pairs = Join-Path $research 'datasets\primevul-original-paired'
$model = Join-Path $research 'model\SmolLM2-135M-93efa2f'
$started = (Get-Date).ToUniversalTime().ToString('o')
$exitCode = 125
$status = 'launcher-error'
try {
    foreach ($path in @($checkout, $python, $source, $pairs, $model)) {
        if (-not (Test-Path -LiteralPath $path)) { throw "Required path missing: $path" }
    }
    $head = (& git -C $checkout rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $head -ne '66355527f9321b235084587855c23e3ec909fd30') { throw 'Source commit changed' }
    $changes = @(& git -C $checkout status --porcelain)
    if ($LASTEXITCODE -ne 0 -or $changes.Count -ne 0) { throw 'Source checkout is not clean' }
    $env:PYTHONPATH = 'src'
    $env:HF_HUB_OFFLINE = '1'
    $env:TRANSFORMERS_OFFLINE = '1'
    $env:HF_DATASETS_OFFLINE = '1'
    $env:TOKENIZERS_PARALLELISM = 'false'
    $arguments = @('-m', 'aluclu.alc_r0.retained_prompt_information', ('"' + $source + '"'), ('"' + $pairs + '"'), ('"' + $model + '"'))
    $worker = Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory $checkout -WindowStyle Hidden -RedirectStandardOutput (Join-Path $evidence 'stdout.log') -RedirectStandardError (Join-Path $evidence 'stderr.log') -PassThru
    $handle = $worker.Handle
    [System.IO.File]::WriteAllText((Join-Path $evidence 'launch.log'), "started_utc=$started`nlauncher_pid=$PID`npython_launcher_pid=$($worker.Id)`nsource_commit=$head`n")
    $worker.WaitForExit()
    $worker.Refresh()
    $exitCode = $worker.ExitCode
    $status = 'python-exited'
}
catch {
    [System.IO.File]::WriteAllText((Join-Path $evidence 'launcher.log'), ($_ | Out-String))
}
finally {
    $finished = (Get-Date).ToUniversalTime().ToString('o')
    [System.IO.File]::WriteAllText((Join-Path $evidence 'exit.log'), "started_utc=$started`nfinished_utc=$finished`nlauncher_pid=$PID`nsource_commit=66355527f9321b235084587855c23e3ec909fd30`nstatus=$status`npython_exit_code=$exitCode`n")
}
exit $exitCode
