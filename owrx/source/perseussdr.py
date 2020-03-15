from .direct import DirectSource
from owrx.command import Flag, Option


#
# perseustest -s 768000 -u 0 -f 14150000 -r-|csdr convert_s8_f|nmux --bufsize 192512 --bufcnt 260 --port 35989 --address 127.0.0.1
# perseustest -a -t0    -o -
# perseustest -d 9 -a -t 100000 -o -  -s 768000 -u 0 -f 14150000 -r-

class PerseussdrSource(DirectSource):
    def getCommandMapper(self):
        return super().getCommandMapper().setBase("perseustest -p -d -1 -a -t 100000 -o -  ").setMappings(
            {
                "samp_rate": Option("-s"),
                "tuner_freq": Option("-f"),
                "rf_gain": Option("-u"),
                "lna_gain": Option("-g"),
                "rf_amp": Option("-x"),
            }
        ).setStatic("-r-")

    def getEventNames(self):
        return super().getEventNames() + [
            "lna_gain",
            "rf_amp",
        ]

    def getFormatConversion(self):
#        return ["csdr convert_s24_f --bigendian"]
#        return ["csdr convert_s24_f", "csdr gain_ff 20"]
        return ["csdr gain_ff 20"]
