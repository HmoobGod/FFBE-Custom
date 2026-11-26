# FFBE-Custom revision 13 resource recovery (Windows PowerShell 5.1+).
# Downloads only original manifest-listed ZIPs. No APK, key, saves or install.
param([string]$Destination = 'E:\FFBE-Revision13')
$ErrorActionPreference = 'Stop'
$pin = '3f77a7c1f7e13dfbd9343fcb023a2cd609c7669bd44fec09d530cf25881ad093'
$source = 'https://raw.githubusercontent.com/Elvlin/exvius-offline/b520e563cbc4364a07ee40331012340dc8aeb841/data/latest.json'
New-Item -ItemType Directory -Path $Destination -Force | Out-Null
$manifest = Join-Path $Destination 'latest.json'
function Test-Exact([string]$Path,[long]$Size,[string]$Hash) {
    if (!(Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
    if ((Get-Item -LiteralPath $Path).Length -ne $Size) { return $false }
    return ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ieq $Hash)
}
if (!(Test-Exact $manifest 7110 $pin)) {
    if (Test-Path -LiteralPath $manifest) { throw "Existing manifest mismatch. Keep it separately and retry in a clean directory." }
    $tmp = "$manifest.part"
    & curl.exe --fail --location --retry 3 --output $tmp $source
    if ($LASTEXITCODE -ne 0 -or !(Test-Exact $tmp 7110 $pin)) { throw 'Manifest retrieval or verification failed.' }
    Move-Item -LiteralPath $tmp -Destination $manifest
}
$m = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
if ($m.revision -ne 13 -or $m.minAppVersionCode -ne 9076 -or $m.packs.Count -ne 23) { throw 'Unexpected manifest' }
$names = @{}
$receipt = @()
foreach ($p in $m.packs) {
    $u = [uri]$p.url
    $name = [IO.Path]::GetFileName($u.AbsolutePath)
    if ($u.Scheme -ne 'https' -or $u.Host -ne 'github.com' -or !$u.AbsolutePath.StartsWith('/Elvlin/exvius-offline/releases/download/') -or $name -notmatch '^exvius-[a-z0-9-]+\.zip$' -or $names.ContainsKey($name)) { throw 'Unexpected archive URL or duplicate name' }
    $names[$name] = $true
    $file = Join-Path $Destination $name
    $part = "$file.part"
    if (!(Test-Exact $file ([long]$p.size) $p.sha256)) {
        if (Test-Path -LiteralPath $file) { throw "Existing archive mismatch: $file. Move it out of this folder and retry." }
        if (Test-Path -LiteralPath $part) {
            if (Test-Exact $part ([long]$p.size) $p.sha256) { Move-Item -LiteralPath $part -Destination $file }
            elseif ((Get-Item -LiteralPath $part).Length -ge [long]$p.size) { throw "Invalid completed partial file: $part. Move it out and retry." }
        }
        if (!(Test-Path -LiteralPath $file)) {
            Write-Host "Downloading $name"
            & curl.exe --fail --location --retry 3 --continue-at - --output $part $p.url
            if ($LASTEXITCODE -ne 0) { throw "Download interrupted: $name. Re-run this script to resume. If the server rejects resume, move the partial file out first." }
            if (!(Test-Exact $part ([long]$p.size) $p.sha256)) { throw "Downloaded archive hash/size mismatch: $name" }
            Move-Item -LiteralPath $part -Destination $file
        }
    }
    Write-Host "PASS $name"
    $receipt += [pscustomobject]@{name=$name;size=[long]$p.size;sha256=$p.sha256}
}
$receiptPath = Join-Path $Destination 'verified-packs.json'
[pscustomobject]@{revision=13;manifestSha256=$pin;verifiedCount=$receipt.Count;packs=$receipt} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
Write-Host "PASS: all 23 original ZIP archives and manifest verified in $Destination"
