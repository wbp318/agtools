# GitHub Actions & CI/CD Pipeline Guide

A beginner-friendly guide to understanding how GitHub Actions works and what our CI/CD pipeline does.

## Table of Contents

1. [What is CI/CD?](#what-is-cicd)
2. [What is GitHub Actions?](#what-is-github-actions)
3. [How It Works (The Big Picture)](#how-it-works-the-big-picture)
4. [Our Pipeline Explained](#our-pipeline-explained)
5. [Viewing Pipeline Results](#viewing-pipeline-results)
6. [Understanding the Workflow File](#understanding-the-workflow-file)
7. [Common Scenarios](#common-scenarios)
8. [Troubleshooting](#troubleshooting)

---

## What is CI/CD?

**CI/CD** stands for **Continuous Integration / Continuous Deployment**.

### Continuous Integration (CI)
Every time you push code, automated tests run to catch bugs early.

```
You push code → Tests run automatically → You get notified if something breaks
```

### Continuous Deployment (CD)
After tests pass, code can be automatically deployed to production.

```
Tests pass → Code deploys automatically → Users see new features
```

### Why Use CI/CD?

| Without CI/CD | With CI/CD |
|---------------|------------|
| Bugs found in production | Bugs caught before merge |
| "It works on my machine" | Tests run in consistent environment |
| Manual testing is slow | Automated testing is fast |
| Scary deployments | Confident deployments |

---

## What is GitHub Actions?

**GitHub Actions** is GitHub's built-in CI/CD system. It's free for public repos and has generous limits for private repos.

### Key Concepts

| Term | What It Means |
|------|---------------|
| **Workflow** | A complete automation process (our CI pipeline) |
| **Job** | A group of steps that run together |
| **Step** | A single task (like "install Python") |
| **Runner** | The computer that runs your workflow |
| **Trigger** | What starts the workflow (push, PR, schedule) |

---

## How It Works (The Big Picture)

Here's what happens when you push code to GitHub:

```
┌─────────────────────────────────────────────────────────────────┐
│  YOUR COMPUTER                                                   │
│  ┌─────────────┐                                                │
│  │ git push    │ ──────────────────────┐                        │
│  └─────────────┘                       │                        │
└────────────────────────────────────────│────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  GITHUB                                                          │
│  ┌─────────────┐     ┌──────────────────────────────────────┐   │
│  │ Receives    │ ──► │ Checks .github/workflows/ folder     │   │
│  │ your code   │     │ for workflow files (*.yml)           │   │
│  └─────────────┘     └──────────────────────────────────────┘   │
│                                         │                        │
│                                         ▼                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  GITHUB ACTIONS RUNNER (a fresh virtual machine)          │   │
│  │  ┌────────────────────────────────────────────────────┐   │   │
│  │  │ 1. Clone your repo                                  │   │   │
│  │  │ 2. Set up Python                                    │   │   │
│  │  │ 3. Install dependencies                             │   │   │
│  │  │ 4. Run tests                                        │   │   │
│  │  │ 5. Report results                                   │   │   │
│  │  └────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                         │                        │
│                                         ▼                        │
│  ┌─────────────┐                                                │
│  │ ✅ Pass or  │ ──► You get notified (email, GitHub UI)        │
│  │ ❌ Fail     │                                                │
│  └─────────────┘                                                │
└─────────────────────────────────────────────────────────────────┘
```

### The Runner (Virtual Machine)

When a workflow runs, GitHub spins up a fresh virtual machine (the "runner"):

- **Clean slate**: No leftover files from previous runs
- **Pre-installed tools**: Git, Python, Node.js, Docker, etc.
- **Temporary**: Destroyed after the workflow finishes
- **Free**: GitHub provides free runners for public repos

---

## Our Pipeline Explained

Our CI pipeline is defined in `.github/workflows/ci.yml`. Here's what it does:

### Visual Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGTOOLS CI PIPELINE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Triggered by: Push to master/main/develop OR Pull Request      │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │    TEST     │  │    LINT     │  │  SECURITY   │              │
│  │             │  │             │  │             │              │
│  │ Python 3.10 │  │ Black       │  │ Bandit      │  ◄── Run in  │
│  │ Python 3.11 │  │ isort       │  │ Safety      │      parallel│
│  │ Python 3.12 │  │ Flake8      │  │             │              │
│  │             │  │             │  │             │              │
│  │ Smoke tests │  │ Style check │  │ Vuln scan   │              │
│  └──────┬──────┘  └─────────────┘  └─────────────┘              │
│         │                                                        │
│         │ (must pass)                                            │
│         ▼                                                        │
│  ┌─────────────┐                                                │
│  │   DOCKER    │                                                │
│  │             │                                                │
│  │ Build image │  ◄── Only runs if TEST passes                  │
│  │ (no push)   │                                                │
│  └─────────────┘                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### The Four Jobs

#### 1. TEST Job
Runs our smoke tests on multiple Python versions to ensure compatibility.

```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']
```

This creates 3 parallel test runs - one for each Python version.

**What it does:**
1. Checks out code
2. Installs Python 3.10, 3.11, OR 3.12
3. Installs dependencies from `requirements.txt`
4. Runs `smoke_test_full.py`
5. Uploads test results as artifacts

#### 2. LINT Job
Checks code style and formatting.

**Tools used:**
- **Black**: Code formatter (are files formatted correctly?)
- **isort**: Import sorter (are imports organized?)
- **Flake8**: Linter (any syntax errors or bad practices?)

These run with `continue-on-error: true` so they warn but don't fail the build.

#### 3. SECURITY Job
Scans for security vulnerabilities.

**Tools used:**
- **Bandit**: Scans Python code for security issues
- **Safety**: Checks dependencies for known vulnerabilities

Also runs with `continue-on-error: true` for warnings.

#### 4. DOCKER Job
Builds the Docker image to ensure it still works.

```yaml
needs: test  # Only runs after TEST job passes
```

---

## Viewing Pipeline Results

### Method 1: GitHub Website

1. Go to your repository on GitHub
2. Click the **"Actions"** tab
3. You'll see a list of workflow runs

```
┌─────────────────────────────────────────────────────────────────┐
│  Actions                                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ CI - Add data export service        2 minutes ago           │
│  ✅ CI - Add deployment guide           15 minutes ago          │
│  ❌ CI - Fix typo in main.py            1 hour ago              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

4. Click on a run to see details
5. Click on a job to see step-by-step logs

### Method 2: Status Badge

Add this to your README to show build status:

```markdown
![CI](https://github.com/wbp318/agtools/actions/workflows/ci.yml/badge.svg)
```

Shows: ![CI](https://github.com/wbp318/agtools/actions/workflows/ci.yml/badge.svg)

### Method 3: Commit Status

On any commit, you'll see a status icon:

- ✅ Green checkmark = All jobs passed
- ❌ Red X = One or more jobs failed
- 🟡 Yellow dot = Jobs still running

### Method 4: Email Notifications

GitHub sends emails when:
- A workflow fails (on by default)
- A workflow succeeds (can enable in settings)

---

## Understanding the Workflow File

Let's break down `.github/workflows/ci.yml`:

```yaml
# The name shown in the Actions tab
name: CI

# TRIGGERS: When does this workflow run?
on:
  push:
    branches: [master, main, develop]  # Run on push to these branches
  pull_request:
    branches: [master, main]           # Run on PRs to these branches

# JOBS: What work should be done?
jobs:
  # First job: Run tests
  test:
    runs-on: ubuntu-latest  # Use Ubuntu Linux runner

    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']  # Test multiple versions

    steps:
      # Step 1: Get the code
      - name: Checkout code
        uses: actions/checkout@v4  # Pre-built action from GitHub

      # Step 2: Install Python
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'  # Cache dependencies for speed

      # Step 3: Install dependencies
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements.txt

      # Step 4: Run tests
      - name: Run smoke tests
        run: |
          cd tests
          python smoke_test_full.py
```

### Key Syntax

| Syntax | Meaning |
|--------|---------|
| `name:` | Human-readable label |
| `on:` | When to trigger |
| `jobs:` | List of jobs to run |
| `runs-on:` | What OS to use |
| `steps:` | List of steps in a job |
| `uses:` | Use a pre-built action |
| `run:` | Run shell commands |
| `with:` | Pass parameters to an action |
| `${{ }}` | Variable interpolation |

---

## Common Scenarios

### Scenario 1: You Push Code

```bash
git add .
git commit -m "Add new feature"
git push
```

**What happens:**
1. GitHub receives your push
2. Sees `.github/workflows/ci.yml`
3. Triggers the CI workflow
4. All 4 jobs start running
5. ~3-5 minutes later, you see results

### Scenario 2: Tests Fail

If the smoke tests fail:

1. You get an email notification
2. The commit shows ❌ on GitHub
3. If it's a PR, merging is blocked (optional setting)

**To fix:**
1. Check the Actions tab for error details
2. Fix the code locally
3. Push again
4. New workflow run starts

### Scenario 3: Viewing Test Results

Test artifacts are saved for 90 days:

1. Go to Actions → Click on a run
2. Scroll to "Artifacts" section
3. Download `smoke-test-results-py3.11`
4. Open the markdown file to see results

### Scenario 4: Re-running a Failed Job

If a job failed due to a flaky test or temporary issue:

1. Go to Actions → Click on the failed run
2. Click "Re-run failed jobs" button
3. Jobs will run again

---

## Troubleshooting

### "Workflow not running"

**Possible causes:**
- Workflow file has syntax errors
- File not in `.github/workflows/` folder
- Branch doesn't match trigger conditions

**Fix:** Check the workflow file for YAML syntax errors.

### "Tests pass locally but fail in CI"

**Possible causes:**
- Different Python version
- Missing environment variables
- Different operating system (Windows vs Linux)

**Fix:** Check what Python version CI uses; test with that version locally.

### "Job takes too long"

**Possible causes:**
- Too many dependencies to install
- Tests are slow

**Fix:**
- Use dependency caching (already enabled with `cache: 'pip'`)
- Optimize slow tests

### "Can't see workflow runs"

**Possible causes:**
- Actions might be disabled for the repo

**Fix:**
1. Go to repo Settings → Actions → General
2. Ensure "Allow all actions" is selected

---

## Quick Reference

### Workflow File Location
```
your-repo/
├── .github/
│   └── workflows/
│       └── ci.yml      ← Our CI pipeline
├── backend/
├── tests/
└── ...
```

### Useful Links

- **Actions Tab**: `https://github.com/wbp318/agtools/actions`
- **Workflow Runs**: `https://github.com/wbp318/agtools/actions/workflows/ci.yml`
- **GitHub Actions Docs**: `https://docs.github.com/en/actions`

### Status Check Commands

```bash
# View recent workflow runs (requires GitHub CLI)
gh run list

# View details of a specific run
gh run view <run-id>

# Watch a run in real-time
gh run watch
```

---

## Summary

1. **CI/CD** = Automated testing and deployment
2. **GitHub Actions** = GitHub's built-in CI/CD system
3. **Workflow** = Automation defined in `.github/workflows/*.yml`
4. **Our pipeline** runs tests, linting, security scans, and Docker builds
5. **View results** in the Actions tab on GitHub
6. **Green checkmark** = Everything passed!

Every time you push code, the pipeline runs automatically. No extra steps needed - just push and check the results!

---

*Last updated: December 2025*
