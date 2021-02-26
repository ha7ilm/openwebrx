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
from owrx.property import PropertyStack, PropertyLayer, PropertyFilter
from owrx.property.filter import ByLambda
from owrx.form import Input, TextInput, NumberInput, CheckboxInput, ModesInput
from owrx.form.converter import OptionalConverter
from owrx.form.device import GainInput, SchedulerInput, WaterfallLevelsInput
from owrx.controllers.settings import Section
from typing import List
from enum import Enum, auto

import logging

logger = logging.getLogger(__name__)


class SdrSourceState(Enum):
    STOPPED = "Stopped"
    STARTING = "Starting"
    RUNNING = "Running"
    STOPPING = "Stopping"
    TUNING = "Tuning"
    FAILED = "Failed"
    DISABLED = "Disabled"

    def __str__(self):
        return self.value


class SdrBusyState(Enum):
    IDLE = auto()
    BUSY = auto()


class SdrClientClass(Enum):
    INACTIVE = auto()
    BACKGROUND = auto()
    USER = auto()


class SdrSourceEventClient(ABC):
    @abstractmethod
    def onStateChange(self, state: SdrSourceState):
        pass

    @abstractmethod
    def onBusyStateChange(self, state: SdrBusyState):
        pass

    def getClientClass(self) -> SdrClientClass:
        return SdrClientClass.INACTIVE


class SdrSource(ABC):
    def __init__(self, id, props):
        self.id = id

        self.commandMapper = None

        self.props = PropertyStack()
        # layer 0 reserved for profile properties

        # layer for runtime writeable properties
        # these may be set during runtime, but should not be persisted to disk with the configuration
        self.props.addLayer(1, PropertyLayer().filter("profile_id"))

        # props from our device config
        self.props.addLayer(2, props)

        # the sdr_id is constant, so we put it in a separate layer
        # this is used to detect device changes, that are then sent to the client
        self.props.addLayer(3, PropertyLayer(sdr_id=id).readonly())

        # finally, accept global config properties from the top-level config
        self.props.addLayer(4, Config.get())

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
        self.state = SdrSourceState.STOPPED if "enabled" not in props or props["enabled"] else SdrSourceState.DISABLED
        self.busyState = SdrBusyState.IDLE

        self.validateProfiles()

        if self.isAlwaysOn() and self.state is not SdrSourceState.DISABLED:
            self.start()

    def _loadProfile(self, profile):
        self.props.replaceLayer(0, PropertyFilter(profile, ByLambda(lambda x: x != "name")))

    def validateProfiles(self):
        props = PropertyStack()
        props.addLayer(1, self.props)
        for id, p in self.props["profiles"].items():
            props.replaceLayer(0, p)
            if "center_freq" not in props:
                logger.warning('Profile "%s" does not specify a center_freq', id)
                continue
            if "samp_rate" not in props:
                logger.warning('Profile "%s" does not specify a samp_rate', id)
                continue
            if "start_freq" in props:
                start_freq = props["start_freq"]
                srh = props["samp_rate"] / 2
                center_freq = props["center_freq"]
                if start_freq < center_freq - srh or start_freq > center_freq + srh:
                    logger.warning('start_freq for profile "%s" is out of range', id)

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

        self._loadProfile(profile)

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

            if self.getState() is SdrSourceState.FAILED:
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
            failed = False

            def wait_for_process_to_end():
                nonlocal failed
                rc = self.process.wait()
                logger.debug("shut down with RC={0}".format(rc))
                self.monitor = None
                if self.getState() is SdrSourceState.RUNNING:
                    failed = True
                    self.setState(SdrSourceState.FAILED)
                else:
                    self.setState(SdrSourceState.STOPPED)

            self.monitor = threading.Thread(target=wait_for_process_to_end, name="source_monitor")
            self.monitor.start()

            retries = 1000
            while retries > 0 and not failed:
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
                failed = True

            try:
                self.postStart()
            except Exception:
                logger.exception("Exception during postStart()")
                failed = True

        self.setState(SdrSourceState.FAILED if failed else SdrSourceState.RUNNING)

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

    def stop(self):
        # don't overwrite failed flag
        # TODO introduce a better solution?
        if self.getState() is not SdrSourceState.FAILED:
            self.setState(SdrSourceState.STOPPING)

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
        if c in self.clients:
            return
        self.clients.append(c)
        c.onStateChange(self.getState())
        hasUsers = self.hasClients(SdrClientClass.USER)
        hasBackgroundTasks = self.hasClients(SdrClientClass.BACKGROUND)
        if hasUsers or hasBackgroundTasks:
            self.start()
            self.setBusyState(SdrBusyState.BUSY if hasUsers else SdrBusyState.IDLE)

    def removeClient(self, c: SdrSourceEventClient):
        if c not in self.clients:
            return

        self.clients.remove(c)

        self.checkStatus()

    def checkStatus(self):
        hasUsers = self.hasClients(SdrClientClass.USER)
        self.setBusyState(SdrBusyState.BUSY if hasUsers else SdrBusyState.IDLE)

        # no need to check for users if we are always-on
        if self.isAlwaysOn():
            return

        hasBackgroundTasks = self.hasClients(SdrClientClass.BACKGROUND)
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

    def getState(self) -> SdrSourceState:
        return self.state

    def setState(self, state: SdrSourceState):
        if state == self.state:
            return
        self.state = state
        for c in self.clients:
            c.onStateChange(state)

    def setBusyState(self, state: SdrBusyState):
        if state == self.busyState:
            return
        self.busyState = state
        for c in self.clients:
            c.onBusyStateChange(state)


