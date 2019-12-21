from owrx.config import PropertyManager
import threading
import subprocess
import os
import socket
import shlex
import time
import signal

import logging

logger = logging.getLogger(__name__)


class SdrSource(object):
    STATE_STOPPED = 0
    STATE_STARTING = 1
    STATE_RUNNING = 2
    STATE_STOPPING = 3
    STATE_TUNING = 4
    STATE_FAILED = 5

    BUSYSTATE_IDLE = 0
    BUSYSTATE_BUSY = 1

    CLIENT_INACTIVE = 0
    CLIENT_BACKGROUND = 1
    CLIENT_USER = 2

    def __init__(self, id, props, port):
        self.id = id
        self.props = props
        self.profile_id = None
        self.activateProfile()
        self.rtlProps = self.props.collect(*self.getEventNames()).defaults(PropertyManager.getSharedInstance())
        self.wireEvents()

        self.port = port
        self.monitor = None
        self.clients = []
        self.spectrumClients = []
        self.spectrumThread = None
        self.process = None
        self.modificationLock = threading.Lock()
        self.failed = False
        self.state = SdrSource.STATE_STOPPED
        self.busyState = SdrSource.BUSYSTATE_IDLE

    def getEventNames(self):
        return [
            "samp_rate",
            "nmux_memory",
            "center_freq",
            "ppm",
            "rf_gain",
            "lna_gain",
            "rf_amp",
            "antenna",
            "if_gain",
            "lfo_offset",
        ]

    def wireEvents(self):
        def restart(name, value):
            logger.debug("restarting sdr source due to property change: {0} changed to {1}".format(name, value))
            self.stop()
            self.start()

        self.rtlProps.wire(restart)

    # override this in subclasses
    def getCommand(self):
        pass

    # override this in subclasses, if necessary
    def getFormatConversion(self):
        return None

    def activateProfile(self, profile_id=None):
        profiles = self.props["profiles"]
        if profile_id is None:
            profile_id = list(profiles.keys())[0]
        if profile_id == self.profile_id:
            return
        logger.debug("activating profile {0}".format(profile_id))
        self.profile_id = profile_id
        profile = profiles[profile_id]
        self.props["profile_id"] = profile_id
        for (key, value) in profile.items():
            # skip the name, that would overwrite the source name.
            if key == "name":
                continue
            self.props[key] = value

    def getId(self):
        return self.id

    def getProfileId(self):
        return self.profile_id

    def getProfiles(self):
        return self.props["profiles"]

    def getName(self):
        return self.props["name"]

    def getProps(self):
        return self.props

    def getPort(self):
        return self.port

    def useNmux(self):
        return True

    def getCommandValues(self):
        dict = self.rtlProps.collect(*self.getEventNames()).__dict__()
        if "lfo_offset" in dict and dict["lfo_offset"] is not None:
            dict["tuner_freq"] = dict["center_freq"] + dict["lfo_offset"]
        else:
            dict["tuner_freq"] = dict["center_freq"]
        return dict

    def start(self):
        self.modificationLock.acquire()
        if self.monitor:
            self.modificationLock.release()
            return

        props = self.rtlProps

        cmd = self.getCommand().format(**self.getCommandValues())

        format_conversion = self.getFormatConversion()
        if format_conversion is not None:
            cmd += " | " + format_conversion

        if self.useNmux():
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
            cmd = cmd + " | nmux --bufsize %d --bufcnt %d --port %d --address 127.0.0.1" % (
                nmux_bufsize,
                nmux_bufcnt,
                self.port,
            )

        # don't use shell mode for commands without piping
        if "|" in cmd:
            self.process = subprocess.Popen(cmd, shell=True, preexec_fn=os.setpgrp)
        else:
            # preexec_fn can go as soon as there's no piped commands left
            # the os.killpg call must be replaced with something more reasonable at the same time
            self.process = subprocess.Popen(shlex.split(cmd), preexec_fn=os.setpgrp)
        logger.info("Started rtl source: " + cmd)

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

        self.postStart()

        self.modificationLock.release()

        self.setState(SdrSource.STATE_FAILED if self.failed else SdrSource.STATE_RUNNING)

    def postStart(self):
        pass

    def isAvailable(self):
        return self.monitor is not None

    def isFailed(self):
        return self.failed

    def stop(self):
        self.setState(SdrSource.STATE_STOPPING)

        self.modificationLock.acquire()

        if self.process is not None:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except ProcessLookupError:
                # been killed by something else, ignore
                pass
        if self.monitor:
            self.monitor.join()
        self.sleepOnRestart()
        self.modificationLock.release()

        self.setState(SdrSource.STATE_STOPPED)

    def sleepOnRestart(self):
        pass

    def hasClients(self, *args):
        clients = [c for c in self.clients if c.getClientClass() in args]
        return len(clients) > 0

    def addClient(self, c):
        self.clients.append(c)
        hasUsers = self.hasClients(SdrSource.CLIENT_USER)
        hasBackgroundTasks = self.hasClients(SdrSource.CLIENT_BACKGROUND)
        if hasUsers or hasBackgroundTasks:
            self.start()
            self.setBusyState(SdrSource.BUSYSTATE_BUSY if hasUsers else SdrSource.BUSYSTATE_IDLE)

    def removeClient(self, c):
        try:
            self.clients.remove(c)
        except ValueError:
            pass

        hasUsers = self.hasClients(SdrSource.CLIENT_USER)
        hasBackgroundTasks = self.hasClients(SdrSource.CLIENT_BACKGROUND)
        self.setBusyState(SdrSource.BUSYSTATE_BUSY if hasUsers else SdrSource.BUSYSTATE_IDLE)
        if not hasUsers and not hasBackgroundTasks:
            self.stop()

    def addSpectrumClient(self, c):
        self.spectrumClients.append(c)
        if self.spectrumThread is None:
            # local import due to circular depencency
            from owrx.fft import SpectrumThread
            self.spectrumThread = SpectrumThread(self)
            self.spectrumThread.start()

    def removeSpectrumClient(self, c):
        try:
            self.spectrumClients.remove(c)
        except ValueError:
            pass
        if not self.spectrumClients and self.spectrumThread is not None:
            self.spectrumThread.stop()
            self.spectrumThread = None

    def writeSpectrumData(self, data):
        for c in self.spectrumClients:
            c.write_spectrum_data(data)

    def setState(self, state):
        if state == self.state:
            return
        self.state = state
        for c in self.clients:
            c.onStateChange(state)

    def setBusyState(self, state):
        if state == self.busyState:
            return
        self.busyState = state
        for c in self.clients:
            c.onBusyStateChange(state)
