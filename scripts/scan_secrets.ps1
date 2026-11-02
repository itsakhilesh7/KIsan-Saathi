# PowerShell secret scanner wrapper
param()

$pythonCmd = "python"
if (Test-Path ".\.venv\Scripts\python.exe") {
    $pythonCmd = ".\.venv\Scripts\python.exe"
}

& $pythonCmd scripts\scan_secrets.py
exit $LASTEXITCODE

