"""
Contains class 'StyleLint' to run StyleLint on CSS files
"""
from .stage_base import Stage
from subprocess import Popen, PIPE


class StyleLint(Stage):
    """
    Stage for running StyleLint on CSS files
    """
    file_formats = ["css"]

    def run(self) -> None:
        for file in self.files:
            if file.split(".")[-1] in self.file_formats:
                print(f"Running StyleLint for {file}")
                # pylint: disable=consider-using-with
                process = Popen(["npm", "install", "stylelint@14.8.3", "&&",
                                 "npm", "install", "stylelint-config-standard@25.0.0", "&&",
                                 "npx", "stylelint", file],
                                stdout=PIPE, stderr=PIPE, shell=True)
                stdout, stderr = process.communicate()
                stdout = stdout.decode("utf8")
                stderr = stderr.decode("utf8")
                print(f"StyleLint Output: '{stdout}'")
                print(f"StyleLint Error(s)/Warning(s): '{stderr}'")
                if process.returncode != 0:
                    raise Exception("StyleLint detected issues")

    def __str__(self) -> str:
        return "StyleLint"
