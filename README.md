# Claude Code Project Template

A **framework-agnostic** template for AI-assisted development with Claude Code. Captures proven development workflow patterns without prescribing a specific tech stack.

## What This Is

This template provides:

- **Development workflow** - Branch-first, clarify, plan, implement, verify
- **Quality enforcement hooks** - Automated checks for tests, linting, branch policy
- **Context management** - Checkpoints and handoffs for long sessions
- **Pattern documentation** - Reference for common architectural decisions

## What This Is NOT

- A starter kit with boilerplate code
- A specific tech stack
- A web framework template

**Key insight**: The value isn't in code scaffolding - it's in the AI-assisted development workflow. Let requirements drive technology decisions.

## Getting Started

### 1. Create Your Project

```bash
# Clone template to new project directory
cp -r /path/to/claude-project-template ~/projects/my-new-project
cd ~/projects/my-new-project

# Initialize git (template doesn't include .git)
git init
git add .
git commit -m "Initial commit from claude-project-template"
```

### 2. Describe Your Project

Edit `BRIEF.md` with a non-technical description of what you're building:

- What is it?
- Why build it?
- For whom?
- Key requirements
- Design inspiration (if UI involved)

### 3. Start Building

```bash
# Start Claude Code
claude

# First message:
# "I'm starting a new project. Read BRIEF.md and help me plan the implementation."
```

Claude will:
1. Read your brief
2. Ask clarifying questions
3. Recommend a tech stack
4. Create an implementation plan
5. Start building with the hooks enforcing quality

## Directory Structure

```
claude-project-template/
├── .claude/
│   ├── settings.json        # Hooks + MCP server configuration
│   ├── hooks/               # Quality enforcement scripts
│   │   ├── pre-commit-check.py
│   │   ├── branch-check.py
│   │   ├── uncommitted-changes-check.py
│   │   ├── post-edit-verify.py
│   │   ├── auto-format.py
│   │   ├── checkpoint-reminder.py
│   │   ├── checkpoint-validator.py
│   │   ├── completion-checklist.py
│   │   ├── session-handoff.py
│   │   ├── spec-update-check.py
│   │   └── implementation-plan-check.py
│   ├── commands/            # Custom slash commands
│   │   ├── commit-push-pr.md
│   │   ├── test-and-commit.md
│   │   ├── web-verify.md
│   │   └── example.md
│   ├── agents/              # Custom subagents
│   │   ├── test-first.md
│   │   └── design-review.md
│   └── ideation/            # Structured ideation workflow
│       └── IDEATION_PROCESS.md
├── CLAUDE.md                # Development workflow
├── BRIEF.md                 # Project description (you edit this)
├── docs/
│   ├── SPEC.md              # Technical spec (grows with project)
│   └── PATTERNS.md          # Architectural patterns reference
├── .gitignore               # Multi-language patterns
└── README.md                # This file
```

## Hooks

The template includes 11 hooks that enforce the development workflow:

| Hook | Type | Purpose |
|------|------|---------|
| `pre-commit-check.py` | Blocking | Runs tests + lint, blocks commits to main |
| `branch-check.py` | Blocking | Prevents editing files on main branch |
| `uncommitted-changes-check.py` | Advisory | Warns about uncommitted changes at session start |
| `post-edit-verify.py` | Advisory | Reminds to run tests after edits |
| `auto-format.py` | Advisory | Auto-formats Python files with black/isort |
| `checkpoint-reminder.py` | Advisory | Reminds to checkpoint every 3-5 edits |
| `checkpoint-validator.py` | Advisory | Validates checkpoint sections, resets step counter |
| `completion-checklist.py` | Blocking | Ensures tests ran before session ends |
| `session-handoff.py` | Blocking | Detects incomplete work, requires handoff |
| `spec-update-check.py` | Stop | Triggers SPEC.md updates on key phrases |
| `implementation-plan-check.py` | Advisory | Reminds to update implementation plans |

### Language Detection

Hooks automatically detect your project type:

- **Python**: pytest, flake8/ruff
- **Node.js**: npm test, eslint
- **Rust**: cargo test, cargo clippy
- **Go**: go test, go vet

## Development Workflow

1. **BRANCH FIRST** - Create feature branch before any changes
2. **CLARIFY** - Ask questions before coding (especially for UI)
3. **PLAN** - Create todo list with implementation steps
4. **IMPLEMENT** - Make incremental changes, checkpoint every 3-5 edits
5. **VERIFY** - Run tests, use Playwright for UI changes

## Customization

### Built-in Commands

The template includes ready-to-use slash commands:

| Command | Description |
|---------|-------------|
| `/commit-push-pr` | Complete workflow from staged changes to PR creation |
| `/test-and-commit` | Run tests first, only commit if passing |
| `/web-verify` | Playwright verification for web routes |
| `/sync-templates` | Analyze project for improvements to propagate to templates |

### Adding Custom Commands

Create `.claude/commands/your-command.md`:

```markdown
# Command Name

Instructions for Claude when this command is invoked.

## Steps
1. Step one
2. Step two
```

Invoke with `/your-command` in Claude Code.

### Ideation Process

For complex features, use the structured ideation workflow in `.claude/ideation/IDEATION_PROCESS.md`. This 7-phase process transforms ideas into implementation-ready packages:

1. **Problem Discovery** - Understand WHY
2. **Solution Definition** - Define WHAT
3. **Design Discovery** - Establish visual language
4. **Design Specification** - Detail HOW it looks
5. **Architecture** - Define HOW it's built
6. **Implementation Planning** - Create development roadmap
7. **Handoff** - Package for implementation

Create feature ideation folders at `.claude/ideation/<feature-name>/` with artifacts from each phase.

### Adding Patterns

Update `docs/PATTERNS.md` with patterns you learn and want to reuse.

### Project-Specific Config

After Claude scaffolds your project:
- Update `docs/SPEC.md` as the project evolves
- Add project-specific entries to `.gitignore`
- Create project-specific commands in `.claude/commands/`

## Syncing Improvements from Projects

As you work on projects, you may discover workflow improvements (new hooks, refined rules, better processes). To propagate these back to the templates:

1. Open the project in Claude Code
2. Run `/sync-templates` or ask "analyze this project for template improvements"
3. Claude will:
   - Compare your project's CLAUDE.md, hooks, commands, and agents against the templates
   - Evaluate each difference for generalizability and value
   - Recommend which improvements should become part of the default templates
   - Apply approved changes to both `claude-project-template` and `cursor-project-template`

No manual logging required - Claude analyzes on demand and you decide what to adopt.

**What might get synced:**
- Workflow patterns that proved useful
- New or improved hooks
- Broadly applicable commands or agents
- Process documentation refinements

**What stays project-specific:**
- BRIEF.md content
- docs/SPEC.md content
- Tech-stack-specific commands

## MCP Servers

The template configures Playwright MCP for visual verification:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    }
  }
}
```

Use Playwright to screenshot and verify UI changes.

## License

MIT - use this template for any project.
