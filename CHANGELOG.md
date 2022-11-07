# Changelog

## Current Main

### New Features

- add content and style to index ([#73])
- use celery as queue to run background tasks ([#72])
- implement web map service client ([#95])
- add module containing the paper format specs ([#99])
- include map scale as request parameter to the backend ([#107])
- add module to generate qr-codes as svg & rlg ([#98])
- add resources (compass and globes as SVG graphics) for map generation ([#101])

### Bug Fixes

- fix analyses after project layout change (Issue: [#58], PR: [#59])

### Other Changes

- add package.json to configure JS and CSS linters ([#71])
- add (responsive) header to base template and introduce a header-message block ([#70])
- endpoint(/create): add UI for map-based area-of-interest and print-layout control ([#42] [#47])
- define new endpoints & add templates for creating a new sketch map ([#55])
- add auto-formatters black and isort ([#39])
- use pre-commit package for managing git hooks ([#52])
- run all linters and formatters as pre-commit hook ([#52])
- run tests in CI ([#32])
- make Python 3.10 the minimal required Python version ([#102])

[#32]: https://github.com/GIScience/sketch-map-tool/pull/32
[#39]: https://github.com/GIScience/sketch-map-tool/pull/39
[#42]: https://github.com/GIScience/sketch-map-tool/issues/42
[#47]: https://github.com/GIScience/sketch-map-tool/issues/47
[#52]: https://github.com/GIScience/sketch-map-tool/pull/52
[#55]: https://github.com/GIScience/sketch-map-tool/pull/55
[#58]: https://github.com/GIScience/sketch-map-tool/issues/58
[#59]: https://github.com/GIScience/sketch-map-tool/pull/59
[#70]: https://github.com/GIScience/sketch-map-tool/pull/70
[#71]: https://github.com/GIScience/sketch-map-tool/pull/71
[#72]: https://github.com/GIScience/sketch-map-tool/pull/72
[#73]: https://github.com/GIScience/sketch-map-tool/pull/73
[#95]: https://github.com/GIScience/sketch-map-tool/pull/95
[#98]: https://github.com/GIScience/sketch-map-tool/pull/98
[#99]: https://github.com/GIScience/sketch-map-tool/pull/99
[#101]: https://github.com/GIScience/sketch-map-tool/pull/101
[#102]: https://github.com/GIScience/sketch-map-tool/pull/102
[#107]: https://github.com/GIScience/sketch-map-tool/pull/107
