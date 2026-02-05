# Git Commands Reference

Quick reference for common git operations in this project.

---

## 📤 Commit & Push Commands

### Quick Commit & Push (Recommended)
```bash
git add '*.py' '*.md' '*.tex' '*.bib' '*.sty' '*.cls' '.cursor/' '.agent/' '.claude/' '.gitignore' '*.code-workspace' && git commit -m "Update: $(date '+%Y-%m-%d %H:%M')" && git push
```
Automatically commits with a timestamp and pushes to GitHub.

### Interactive Commit & Push
```bash
read -p "Enter commit message: " msg && git add '*.py' '*.md' '*.tex' '*.bib' '*.sty' '*.cls' '.cursor/' '.agent/' '.claude/' '.gitignore' '*.code-workspace' && git commit -m "$msg" && git push
```
Prompts you for a commit message, then commits and pushes.

### Manual Commit & Push
```bash
git add '*.py' '*.md' '*.tex' '*.bib' '*.sty' '*.cls' '.cursor/' '.agent/' '.claude/' '.gitignore' '*.code-workspace'
git commit -m "describe your changes here"
git push
```

### Step by Step

1. **Stage your changes**
   ```bash
   git add '*.py' '*.md' '*.tex' '*.bib' '*.sty' '*.cls' '.cursor/' '.agent/' '.claude/' '.gitignore' '*.code-workspace'
   ```
   This stages Python, Markdown, LaTeX source, and config files (respects .gitignore).

2. **Commit with a description**
   ```bash
   git commit -m "your description"
   ```
   Example: `git commit -m "fixed login bug"`

3. **Push to GitHub**
   ```bash
   git push
   ```
   This uploads everything to GitHub.

### One Command with Custom Message
```bash
git add '*.py' '*.md' '*.tex' '*.bib' '*.sty' '*.cls' '.cursor/' '.agent/' '.claude/' '.gitignore' '*.code-workspace' && git commit -m "your description" && git push
```

### Check What Will Be Committed
```bash
git status
```
Shows what files changed and will be committed.

### Check What's Ignored
```bash
git status --ignored
```

---

## 🔄 Sync Commands (Pull, Fetch, Merge)

### Quick Pull (Fetch + Merge)
```bash
git pull
```
Downloads changes from GitHub and merges them into your current branch.

### Pull with Rebase
```bash
git pull --rebase
```
Downloads changes and replays your commits on top (cleaner history).

### Pull Specific Branch
```bash
git pull origin branch-name
```
Pulls changes from a specific branch.

### Fetch All Remotes
```bash
git fetch --all
```
Downloads all changes from GitHub without merging (safe to inspect first).

### Fetch and Prune Deleted Branches
```bash
git fetch --prune
```
Updates your local repository and removes references to deleted remote branches.

### Check What Would Be Pulled
```bash
git fetch
git log HEAD..origin/main --oneline
```
Shows commits that would be pulled without actually pulling them.

### Merge Specific Branch
```bash
git merge branch-name
```
Merges another branch into your current branch.

### Abort Merge (If Conflicts)
```bash
git merge --abort
```
Cancels a merge that has conflicts and returns to pre-merge state.

### Safe Sync Workflow
```bash
# 1. Fetch changes first
git fetch

# 2. Check what's new
git log HEAD..origin/main --oneline

# 3. Pull if safe
git pull

# 4. Push your changes
git push
```

### Sync Before Commit Workflow
```bash
# 1. Pull latest changes first
git pull

# 2. Stage your changes
git add '*.py' '*.md' '*.tex' '*.bib' '*.sty' '*.cls' '.cursor/' '.agent/' '.claude/' '.gitignore' '*.code-workspace'

# 3. Commit
git commit -m "your message"

# 4. Push
git push
```

---

## 🔍 Pre-commit Hooks

### What Are Pre-commit Hooks?

Pre-commit hooks are **automated checks** that run before each commit. They help catch issues early by automatically checking code quality.

When you run `git commit`, these checks run automatically:
- **Ruff**: Lints and formats Python code
- **MyPy**: Type checking for Python files
- **File checks**: Removes trailing whitespace, checks YAML/JSON syntax
- **Tests**: Runs quick pytest smoke tests
- **Large file detection**: Prevents files >1MB from being committed

**Flow:**
```
git commit → Pre-commit runs → All pass? → Commit succeeds
                            ↓ Any fail? → Commit blocked → Fix issues → Try again
```

### Install Pre-commit Hooks (First Time)
```bash
pre-commit install
```
Sets up hooks in your local repository.

### Run Hooks Manually (Without Committing)
```bash
pre-commit run --all-files
```
Runs all checks on all files to see what would fail.

### Run Hooks on Staged Files Only
```bash
pre-commit run
```
Checks only the files you've staged with `git add`.

### Update Pre-commit Hooks
```bash
pre-commit autoupdate
```
Updates hook versions to latest releases.

### Skip Hooks (Emergency Only - Not Recommended)
```bash
git commit --no-verify -m "emergency fix"
```
Bypasses all pre-commit checks. **Use sparingly!**

### Handling Hook Failures

If pre-commit hooks fail:

1. **Read the error messages** - They tell you what's wrong
2. **Let hooks auto-fix** - Many hooks (like ruff) fix issues automatically
3. **Stage the fixes** - After auto-fixes: `git add .`
4. **Try committing again** - `git commit -m "your message"`

Example:
```bash
# Try to commit
git commit -m "Add feature"

# Hook fails and auto-fixes files
# Ruff formatted 3 files

# Stage the auto-fixed files
git add .

# Try again
git commit -m "Add feature"
# ✓ Success!
```

### Common Pre-commit Issues

**Issue: "Ruff would reformat"**
- **Fix**: Ruff auto-formats, just stage and commit again

**Issue: "MyPy type errors"**
- **Fix**: Add type hints or use `# type: ignore` comments

**Issue: "Trailing whitespace"**
- **Fix**: Auto-removed, just stage and commit again

**Issue: "File is too large"**
- **Fix**: Don't commit large files, add to .gitignore or use Git LFS

---

## 🔧 Useful Git Commands

### View Commit History
```bash
git log --oneline -10
```
Shows last 10 commits in compact format.

### View Changes in Files
```bash
git diff
```
Shows unstaged changes.

```bash
git diff --staged
```
Shows staged changes (what will be committed).

### Undo Last Commit (Keep Changes)
```bash
git reset --soft HEAD~1
```
Undoes last commit but keeps your changes staged.

### Undo Last Commit (Discard Changes)
```bash
git reset --hard HEAD~1
```
⚠️ **Warning**: Permanently deletes your last commit and changes!

### View Remote Repository URL
```bash
git remote -v
```
Shows GitHub repository URL.

### Check Current Branch
```bash
git branch
```
Shows all local branches, highlights current branch.

---

## 📋 Quick Reference Summary

| Task | Command |
|------|---------|
| Quick commit + push | `git add ... && git commit -m "Update: $(date '+%Y-%m-%d %H:%M')" && git push` |
| Pull latest changes | `git pull` |
| Check status | `git status` |
| View history | `git log --oneline -10` |
| Install pre-commit | `pre-commit install` |
| Run hooks manually | `pre-commit run --all-files` |
| Skip hooks (emergency) | `git commit --no-verify -m "message"` |
| Undo last commit | `git reset --soft HEAD~1` |

---

**Repository**: https://github.com/surajinacademia/cellpose_mcp
