#!/usr/bin/python3
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

import logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    pm = PropertyManager.getSharedInstance().loadConfig()

    if "sdrhu_public_listing" not in pm or not pm["sdrhu_public_listing"]:
        logger.error('Public listing on sdr.hu is not activated. Please check "sdrhu_public_listing" in your config.')
        exit(1)
    if "sdrhu_key" not in pm or pm["sdrhu_key"] is None or pm["sdrhu_key"] == "":
        logger.error('Missing "sdrhu_key" in your config. Aborting')
        exit(1)
    SdrHuUpdater().update()
