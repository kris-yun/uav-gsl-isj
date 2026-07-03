# Claude Code CLI Launcher
# Runs the ablation task in non-interactive mode

$ErrorActionPreference = "Continue"
$logFile = "D:\ZYC\A-gas\automation\results\claude_cli_output.log"
$instruction = Get-Content "D:\ZYC\A-gas\automation\manual\phase1_ablation.txt" -Raw

Write-Host "$(Get-Date -Format 'HH:mm:ss') Starting Claude Code CLI..."
Write-Host "$(Get-Date -Format 'HH:mm:ss') Instruction: $($instruction.Substring(0, [Math]::Min(100, $instruction.Length)))..."

# Run claude in print mode with the instruction
$env:CLAUDE_CODE_ENTRYPOINT = "cli"
$result = & claude -p --dangerously-skip-permissions --add-dir "D:\ZYC\A-gas" $instruction 2>&1

$result | Out-File -FilePath $logFile -Encoding utf8
Write-Host "$(Get-Date -Format 'HH:mm:ss') Done! Output saved to $logFile"
Write-Host "$(Get-Date -Format 'HH:mm:ss') Output length: $($result.ToString().Length) chars"
