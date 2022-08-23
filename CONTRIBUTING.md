# Contribution Guideline

Please contribute to this repository through creating [issues](https://github.com/GIScience/sketch-map-tool/issues/new) and [pull requests](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/about-pull-requests).

### Issues

Bugs reports and enhancement suggestions are tracked via issues. Each issue should contain following information:

- A clear and descriptive title
- Description
- Current behavior and expected behavior
- Error message and stack trace

Issues should serve as the basis for creating a pull request. They should have at least one tag associated with them.

### Pull Requests (PR)

Pull requests (PR) are created to address one single issue or multiple. Either the assignee or the creator of the PR is responsible for merging.
Each PR has to be approved by at least one reviewer before merging it. A person can be assigned as reviewer by either mark them as such or asking for a review by tagging the person in the description/comment of the PR.

A draft pull request can be made even if the branch is not ready to be merged yet. This way people/reviewer know that there is someone still working on that branch actively. This gives them the opportunity share their thoughts knowing that the pull request is still subject to change and does not need a full review yet.

The [CHANGELOG.md](CHANGELOG.md) describes changes made in a pull request. It should contain a short description of the performed changes, as well as (a) link(s) to issue(s) or pull request.

#### Review Process

1. Dev makes a PR.
2. Rev reviews and raises some comments if necessary.
3. Dev addresses the comments and leaves responses explaining what has to be done. In cases where Dev just implemented Rev's suggestion, a simple "Done" is sufficient.
4. Rev reviews the changes and
    - If Rev is happy with a change, then Rev resolves the comment.
    - If Rev is still unsatisfied with a change, then Rev adds another comment explaining what is still missing.
5. Restart from 3 until all comments are resolved.
6. If all issues are resolved the PR gets marked as approved and can be merged.

### Git Workflow

All development work is based on the main branch (`main`). Pull requests are expected to target the `main` branch.

## Style Guide

### Python

In short:
- Guideline: [PEP8](https://peps.python.org/pep-0008/), [PEP 484 (Type Hints)](https://peps.python.org/pep-0484/)
- Linter: [flake8](https://flake8.pycqa.org), [Pylint](https://pylint.pycqa.org/), [mypy](http://mypy-lang.org/), [bandit](https://github.com/PyCQA/bandit)

#### Linters

This project uses [flake8](https://flake8.pycqa.org), [Pylint](https://pylint.pycqa.org/), [mypy](http://mypy-lang.org/) and [bandit](https://github.com/PyCQA/bandit) to ensure consistent code style.

Run those linter's with following commands:

```bash
flake8 .
pylint .
mypy --strict .
bandit .
```

*Tips:*
- Mark in-line that flake8 should not raise any error: `print()  # noqa`
- Mark in-line that pylint should not raise any error: `# pylint: disable=rule-name`
- Mark in-line that bandit should not raise any error: `# nosec`

### HTML

See [.htmlhintrc](.htmlhintrc) and the [documentation of these rules](https://github.com/htmlhint/HTMLHint/tree/master/docs/user-guide/rules)

### JavaScript

[Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript) with some modifications (see [.eslintrc.json](.eslintrc.json))

### CSS

[stylelint-config-standard](https://github.com/stylelint/stylelint-config-standard) with some modifications (see [.stylelintrc.json](.stylelintrc.json))  

## Commit Hooks

If you discover any violations in the existing code, feel very welcome to fix them. To facilitate paying attention to these conventions, please make sure that for your pull request all checks succeed. You can also set up git hooks to automatically run relevant linters before your code is committed, see [.hooks/README.MD](.hooks/README.MD) for more info. Please also make sure that everything you modify or add is covered by [unit tests](test).

## Tests

Please provide tests.
