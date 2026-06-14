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
  shift
  echo "Protecting branch: $branch"
  gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    "repos/${REPO}/branches/${branch}/protection" \
    -f required_status_checks.strict=true \
    -f 'required_status_checks.contexts[]=Backend (Django)' \
    -f 'required_status_checks.contexts[]=Frontend (Vite/React)' \
    -F enforce_admins=false \
    -F required_pull_request_reviews.required_approving_review_count="$1" \
    -F required_pull_request_reviews.dismiss_stale_reviews=true \
    -F restrictions=null \
    -F allow_force_pushes=false \
    -F allow_deletions=false
}

protect main 1
protect staging 0
protect develop 0

echo "Done. Review rules under: https://github.com/${REPO}/settings/branches"
