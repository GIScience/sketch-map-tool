"""
Contains class 'Pylint' to run Pylint on Python files
"""
import os
from subprocess import PIPE, Popen  # nosec

from .stage_base import Stage


class Pylint(Stage):
    """
    Stage for running Pylint on Python files
    """

    file_formats = ["py"]

    def __str__(self) -> str:
        return "Pylint"

    def run(self) -> None:
        print()
        if os.name == "nt":
            activate_env = [".\\pylint_env\\Scripts\\activate"]
        else:
            activate_env = ["source", "pylint_env/bin/activate"]
        # pylint: disable=consider-using-with
        process = Popen(
            [
                "python",
                "-m",
                "venv",
                "pylint_env",
                "&&",
                *activate_env,
                "&&",
                "pip",
                "install",
                "-r",
                f"{os.path.dirname(__file__)}{os.sep}pylint_requirements.txt",
                "&&",
                "pip",
                "install",
                "-r",
                "requirements.txt",
            ],
            shell=True,  # nosec
        )
        process.communicate()
        for file in self.files:
            if file.split(".")[-1] in self.file_formats:
                print(f"Running pylint for {file}")
                process = Popen(
                    [*activate_env, "&&", "python", "-m", "pylint", file],
                    stdout=PIPE,
                    stderr=PIPE,
                    shell=True,  # nosec
                )
                stdout, stderr = process.communicate()
                stdout_str = stdout.decode("utf8")
                stderr_str = stderr.decode("utf8")
                if stderr_str != "":
                    if "ERROR" in stderr_str:
                        raise Exception(f"Error when running pylint: '{stderr_str}'")
                    print(f"stderr output from pylint: '{stderr_str}")
                if stdout_str != "":
                    print(f"Pylint output: '{stdout_str}'")
                    if (
                        "Your code has been rated" in stdout_str
                        and "at 10.00/10" not in stdout_str
                    ):
                        raise Exception("Pylint score below 10.00")
