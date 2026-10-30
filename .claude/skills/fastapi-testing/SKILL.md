TaskAPI/
│
├── .claude/
│   └── skills/
│       └── fastapi-testing/
│           └── SKILL.md
```

Create the Skill definition with the following prompt:
```
---
name: fastapi-testing
description: Generate comprehensive pytest test suites for FastAPI applications.
---

# FastAPI Testing Skill

Use this Skill whenever the user asks you to:

- Generate API test cases
- Test FastAPI endpoints
- Improve API test coverage
- Validate request and response models

## Instructions

When invoked:

1. Generate pytest-compatible test cases.
2. Use FastAPI's TestClient.
3. Test successful requests.
4. Test validation failures.
5. Test common edge cases.
6. Verify HTTP status codes.
7. Verify response payloads.
8. Suggest any missing test scenarios.

Always generate clean, well-structured, maintainable test code.