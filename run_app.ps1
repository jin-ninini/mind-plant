$ErrorActionPreference = "Stop"

$script:streamlitProcess = $null

$cancelHandler = [ConsoleCancelEventHandler] {
    param($sender, $eventArgs)

    $eventArgs.Cancel = $true
    Write-Host ""
    Write-Host "Stopping MindPlant Streamlit server..."

    if ($script:streamlitProcess -and -not $script:streamlitProcess.HasExited) {
        Stop-Process -Id $script:streamlitProcess.Id -Force
    }

    exit 0
}

[Console]::CancelKeyPress += $cancelHandler

try {
    Write-Host ""
    Write-Host "========================================"
    Write-Host "Starting MindPlant Streamlit server..."
    Write-Host "Open the local URL shown by Streamlit in your browser."
    Write-Host "To stop the server, return to this terminal and press Ctrl+C."
    Write-Host "========================================"
    Write-Host ""

    $script:streamlitProcess = Start-Process `
        -FilePath "python" `
        -ArgumentList @("-m", "streamlit", "run", "src/app.py") `
        -NoNewWindow `
        -PassThru

    while (-not $script:streamlitProcess.HasExited) {
        Start-Sleep -Milliseconds 200
    }

    exit $script:streamlitProcess.ExitCode
}
finally {
    if ($script:streamlitProcess -and -not $script:streamlitProcess.HasExited) {
        Stop-Process -Id $script:streamlitProcess.Id -Force
    }
}
