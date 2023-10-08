from distutils.version import LooseVersion

_versionstring = "1.2.2"
looseversion = LooseVersion(_versionstring)
openwebrx_version = "v{0}".format(looseversion)
