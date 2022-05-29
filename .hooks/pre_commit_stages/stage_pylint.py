"""
Contains class 'Pylint' to run Pylint on Python files
"""
import os
from .stage_base import Stage
from subprocess import Popen, PIPE


class Pylint(Stage):
    """
    Stage for running Pylint on Python files
    """
    file_formats = ["py"]

    def __str__(self):
        return "Pylint"

    def run(self):
        print()
        if os.name == "nt":
            activate_env = [".\\pylint_env\\Scripts\\activate"]
        else:
            activate_env = ["source", "pylint_env/bin/activate"]
        for file in self.files:
            if file.split(".")[-1] in self.file_formats:
                print(f"Running pylint for {file}")
                # pylint: disable=consider-using-with
                process = Popen(["python", "-m", "venv", "pylint_env", "&&",
                                 *activate_env, "&&",
                                 "pip", "install", "-r",
                                 f"{os.path.dirname(__file__)}{os.sep}pylint_requirements.txt",
                                 "&&",
                                 "python", "-m", "pylint", file], stdout=PIPE,
                                stderr=PIPE, shell=True)
                stdout, stderr = process.communicate()
                stdout = stdout.decode("utf8")
                stderr = stderr.decode("utf8")
                if stderr != "":
                    if "ERROR" in stderr:
                        raise Exception(f"Error when running pylint: '{stderr}'")
                    print(f"stderr output from pylint: '{stderr}")
                if stdout != "":
                    print(f"Pylint output: '{stdout}'")
                    if "Your code has been rated" in stdout and "at 10.00/10" not in stdout:
                        raise Exception("Pylint score below 10.00")
