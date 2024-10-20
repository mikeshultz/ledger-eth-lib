# Development Notes

## Docs

A good way to work on docs is to use `sphinx-autobuild` that will build the docs and start a local Web server that will auto-reload on save.

    sphinx-autobuild --watch ledgereth/ docs/ build/docs/

Then you can visit http://127.0.0.1:8000 to view the docs locally.

## Linting

Make sure to lint your work:

    python setup.py lint

## Release

To release this package, create a new GitHub release and publish it.
