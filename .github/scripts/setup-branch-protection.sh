#!/usr/bin/env bash
# Apply branch protection rules to main, staging, and develop.
#
# Requires: gh CLI (https://cli.github.com/), authenticated as a user with
# admin rights on the repo: `gh auth login`
#
# Usage: ./.github/scripts/setup-branch-protection.sh owner/repo

set -euo pipefail

REPO="${1:?Usage: $0 owner/repo}"

protect() {
  local branch="$1"
  local approvals="$2"
  echo "Protecting branch: $branch"
  gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    "repos/${REPO}/branches/${branch}/protection" \
    --input - <<EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["Backend (Django)", "Frontend (Vite/React)"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": ${approvals},
    "dismiss_stale_reviews": true
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
}

protect main 1
protect staging 0
protect develop 0

echo "Done. Review rules under: https://github.com/${REPO}/settings/branches"
