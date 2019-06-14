import pathlib

import os_aio_pod


def test_version():
    version_file = (
        pathlib.Path(__file__).parents[1].joinpath("src/os_aio_pod/VERSION").absolute()
    )
    assert os_aio_pod.__version__ == open(version_file).read().strip()


if __name__ == "__main__":
    test_version()
