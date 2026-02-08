# Ideation System Process

> A structured workflow that transforms a simple idea/prompt into a complete execution package (requirements, design specs, prototypes, architecture) through iterative discovery and feedback.

**Input:** Simple prompt (e.g., "expense tracking for roommates")
**Output:** Complete package ready for implementation

---

## Core Principles

| Principle | Description |
|-----------|-------------|
| **Reaction-based refinement** | Generate 2-4 options, user reacts (select/comment), converge. Never ask "what do you want?" - show options instead. |
| **Progressive fidelity** | Start loose (concepts), formalize as understanding deepens (specs → prototypes) |
| **Interview mode** | Streamlined interaction - present choices, user selects. Minimize prose, maximize decisions. |
| **Feedback propagation** | Changes in one area trigger review of dependent areas |
| **First principles reasoning** | Challenge assumptions, explore "why" before "how", document trade-offs |
| **Visual validation** | 80-85% fidelity prototypes required before greenlight |

---

## Workflow Phases

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: PROBLEM DISCOVERY                                             │
│  Goal: Understand WHY we're doing this                                  │
│                                                                         │
│  Activities:                                                            │
│  - Identify the pain point                                              │
│  - Understand current state / workarounds                               │
│  - Define target users                                                  │
│  - Explore "why" chains (keep asking why until hitting fundamental)     │
│  - List assumptions (validated vs unvalidated)                          │
│                                                                         │
│  Output: discovery.md                                                   │
│  Exit criteria: Problem clearly articulated, user confirmed             │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: SOLUTION DEFINITION                                           │
│  Goal: Define WHAT we're building                                       │
│                                                                         │
│  Activities:                                                            │
│  - Generate 2-4 solution directions                                     │
│  - User reacts, selects direction                                       │
│  - Define scope (in/out)                                                │
│  - Write user stories / requirements                                    │
│  - Define success criteria                                              │
│                                                                         │
│  Output: requirements.md                                                │
│  Exit criteria: Scope locked, requirements clear                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 3: DESIGN DISCOVERY                                              │
│  Goal: Establish design language (if not exists)                        │
│                                                                         │
│  Activities:                                                            │
│  - Review existing product design (if any)                              │
│  - Gather references (what user likes/dislikes)                         │
│  - Generate 2-3 visual directions                                       │
│  - User reacts, converge on style                                       │
│  - Document design principles                                           │
│                                                                         │
│  Output: design-language.md                                             │
│  Exit criteria: Design direction established                            │
│  Note: Can skip if design language already exists for project           │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 4: DESIGN SPECIFICATION                                          │
│  Goal: Detail HOW it looks and works                                    │
│                                                                         │
│  Activities:                                                            │
│  - Map user flow end-to-end                                             │
│  - For each screen:                                                     │
│    - Generate 2-3 layout options                                        │
│    - User reacts, select approach                                       │
│    - Specify: layout, components, interactions, copy, states            │
│  - Document edge cases (empty, error, loading, offline)                 │
│  - Generate HTML/CSS prototypes                                         │
│                                                                         │
│  Output: design-specs/, prototypes/                                     │
│  Exit criteria: User approves prototypes                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 5: ARCHITECTURE                                                  │
│  Goal: Define HOW it's built                                            │
│                                                                         │
│  Activities:                                                            │
│  - Identify technical components needed                                 │
│  - Define data models                                                   │
│  - Define API contracts                                                 │
│  - Identify risks and mitigations                                       │
│  - Suggest high-level implementation phases                             │
│                                                                         │
│  Output: architecture.md                                                │
│  Exit criteria: Technically feasible, approach clear                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 6: IMPLEMENTATION PLANNING                                       │
│  Goal: Create actionable development roadmap                            │
│                                                                         │
│  Activities:                                                            │
│  - Break architecture into Epics (major workstreams)                    │
│  - Break Epics into Stories (implementable units)                       │
│  - Define acceptance criteria for each story                            │
│  - Identify dependencies between stories                                │
│  - Estimate complexity (S/M/L) for prioritization                       │
│  - Define test requirements per story                                   │
│                                                                         │
│  Output: implementation-plan.md                                         │
│  Exit criteria: All stories have clear acceptance criteria              │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 7: HANDOFF                                                       │
│  Goal: Package everything for implementation                            │
│                                                                         │
│  Activities:                                                            │
│  - Compile all artifacts                                                │
│  - Write executive summary                                              │
│  - Note what needs human refinement (15-20%)                            │
│  - Define verification criteria                                         │
│                                                                         │
│  Output: Complete handoff package                                       │
│  Exit criteria: Ready for plan mode / implementation                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Research When Stuck

