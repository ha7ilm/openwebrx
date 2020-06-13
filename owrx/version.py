from distutils.version import StrictVersion

_versionstring = "0.19.1"
strictversion = StrictVersion(_versionstring)
openwebrx_version = "v{0}".format(strictversion)
