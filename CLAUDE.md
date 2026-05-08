# CLAUDE.md

This file provides guidance for AI assistants (Claude Code and similar tools) working in this repository.

## Repository Overview

This is the **Originalman111/Originalman111** GitHub profile repository. In GitHub, a repository whose name matches the owner's username is special: its `README.md` is rendered directly on the owner's public profile page at `https://github.com/Originalman111`.

**Current state:** The repository was initialized on 2026-04-26 and contains only a `.gitkeep` placeholder. No content has been added yet.

## Repository Purpose

This repo's primary deliverable is a `README.md` file that serves as a GitHub profile landing page. Common uses include:

- Personal or organization bio
- Featured projects and links
- Skills, tools, and technologies
- Contact information and social links
- Dynamic badges (GitHub stats, language usage, etc.)
- Pinned project highlights

## File Structure (Expected)

```
/
├── CLAUDE.md          # This file — AI assistant guidance
├── README.md          # GitHub profile page (primary deliverable)
└── assets/            # Optional: images, GIFs, or other media
```

## Development Workflow

### Branching

- Default/stable branch: `main`
- Feature branches follow the pattern: `claude/<short-description>-<id>` (e.g., `claude/add-claude-documentation-UH98r`)
- Always develop on the designated feature branch; never push directly to `main` without a pull request

### Commit Messages

- Use clear, present-tense imperative messages: `Add profile README`, `Update skills section`
- Keep the subject line under 72 characters
- Reference the purpose, not the mechanism ("Add bio section" not "Edit README.md line 5")

### Pull Requests

- Open PRs as **drafts** initially; mark ready when complete
- Target `main` as the base branch
- PR title should match the intent of the branch (concise, ≤70 chars)
- Always create a PR after pushing a feature branch — do not leave pushed branches without a corresponding PR

### Git Push Pattern

```bash
git push -u origin <branch-name>
```

If a push fails due to network errors, retry up to 4 times with exponential backoff (2s → 4s → 8s → 16s).

## Working on the README

When creating or editing `README.md` for this profile:

1. **Check existing content first** — read the file before editing
2. **Markdown only** — GitHub profile READMEs render standard GitHub Flavored Markdown (GFM)
3. **Images/GIFs** — store in an `assets/` directory and reference with relative paths or raw GitHub URLs
4. **Badges** — use shields.io or similar services; test that badge URLs are valid
5. **Keep it concise** — profile pages are scanned quickly; prioritize clarity over length
6. **No secrets** — never commit tokens, API keys, or credentials

## AI Assistant Conventions

### General Rules

- Read files before editing them
- Prefer editing existing files over creating new ones
- Do not add unnecessary files (no extra docs, no temp files)
- Do not commit unless explicitly asked
- Do not push to `main` directly — always use a feature branch and PR

### Scope Discipline

- Make only the changes requested; do not refactor unrelated content
- Do not introduce new dependencies or tooling unless asked
- Do not add placeholder content ("TODO", "Coming soon") unless the user requests it

### GitHub Interactions

- Use GitHub MCP tools (`mcp__github__*`) for all GitHub API interactions
- Scope is restricted to the `originalman111/originalman111` repository only
- Post comments on PRs/issues sparingly — only when a reply is genuinely necessary

### When the Repo is Empty

If no `README.md` exists yet, ask the user what content they want before creating one. Do not generate a profile README with invented personal details.

## Quick Reference

| Task | Command |
|---|---|
| Check current branch | `git branch` |
| Stage specific file | `git add <file>` |
| Commit with message | `git commit -m "message"` |
| Push branch | `git push -u origin <branch>` |
| View recent commits | `git log --oneline -10` |
