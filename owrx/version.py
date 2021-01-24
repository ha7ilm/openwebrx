from distutils.version import LooseVersion

_versionstring = "0.20.2"
looseversion = LooseVersion(_versionstring)
openwebrx_version = "v{0}".format(looseversion)
