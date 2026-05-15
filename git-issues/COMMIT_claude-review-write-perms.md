fix(ci): grant claude-code-review write perms on PRs and issues

The Claude review action ran for ~10 minutes on PR #11 and reported
`conclusion: success`, but posted no comment, review, or thread because
the job only had `pull-requests: read` / `issues: read`. Without write
access the action cannot post its verdict, which silently defeats the
review gate downstream skills (address-feedback, await-claude-review)
depend on.

Promote both scopes to `write`. `contents` stays at `read` and the
action still has no ability to push commits.
