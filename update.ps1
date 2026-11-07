# update.ps1 - thin alias for the Update action of setup.ps1 (T271), as update.sh is for setup.sh.
#
# Run it inside your project's git repository, from the same checkout of the kit as setup.ps1:
#   powershell -ExecutionPolicy Bypass -File C:\path\to\easy-kit\update.ps1
#   pwsh -File C:\path\to\easy-kit\update.ps1 -Yes        (no questions: keep every edited file)
#
# It refuses to run where Easy Kit is not installed (no .claude/harness-lock.json). The
# EASYKIT_ACTION seam is internal: it is set for this one setup.ps1 run and restored after it.
param([switch]$Yes)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$setup = [IO.Path]::Combine($PSScriptRoot, 'setup.ps1')
if (-not [IO.File]::Exists($setup)) {
    [Console]::Error.WriteLine('[error] update.ps1 is part of the Easy Kit installer and needs setup.ps1 beside it. Run setup.ps1 from a checkout of the kit inside your project, and choose Update.')
    exit 1
}
$saved = $env:EASYKIT_ACTION
$env:EASYKIT_ACTION = 'update'
$code = 1
try {
    & $setup -Yes:$Yes
    $code = $LASTEXITCODE
} finally {
    $env:EASYKIT_ACTION = $saved
}
exit $code
