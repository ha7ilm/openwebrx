#!/usr/bin/python2
"""

    This file is part of OpenWebRX, 
    an open-source SDR receiver software with a web UI.
    Copyright (c) 2013-2015 by Andras Retzler <randras@sdr.hu>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import config_webrx as cfg, time, subprocess

def run(continuously=True):
    if not cfg.sdrhu_key: return 
    firsttime="(Your receiver is soon getting listed on sdr.hu!)"
    while True:
        cmd = "wget --timeout=15 -4qO- https://sdr.hu/update --post-data \"url=http://"+cfg.server_hostname+":"+str(cfg.web_port)+"&apikey="+cfg.sdrhu_key+"\" 2>&1"
        print "[openwebrx-sdrhu]", cmd
        returned=subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).communicate()
        returned=returned[0]
        #print returned
        if "UPDATE:" in returned:
            retrytime_mins = 20
            value=returned.split("UPDATE:")[1].split("\n",1)[0]
            if value.startswith("SUCCESS"):
                print "[openwebrx-sdrhu] Update succeeded! "+firsttime
                firsttime=""
            else:
                print "[openwebrx-sdrhu] Update failed, your receiver cannot be listed on sdr.hu! Reason:", value
        else:
            retrytime_mins = 2
            print "[openwebrx-sdrhu] wget failed while updating, your receiver cannot be listed on sdr.hu!"
        if not continuously: break
        time.sleep(60*retrytime_mins)

if __name__=="__main__":
    run(False)

