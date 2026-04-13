# Well-Worn Tools

A curated collection of 20 Claude Code skills for software engineering excellence. Each skill follows Anthropic's production skill format with YAML frontmatter, progressive disclosure, and optimized triggering.

## Skills

| Skill | Description |
|-------|-------------|
| **architectural-decisions** | Structured trade-off analysis for choosing between libraries, patterns, and technologies |
| **backlog-grooming** | Systematic GitHub backlog maintenance: review PRs, close issues, identify gaps |
| **bug-squashing-methodology** | 5-step bug fix process with root cause analysis and TDD |
| **ci-debugging** | Debug CI test failures with structured protocol |
| **comprehensive-pr-review** | 10-section PR review covering security, quality, testing, and docs |
| **concurrency** | Safe concurrent code patterns across Python, TypeScript, Go, and Rust |
| **documentation** | Language-specific documentation patterns for docstrings, module docs, and API references |
| **error-handling** | Robust error handling that fails fast with clear diagnostics |
| **file-naming-conventions** | ISO 8601 date-prefix naming for documents and plans |
| **frontend-aesthetics** | Polished, accessible frontend UI with design tokens and semantic HTML |
| **max-quality-no-shortcuts** | Anti-bypass philosophy: fix root causes instead of adding `noqa` / `type: ignore` |
| **mutation-testing** | Write high-value tests that kill mutants through logic validation |
| **prompt-engineering** | Transform vague requests into effective 6-component prompts |
| **security** | Secure coding practices against OWASP top 10 across four languages |
| **skill-craft** | Meta-skill for building and validating production-quality skills |
| **stay-green** | 2-gate TDD workflow: Red-Green-Refactor + pre-commit quality checks |
| **testing** | Comprehensive test writing with TDD, AAA pattern, and language-specific frameworks |
| **tracer-code** | Incremental system building: wire the skeleton first, then replace stubs |
| **user-facing-error-messages** | Audit and rewrite user-facing error messages so users can self-serve instead of emailing support |
| **vibe** | Code style, naming conventions, and structural patterns for consistent codebases |

## Installation

### Claude Code

Copy the `.claude/skills/` directory into your project:

```bash
cp -r .claude/skills/ /path/to/your/project/.claude/skills/
```

Or symlink individual skills:

```bash
ln -s /path/to/well-worn-tools/.claude/skills/stay-green /path/to/your/project/.claude/skills/stay-green
```

### Claude.ai

Zip any skill folder and upload via **Settings > Capabilities > Skills**.

## Structure

Each skill follows the standard directory format:

```
skill-name/
├── SKILL.md          # Core instructions (always loaded when relevant)
├── references/       # Detailed docs loaded on demand (optional)
├── scripts/          # Executable tooling (optional)
└── assets/           # Templates, fonts, icons (optional)
```

Skills use three levels of progressive disclosure:

1. **YAML frontmatter** — always in system prompt; tells Claude *when* to use the skill
2. **SKILL.md body** — loaded when relevant; contains full instructions
3. **references/** — loaded on demand; detailed patterns, examples, templates

## License

MIT
