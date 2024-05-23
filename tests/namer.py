import os

from approvaltests import Namer

from tests import FIXTURE_DIR

APPROVED_DIR = FIXTURE_DIR / "approved"


class PytestNamer(Namer):
    def __init__(self):
        """An approval tests Namer for naming approved and received text files.

        The Namer includes fixture dir, module, class and function in name.

        This class utilizes the `PYTEST_CURRENT_TEST` environment variable, which
        consist of the nodeid and the current stage:
        `relative/path/to/test_file.py::TestClass::test_func[a] (call)`

        For better readability this class formats the filename to something like:
        `test_file-TestClass-test_func-a
        """
        # TODO: name clashes are possible.
        # Include dir names (except tests/integration/) to avoid name clashes
        nodeid = os.environ["PYTEST_CURRENT_TEST"]
        nodeid_without_dir = nodeid.split("/")[-1]
        parts = nodeid_without_dir.split("::")
        raw = "-".join(parts)
        self.name = (
            raw.replace(".py", "")
            .replace("[", "-")
            .replace("]", "")
            .replace(" (call)", "")
        )

    def get_received_filename(self) -> str:
        return str(APPROVED_DIR / str(self.name + ".received" + ".txt"))

    def get_approved_filename(self) -> str:
        return str(APPROVED_DIR / str(self.name + ".approved" + ".txt"))
