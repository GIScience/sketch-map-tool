"""
Contains class 'Mypy' to run mypy on Python files
"""
import os
from .stage_base import Stage
from subprocess import Popen, PIPE  # nosec


class Mypy(Stage):
    """
    Stage for running mypy on Python files
    """
    file_formats = ["py"]

    def __str__(self) -> str:
        return "mypy"

    def run(self) -> None:
        print()
        # pylint:disable=duplicate-code  # Potentially contains duplicates of pylint stage
        if os.name == "nt":
            activate_env = [".\\pylint_env\\Scripts\\activate"]
        else:
            activate_env = ["source", "pylint_env/bin/activate"]
        # pylint: disable=consider-using-with
        process = Popen(["python", "-m", "venv", "pylint_env", "&&",  # nosec
                         *activate_env, "&&",
                         "pip", "install", "-r",
                         f"{os.path.dirname(__file__)}{os.sep}mypy_requirements.txt"], shell=True)
        process.communicate()
        for file in self.files:
            if file.split(".")[-1] in self.file_formats:
                print(f"Running mypy for {file}")
                process = Popen([*activate_env, "&&",
                                 "python", "-m", "mypy", "--strict", file], stdout=PIPE,
                                stderr=PIPE, shell=True)
                stdout, stderr = process.communicate()
                stdout_str = stdout.decode("utf8")
                stderr_str = stderr.decode("utf8")
                if stderr_str != "":
                    if "ERROR" in stderr_str:
                        raise Exception(f"Error when running mypy: '{stderr_str}'")
                    print(f"stderr output from mypy: '{stderr_str}")
                if stdout_str != "":
                    print(f"mypy output: '{stdout_str}'")
                if process.returncode != 0:
                    raise Exception("mypy detected errors (see above)")
