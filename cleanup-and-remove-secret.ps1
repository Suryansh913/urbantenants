# cleanup-and-remove-secret.ps1

$ErrorActionPreference = "Stop"

function Write-Heading($Text) {
    Write-Host ""
    Write-Host "==== $Text ====" -ForegroundColor Cyan
}

Write-Heading "Checking Git repository"

git rev-parse --is-inside-work-tree *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Not inside a Git repository." -ForegroundColor Red
    exit 1
}

Write-Host "Skipping working tree check..."

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backup = "backup-before-cleanup-$timestamp"

Write-Heading "Creating backup branch"

git branch $backup
Write-Host "Backup branch: $backup"

Write-Heading "Checking git-filter-repo"

git filter-repo --version *> $null

if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing git-filter-repo..."
    python -m pip install --user git-filter-repo

    git filter-repo --help *> $null

    if ($LASTEXITCODE -ne 0) {
        Write-Host "git-filter-repo installation failed." -ForegroundColor Red
        exit 1
    }
}

Write-Heading "Removing debug_log.txt from history"

git filter-repo --invert-paths --path debug_log.txt --force

if (!(Test-Path ".gitignore")) {
    New-Item ".gitignore" -ItemType File | Out-Null
}

if (!(Select-String ".gitignore" "^debug_log.txt$" -Quiet -ErrorAction SilentlyContinue)) {
    Add-Content ".gitignore" "debug_log.txt"
    git add .gitignore
    git commit -m "Ignore debug_log.txt"
}

Write-Heading "Cleaning repository"

git reflog expire --expire=now --all
git gc --prune=now --aggressive

Write-Heading "Checking history"

$found = git log --all -- debug_log.txt

if ($found) {
    Write-Host "debug_log.txt is still present in history." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "IMPORTANT!"
Write-Host "Rotate your Cashfree API Key before pushing."

Read-Host "Press ENTER after rotating the key"

$confirm = Read-Host "Type YES to force push"

if ($confirm -ne "YES") {
    Write-Host "Cancelled."
    exit
}

Write-Heading "Force pushing"

git push origin main --force

Write-Heading "Done"

git status

git log --oneline -10

Write-Host ""
Write-Host "Cleanup completed successfully."