**In any phase, when facing unclear decisions:**

1. **Identify the uncertainty** - What specifically are we unsure about?
2. **Research existing solutions:**
   - How do competitors/similar products handle this?
   - What patterns exist in the industry?
   - What have others tried that failed?
   - Are there relevant design patterns or best practices?
3. **Synthesize findings** - Present options informed by research
4. **Present to user** - "Here's how others solve this: [A, B, C]. Which resonates?"

**Research triggers:**
- No clear "right answer" among options
- User says "I'm not sure"
- Novel problem with no obvious precedent
- High-stakes decision with significant trade-offs

**Research sources:**
- Competitor products (screenshots, flows)
- Design pattern libraries
- Industry best practices
- Case studies / post-mortems
- User research (if available)

**Document findings in artifacts:**
```markdown
## Research: [Topic]
### Question
What were we trying to figure out?

### Findings
| Source | Approach | Pros | Cons |
|--------|----------|------|------|
| Competitor A | ... | ... | ... |
| Competitor B | ... | ... | ... |

### Recommendation
Based on research, we recommend X because...
```

---

## Feedback Loops

Any phase can loop back to previous phases when feedback invalidates earlier decisions:

```
Discovery ↔ Definition ↔ Design ↔ Architecture
    ↑____________|___________|_________|
```

When user provides feedback:
1. Classify: Which phase does this affect?
2. Update: Modify relevant artifact
3. Check dependencies: Does this impact later phases?
4. Propagate: Trigger re-review of affected areas
5. Surface: Ask new questions that emerge

---

## Interaction Model: Interview Mode

**Structure each decision point as:**
```
┌─────────────────────────────────────────────────────────────┐
│  QUESTION: [Clear, specific question]                       │
│                                                             │
│  ○ A) [Option label]                                        │
│       [1-2 sentence description]                            │
│                                                             │
│  ○ B) [Option label]                                        │
│       [1-2 sentence description]                            │
│                                                             │
│  ○ C) [Option label]                                        │
│       [1-2 sentence description]                            │
│                                                             │
│  ○ D) Other: [free text]                                    │
│                                                             │
│  [Optional context that informs the decision]               │
└─────────────────────────────────────────────────────────────┘
```

**User responds with:**
- Single letter: "B"
- Letter with modification: "B but with X"
- Commentary: "None of these, I want Y"

**System then:**
- Acknowledges decision
- Updates artifacts
- Moves to next decision or presents refined options

---

## Artifact Structure

```
.claude/ideation/<project-slug>/
├── README.md                    # Session status, how to resume
├── discovery.md                 # Problem space, users, insights
├── requirements.md              # Scope, user stories, success criteria
├── design-language.md           # Visual/interaction principles
├── decisions.md                 # All decisions with rationale
├── design-specs/
│   ├── screen-1-name.md         # Per-screen specification
│   ├── screen-2-name.md
│   └── ...
├── architecture.md              # Technical approach
├── implementation-plan.md       # Epics, stories, acceptance criteria
├── prototypes/
│   ├── index.html               # Entry point
│   ├── screen-1.html
│   ├── screen-2.html
│   └── styles.css
└── handoff/
    ├── SPEC.md                  # Executive summary
    ├── implementation-order.md  # Suggested build sequence
    └── refinement-notes.md      # What needs human polish
```

---

## Artifact Templates

### discovery.md
```markdown
# Discovery: [Project Name]

## Status: DRAFT | COMPLETE
## Last Updated: [timestamp]

## Problem Statement
[1-2 paragraphs describing the problem]

## Current State
How do users handle this today? What are the pain points?

## Target Users
Who has this problem? How acute is it?

## "Why" Chain
1. Why is this a problem? → [answer]
2. Why does that matter? → [answer]
3. [Continue until fundamental truth]

## Assumptions
| Assumption | Evidence | Confidence | To Validate |
|------------|----------|------------|-------------|
| ... | ... | Low/Med/High | ... |

## Open Questions
- [ ] [Blocking question]
- [ ] [Non-blocking question]
```

