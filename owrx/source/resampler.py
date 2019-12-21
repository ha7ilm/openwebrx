from . import SdrSource
import subprocess
import threading
import os
import socket
import time

import logging

logger = logging.getLogger(__name__)


class Resampler(SdrSource):
    def __init__(self, props, port, sdr):
        sdrProps = sdr.getProps()
        self.shift = (sdrProps["center_freq"] - props["center_freq"]) / sdrProps["samp_rate"]
        self.decimation = int(float(sdrProps["samp_rate"]) / props["samp_rate"])
        if_samp_rate = sdrProps["samp_rate"] / self.decimation
        self.transition_bw = 0.15 * (if_samp_rate / float(sdrProps["samp_rate"]))
        props["samp_rate"] = if_samp_rate

        self.sdr = sdr
        super().__init__(None, props, port)

    def start(self):
        if self.isFailed():
            return

        self.modificationLock.acquire()
        if self.monitor:
            self.modificationLock.release()
            return

        self.setState(SdrSource.STATE_STARTING)

        props = self.rtlProps

        resampler_command = [
            "nc -v 127.0.0.1 {nc_port}".format(nc_port=self.sdr.getPort()),
            "csdr shift_addition_cc {shift}".format(shift=self.shift),
            "csdr fir_decimate_cc {decimation} {ddc_transition_bw} HAMMING".format(
                decimation=self.decimation, ddc_transition_bw=self.transition_bw
            ),
        ]

        nmux_bufcnt = nmux_bufsize = 0
        while nmux_bufsize < props["samp_rate"] / 4:
            nmux_bufsize += 4096
        while nmux_bufsize * nmux_bufcnt < props["nmux_memory"] * 1e6:
            nmux_bufcnt += 1
        if nmux_bufcnt == 0 or nmux_bufsize == 0:
            logger.error(
                "Error: nmux_bufsize or nmux_bufcnt is zero. These depend on nmux_memory and samp_rate options in config_webrx.py"
            )
            self.modificationLock.release()
            return
        logger.debug("nmux_bufsize = %d, nmux_bufcnt = %d" % (nmux_bufsize, nmux_bufcnt))
        resampler_command += [
            "nmux --bufsize %d --bufcnt %d --port %d --address 127.0.0.1" % (nmux_bufsize, nmux_bufcnt, self.port)
        ]
        cmd = " | ".join(resampler_command)
        logger.debug("resampler command: %s", cmd)
        self.process = subprocess.Popen(cmd, shell=True, preexec_fn=os.setpgrp)
        logger.info("Started resampler source: " + cmd)

        available = False

        def wait_for_process_to_end():
            rc = self.process.wait()
            logger.debug("shut down with RC={0}".format(rc))
            self.monitor = None

        self.monitor = threading.Thread(target=wait_for_process_to_end)
        self.monitor.start()

        retries = 1000
        while retries > 0:
            retries -= 1
            if self.monitor is None:
                break
            testsock = socket.socket()
            try:
                testsock.connect(("127.0.0.1", self.getPort()))
                testsock.close()
                available = True
                break
            except:
                time.sleep(0.1)

        if not available:
            self.failed = True

        self.modificationLock.release()

        self.setState(SdrSource.STATE_FAILED if self.failed else SdrSource.STATE_RUNNING)

    def activateProfile(self, profile_id=None):
        pass
