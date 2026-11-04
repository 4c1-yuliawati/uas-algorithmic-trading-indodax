# Commit and GitHub evidence

This ZIP contains a local `.git` repository with an initial project-scaffold commit made at its actual creation time. That timestamp is after the assignment's 4 Nov 2026 12:00 WIB freeze deadline; it is not a timely freeze commit.

To publish the full history:

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git branch -M main
git push -u origin main
```

Then copy the public repository URL and `git rev-parse HEAD` / `git show -s --format=%cI HEAD` into `docs/submission-notes.txt`. Do not force-push. Use your own GitHub account and record any later changes in new commits.
