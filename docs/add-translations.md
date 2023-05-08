# Add translations
The Sketch Map Tool uses [Flask-babel](https://github.com/python-babel/flask-babel) for internationalisation. 
It is configured in [babel.cfg](../babel.cfg) to look for strings to be translated in all Python files and Jinja2 
templates.

1.  To add a string to be translated, use `gettext("my string")` (imported from `flask_babel`) in the Python code and 
`{{ _("my string") }}` in the templates.

2. To obtain all strings for translation, run the following from commandline 
   ```
   poetry run pybabel extract -F babel.cfg -o messages.pot .
   ```
   Note: to ignore certain directories, you can use the option `--ignore-dirs my_dir`

   After running this command, a file `messages.pot` has been created containing all strings that have been marked for 
   translation.

3. Then, run another command to **initially** create the translation file (see below for how to update) for a certain language (in this case `de`). Repeat for each 
language for which you want to provide translations.  

   **NOTE:** Only run the following command to initially create the translation file for a language. It will **overwrite** 
   existing translations for the specified language otherwise. 

   ```
   poetry run pybabel init -i messages.pot -d sketch_map_tool/translations -l de
   ```

   This has created a file under `translations/LANGUAGE_CODE/LC_MESSAGES/messages.po` in which you can enter the 
translations. Either edit the file directly or use software for handling PO files, e.g. [Poedit](https://github.com/vslavik/poedit).

   If you want to **update** the translations for a language for which already some translations exists, e.g. because a new 
string has been added, run

   ```
   poetry run pybabel update -i messages.pot -d sketch_map_tool/translations
   ```
   to add the new string(s) to all existing PO files. This keeps existing translations.

4. As soon as all translations have been added, they need to be compiled, running

   ```
   poetry run pybabel compile -d sketch_map_tool/translations
   ```

Now the app should automatically use the provided translations in case the respective locality is chosen.

## Troubleshooting
* Make sure that the translations are stored under `sketch_map_tool/translations`