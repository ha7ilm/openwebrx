from owrx.config import PropertyManager
import threading
import subprocess
import os
import socket
import shlex
import time
import signal
from abc import ABC, abstractmethod
from owrx.command import CommandMapper

import logging

logger = logging.getLogger(__name__)


class SdrSource(ABC):
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
        self.commandMapper = CommandMapper()

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
            "center_freq",
            "ppm",
            "rf_gain",
            "lfo_offset",
        ]

    def getCommandMapper(self):
        return self.commandMapper

    @abstractmethod
    def onPropertyChange(self, name, value):
        pass

    def wireEvents(self):
        self.rtlProps.wire(self.onPropertyChange)

    def getCommand(self):
        return [self.getCommandMapper().map(self.getCommandValues())]

    def activateProfile(self, profile_id=None):
        profiles = self.props["profiles"]
        if profile_id is None:
            profile_id = list(profiles.keys())[0]
        if profile_id not in profiles:
            logger.warning("invalid profile %s for sdr %s. ignoring", profile_id, self.id)
            return
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

    def getCommandValues(self):
        dict = self.rtlProps.collect(*self.getEventNames()).__dict__()
        if "lfo_offset" in dict and dict["lfo_offset"] is not None:
            dict["tuner_freq"] = dict["center_freq"] + dict["lfo_offset"]
        else:
            dict["tuner_freq"] = dict["center_freq"]
        return dict

    def start(self):
        with self.modificationLock:
            if self.monitor:
                return

            cmd = self.getCommand()
            cmd = [c for c in cmd if c is not None]

            # don't use shell mode for commands without piping
            if len(cmd) > 1:
                # multiple commands with pipes
                cmd = "|".join(cmd)
                self.process = subprocess.Popen(cmd, shell=True, preexec_fn=os.setpgrp)
            else:
                # single command
                cmd = cmd[0]
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

            try:
                self.postStart()
            except Exception:
                logger.exception("Exception during postStart()")
                self.failed = True

        self.setState(SdrSource.STATE_FAILED if self.failed else SdrSource.STATE_RUNNING)

    def postStart(self):
        pass

    def isAvailable(self):
        return self.monitor is not None

    def isFailed(self):
        return self.failed

    def stop(self):
        self.setState(SdrSource.STATE_STOPPING)

        with self.modificationLock:

            if self.process is not None:
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                except ProcessLookupError:
                    # been killed by something else, ignore
                    pass
            if self.monitor:
                self.monitor.join()

        self.setState(SdrSource.STATE_STOPPED)

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

    def getState(self):
        return self.state

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
