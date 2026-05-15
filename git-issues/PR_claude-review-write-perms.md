## Summary

Grants `pull-requests: write` and `issues: write` to the `claude-review` job in `.github/workflows/claude-code-review.yml` so the action can actually post its verdict comment.

## Context

On PR #11, the action ran for ~10 minutes and returned `conclusion: success`, but produced no top-level comment, no review, and no line-level threads. The job permissions block was:

```yaml
permissions:
  contents: read
  pull-requests: read    # <-- cannot post comments
  issues: read           # <-- cannot post issue-style comments (PR top-level comments use this scope)
  id-token: write
```

Without write access on those scopes, the action's comment-posting step silently no-ops. That defeats the verdict gate the `address-feedback` and `await-claude-review` skills rely on — they look for a top-level `Verdict: LGTM | CHANGES_REQUESTED | COMMENTS` comment for the current HEAD and can't make a merge decision without one.

## Changes

- `.github/workflows/claude-code-review.yml`: promote `pull-requests` and `issues` from `read` to `write`. `contents` stays `read`; the action still cannot push commits.

## Test Plan

- [ ] `actionlint` (Workflow Lint job) passes on the diff.
- [ ] On this PR, the `claude-review` action posts a top-level comment ending with a `Verdict:` line.
- [ ] On a follow-up PR (any next PR), the verdict comment appears and `address-feedback` can parse it.
