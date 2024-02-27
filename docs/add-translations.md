# Translation

The Sketch Map Tool uses [Babel](https://babel.pocoo.org/en/latest/) through [Flask Babel](https://github.com/python-babel/flask-babel) for internationalization.
It is configured ([babel.cfg](../babel.cfg)) to look for strings to be translated in all Jinja2 HTML templates.
Text to be translated in Python files need to be manually selected and wrapped in a `gettext` function call (E.g. Error messages in `routes.py`).
Please refer to to the official documentation of [Flask Babel](https://python-babel.github.io/flask-babel/index.html#translating-applications) regarding the process of translating the application.

In short following steps need to be executed:

## Add a new translation

```bash
cd sketch_map_tool
pybabel extract -F config/babel.cfg -o messages.pot .
pybabel init -i messages.pot -d translations -l de
pybabel compile -d translations
```

## Update an existing translation

```bash
cd sketch_map_tool
pybabel extract -F config/babel.cfg -o messages.pot .
pybabel update -i messages.pot -d translations
pybabel compile -d translations
```
