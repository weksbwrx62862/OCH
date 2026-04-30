---
name: github-to-skills
description: Automated factory for converting GitHub repositories into specialized AI skills. Use this skill when the user provides a GitHub URL and wants to "package", "wrap", or "create a skill" from it. It automatically fetches repository details, latest commit hashes, and generates a standardized skill structure with enhanced metadata suitable for lifecycle management.
license: MIT
---

# GitHub to Skills Factory

This skill automates the conversion of GitHub repositories into fully functional AI skills.

## Core Functionality

1. **Analysis**: Fetches repository metadata (Description, README, Latest Commit Hash).
2. **Scaffolding**: Creates a standardized skill directory structure.
3. **Metadata Injection**: Generates `SKILL.md` with extended frontmatter for future automated management.
4. **Wrapper Generation**: Creates a wrapper to interface with the tool.

## Usage

**Trigger**: `/GitHub-to-skills <github_url>` or "Package this repo into a skill: <url>"

### Required Metadata Schema

Every skill created by this factory MUST include the following extended YAML frontmatter in its `SKILL.md`:

```yaml
---
name: <kebab-case-repo-name>
description: <concise-description-for-agent-triggering>
github_url: <original-repo-url>
github_hash: <latest-commit-hash-at-time-of-creation>
version: <tag-or-0.1.0>
created_at: <ISO-8601-date>
entry_point: scripts/wrapper.py
dependencies: # List main dependencies if known
---
```
