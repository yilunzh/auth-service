---
description: Example skill - delete this file and create your own
---

# Example Skill

This is a template for creating custom slash commands (skills) in Claude Code.

## How Skills Work

- Files in `.claude/commands/` become available as `/command-name`
- The filename (without `.md`) is the command name
- The `description` in frontmatter shows in autocomplete
- Everything below the frontmatter is instructions for Claude

## Creating Your Own Skills

1. Copy this file to a new name (e.g., `deploy.md`)
2. Update the frontmatter description
3. Write instructions for what Claude should do

## Example Skills You Might Create

### `/deploy` - Deployment workflow
```markdown
---
description: Deploy the application to production
---

# Deploy

1. Run tests to ensure everything passes
2. Build the production bundle
3. Deploy using [your platform's CLI]
4. Verify deployment health
```

### `/db-migrate` - Database migrations
```markdown
---
description: Create and run database migrations
---

# Database Migration

1. Generate migration from model changes
2. Review the generated migration
3. Apply migration to development database
4. Test that existing data migrates correctly
```

### `/release` - Create a release
```markdown
---
description: Create a new release with changelog
---

# Release

1. Determine version bump (major/minor/patch)
2. Update version in package files
3. Generate changelog from commits since last release
4. Create git tag
5. Push tag to trigger release workflow
```

## Instructions for Claude

When this skill is invoked, respond with a brief explanation of how to create custom skills, and offer to help create one based on the user's workflow.

Ask:
1. What workflow would you like to automate?
2. What steps are involved?
3. Are there any conditions or variations?
