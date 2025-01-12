<#
.SYNOPSIS
    Network OS-level discovery tool using a service account.
.DESCRIPTION
    This script:
    1. Authenticates with a service account.
    2. Retrieves a list of computers from Active Directory.
    3. Queries OS-level information from each computer via WMI.
    4. Outputs discovery results to the console (and optionally CSV).

    Note: 
    - You must have RSAT (Remote Server Administration Tools) or 
      equivalent modules for AD commands to work (e.g., the ActiveDirectory module).
    - Make sure WinRM is enabled or WMI is open on the target hosts.
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ServiceAccountUsername,

    [Parameter(Mandatory=$true)]
    [string]$ServiceAccountPassword,

    [switch]$UseWinRM  # Toggle to demonstrate WinRM approach instead of WMI
)

# -----------------------
# 1. Secure the credentials
# -----------------------
try {
    # Convert clear-text password to SecureString
    $secPassword = ConvertTo-SecureString -String $ServiceAccountPassword -AsPlainText -Force
    # Create a credential object
    $credential = New-Object System.Management.Automation.PSCredential($ServiceAccountUsername, $secPassword)
}
catch {
    Write-Host "[!] Failed to create credential object. Error: $($_.Exception.Message)"
    return
}

# -----------------------
# 2. Get all domain-joined computers
# -----------------------
Write-Host "[*] Retrieving computers from Active Directory..."

try {
    Import-Module ActiveDirectory -ErrorAction Stop
    $computers = Get-ADComputer -Filter * -Properties OperatingSystem, DNSHostName | Select-Object -Unique
}
catch {
    Write-Host "[!] Error retrieving AD computers. Ensure you have RSAT installed and AD modules available."
    Write-Host "    Exception: $($_.Exception.Message)"
    return
}

Write-Host "[*] Found $($computers.Count) computers in Active Directory."

# -----------------------
# 3. Function for OS-level discovery
# -----------------------
function Get-OSInfoWMI {
    param(
        [string]$ComputerName,
        [System.Management.Automation.PSCredential]$Cred
    )

    # WMI query to Win32_OperatingSystem
    $osInfo = Get-WmiObject -Class Win32_OperatingSystem `
                            -ComputerName $ComputerName `
                            -Credential $Cred `
                            -ErrorAction Stop

    return $osInfo
}

function Get-OSInfoWinRM {
    param(
        [string]$ComputerName,
        [System.Management.Automation.PSCredential]$Cred
    )

    # Alternatively, use the WSMan/WinRM-based approach:
    # PowerShell remoting must be enabled on the remote machine.
    $session = New-PSSession -ComputerName $ComputerName -Credential $Cred -ErrorAction Stop
    $osInfo = Invoke-Command -Session $session -ScriptBlock {
        Get-CimInstance Win32_OperatingSystem
    }
    Remove-PSSession -Session $session
    return $osInfo
}

# -----------------------
# 4. Enumerate all systems concurrently
# -----------------------
# For better performance, use PowerShell jobs or ThreadJobs. 
# Below is an example using ThreadJobs (PowerShell 7+).
$results = foreach ($comp in $computers) {
    Start-ThreadJob -ScriptBlock {
        param($c, $useWinRM, $cred)

        # If the system is offline or you lack permissions, it’ll throw.
        # Wrap in try/catch for graceful handling.
        $result = [PSCustomObject]@{
            ComputerName = $c.Name
            DNSHostName  = $c.DNSHostName
            OS           = $null
            ServicePack  = $null
            Version      = $null
            LastBootUp   = $null
            Status       = "Failed"
        }

        try {
            if ($useWinRM) {
                $osData = Get-OSInfoWinRM -ComputerName $c.DNSHostName -Cred $cred
            } else {
                $osData = Get-OSInfoWMI   -ComputerName $c.DNSHostName -Cred $cred
            }

            $result.OS          = $osData.Caption
            $result.ServicePack = $osData.ServicePackMajorVersion
            $result.Version     = $osData.Version
            $result.LastBootUp  = $osData.ConvertToDateTime($osData.LastBootUpTime)
            $result.Status      = "Success"
        }
        catch {
            # Logging the error message for diagnostic
            $errorMsg = $_.Exception.Message
            $result.Status = "Error: $errorMsg"
        }

        return $result
    } -ArgumentList $comp, $UseWinRM, $credential
}

Write-Host "[*] Waiting for discovery jobs to complete..."
Wait-Job -Job $results | Out-Null

# Retrieve the results from each job
$finalResults = Receive-Job -Job $results

# Clean up jobs
Remove-Job -Job $results | Out-Null

# -----------------------
# 5. Output the final results
# -----------------------
Write-Host "`n===== Discovery Results ====="
$finalResults | Select-Object ComputerName, DNSHostName, OS, ServicePack, Version, LastBootUp, Status | 
    Format-Table -AutoSize

# Optionally, export the results to a CSV
# $finalResults | Export-Csv -NoTypeInformation -Path .\DiscoveryResults.csv

Write-Host "`n[*] Discovery complete!"
