from setuptools import find_packages, setup


def read(*filenames, **kwargs):
    import io
    from os.path import dirname, join

    encoding = kwargs.get("encoding", "utf-8")
    sep = kwargs.get("sep", "\n")
    buf = []
    for filename in filenames:
        with io.open(join(dirname(__file__), filename), encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


setup(
    name="os-aio-pod",
    version=read("src/os_aio_pod/VERSION").strip(),
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    license="MIT License",
    description="A container of aio components.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Ozzy",
    author_email="cfhamlet@gmail.com",
    url="https://github.com/cfhamlet/os-aio-pod",
    install_requires=open("requirements/requirements.txt").read().split("\n"),
    python_requires=">=3.6",
    zip_safe=False,
    entry_points={"console_scripts": ["os-aio-pod = os_aio_pod.main:main"]},
    extras_require={
        "uvloop": ["uvloop"],
        "uvicorn": ["uvicorn"],
        "aiohttp": ["aiohttp"],
        "aiomonitor": ["aiomonitor"],
    },
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
)
