---
name: pb-writing-skills
description: Use when creating new skills, editing existing skills, or verifying skills work before deployment
---

# pb-writing-skills

Create, edit, and verify agent skills. Skills are code that shapes agent behavior — treat them with the same rigor as production code.

**Core principle:** Skills are not prose. They are behavioral contracts that must be tested.

## Creating a New Skill

### 1. Identify the Trigger

Every skill needs a clear trigger condition:

- What user action or situation activates this skill?
- What's the earliest point it should trigger?
- What's the latest point it's still useful?

### 2. Define the Contract

The skill must specify:

- **Input:** What context does the skill need?
- **Process:** What steps must be followed?
- **Output:** What should the skill produce?
- **Constraints:** What must NOT happen?

### 3. Write the SKILL.md

```markdown
---
name: skill-name
description: Clear, concise description for auto-triggering
---

# Skill Name

## Overview

[1-2 sentences: what this skill does and why]

## When to Use

[Specific trigger conditions]

## The Process

[Numbered steps with clear instructions]

## Constraints

[What NOT to do]

## Integration

[How this skill connects to others]
```

### 4. Test the Skill

Before deploying:

1. Install in a test environment
2. Trigger the skill with a real scenario
3. Verify behavior matches expectations
4. Check for conflicts with other skills

## Editing Existing Skills

### Rules for Modification

1. **Understand before changing** — read the entire skill and its rationale
2. **Preserve carefully-tuned content** — Red Flags tables, rationalization lists, discipline patterns
3. **Test changes** — run the skill in a real session before committing
4. **Document why** — explain what problem the change solves

### What NOT to Change

- Red Flags tables (anti-rationalization patterns)
- "Iron Law" sections (non-negotiable rules)
- Skill trigger conditions (unless adding new triggers)
- Integration points with other skills

## Skill Quality Checklist

Before marking a skill complete:

- [ ] Clear trigger condition in description
- [ ] Numbered steps (not prose)
- [ ] Explicit constraints ("NEVER" list)
- [ ] Integration points documented
- [ ] Tested in real scenario
- [ ] No conflicts with existing skills

## Integration with pb-spec

- **New pb-spec skills:** Use this to create new workflow skills
- **Skill maintenance:** Use when updating existing skills
- **Quality assurance:** Use to verify skill behavior before release
