# Check if running as administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    # Not running as admin, re-launch as admin
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

try {
    # Define the new hosts content
    $newHostsContent = @"
127.0.0.1       localhost
::1             localhost

# Block example sites
0.0.0.0         chatgpt.com
0.0.0.0         gemini.google.com
0.0.0.0         google.com
0.0.0.0         www.google.com
0.0.0.0         brainly.co.id
0.0.0.0         copilot.microsoft.com
0.0.0.0         claude.ai
0.0.0.0         www.meta.ai
0.0.0.0         meta.ai
0.0.0.0         youtube.com
0.0.0.0         www.youtube.com
0.0.0.0         m.youtube.com
0.0.0.0         chat.qwen.ai
0.0.0.0         chat.deepseek.com
0.0.0.0         www.deepseek.com
0.0.0.0         www.tiktok.com
0.0.0.0         m.tiktok.com
0.0.0.0         tiktok.com
0.0.0.0         bing.com
0.0.0.0         www.bing.com
"@

    # Path to the hosts file
    $hostsPath = "$env:SystemRoot\System32\drivers\etc\hosts"

    # Optional: Backup existing hosts file
    Copy-Item -Path $hostsPath -Destination "$hostsPath.bak" -Force

    # Replace the hosts file content
    Set-Content -Path $hostsPath -Value $newHostsContent -Force -Encoding ASCII

    Write-Output "Hosts file successfully replaced."
    ipconfig /flushdns

}
catch {
    Write-Host "An error occurred: $_" -ForegroundColor Red
}

