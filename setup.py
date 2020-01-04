from glob import glob
from setuptools import setup, find_namespace_packages
from owrx.version import strictversion

setup(
    name="OpenWebRX",
    version=str(strictversion),
    packages=find_namespace_packages(include=["owrx", "owrx.source", "csdr", "htdocs"]),
    package_data={"htdocs": [f[len("htdocs/") :] for f in glob("htdocs/**/*", recursive=True)]},
    entry_points={"console_scripts": ["openwebrx=owrx.__main__:main"]},
    # use the github page for now
    url="https://github.com/jketterl/openwebrx",
    author="András Retzler, Jakob Ketterl",
    author_email="randras@sdr.hu, jakob.ketterl@gmx.de",
    maintainer="Jakob Ketterl",
    maintainer_email="jakob.ketterl@gmx.de",
    license="GAGPL",
    python_requires=">=3.6",
)
