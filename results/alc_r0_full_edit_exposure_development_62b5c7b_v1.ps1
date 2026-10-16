param([switch]$PreflightOnly)
$ErrorActionPreference = 'Stop'
$taskCheckout = 'C:\Users\kaann\Desktop\03_Projeler_Arge\ALUCLU\.worktrees\unified-lifelong-cognition-local'
$taskExpectedCommit = '62b5c7b6577078db5aa79fd2822a9b2381286597'
$taskPython = 'C:\Users\kaann\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\ALUCLU\research\alc-r0-smollm2-135m-v1\windows-training\.venv\Scripts\python.exe'
$taskSource = 'C:\Users\kaann\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\ALUCLU\research\alc-r0-smollm2-135m-v1\datasets\primevul-original\authors-drive-19iLaNDS0z99N8kB_jBRTmDLehwZBolMY'
$taskPaired = 'C:\Users\kaann\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\ALUCLU\research\alc-r0-smollm2-135m-v1\datasets\primevul-original-paired'
$taskSnapshot = 'C:\Users\kaann\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\ALUCLU\research\alc-r0-smollm2-135m-v1\model\SmolLM2-135M-93efa2f'
$taskNative = 'C:\Users\kaann\Desktop\03_Projeler_Arge\ALUCLU\.research-evidence\alc_r0_banded_native_20261002\build-d739a35-v1\receipt.json'
$taskGeometry = Join-Path $taskCheckout 'results\alc_r0_banded_pair_resource_census_full_f7af513_20261003.stdout.log'
$taskStem = 'C:\Users\kaann\Desktop\03_Projeler_Arge\ALUCLU\.research-evidence\alc_r0_banded_native_20261002\full-edit-exposure-development-62b5c7b-v1'
Set-Location -LiteralPath $taskCheckout
$taskHead = git rev-parse HEAD
if ($LASTEXITCODE -ne 0 -or $taskHead -ne $taskExpectedCommit) { throw 'source freeze mismatch' }
$taskDirty = @(git status --porcelain --untracked-files=all)
if ($LASTEXITCODE -ne 0 -or $taskDirty.Count -ne 0) { throw 'source checkout is not clean' }
foreach ($taskPath in @($taskPython, $taskSource, $taskPaired, $taskSnapshot, $taskNative, $taskGeometry)) {
    if (-not (Test-Path -LiteralPath $taskPath)) { throw 'required pinned path missing' }
    if ($taskPath.Contains('"')) { throw 'path contains unsupported argument quote' }
}
$taskPins = @{
    $taskGeometry = '6ffd5f601d2aef5df092307b24dc21a7aefc12b211e849fadd4042d87e28adc7'
    $taskNative = 'ec5463427664884af4c2315031733fe3eb9a496abc84322b5fefba46db4e8d61'
    (Join-Path $taskCheckout 'src\aluclu\alc_r0\full_development_banded_edit_exposure.py') = '0e14a062d61d88e9412840f52dae7cde1f8768e8c0880ccb790a33e18a7415fe'
    (Join-Path $taskCheckout 'tests\test_alc_r0_full_development_banded_edit_exposure.py') = 'dc80d31c317cd4394cfa642da451d8fb8781ca035b1c0cd99d6b21d2ae49b571'
}
foreach ($taskPin in $taskPins.GetEnumerator()) {
    if ((Get-FileHash -LiteralPath $taskPin.Key -Algorithm SHA256).Hash.ToLower() -ne $taskPin.Value) { throw 'pinned bytes changed' }
}
foreach ($taskExtension in @('.stdout.log','.stderr.log','.exit.log','.launch.json','.observations.jsonl')) {
    if (Test-Path -LiteralPath ($taskStem + $taskExtension)) { throw 'artifact already exists; no retry/overwrite' }
}
$taskArguments = @('-B','-m','aluclu.alc_r0.full_development_banded_edit_exposure', $taskSource, $taskPaired, $taskSnapshot, $taskNative, $taskGeometry)
if ($PreflightOnly) {
    [pscustomobject]@{preflight_only=$true;source_commit=$taskHead;python=$taskPython;arguments=$taskArguments;working_directory=$taskCheckout} | ConvertTo-Json -Depth 4
    exit 0
}
$env:PYTHONPATH = 'src'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:TOKENIZERS_PARALLELISM = 'false'
$taskUtf8 = [System.Text.UTF8Encoding]::new($false)
$taskStarted = [DateTimeOffset]::UtcNow
$taskClock = [System.Diagnostics.Stopwatch]::StartNew()
# Start one child, hold this exact Process handle, no retry/resume or process-tree wait.
$taskChild = Start-Process -FilePath $taskPython -ArgumentList $taskArguments -WorkingDirectory $taskCheckout -WindowStyle Hidden -PassThru -RedirectStandardOutput ($taskStem + '.stdout.log') -RedirectStandardError ($taskStem + '.stderr.log')
$taskLaunch = [pscustomobject]@{
    source_commit=$taskHead;wrapper_pid=$PID;child_pid=$taskChild.Id;started_utc=$taskStarted.ToString('o')
    python=$taskPython;arguments=$taskArguments;working_directory=$taskCheckout
    launcher_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLower()
    training_authority=$false;held_out_data_present=$false
}
[System.IO.File]::WriteAllText($taskStem + '.launch.json', ($taskLaunch | ConvertTo-Json -Depth 5) + "`n", $taskUtf8)
$taskSampledPeakRss = [int64]0
$taskSampledPeakPrivate = [int64]0
$taskLastCpu = $null
while (-not $taskChild.HasExited) {
    # Observations do not change the workload, kill it, or classify math results.
    try {
        $taskChild.Refresh()
        # Windows venv python.exe is a launcher. Observe its exact module worker,
        # not the tiny launcher, and fail observation closed if identity is unclear.
        $taskWorkers = @(Get-CimInstance Win32_Process -Filter ("ParentProcessId=" + $taskChild.Id + " AND name='python.exe'") | Where-Object { $_.CommandLine -like '* -m aluclu.alc_r0.full_development_banded_edit_exposure *' })
        if ($taskWorkers.Count -ne 1) { throw 'exact Python worker not yet available' }
        $taskWorker = Get-Process -Id $taskWorkers[0].ProcessId -ErrorAction Stop
        $taskRss = [int64]$taskWorker.WorkingSet64
        $taskPrivate = [int64]$taskWorker.PrivateMemorySize64
        $taskCpu = $taskWorker.TotalProcessorTime.TotalSeconds
        $taskSampledPeakRss = [Math]::Max($taskSampledPeakRss, $taskRss)
        $taskSampledPeakPrivate = [Math]::Max($taskSampledPeakPrivate, $taskPrivate)
        $taskLastCpu = $taskCpu
        $taskObservation = [pscustomobject]@{utc=[DateTimeOffset]::UtcNow.ToString('o');launcher_pid=$taskChild.Id;worker_pid=$taskWorker.Id;scope='exact-module-worker';cpu_seconds=$taskCpu;working_set_bytes=$taskRss;private_bytes=$taskPrivate;elapsed_seconds=$taskClock.Elapsed.TotalSeconds}
        [System.IO.File]::AppendAllText($taskStem + '.observations.jsonl', ($taskObservation | ConvertTo-Json -Compress) + "`n", $taskUtf8)
    } catch {
        # An observation race is not terminal; the same Process handle remains authoritative.
        [System.IO.File]::AppendAllText($taskStem + '.observations.jsonl', ('{"observation_unavailable":true,"utc":"' + [DateTimeOffset]::UtcNow.ToString('o') + '"}') + "`n", $taskUtf8)
    }
    Start-Sleep -Seconds 2
}
$taskChild.WaitForExit()
$taskChild.Refresh()
$taskClock.Stop()
if ($null -eq $taskChild.ExitCode) { throw 'actual child exit unavailable; no success inference' }
$taskActualExit = [int]$taskChild.ExitCode
$taskTerminal = [pscustomobject]@{
    actual_exposure_exit_code=$taskActualExit;source_commit=$taskHead;child_pid=$taskChild.Id
    finished_utc=[DateTimeOffset]::UtcNow.ToString('o');elapsed_seconds=$taskClock.Elapsed.TotalSeconds
    sampled_peak_working_set_bytes=$taskSampledPeakRss;sampled_peak_private_bytes=$taskSampledPeakPrivate
    last_observed_cpu_seconds=$taskLastCpu;observations_are_sampled_not_guaranteed_os_peaks=$true
    observation_scope='exact-module-worker-not-venv-launcher'
    stdout_sha256=(Get-FileHash -LiteralPath ($taskStem + '.stdout.log') -Algorithm SHA256).Hash.ToLower()
    stderr_sha256=(Get-FileHash -LiteralPath ($taskStem + '.stderr.log') -Algorithm SHA256).Hash.ToLower()
    training_authority=$false;held_out_data_present=$false
}
[System.IO.File]::WriteAllText($taskStem + '.exit.log', ($taskTerminal | ConvertTo-Json -Depth 4) + "`n", $taskUtf8)
exit $taskActualExit
