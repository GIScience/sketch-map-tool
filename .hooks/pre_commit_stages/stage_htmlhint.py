"""
Contains class 'HTMLHint' to run HTMLHint on HTML files
"""
from subprocess import PIPE, Popen  # nosec

from .stage_base import Stage


class HTMLHint(Stage):
    """
    Stage for running HTMLHint on HTML files
    """

    file_formats = ["html", "vm"]
    ignore_files = ["analyses/html_gen/template.html"]

    def run(self) -> None:
        for file in self.files:
            if file.split(".")[-1] in self.file_formats:
                print(f"Running HTMLHint for {file}")
                if file in self.ignore_files:
                    print("Skipping file listed in 'ignore_files'")
                    continue
                # pylint: disable=consider-using-with
                process = Popen(
                    [
                        "npm",
                        "install",
                        "htmlhint@1.1.4",
                        "&&",
                        "npx",
                        "htmlhint",
                        file,
                    ],
                    stdout=PIPE,
                    stderr=PIPE,
                    shell=True,  # nosec
                )
                stdout, stderr = process.communicate()
                stdout_str = stdout.decode("utf8")
                stderr_str = stderr.decode("utf8")
                print(f"HTMLHint Output: '{stdout_str}'")
                print(f"HTMLHint Error(s)/Warning(s): '{stderr_str}'")
                if process.returncode != 0:
                    raise Exception("HTMLHint detected issues")

    def __str__(self) -> str:
        return "HTMLHint"
