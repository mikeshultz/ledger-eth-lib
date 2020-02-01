# Development Notes

## Release

1) Bump version
2) Build: `python setup.py sdist bdist_wheel`
3) Upload to PyPi `twine upload --repository-url https://test.pypi.org/legacy/ dist/*`
