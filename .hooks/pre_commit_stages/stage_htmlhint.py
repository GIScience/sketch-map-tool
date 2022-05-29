"""
Contains class 'HTMLHint' to run HTMLHint on HTML files
"""
from subprocess import Popen, PIPE
from .stage_base import Stage


class HTMLHint(Stage):
    """
    Stage for running HTMLHint on HTML files
    """
    file_formats = ["html", "vm"]

    def run(self) -> None:
        for file in self.files:
            if file.split(".")[-1] in self.file_formats:
                print(f"Running HTMLHint for {file}")
                # pylint: disable=consider-using-with
                process = Popen(["npm", "install", "htmlhint@1.1.4", "&&",
                                 "npx", "htmlhint", file],
                                stdout=PIPE, stderr=PIPE, shell=True)
                stdout, stderr = process.communicate()
                stdout = stdout.decode("utf8")
                stderr = stderr.decode("utf8")
                print(f"HTMLHint Output: '{stdout}'")
                print(f"HTMLHint Error(s)/Warning(s): '{stderr}'")
                if process.returncode != 0:
                    raise Exception("HTMLHint detected issues")

    def __str__(self) -> str:
        return "HTMLHint"
