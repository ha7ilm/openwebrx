from owrx.config import Config
import threading
import subprocess
import os
import socket
import shlex
import time
import signal
from abc import ABC, abstractmethod
from owrx.command import CommandMapper
from owrx.socket import getAvailablePort
from owrx.property import PropertyStack, PropertyLayer

import logging

logger = logging.getLogger(__name__)


class SdrSourceEventClient(ABC):
    @abstractmethod
    def onStateChange(self, state):
        pass

    @abstractmethod
    def onBusyStateChange(self, state):
        pass

    def getClientClass(self):
        return SdrSource.CLIENT_INACTIVE


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

    def __init__(self, id, props):
        self.id = id

        self.commandMapper = None

        self.props = PropertyStack()
        # layer 0 reserved for profile properties
        self.props.addLayer(1, props)
        self.props.addLayer(2, Config.get())
        self.sdrProps = self.props.filter(*self.getEventNames())

        self.profile_id = None
        self.activateProfile()
        self.wireEvents()

        self.port = getAvailablePort()
        self.monitor = None
        self.clients = []
        self.spectrumClients = []
        self.spectrumThread = None
        self.spectrumLock = threading.Lock()
        self.process = None
        self.modificationLock = threading.Lock()
        self.failed = False
        self.state = SdrSource.STATE_STOPPED
        self.busyState = SdrSource.BUSYSTATE_IDLE

        self.validateProfiles()

        if self.isAlwaysOn():
            self.start()

    def validateProfiles(self):
        props = PropertyStack()
        props.addLayer(1, self.props)
        for id, p in self.props["profiles"].items():
            props.replaceLayer(0, self._getProfilePropertyLayer(p))
            if "center_freq" not in props:
                logger.warning("Profile \"%s\" does not specify a center_freq", id)
                continue
            if "samp_rate" not in props:
                logger.warning("Profile \"%s\" does not specify a samp_rate", id)
                continue
            if "start_freq" in props:
                start_freq = props["start_freq"]
                srh = props["samp_rate"] / 2
                center_freq = props["center_freq"]
                if start_freq < center_freq - srh or start_freq > center_freq + srh:
                    logger.warning("start_freq for profile \"%s\" is out of range", id)

    def _getProfilePropertyLayer(self, profile):
        layer = PropertyLayer()
        for (key, value) in profile.items():
            # skip the name, that would overwrite the source name.
            if key == "name":
                continue
            layer[key] = value
        return layer

    def isAlwaysOn(self):
        return "always-on" in self.props and self.props["always-on"]

    def getEventNames(self):
        return [
            "samp_rate",
            "center_freq",
            "ppm",
            "rf_gain",
            "lfo_offset",
        ] + list(self.getCommandMapper().keys())

    def getCommandMapper(self):
        if self.commandMapper is None:
            self.commandMapper = CommandMapper()
        return self.commandMapper

    @abstractmethod
    def onPropertyChange(self, changes):
        pass

    def wireEvents(self):
        self.sdrProps.wire(self.onPropertyChange)

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
        self.props["profile_id"] = profile_id
        profile = profiles[profile_id]
        self.profile_id = profile_id

        layer = self._getProfilePropertyLayer(profile)
        self.props.replaceLayer(0, layer)

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
        dict = self.sdrProps.__dict__()
        if "lfo_offset" in dict and dict["lfo_offset"] is not None:
            dict["tuner_freq"] = dict["center_freq"] + dict["lfo_offset"]
        else:
            dict["tuner_freq"] = dict["center_freq"]
        return dict

    def start(self):
        with self.modificationLock:
            if self.monitor:
                return

            if self.isFailed():
                return

            try:
                self.preStart()
            except Exception:
                logger.exception("Exception during preStart()")

            cmd = self.getCommand()
            cmd = [c for c in cmd if c is not None]

            # don't use shell mode for commands without piping
            if len(cmd) > 1:
                # multiple commands with pipes
                cmd = "|".join(cmd)
                self.process = subprocess.Popen(cmd, shell=True, start_new_session=True)
            else:
                # single command
                cmd = cmd[0]
                # start_new_session can go as soon as there's no piped commands left
                # the os.killpg call must be replaced with something more reasonable at the same time
                self.process = subprocess.Popen(shlex.split(cmd), start_new_session=True)
            logger.info("Started sdr source: " + cmd)

            available = False

            def wait_for_process_to_end():
                rc = self.process.wait()
                logger.debug("shut down with RC={0}".format(rc))
                self.monitor = None
                if self.getState() == SdrSource.STATE_RUNNING:
                    self.failed = True
                    self.setState(SdrSource.STATE_FAILED)
                else:
                    self.setState(SdrSource.STATE_STOPPED)

            self.monitor = threading.Thread(target=wait_for_process_to_end, name="source_monitor")
            self.monitor.start()

            retries = 1000
            while retries > 0 and not self.isFailed():
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

    def preStart(self):
        """
        override this method in subclasses if there's anything to be done before starting up the actual SDR
        """
        pass

    def postStart(self):
        """
        override this method in subclasses if there's things to do after the actual SDR has started up
        """
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

    def hasClients(self, *args):
        clients = [c for c in self.clients if c.getClientClass() in args]
        return len(clients) > 0

    def addClient(self, c: SdrSourceEventClient):
        self.clients.append(c)
        c.onStateChange(self.getState())
        hasUsers = self.hasClients(SdrSource.CLIENT_USER)
        hasBackgroundTasks = self.hasClients(SdrSource.CLIENT_BACKGROUND)
        if hasUsers or hasBackgroundTasks:
            self.start()
            self.setBusyState(SdrSource.BUSYSTATE_BUSY if hasUsers else SdrSource.BUSYSTATE_IDLE)

    def removeClient(self, c: SdrSourceEventClient):
        try:
            self.clients.remove(c)
        except ValueError:
            pass

        hasUsers = self.hasClients(SdrSource.CLIENT_USER)
        self.setBusyState(SdrSource.BUSYSTATE_BUSY if hasUsers else SdrSource.BUSYSTATE_IDLE)

        # no need to check for users if we are always-on
        if self.isAlwaysOn():
            return

        hasBackgroundTasks = self.hasClients(SdrSource.CLIENT_BACKGROUND)
        if not hasUsers and not hasBackgroundTasks:
            self.stop()

    def addSpectrumClient(self, c):
        if c in self.spectrumClients:
            return

        # local import due to circular depencency
        from owrx.fft import SpectrumThread

        self.spectrumClients.append(c)
        with self.spectrumLock:
            if self.spectrumThread is None:
                self.spectrumThread = SpectrumThread(self)
                self.spectrumThread.start()

    def removeSpectrumClient(self, c):
        try:
            self.spectrumClients.remove(c)
        except ValueError:
            pass
        with self.spectrumLock:
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
