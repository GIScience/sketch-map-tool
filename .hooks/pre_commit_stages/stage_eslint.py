"""
Contains class 'ESLint' to run ESLint on JavaScript files
"""
from .stage_base import Stage
from subprocess import Popen, PIPE  # nosec


class ESLint(Stage):
    """
    Stage for running ESLint on JavaScript files
    """
    file_formats = ["js"]

    def run(self) -> None:
        for file in self.files:
            if file.split(".")[-1] in self.file_formats:
                print(f"Running ESLint for {file}")
                # pylint: disable=consider-using-with
                process = Popen(["npm", "install", "eslint@8.10.0", "&&",    # nosec
                                 "npm", "install", "eslint-config-airbnb-base@15.0.0", "&&",
                                 "npx", "eslint", file], stdout=PIPE,
                                stderr=PIPE, shell=True)
                stdout, stderr = process.communicate()
                stdout = stdout.decode("Windows-1252")
                stderr = stderr.decode("Windows-1252")
                print(f"ESLint Output: '{stdout}'")
                print(f"ESLint Error(s)/Warning(s): '{stderr}'")
                if process.returncode != 0:
                    raise Exception("ESLint detected errors")

    def __str__(self) -> str:
        return "ESLint"
