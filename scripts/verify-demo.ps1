# Phase 10.2/10.3 integration check — runs the automatable parts of the
# verification checklist against a live backend. Requires the backend to be
# running with the demo_migration.sql applied to the target Supabase.
#
# Usage:
#   .\scripts\verify-demo.ps1                  # defaults to http://localhost:8000
#   .\scripts\verify-demo.ps1 -BaseUrl <url>   # point at another host
#
# Items 5 (refresh-restore), 6 (16th-prompt upsell), 7 (.docx finalize),
# 12 (parent platform claim handoff), 16 (30-day expiry), and 17 (cookie wipe)
# are not automatable here — they need a browser session or wall-clock time.

[CmdletBinding()]
param(
    [string]$BaseUrl = "http://localhost:8000",
    [int]$HourlyLimit = 3
)

$ErrorActionPreference = "Stop"
$script:Passed = 0
$script:Failed = 0
$script:Results = @()

function Assert-Condition {
    param(
        [string]$Name,
        [bool]$Condition,
        [string]$Detail = ""
    )
    if ($Condition) {
        $script:Passed++
        Write-Host ("  PASS  {0}" -f $Name) -ForegroundColor Green
    }
    else {
        $script:Failed++
        Write-Host ("  FAIL  {0}" -f $Name) -ForegroundColor Red
        if ($Detail) { Write-Host ("        {0}" -f $Detail) -ForegroundColor DarkGray }
    }
    $script:Results += [pscustomobject]@{ Name = $Name; Passed = $Condition; Detail = $Detail }
}

function Invoke-Demo {
    param(
        [string]$Method = "GET",
        [string]$Path,
        [Microsoft.PowerShell.Commands.WebRequestSession]$Session,
        $Body = $null,
        [hashtable]$Headers = @{}
    )
    $params = @{
        Method          = $Method
        Uri             = "$BaseUrl$Path"
        WebSession      = $Session
        Headers         = $Headers
        UseBasicParsing = $true
        SkipHttpErrorCheck = $true
        ErrorAction     = "Stop"
    }
    if ($null -ne $Body) {
        $params.Body = ($Body | ConvertTo-Json -Compress)
        $params.ContentType = "application/json"
    }
    Invoke-WebRequest @params
}

Write-Host "Verifying demo backend at $BaseUrl" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------------------------
# Section 1 — root health + dead routers (checklist items 13-15)
# ---------------------------------------------------------------------------
Write-Host "[1/4] Health + dead routers" -ForegroundColor Yellow

$rootSession = [Microsoft.PowerShell.Commands.WebRequestSession]::new()
$root = Invoke-Demo -Path "/" -Session $rootSession
Assert-Condition "Root returns 200" ($root.StatusCode -eq 200) $root.StatusCode

foreach ($dead in @(
    @{ Method = "POST"; Path = "/api/auth/login" },
    @{ Method = "GET";  Path = "/api/auth/me" },
    @{ Method = "GET";  Path = "/api/external_auth/callback" },
    @{ Method = "GET";  Path = "/api/datasets" },
    @{ Method = "POST"; Path = "/api/generate" },
    @{ Method = "GET";  Path = "/api/projects/00000000-0000-0000-0000-000000000000" }
)) {
    $resp = Invoke-Demo -Method $dead.Method -Path $dead.Path -Session $rootSession
    Assert-Condition ("{0} {1} -> 404" -f $dead.Method, $dead.Path) ($resp.StatusCode -eq 404) ("got {0}" -f $resp.StatusCode)
}

# ---------------------------------------------------------------------------
# Section 2 — session cookie minting + reuse (items 1, 5)
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[2/4] Session cookie minting" -ForegroundColor Yellow

$s1 = [Microsoft.PowerShell.Commands.WebRequestSession]::new()
$mint = Invoke-Demo -Path "/api/demo" -Session $s1
Assert-Condition "GET /api/demo (mint) returns 200" ($mint.StatusCode -eq 200) $mint.StatusCode

