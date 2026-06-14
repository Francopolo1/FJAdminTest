# Branching Strategy

This project uses a three-branch model:

| Branch    | Purpose                                   | Deploys to  |
|-----------|--------------------------------------------|-------------|
| `main`    | Production-ready code only                  | Production  |
| `staging` | Pre-production integration / QA             | Staging     |
| `develop` | Active development, default branch for PRs  | —           |

## Workflow

1. Create feature branches off `develop`:
   `git checkout -b feature/my-change develop`
2. Open a PR from `feature/my-change` into `develop`. CI (`.github/workflows/ci.yml`)
   runs backend checks/tests and frontend lint/build on every PR.
3. When `develop` is ready for QA, open a PR from `develop` into `staging`.
   Merging triggers `.github/workflows/cd-staging.yml`, deploying to the
   staging environment.
4. When `staging` has been verified, open a PR from `staging` into `main`.
   Merging triggers `.github/workflows/cd-production.yml`, deploying to
   production (the `production` GitHub Environment can require manual
   reviewer approval).

## Branch protection

Run `.github/scripts/setup-branch-protection.sh` (requires the `gh` CLI,
authenticated as a repo admin) to apply the recommended protection rules to
`main`, `staging`, and `develop`. See that script for the exact rules, which
include:

- Require a pull request before merging (no direct pushes)
- Require the `CI / Backend (Django)` and `CI / Frontend (Vite/React)` status
  checks to pass
- Require branches to be up to date before merging
- `main` additionally requires at least 1 approving review
