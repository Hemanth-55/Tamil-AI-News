---
name: session-end
description: Save this session to the repo so nothing is lost. Use when Hemi says "wrap up", "save", "update the log" or is ending the session.
---

# Session end

1. Add an entry at the TOP of `notes/session-log.md` (under the title):
   ```
   ## YYYY-MM-DD: <short title>
   - Done: ...
   - Decisions: ...
   - Next: ...
   ```
   Keep it to facts, not a transcript.
2. Update `notes/backlog.md` (tick done items, add new ones) and `notes/decisions.md` if anything lasting was decided.
3. Check that nothing secret is staged (keys, passwords, tokens, .env).
4. Commit, then `git pull --rebase`, then push. If the rebase conflicts in `notes/`, keep BOTH sides' entries, newest first.
5. Feature work on a branch: push the branch. Don't merge to `main` without Hemi's OK.
6. Tell Hemi in one line what was saved.
