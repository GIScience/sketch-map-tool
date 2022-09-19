"""
Contains class 'ESLint' to run ESLint on JavaScript files
"""
from subprocess import PIPE, Popen  # nosec

from .stage_base import Stage


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
                process = Popen(
                    [
                        "npm",
                        "install",
                        "eslint@8.10.0",
                        "&&",
                        "npm",
                        "install",
                        "eslint-config-airbnb-base@15.0.0",
                        "&&",
                        "npx",
                        "eslint",
                        file,
                    ],
                    stdout=PIPE,
                    stderr=PIPE,
                    shell=True,  # nosec
                )
                stdout, stderr = process.communicate()
                stdout_str = stdout.decode("Windows-1252")
                stderr_str = stderr.decode("Windows-1252")
                print(f"ESLint Output: '{stdout_str}'")
                print(f"ESLint Error(s)/Warning(s): '{stderr_str}'")
                if process.returncode != 0:
                    raise Exception("ESLint detected errors")

    def __str__(self) -> str:
        return "ESLint"