### requirements.md
```markdown
# Requirements: [Project Name]

## Status: DRAFT | COMPLETE
## Last Updated: [timestamp]
## Depends On: discovery.md

## Scope
### In Scope
- [Item 1]
- [Item 2]

### Out of Scope
- [Item 1]
- [Item 2]

## User Stories
### [Category]
- As a [user], I can [action] so that [benefit]
  - Acceptance: [criteria]

## Success Criteria
How will we know this works?
- [Metric 1]
- [Metric 2]

## Constraints
- [Technical constraint]
- [Business constraint]
```

### Screen Spec Template
```markdown
# Screen: [Screen Name]

## Purpose
What does this screen accomplish?

## Entry Points
How does user get here?

## Layout
[ASCII mockup or description]

## Components
| Component | Behavior | States |
|-----------|----------|--------|
| ... | ... | ... |

## Interactions
| Trigger | Action | Result |
|---------|--------|--------|
| ... | ... | ... |

## Content/Copy
| Element | Copy |
|---------|------|
| Title | "..." |
| Empty state | "..." |
| Error | "..." |

## Edge Cases
- Loading: [description]
- Empty: [description]
- Error: [description]
- Offline: [description]
```

### implementation-plan.md
```markdown
# Implementation Plan: [Project Name]

## Status: DRAFT | COMPLETE
## Last Updated: [timestamp]
## Depends On: architecture.md

---

## Epic Overview

| Epic | Description | Stories | Complexity |
|------|-------------|---------|------------|
| E1: [Name] | [Brief description] | X stories | S/M/L |
| E2: [Name] | [Brief description] | X stories | S/M/L |

---

## Epic 1: [Epic Name]

**Goal:** [What this epic accomplishes]
**Dependencies:** [Other epics or external requirements]

### Story 1.1: [Story Title]

**As a** [user type]
**I want** [capability]
**So that** [benefit]

**Acceptance Criteria:**
- [ ] [Specific, testable criterion]
- [ ] [Specific, testable criterion]
- [ ] [Specific, testable criterion]

**Technical Notes:**
- [Implementation hint or constraint]

**Test Requirements:**
- [ ] Unit: [what to test]
- [ ] Integration: [what to test]
- [ ] E2E: [what to test]

**Complexity:** S / M / L
**Depends On:** [Story IDs or "None"]

---

### Story 1.2: [Story Title]
[Repeat structure...]

---

## Epic 2: [Epic Name]
[Repeat structure...]

---

## Dependency Graph

```
[Visual representation of story dependencies]
E1.S1 ──► E1.S2 ──► E2.S1
              └──► E1.S3 ──► E2.S2
```

---

## Implementation Order

Suggested sequence based on dependencies and risk:

1. **Phase 1:** [Stories to complete first]
2. **Phase 2:** [Stories that depend on Phase 1]
3. **Phase 3:** [Final stories]

---

## Definition of Done

A story is complete when:
- [ ] All acceptance criteria pass
- [ ] Unit tests written and passing
- [ ] Integration tests (if applicable) passing
- [ ] Code reviewed
- [ ] No new linter warnings
- [ ] Documentation updated (if user-facing)
```

---

## Session Persistence

**Cross-session resumption:**
```
User: /ideate --resume bank-import

System: Resuming "bank-import" ideation...

Last session: Jan 30, Design Specification phase
Status: 3 of 7 screens specified

Key decisions made:
- [Decision 1]
- [Decision 2]

Open questions (1 blocking):
- [Question]

Picking up where we left off...
```

**Context to preserve:**
- All artifact files
- Decision history with rationale
- Current phase and progress
- Open questions
- User preferences/reactions captured

---

## Integration Points

**Entry:**
- `/ideate "concept description"` - Start new session
- `/ideate --resume <project>` - Resume existing
- `/ideate --list` - Show active ideation sessions

**Exit to Plan Mode:**
- Ideation produces handoff package
- User approves package
- System: "Ready for implementation. Enter plan mode?"
- Plan mode receives ideation artifacts as input

---

## Implementation Phases

**Phase 1: MVP (Manual)**
- Agent instructions in `.claude/agents/ideate.md`
- Manual artifact creation
- Interview mode via AskUserQuestion tool
- HTML prototypes via Write tool

**Phase 2: Structured**
- Formal `/ideate` command
- Automated artifact scaffolding
- Session state management
- Resume functionality

**Phase 3: Enhanced**
- Global taste system
- Learned preferences
- Design asset generation integration
- Multi-project support