class SdrDeviceDescriptionMissing(Exception):
    pass


class OptionalSection(Section):
    def __init__(self, title, inputs: List[Input], mandatory, optional):
        super().__init__(title, *inputs)
        self.mandatory = mandatory
        self.optional = optional
        self.optional_inputs = []

    def classes(self):
        classes = super().classes()
        classes.append("optional-section")
        return classes

    def _is_optional(self, input):
        return input.id in self.optional

    def render_optional_select(self):
        return """
            <hr class="row" />
            <div class="form-group row">
                <label class="col-form-label col-form-label-sm col-3">
                    Additional optional settings
                </label>
                <div class="input-group input-group-sm col-9 p-0">
                    <select class="form-control from-control-sm optional-select">
                        {options}
                    </select>
                    <div class="input-group-append">
                        <button class="btn btn-success option-add-button">Add</button>
                    </div>
                </div>
            </div>
        """.format(
            options="".join(
                """
                    <option value="{value}">{name}</option>
                """.format(
                    value=input.id,
                    name=input.getLabel(),
                )
                for input in self.optional_inputs
            )
        )

    def render_optional_inputs(self, data):
        return """
            <div class="optional-inputs" style="display: none;">
                {inputs}
            </div>
        """.format(
            inputs="".join(self.render_input(input, data) for input in self.optional_inputs)
        )

    def render_inputs(self, data):
        return super().render_inputs(data) + self.render_optional_select() + self.render_optional_inputs(data)

    def render(self, data):
        indexed_inputs = {input.id: input for input in self.inputs}
        visible_keys = set(self.mandatory + [k for k in self.optional if k in data])
        optional_keys = set(k for k in self.optional if k not in data)
        self.inputs = [input for k, input in indexed_inputs.items() if k in visible_keys]
        for input in self.inputs:
            if self._is_optional(input):
                input.setRemovable()
        self.optional_inputs = [input for k, input in indexed_inputs.items() if k in optional_keys]
        for input in self.optional_inputs:
            input.setRemovable()
            input.setDisabled()
        return super().render(data)

    def parse(self, data):
        data = super().parse(data)
        # remove optional keys if they have been removed from the form
        for k in self.optional:
            if k not in data:
                data[k] = None
        return data


class SdrDeviceDescription(object):
    @staticmethod
    def getByType(sdr_type: str) -> "SdrDeviceDescription":
        try:
            className = "".join(x for x in sdr_type.title() if x.isalnum()) + "DeviceDescription"
            module = __import__("owrx.source.{0}".format(sdr_type), fromlist=[className])
            cls = getattr(module, className)
            return cls()
        except (ModuleNotFoundError, AttributeError):
            raise SdrDeviceDescriptionMissing("Device description for type {} not available".format(sdr_type))

    def getInputs(self) -> List[Input]:
        return [
            TextInput("name", "Device name"),
            CheckboxInput("enabled", "Enable this device", converter=OptionalConverter(defaultFormValue=True)),
            GainInput("rf_gain", "Device gain", self.hasAgc()),
            NumberInput(
                "ppm",
                "Frequency correction",
                append="ppm",
            ),
            CheckboxInput(
                "always-on",
                "Keep device running at all times",
                infotext="Prevents shutdown of the device when idle. Useful for devices with unreliable startup.",
            ),
            CheckboxInput(
                "services",
                "Run background services on this device",
            ),
            NumberInput(
                "lfo_offset",
                "Oscilator offset",
                append="Hz",
                infotext="Use this when the actual receiving frequency differs from the frequency to be tuned on the"
                + " device. <br/> Formula: Center frequency + oscillator offset = sdr tune frequency",
            ),
            WaterfallLevelsInput("waterfall_levels", "Waterfall levels"),
            SchedulerInput("scheduler", "Scheduler"),
            NumberInput("center_freq", "Center frequency", append="Hz"),
            NumberInput("samp_rate", "Sample rate", append="S/s"),
            NumberInput("start_freq", "Initial frequency", append="Hz"),
            ModesInput("start_mod", "Initial modulation"),
            NumberInput("initial_squelch_level", "Initial squelch level", append="dBFS"),
        ]

    def hasAgc(self):
        # default is True since most devices have agc. override in subclasses if agc is not available
        return True

    def getMandatoryKeys(self):
        return ["name", "enabled"]

    def getOptionalKeys(self):
        return [
            "ppm",
            "always-on",
            "services",
            "rf_gain",
            "lfo_offset",
            "waterfall_levels",
            "scheduler",
        ]

    def getProfileMandatoryKeys(self):
        return ["center_freq", "samp_rate", "start_freq", "start_mod"]

    def getProfileOptionalKeys(self):
        return ["initial_squelch_level", "rf_gain", "lfo_offset", "waterfall_levels"]

    def getDeviceSection(self):
        return OptionalSection("Device settings", self.getInputs(), self.getMandatoryKeys(), self.getOptionalKeys())

    def getProfileSection(self):
        return OptionalSection(
            "Profile settings",
            self.getInputs(),
            self.getProfileMandatoryKeys(),
            self.getProfileOptionalKeys(),
        )
