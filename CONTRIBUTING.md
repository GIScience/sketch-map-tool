# Contribution

Please always feel free to reach out to us via E-Mail (sketch-map-tool@heigit.org) to report any bug, to give feedbag or to receive support.

There are various other ways to contribute to the Sketch Map Tool: 

- Help to translate the Sketch Map Tool via [crowdin](https://crowdin.com/project/sketch-map-tool). If you have an active community
using the Sketch Map Tool using a currently unsupported language, feel free to reach out to us, so we can talk about adding it. 
- Create [issues](https://github.com/GIScience/sketch-map-tool/issues/new) to report bugs or suggest new features.
- Create [pull requests](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/about-pull-requests) to address issues.

## Issues

Bugs reports and enhancement suggestions are tracked via issues. Each issue should contain following information:

- A clear and descriptive title
- Description
- Current behavior and expected behavior
- Error message and stack trace

Issues should serve as the basis for creating a pull request. They should have at least one tag associated with them.

## Pull Requests (PR)

Pull requests (PR) are created to address one single issue or multiple. Either the assignee or the creator of the PR is responsible for merging.
Each PR has to be approved by at least one reviewer before merging it. A person can be assigned as reviewer by either mark them as such or asking for a review by tagging the person in the description/comment of the PR.

A draft pull request can be made even if the branch is not ready to be merged yet. This way people/reviewer know that there is someone still working on that branch actively. This gives them the opportunity share their thoughts knowing that the pull request is still subject to change and does not need a full review yet.

The [CHANGELOG.md](CHANGELOG.md) describes changes made in a pull request. It should contain a short description of the performed changes, as well as (a) link(s) to issue(s) or pull request.

### Review Process

1. Dev makes a PR.
2. Rev reviews and raises some comments if necessary.
3. Dev addresses the comments and leaves responses explaining what has to be done. In cases where Dev just implemented Rev's suggestion, a simple "Done" is sufficient.
4. Rev reviews the changes and
    - If Rev is happy with a change, then Rev resolves the comment.
    - If Rev is still unsatisfied with a change, then Rev adds another comment explaining what is still missing.
5. Restart from 3 until all comments are resolved.
6. If all issues are resolved the PR gets marked as approved and can be merged.

## Git Workflow

All development work is based on the main branch (`main`). Pull requests are expected to target the `main` branch.

## Style Guide

### Python

In short:
- Guideline: [PEP8](https://peps.python.org/pep-0008/), [PEP 484 (Type Hints)](https://peps.python.org/pep-0484/)

#### Linters and Autoformatter

This project uses [`ruff`](https://github.com/astral-sh/ruff) to ensure consistent code style.

```bash
ruff check --fix
ruff format
```

### JavaScript and CSS

In short:
- Guide: [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- Linter: [eslint](https://eslint.org/) and [stylelint](https://stylelint.io/)

#### Linters

This project uses [eslint](https://eslint.org/) (see `.eslintrc.json`) and [stylelint](https://stylelint.io/) (see `stylelintrc.json`)

Run those linter's with following commands:

```bash
# print linting errors to the console
npm run lint

# try to fix the above mentioned problems
npm run lint:fix
```

### Pre-Commit Hooks

[prek](https://prek.j178.dev/) is set up to run above mentioned tools (linters and formatters) prior to any git commit. In contrast to above described commands running these hooks will not apply any changes to the code base. Instead, 'prek' checks if there would be any changes to be made.

Tip: To run all hooks once execute `uv run prek run --all-files`
