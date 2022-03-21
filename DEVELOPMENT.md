# Development Notes

## Linting

Make sure to lint your work:

    python setup.py lint

## Release

1) Bump version (`bump2version patch`).  This will update the version in source and make a commit and version tag.  Don't forget to push your tags: `git push --follow-tags`.
2) Merge branch into `master`
3) Create GitHub release with tag created by bump2version and release will happen automatically

**TIP**: Instead of `--follow-tags`, you can configure git to always do this on push: `git config --global push.followTags true`
