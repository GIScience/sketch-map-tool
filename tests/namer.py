import os
from pathlib import Path
from typing import Any

from approvaltests import Namer, ScenarioNamer
from approvaltests.namer.namer_base import NamerBase

from tests import FIXTURE_DIR

APPROVED_DIR = FIXTURE_DIR / "approved"


class PytestNamer(NamerBase):
    def __init__(self, extension=None):
        """An approval tests Namer for naming approved and received text files.

        The Namer includes fixture dir, module, class and function in name.

        This class utilizes the `PYTEST_CURRENT_TEST` environment variable, which
        consist of the nodeid and the current stage:
        `relative/path/to/test_file.py::TestClass::test_func[a] (call)`
        """
        # pytest node ID w/out directories
        self.nodeid = os.environ["PYTEST_CURRENT_TEST"].split("/")[-1]
        NamerBase.__init__(self, extension)

    def get_file_name(self) -> str:
        """File name is pytest nodeid w/out file name and ` (call)` postfix."""
        return self.nodeid.split("::")[1].replace(" (call)", "")

    def get_directory(self) -> Path:
        """Directory is `tests/fixtures/approval/{file_name}/`."""
        # TODO: name clashes are possible.
        # Include dir names (except tests/integration/) to avoid name clashes
        return APPROVED_DIR / self.nodeid.split("::")[0].replace(".py", "")

    def get_config(self) -> dict:
        return {}


class PytestScenarioNamer(ScenarioNamer):
    def get_basename(self) -> str:
        basename = self.base_namer.get_basename()
        names = [f"[{n}]" for n in self.scenario_names]
        scenarios = ".".join(names)
        return f"{basename}.{scenarios}"


class PytestNamerFactory:
    @staticmethod
    def with_parameters(*args: Any) -> Namer:
        return PytestScenarioNamer(PytestNamer(), *args)
