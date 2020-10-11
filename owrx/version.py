from distutils.version import LooseVersion

_versionstring = "0.21.0-dev"
looseversion = LooseVersion(_versionstring)
openwebrx_version = "v{0}".format(looseversion)
