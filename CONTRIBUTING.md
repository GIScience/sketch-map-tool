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
- Linter: [flake8](https://flake8.pycqa.org), [mypy](http://mypy-lang.org/), [bandit](https://github.com/PyCQA/bandit)

#### Linters

This project uses [flake8](https://flake8.pycqa.org), [mypy](http://mypy-lang.org/) and [bandit](https://github.com/PyCQA/bandit) to ensure consistent code style.

Run those linter's with following commands:

```bash
flake8 .
mypy --strict .
bandit -r .
```

*Tips:*
- Mark in-line that flake8 should not raise any error: `print()  # noqa`
- Mark in-line that bandit should not raise any error: `# nosec`

### JavaScript and CSS

In short:
- Guide: [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- Linter: [eslint](https://eslint.org/) and [stylelint](https://stylelint.io/)

#### Linters

This project uses [eslint](https://eslint.org/) (see `.eslintrc.json`) and [stylelint](https://stylelint.io/) (see `stylelintrc.json`)


### Pre-Commit Hooks

[pre-commit](https://pre-commit.com/) is set up to run above mentioned tools (linters and formatters) prior to any git commit. In contrast to above described commands running these hooks will not apply any changes to the code base. Instead, 'pre-commit' checks if there would be any changes to be made.

Tip: To run all hooks once execute `pre-commit run --all-files`


## Tests

Please provide tests.
