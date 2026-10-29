"""Loads the JSON configuration file."""

import json

from micropython import const

"""
    Error codes, stored in errno on every ConfigError.
"""

ECONFIGBADTYPE = const(0)
EBADCONFIGPATH = const(1)
EBADCONFIGPARSE = const(2)


class ConfigError(Exception):
    def __init__(self, errno, msg):
        super().__init__(msg)
        self.errno = errno


DEFAULT_PATH = "/config.json"


def init_config(*, path=DEFAULT_PATH) -> dict | None:
    """Return the config at path as a dict. Raises ConfigError if it cannot be read or parsed."""
    try:
        if type(path) is str:
            with open(path) as f:
                config = json.load(f)
                if (t := type(config)) is dict:
                    return config
                else:
                    raise ConfigError(
                        ECONFIGBADTYPE, f"error=expected a dict, got, type={t}"
                    )
        else:
            raise ConfigError(EBADCONFIGPATH, f"error=bad config path, path={path}")

    except OSError as err:
        raise ConfigError(
            EBADCONFIGPATH, f"error=os could not find path, path={path}, err={err}"
        )
    except ValueError as err:
        raise ConfigError(EBADCONFIGPARSE, f"error=could not parse config, err={err}")


if __name__ == "__main__":
    init_config()
