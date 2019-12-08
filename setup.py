from setuptools import setup, find_packages
from owrx.version import strictversion

setup(
    name="OpenWebRX",
    version=str(strictversion),
    packages=find_packages(),
    entry_points={"console_scripts": ["openwebrx=openwebrx:main"]},
    # use the github page for now
    url="https://github.com/jketterl/openwebrx",
    author="András Retzler, Jakob Ketterl",
    author_email="randras@sdr.hu, jakob.ketterl@gmx.de",
    maintainer="Jakob Ketterl",
    maintainer_email="jakob.ketterl@gmx.de",
    license="GAGPL",
)
