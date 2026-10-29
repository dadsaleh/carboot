"""Unit tests for config.py."""

# pyright: reportOptionalContextManager=false

import json
import os
import unittest

from config import (
    EBADCONFIGPARSE,
    EBADCONFIGPATH,
    ECONFIGBADTYPE,
    ConfigError,
    init_config,
)

TMP_PATH = "test/tmp_config.json"
MISSING_PATH = "test/missing_config.json"


def _write(data: str) -> str:
    """Write data to TMP_PATH and return the path."""
    with open(TMP_PATH, "w") as f:
        f.write(data)
    return TMP_PATH


class TestInitConfig(unittest.TestCase):
    def tearDown(self):
        try:
            os.remove(TMP_PATH)
        except OSError:
            pass

    def assertErrno(self, errno, path):
        with self.assertRaises(ConfigError) as cm:
            init_config(path=path)
        self.assertEqual(cm.exception.errno, errno)

    def test_loads_dict(self):
        config = {"a": "b", "n": 1, "nested": {"x": [1, 2]}}
        self.assertEqual(init_config(path=_write(json.dumps(config))), config)

    def test_loads_empty_dict(self):
        self.assertEqual(init_config(path=_write("{}")), {})

    def test_rejects_missing_file(self):
        self.assertErrno(EBADCONFIGPATH, MISSING_PATH)

    def test_rejects_bad_json(self):
        for data in ('{"a": "b"', "", "not json"):
            with self.subTest(data=data):
                self.assertErrno(EBADCONFIGPARSE, _write(data))

    def test_rejects_non_dict_json(self):
        for data in ("[1, 2]", '"text"', "1", "null"):
            with self.subTest(data=data):
                self.assertErrno(ECONFIGBADTYPE, _write(data))

    def test_rejects_non_string_path(self):
        for path in (None, 1, ["config.json"]):
            with self.subTest(path=path):
                self.assertErrno(EBADCONFIGPATH, path)

    def test_path_is_keyword_only(self):
        with self.assertRaises(TypeError):
            init_config(_write("{}"))  # type: ignore


if __name__ == "__main__":
    unittest.main()
