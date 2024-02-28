# Translation

The Sketch Map Tool uses [Babel](https://babel.pocoo.org/en/latest/) through [Flask Babel](https://github.com/python-babel/flask-babel) for internationalization.
It is configured ([babel.cfg](../babel.cfg)) to look for strings to be translated in all Jinja2 HTML templates.
Text to be translated in Python files need to be manually selected and wrapped in a `gettext` function call (E.g. Error messages in `routes.py`).
Please refer to to the official documentation of [Flask Babel](https://python-babel.github.io/flask-babel/index.html#translating-applications) regarding the process of translating the application.


# Automatic Approach:

The Sketch Map Tool uses crowdin to help as a platform for translations. To get the strings which need to be translated the github
action [github-to-crowdin.yml](../.github/workflows/github-to-crowdin.yml) is used. It is executed once anything is pushed into origin/main.

To get the translated strings from crowdin to github the github action [crowdin-to-github.yml](../.github/workflows/crowdin-to-github.yml)
is used. It runs daily and opens a new pullrequest if new translation string where added.


# Manual Approach: 
Without the help of tools like crowdin, things would have to look like this:

## Add a new translation

```bash
pybabel extract -F config/babel.cfg -o messages.pot .
pybabel init -i messages.pot -d sketch_map_tool/translations -l de
pybabel compile -d sketch_map_tool/translations
```

## Update an existing translation

```bash
cd sketch_map_tool
pybabel extract -F config/babel.cfg -o messages.pot .
pybabel update -i messages.pot -d sketch_map_tool/translations
pybabel compile -d sketch_map_tool/translations
```
