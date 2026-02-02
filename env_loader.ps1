.\.venv\Scripts\Activate.ps1
Get-Content .\.env | ForEach-Object {
  $line = $_.Trim()
  if (-not $line -or $line.StartsWith("#")) { return }
  $k, $v = $line.Split("=", 2)
  [Environment]::SetEnvironmentVariable($k, $v, "Process")
}

Write-Output "Ready. Now run: dbl-gateway serve --host 127.0.0.1 --port 8010"
