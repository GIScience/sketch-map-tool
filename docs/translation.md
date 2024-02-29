# Translation

## Internationalization

The Sketch Map Tool uses [Babel](https://babel.pocoo.org/en/latest/) through [Flask Babel](https://github.com/python-babel/flask-babel) for internationalization.
It is configured ([babel.cfg](../babel.cfg)) to look for strings to be translated in all Jinja2 HTML templates.
Text to be translated in Python files need to be manually selected and wrapped in a `gettext` function call (E.g. Error messages in `routes.py`).
Please refer to to the official documentation of [Flask Babel](https://python-babel.github.io/flask-babel/index.html#translating-applications) regarding the process of translating the application.

## Translation via Crowdin

The Sketch Map Tool uses the platform [Crowdin](https://crowdin.com/) for translation.

Text marked for translation is send from GitHub to Crowdin via GitHub Action ([github-to-crowdin.yml](../.github/workflows/github-to-crowdin.yml)). The action triggers on push to `main`.

Translated text is send from Crowdin to GitHub via GitHub Action ([crowdin-to-github.yml](../.github/workflows/crowdin-to-github.yml)). The action triggers regularly and results in a PR when new translations are available.

## Manual Translation

> Note: Since Crowdin is used for translation following section is not longer relevant.

The basic process for translation on a local machine would look something like this:

### Add a new translation

```bash
pybabel extract -F config/babel.cfg -o messages.pot .
pybabel init -i messages.pot -d sketch_map_tool/translations -l de
pybabel compile -d sketch_map_tool/translations
```

### Update an existing translation

```bash
cd sketch_map_tool
pybabel extract -F config/babel.cfg -o messages.pot .
pybabel update -i messages.pot -d sketch_map_tool/translations
pybabel compile -d sketch_map_tool/translations
```

