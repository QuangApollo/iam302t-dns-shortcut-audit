#!/usr/bin/env bash
# Run only from the compact GitHub-ready package after gh authentication.
set -euo pipefail
cd -- "$(dirname -- "$0")"
command -v gh >/dev/null || { echo 'Install GitHub CLI, then run gh auth login.'; exit 1; }
gh auth status >/dev/null 2>&1 || { echo 'Run gh auth login, then rerun this script.'; exit 1; }
project_login="$(gh api user --jq .login)"
project_user_id="$(gh api user --jq .id)"
project_repo="${1:-iam302t-dns-shortcut-audit}"
[[ "$project_repo" =~ ^[A-Za-z0-9_.-]+$ ]] || { echo 'Invalid repository name.'; exit 1; }
[[ ! -d .git ]] || { echo 'This folder is already a git checkout; use its existing remote.'; exit 1; }
git init --initial-branch=main
git config user.name "$project_login"
git config user.email "${project_user_id}+${project_login}@users.noreply.github.com"
git add .
git commit -m 'Add checksum-pinned DNS tunneling audit and focused revision'
gh repo create "$project_login/$project_repo" --public --source . --remote origin --push
echo "Published: https://github.com/$project_login/$project_repo"
echo 'Next: set the verified URL in the full submission project and recompile both PDFs.'
