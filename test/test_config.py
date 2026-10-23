import os
import random
import unittest

from config import init_config

GOOD_CONFIG = """{"a": "b"}"""

PATH = "test/"

created_mocks = []
cleanup = False


class TestConfig(unittest.TestCase):
    def test_loads_valid_configuration_file(self):
        config_path = _create_mock(GOOD_CONFIG)
        if (
            config_path != None
            and (r := init_config(config_path, fail_open=True)) != None
        ):
            try:
                t = r["a"]
            except KeyError:
                self.fail()
            self.assertEqual(t, "b")
        else:
            self.fail()

    # If disabled, you must manaually delete the files afterward
    def tearDown(self):
        if len(created_mocks) > 0 and cleanup:
            for path in created_mocks:
                os.remove(path)


def _create_mock(data: str) -> str | None:
    try:
        name = PATH + "test_config_" + (str(random.random()).replace(".", "")) + ".json"

        with open(name, "w") as f:
            f.write(data)
    except Exception:  # noqa BLE001
        return None
    created_mocks.append(name)
    return name


if __name__ == "__main__":
    unittest.main()
