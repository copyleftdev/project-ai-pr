<#
.SYNOPSIS
    Secure Network OS-level discovery tool using a service account.

.DESCRIPTION
    - This refactored script avoids storing the service account password 
      in plain text or script parameters.
    - Instead, it either prompts for credentials (Approach A) or retrieves 
      them securely from the Windows Credential Manager (Approach B).
    - Recommends using WinRM over HTTPS or a secured WMI channel to mitigate 
      network-level security concerns.

.NOTES
    - You must have RSAT (or equivalent AD modules) to run ActiveDirectory commands.
    - Ensure remote hosts allow secure WMI or WinRM communication.
    - Requires PowerShell 7+ for ThreadJobs (or adjust accordingly).
#>

param(
    [switch]$UseWinRM  # Toggle to demonstrate WinRM approach instead of WMI
)

Import-Module ActiveDirectory -ErrorAction Stop

# -----------------------
# Choose either Approach A or Approach B
# -----------------------

# APPROACH A: Prompt the user for credentials at runtime.
# $credential = Get-Credential -Message "Please enter the service account credentials"

# APPROACH B: Retrieve credentials from the Windows Credential Manager.
# To use this approach:
#   1) Ensure you've stored credentials in Windows Credential Manager
#      e.g., via cmdkey.exe:
#         cmdkey /add:MYDOMAIN\ServiceAccount /user:MYDOMAIN\ServiceAccount /pass
#   2) Then set $TargetCredentialName accordingly.
#   3) Use the CredentialManager module or a custom function (below) to retrieve it.

$TargetCredentialName = "MYDOMAIN\\ServiceAccount"

function Get-StoredCredential {
    param(
        [Parameter(Mandatory=$true)]
        [string]$TargetName
    )
    # This function requires the CredentialManager module or a custom method to pull from Windows.
    # In PowerShell 7+, you can install the 'CredentialManager' module from the PSGallery:
    #    Install-Module CredentialManager
    # Then:
    #    return Get-StoredCredential -Target $TargetName
    #
    # For demonstration, here's a simplified example:
    try {
        if (Get-Module -ListAvailable -Name CredentialManager) {
            Import-Module CredentialManager -ErrorAction Stop
            $cred = Get-StoredCredential -Target $TargetName
            if (!$cred) {
                throw "No stored credential found for $TargetName."
            }
            return $cred
        }
        else {
            throw "The CredentialManager module is not installed. Please install it or switch to Approach A."
        }
    }
    catch {
        Write-Error "[!] Failed to retrieve stored credential: $($_.Exception.Message)"
        return $null
    }
}

# Uncomment whichever approach you prefer:
# $credential = Get-Credential -Message "Please enter the service account credentials"
$credential = Get-StoredCredential -TargetName $TargetCredentialName

if (-not $credential) {
    Write-Error "[!] No credential found or provided. Exiting script."
    return
}

# -----------------------
# 1. Get all domain-joined computers
# -----------------------
Write-Host "[*] Retrieving computers from Active Directory..."

try {
    # Example: Retrieve all computers
    # For security, consider filtering by specific OU or computer name pattern
    $computers = Get-ADComputer -Filter * -Properties OperatingSystem, DNSHostName | Select-Object -Unique
}
catch {
    Write-Host "[!] Error retrieving AD computers: $($_.Exception.Message)"
    return
}

Write-Host "[*] Found $($computers.Count) computers in Active Directory."

# -----------------------
# 2. Functions for OS-level discovery
# -----------------------
function Get-OSInfoWMI {
    param(
        [string]$ComputerName,
        [System.Management.Automation.PSCredential]$Cred
    )
    # In a secure environment, you might set up IPsec or other encryption for WMI 
    # to protect these queries over the network.
    # Also ensure the account has appropriate permissions on the remote system.
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
    # For best security, consider configuring WinRM over HTTPS.
    # See: https://docs.microsoft.com/powershell/scripting/learn/remoting/winrmsecurity
    $session = $null
    try {
        $session = New-PSSession -ComputerName $ComputerName -UseSSL -Credential $Cred -ErrorAction Stop
        $osInfo = Invoke-Command -Session $session -ScriptBlock {
            Get-CimInstance Win32_OperatingSystem
        }
    }
    finally {
        if ($session) {
            Remove-PSSession -Session $session
        }
    }
    return $osInfo
}

# -----------------------
# 3. Enumerate systems concurrently
# -----------------------
$jobs = foreach ($comp in $computers) {
    Start-ThreadJob -ScriptBlock {
        param($c, $useWinRM, $cred)

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
                $osData = Get-OSInfoWMI -ComputerName $c.DNSHostName -Cred $cred
            }

            $result.OS          = $osData.Caption
            $result.ServicePack = $osData.ServicePackMajorVersion
            $result.Version     = $osData.Version
            $result.LastBootUp  = $osData.ConvertToDateTime($osData.LastBootUpTime)
            $result.Status      = "Success"
        }
        catch {
            $result.Status = "Error: " + $_.Exception.Message
        }

        return $result
    } -ArgumentList $comp, $UseWinRM, $credential
}

Write-Host "[*] Waiting for discovery jobs to complete..."
Wait-Job -Job $jobs | Out-Null

# Collect results
$finalResults = Receive-Job -Job $jobs

# Clean up
Remove-Job -Job $jobs | Out-Null

# -----------------------
# 4. Output the final results
# -----------------------
Write-Host "`n===== Discovery Results ====="
$finalResults | 
    Select-Object ComputerName, DNSHostName, OS, ServicePack, Version, LastBootUp, Status |
    Format-Table -AutoSize

# Optional: export to CSV
# $finalResults | Export-Csv -NoTypeInformation -Path .\DiscoveryResults.csv

Write-Host "`n[*] Discovery complete!"
