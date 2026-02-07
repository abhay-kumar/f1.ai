# Release

Create a new release by pushing changes to a branch, creating a PR, merging it, and tagging a new version.

## Input

**Version bump type** (optional): $ARGUMENTS

- `major` - Breaking changes (v1.0.0 -> v2.0.0)
- `minor` - New features (v1.3.0 -> v1.4.0) [default]
- `patch` - Bug fixes (v1.3.0 -> v1.3.1)

If no argument provided, defaults to `minor`.

## Instructions

### 1. Pre-flight Checks

First verify there are changes to release:

```bash
git status --short
```

If no changes exist, inform the user and stop.

Check that we're on the main branch or can safely create a feature branch:

```bash
git branch --show-current
```

### 2. Analyze Changes

Review the staged/unstaged changes to generate an appropriate branch name and commit message:

```bash
git diff --stat
git diff --cached --stat
```

Create a descriptive branch name based on the changes (e.g., `feature/add-podcast-commands`, `fix/video-encoding-bug`, `chore/update-dependencies`).

### 3. Create Feature Branch and Commit

```bash
git checkout -b {branch-name}
git add -A
git commit -m "{descriptive commit message}"
```

The commit message should:
- Have a clear summary line (50 chars or less)
- Include bullet points for each major change
- Follow conventional commit style when appropriate

### 4. Push Branch

```bash
git push -u origin {branch-name}
```

If push fails due to large files:
- Identify large files: `find . -type f -size +50M -not -path './.git/*'`
- Suggest adding them to `.gitignore`
- Reset commit, update gitignore, and retry

### 5. Create Pull Request

```bash
gh pr create --title "{PR title}" --body "{PR description}" --base main
```

The PR description should include:
- Summary section
- List of changes
- Any breaking changes (for major versions)

### 6. Merge Pull Request

```bash
gh pr merge {pr-number} --merge --delete-branch
```

This will:
- Merge the PR to main
- Delete the remote branch
- Delete the local branch
- Switch back to main

### 7. Create Version Tag

Determine the new version:

```bash
git tag --sort=-v:refname | head -1
```

Calculate the next version based on the bump type argument:
- If current is `v1.3.0` and bump is `minor` -> `v1.4.0`
- If current is `v1.3.0` and bump is `major` -> `v2.0.0`
- If current is `v1.3.0` and bump is `patch` -> `v1.3.1`
- If no tags exist, start with `v1.0.0`

Create and push the tag:

```bash
git tag -a {new-version} -m "{new-version} - {brief description of changes}"
git push origin {new-version}
```

### 8. Report Summary

Display a summary of what was done:
- Branch name created
- PR URL
- New version tag
- List of files changed

## Example Usage

```
/release           # Creates a minor version bump
/release minor     # Same as above
/release patch     # Creates a patch version bump
/release major     # Creates a major version bump
```

## Error Handling

- **No changes**: Stop and inform user
- **Not on main**: Warn but allow proceeding from feature branch
- **Push fails**: Check for large files, suggest gitignore updates
- **PR creation fails**: Check gh CLI authentication
- **Merge conflicts**: Stop and ask user to resolve manually