$setCookie = ($mint.Headers["Set-Cookie"] | ForEach-Object { $_ }) -join "; "
Assert-Condition "Set-Cookie includes demo_session_id" ($setCookie -match "demo_session_id=") $setCookie
Assert-Condition "Cookie is HttpOnly"                  ($setCookie -match "(?i)httponly") $setCookie
Assert-Condition "Cookie is SameSite=Lax"              ($setCookie -match "(?i)samesite=lax") $setCookie

$mintBody = $mint.Content | ConvertFrom-Json
$firstId = $mintBody.session_id
Assert-Condition "Mint body has UUID session_id" `
    ($firstId -match "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$") `
    $firstId

$reuse = Invoke-Demo -Path "/api/demo" -Session $s1
$reuseBody = $reuse.Content | ConvertFrom-Json
Assert-Condition "Second GET reuses the same session_id" ($reuseBody.session_id -eq $firstId) ("{0} != {1}" -f $reuseBody.session_id, $firstId)

# ---------------------------------------------------------------------------
# Section 3 — CRUD round trip (items 4 indirectly, plus PUT/DELETE)
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[3/4] /api/demo CRUD" -ForegroundColor Yellow

$put = Invoke-Demo -Method "PUT" -Path "/api/demo" -Session $s1 -Body @{
    grant_id    = "verify-script-grant"
    template_id = "verify-script-template"
}
Assert-Condition "PUT /api/demo returns 200" ($put.StatusCode -eq 200) $put.StatusCode
$putBody = $put.Content | ConvertFrom-Json
Assert-Condition "PUT round-trips grant_id"    ($putBody.grant_id -eq "verify-script-grant")    $putBody.grant_id
Assert-Condition "PUT round-trips template_id" ($putBody.template_id -eq "verify-script-template") $putBody.template_id

$del = Invoke-Demo -Method "DELETE" -Path "/api/demo" -Session $s1
Assert-Condition "DELETE /api/demo returns 200" ($del.StatusCode -eq 200) $del.StatusCode
$delBody = $del.Content | ConvertFrom-Json
Assert-Condition "DELETE returns status=reset"  ($delBody.status -eq "reset") $delBody.status
Assert-Condition "DELETE keeps the same session_id" ($delBody.session_id -eq $firstId) $delBody.session_id

# ---------------------------------------------------------------------------
# Section 4 — IP rate limit (checklist item 11)
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[4/4] IP rate limit (HourlyLimit=$HourlyLimit)" -ForegroundColor Yellow
Write-Host "  Note: requires DEMO_IP_HOURLY_LIMIT=$HourlyLimit on the backend." -ForegroundColor DarkGray

$rateCodes = @()
for ($i = 1; $i -le ($HourlyLimit + 2); $i++) {
    # Fresh session each time to force the mint branch.
    $s = [Microsoft.PowerShell.Commands.WebRequestSession]::new()
    $r = Invoke-Demo -Path "/api/demo" -Session $s
    $rateCodes += $r.StatusCode
}

$first200Count = ($rateCodes | Where-Object { $_ -eq 200 } | Measure-Object).Count
$last429Count  = ($rateCodes | Where-Object { $_ -eq 429 } | Measure-Object).Count
Assert-Condition "First $HourlyLimit mint attempts return 200" ($first200Count -ge $HourlyLimit) ("codes: {0}" -f ($rateCodes -join ","))
Assert-Condition "Subsequent attempts return 429"              ($last429Count -ge 1)             ("codes: {0}" -f ($rateCodes -join ","))

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor DarkGray
$total = $script:Passed + $script:Failed
Write-Host ("Verification: {0}/{1} passed" -f $script:Passed, $total) `
    -ForegroundColor $(if ($script:Failed -eq 0) { "Green" } else { "Red" })

if ($script:Failed -gt 0) { exit 1 } else { exit 0 }
