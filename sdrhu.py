#!/usr/bin/python2
"""

    This file is part of OpenWebRX, 
    an open-source SDR receiver software with a web UI.
    Copyright (c) 2013-2015 by Andras Retzler <randras@sdr.hu>
    Copyright (c) 2019 by Jakob Ketterl <dd5jfk@darc.de>

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

from owrx.sdrhu import SdrHuUpdater
from owrx.config import PropertyManager

if __name__ == "__main__":
    pm = PropertyManager.getSharedInstance().loadConfig("config_webrx")

    if not "sdrhu_key" in pm:
        exit(1)
    SdrHuUpdater().update()
