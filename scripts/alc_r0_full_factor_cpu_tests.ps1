param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Focused', 'Regression')]
    [string]$Suite,
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9_]{1,100}$')]
    [string]$ArtifactStem
)

# Fixed fake/pure CPU tests only. Not an actual-host or GPU launcher.
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$taskPython = 'C:\Users\kaann\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\ALUCLU\research\alc-r0-smollm2-135m-v1\windows-training\.venv\Scripts\python.exe'
$taskTests = if ($Suite -eq 'Focused') {
    @('tests/test_alc_r0_reference_stress_full_factors.py')
} else {
    @(
        'tests/test_alc_r0_reference_stress_execution.py',
        'tests/test_alc_r0_reference_stress_start.py',
        'tests/test_alc_r0_reference_stress_inputs.py',
        'tests/test_alc_r0_reference_qv_artifact.py',
        'tests/test_alc_r0_reference_qv_optimizer.py',
        'tests/test_alc_r0_parity_factory.py',
        'tests/test_alc_r0_checkpoint_optimizer.py'
    )
}
$taskPrefix = Join-Path (Join-Path $taskRoot 'results') $ArtifactStem
foreach ($suffix in @('.stdout.log', '.stderr.log', '.exit.log', '.xml', '.start.json')) {
    if (Test-Path -LiteralPath ($taskPrefix + $suffix)) {
        throw 'Existing evidence must not be overwritten; use a fresh stem.'
    }
}
if (-not (Test-Path -LiteralPath $taskPython -PathType Leaf)) {
    throw 'Existing pinned Python runtime missing; no installation permitted.'
}
foreach ($taskTest in $taskTests) {
    if (-not (Test-Path -LiteralPath (Join-Path $taskRoot $taskTest) -PathType Leaf)) {
        throw "Fixed test missing: $taskTest"
    }
}
$taskMemory = Get-CimInstance Win32_OperatingSystem
if ($taskMemory.FreePhysicalMemory -lt 1048576 -or $taskMemory.FreeVirtualMemory -lt 3145728) {
    throw 'Defer CPU test: below operational memory headroom, not a scientific failure.'
}
foreach ($taskProcess in (Get-CimInstance Win32_Process)) {
    if ($taskProcess.CommandLine -match '\bpytest\b') {
        foreach ($taskTest in $taskTests) {
            if ($taskProcess.CommandLine.Contains($taskTest)) {
                throw 'Potential duplicate fixed test is live; do not relaunch.'
            }
        }
    }
}
$taskArgs = @('-m', 'pytest') + $taskTests + @('-q', "--junitxml=results/$ArtifactStem.xml")
$taskStarted = [DateTimeOffset]::Now
$taskStart = [ordered]@{
    suite = $Suite
    python = $taskPython
    worktree = $taskRoot
    arguments = $taskArgs
    started_at = $taskStarted.ToString('o')
    free_physical_kib = $taskMemory.FreePhysicalMemory
    free_virtual_kib = $taskMemory.FreeVirtualMemory
    scope = 'FAKE_PURE_CPU_ONLY_NOT_HOST_RESOURCE_OR_LEARNING_ACCEPTANCE'
}
[IO.File]::WriteAllText($taskPrefix + '.start.json', ($taskStart | ConvertTo-Json -Depth 4), [Text.UTF8Encoding]::new($false))
$taskOldPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = Join-Path $taskRoot 'src'
    $taskChild = Start-Process -FilePath $taskPython -ArgumentList $taskArgs `
        -WorkingDirectory $taskRoot -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput ($taskPrefix + '.stdout.log') `
        -RedirectStandardError ($taskPrefix + '.stderr.log')
    # Retain the native handle before exit; Windows PowerShell may otherwise
    # expose a null ExitCode after WaitForExit/Refresh for Start-Process children.
    $taskHandle = $taskChild.Handle
    if ($taskHandle -eq [IntPtr]::Zero) { throw 'Child handle unavailable.' }
    $taskChild.WaitForExit()
    $taskChild.Refresh()
    $taskExit = $taskChild.ExitCode
    if ($null -eq $taskExit) { throw 'Child exit unavailable; do not manufacture exit evidence.' }
    $taskTerminal = "pytest_exit_code=$taskExit`nchild_pid=$($taskChild.Id)`nobserved_at=$([DateTimeOffset]::Now.ToString('o'))`n"
    [IO.File]::WriteAllText($taskPrefix + '.exit.log', $taskTerminal, [Text.UTF8Encoding]::new($false))
    exit $taskExit
} finally {
    $env:PYTHONPATH = $taskOldPath
}
