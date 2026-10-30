# Project skills

Each skill is its own folder containing a `SKILL.md`:

```
.claude/skills/
  my-skill/
    SKILL.md          required: frontmatter + instructions
    reference.md      optional: extra docs Claude reads on demand
    scripts/          optional: helper scripts the skill can run
```

`SKILL.md` starts with YAML frontmatter:

```markdown
---
name: my-skill
description: What this skill does and when Claude should use it.
---

# My skill

Instructions for Claude go here.
```

`name` must match the folder name (lowercase, hyphenated). `description` is
the only part always loaded into context, so it decides whether the skill
gets triggered -- state both what it does and when to use it.

Skills in this folder are available to anyone working in this repo. Personal
skills go in `~/.claude/skills/` instead.
