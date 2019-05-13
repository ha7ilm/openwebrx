import threading
import subprocess
import time
from owrx.config import PropertyManager

import logging
logger = logging.getLogger(__name__)


class SdrHuUpdater(threading.Thread):
    def __init__(self):
        self.doRun = True
        super().__init__(daemon = True)

    def update(self):
        pm = PropertyManager.getSharedInstance()
        cmd = "wget --timeout=15 -4qO- https://sdr.hu/update --post-data \"url=http://{server_hostname}:{web_port}&apikey={sdrhu_key}\" 2>&1".format(**pm.__dict__())
        logger.debug(cmd)
        returned=subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).communicate()
        returned=returned[0].decode('utf-8')
        if "UPDATE:" in returned:
            retrytime_mins = 20
            value=returned.split("UPDATE:")[1].split("\n",1)[0]
            if value.startswith("SUCCESS"):
                logger.info("Update succeeded!")
            else:
                logger.warning("Update failed, your receiver cannot be listed on sdr.hu! Reason: %s", value)
        else:
            retrytime_mins = 2
            logger.warning("wget failed while updating, your receiver cannot be listed on sdr.hu!")
        return retrytime_mins

    def run(self):
        while self.doRun:
            retrytime_mins = self.update()
            time.sleep(60*retrytime_mins)
