# PowerShell secret scanner wrapper
param()

$pythonCmd = "python"
if (Test-Path "existing-code\.venv\Scripts\python.exe") {
    $pythonCmd = "existing-code\.venv\Scripts\python.exe"
}

& $pythonCmd scripts\scan_secrets.py
exit $LASTEXITCODE
