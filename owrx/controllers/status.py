from . import Controller
from owrx.client import ClientRegistry
from owrx.version import openwebrx_version
from owrx.sdr import SdrService
from owrx.config import Config
import os
import json
import pkg_resources


class StatusController(Controller):
    def indexAction(self):
        pm = Config.get()
        # convert to old format
        gps = (pm["receiver_gps"]["lat"], pm["receiver_gps"]["lon"])
        avatar_path = pkg_resources.resource_filename("htdocs", "gfx/openwebrx-avatar.png")
        # TODO keys that have been left out since they are no longer simple strings: sdr_hw, bands, antenna
        vars = {
            "status": "active",
            "name": pm["receiver_name"],
            "op_email": pm["receiver_admin"],
            "users": ClientRegistry.getSharedInstance().clientCount(),
            "users_max": pm["max_clients"],
            "gps": gps,
            "asl": pm["receiver_asl"],
            "loc": pm["receiver_location"],
            "sw_version": openwebrx_version,
            "avatar_ctime": os.path.getctime(avatar_path),
        }
        self.send_response("\n".join(["{key}={value}".format(key=key, value=value) for key, value in vars.items()]))

    def getProfileStats(self, profile):
        return {
            "name": profile["name"],
            "center_freq": profile["center_freq"],
            "sample_rate": profile["samp_rate"],
        }

    def getReceiverStats(self, receiver):
        stats = {
            "name": receiver.getName(),
            # TODO would be better to have types from the config here
            "type": type(receiver).__name__,
            "profiles": [self.getProfileStats(p) for p in receiver.getProfiles().values()]
        }
        return stats

    def jsonAction(self):
        pm = Config.get()

        status = {
            "receiver": {
                "name": pm["receiver_name"],
                "admin": pm["receiver_admin"],
                "gps": pm["receiver_gps"],
                "asl": pm["receiver_asl"],
                "location": pm["receiver_location"],
            },
            "max_clients": pm["max_clients"],
            "version": openwebrx_version,
            "sdrs": [self.getReceiverStats(r) for r in SdrService.getSources().values()]
        }
        self.send_response(json.dumps(status), content_type="application/json")
