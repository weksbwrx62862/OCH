---
name: skill-manager
description: Lifecycle manager for GitHub-based skills. Use this to batch scan your skills directory, check for updates on GitHub, and perform guided upgrades of your skill wrappers.
license: MIT
---

# Skill Lifecycle Manager

This skill helps you maintain your library of GitHub-wrapped skills by automating the detection of updates and assisting in the refactoring process.

## Core Capabilities

1. **Audit**: Scans your local skills folder for skills with `github_url` metadata.
2. **Check**: Queries GitHub to compare local commit hashes against the latest remote HEAD.
3. **Report**: Generates a status report identifying which skills are "Stale" or "Current".
4. **Update Workflow**: Provides a structured process for the Agent to upgrade a skill.
5. **Inventory Management**: Lists all local skills and provides deletion capabilities.

## Usage

**Trigger**: `/skill-manager check` or "Scan my skills for updates"
**Trigger**: `/skill-manager list` or "List my skills"
**Trigger**: `/skill-manager delete <skill_name>` or "Delete skill <skill_name>"
