from owrx.source.direct import DirectSource
from owrx.command import Option
import time


class Rf103Source(DirectSource):
    def getCommandMapper(self):
        return super().getCommandMapper().setBase("rf103_sdr -i /home/jakob/workspace/RF103/rx888.img").setMappings({
            "samp_rate": Option("-s"),
            "center_freq": Option("-f"),
            "attenuation": Option("-a"),
        })

    def sleepOnRestart(self):
        time.sleep(1)
