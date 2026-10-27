import errno
import os
import random
import unittest

from config import init_config

G1 = """{"a": "b"}"""
B2 = """{"a": "b"""


PATH = "test/"

created_mocks = []
cleanup = True


class TestConfig(unittest.TestCase):
    def test_loads_valid_configuration_file(self):
        config_path = _create_mock(G1)
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

    def test_init_config_returns_none_when_invalid_configuration_fail_open(self):
        config_path = _create_mock(B2)
        r = "xyz"
        if (
            config_path != None
            and (r := init_config(config_path, fail_open=True)) != None
        ):
            self.fail()  # Fails if we did not get None
        self.assertEqual(r, None)

    def test_init_config_returns_none_when_config_cannot_be_found_fail_open(self):
        import binascii

        r = "xyz"
        bad_path = (binascii.hexlify(os.urandom(32))).decode()
        if (r := init_config(bad_path, fail_open=True)) != None:
            self.fail()
        self.assertEqual(r, None)

    def test_init_config_sys_exit_when_config_cannot_be_found_fail_closed(self):
        import binascii

        bad_path = (binascii.hexlify(os.urandom(32))).decode()
        try:
            _ = init_config(bad_path, fail_open=False)
        except SystemExit:
            return
        self.fail()

    def test_init_config_sys_exit_when_invalid_config_fail_closed(self):
        config_path = _create_mock(B2)
        if config_path == None:
            self.fail()
        try:
            _ = init_config(config_path, fail_open=False)
        except SystemExit:
            return
        self.fail()

    # If cleanup is disabled, you must manually delete the files afterward
    def tearDown(self):
        if len(created_mocks) > 0 and cleanup:
            try:
                for path in created_mocks:
                    if path in created_mocks:
                        os.remove(path)
                        created_mocks.remove(path)
                        print(f"removed_path={path}")
            except OSError as err:
                if err.errno == errno.ENOENT:
                    print("failed to remove one or more testing files")


def _create_mock(data: str) -> str | None:
    name = PATH + "test_config_" + (str(random.random()).replace(".", "")) + ".json"

    with open(name, "w") as f:
        f.write(data)

    if name not in created_mocks:
        created_mocks.append(name)
    return name


if __name__ == "__main__":
    unittest.main()
