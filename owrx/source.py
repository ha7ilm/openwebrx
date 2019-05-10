import subprocess
from owrx.config import PropertyManager, FeatureDetector, UnknownFeatureException
import threading
import csdr
import time
import os
import signal
import sys
import socket
import logging

logger = logging.getLogger(__name__)

class SdrService(object):
    sdrProps = None
    sources = {}
    lastPort = None
    @staticmethod
    def getNextPort():
        pm = PropertyManager.getSharedInstance()
        (start, end) = pm["iq_port_range"]
        if SdrService.lastPort is None:
            SdrService.lastPort = start
        else:
            SdrService.lastPort += 1
            if SdrService.lastPort > end:
                raise IndexError("no more available ports to start more sdrs")
        return SdrService.lastPort
    @staticmethod
    def loadProps():
        if SdrService.sdrProps is None:
            pm = PropertyManager.getSharedInstance()
            featureDetector = FeatureDetector()
            def loadIntoPropertyManager(dict: dict):
                propertyManager = PropertyManager()
                for (name, value) in dict.items():
                    propertyManager[name] = value
                return propertyManager
            def sdrTypeAvailable(value):
                try:
                    if not featureDetector.is_available(value["type"]):
                        logger.error("The RTL source type \"{0}\" is not available. please check requirements.".format(value["type"]))
                        return False
                    return True
                except UnknownFeatureException:
                    logger.error("The RTL source type \"{0}\" is invalid. Please check your configuration".format(value["type"]))
                    return False
            # transform all dictionary items into PropertyManager object, filtering out unavailable ones
            SdrService.sdrProps = {
                name: loadIntoPropertyManager(value) for (name, value) in pm["sdrs"].items() if sdrTypeAvailable(value)
            }
            logger.info("SDR sources loaded. Availables SDRs: {0}".format(", ".join(map(lambda x: x["name"], SdrService.sdrProps.values()))))
    @staticmethod
    def getSource(id = None):
        SdrService.loadProps()
        if id is None:
            # TODO: configure default sdr in config? right now it will pick the first one off the list.
            id = list(SdrService.sdrProps.keys())[0]
        sources = SdrService.getSources()
        return sources[id]
    @staticmethod
    def getSources():
        SdrService.loadProps()
        for id in SdrService.sdrProps.keys():
            if not id in SdrService.sources:
                props = SdrService.sdrProps[id]
                className = ''.join(x for x in props["type"].title() if x.isalnum()) + "Source"
                cls = getattr(sys.modules[__name__], className)
                SdrService.sources[id] = cls(props, SdrService.getNextPort())
        return SdrService.sources


class SdrSource(object):
    def __init__(self, props, port):
        self.props = props
        self.activateProfile()
        self.rtlProps = self.props.collect(
            "type", "samp_rate", "nmux_memory", "center_freq", "ppm", "rf_gain", "lna_gain", "rf_amp"
        ).defaults(PropertyManager.getSharedInstance())

        def restart(name, value):
            logger.debug("restarting sdr source due to property change: {0} changed to {1}".format(name, value))
            self.stop()
            self.start()
        self.rtlProps.wire(restart)
        self.port = port
        self.monitor = None
        self.clients = []
        self.spectrumClients = []
        self.spectrumThread = None
        self.process = None
        self.modificationLock = threading.Lock()

        # override these in subclasses as necessary
        self.command = None
        self.format_conversion = None

    def activateProfile(self, id = None):
        profiles = self.props["profiles"]
        if id is None:
            id = list(profiles.keys())[0]
        logger.debug("activating profile {0}".format(id))
        profile = profiles[id]
        for (key, value) in profile.items():
            # skip the name, that would overwrite the source name.
            if key == "name": continue
            self.props[key] = value

    def getProfiles(self):
        return self.props["profiles"]

    def getName(self):
        return self.props["name"]

    def getProps(self):
        return self.props

    def getPort(self):
        return self.port

    def start(self):
        self.modificationLock.acquire()
        if self.monitor:
            self.modificationLock.release()
            return

        props = self.rtlProps

        start_sdr_command = self.command.format(
            samp_rate = props["samp_rate"],
            center_freq = props["center_freq"],
            ppm = props["ppm"],
            rf_gain = props["rf_gain"],
            lna_gain = props["lna_gain"],
            rf_amp = props["rf_amp"]
        )

        if self.format_conversion is not None:
            start_sdr_command += " | " + self.format_conversion

        nmux_bufcnt = nmux_bufsize = 0
        while nmux_bufsize < props["samp_rate"]/4: nmux_bufsize += 4096
        while nmux_bufsize * nmux_bufcnt < props["nmux_memory"] * 1e6: nmux_bufcnt += 1
        if nmux_bufcnt == 0 or nmux_bufsize == 0:
            logger.error("Error: nmux_bufsize or nmux_bufcnt is zero. These depend on nmux_memory and samp_rate options in config_webrx.py")
            self.modificationLock.release()
            return
        logger.debug("nmux_bufsize = %d, nmux_bufcnt = %d" % (nmux_bufsize, nmux_bufcnt))
        cmd = start_sdr_command + " | nmux --bufsize %d --bufcnt %d --port %d --address 127.0.0.1" % (nmux_bufsize, nmux_bufcnt, self.port)
        self.process = subprocess.Popen(cmd, shell=True, preexec_fn=os.setpgrp)
        logger.info("Started rtl source: " + cmd)

        while True:
            testsock = socket.socket()
            try:
                testsock.connect(("127.0.0.1", self.getPort()))
                testsock.close()
                break
            except:
                time.sleep(0.1)


        def wait_for_process_to_end():
            rc = self.process.wait()
            logger.debug("shut down with RC={0}".format(rc))
            self.monitor = None

        self.monitor = threading.Thread(target = wait_for_process_to_end)
        self.monitor.start()

        self.spectrumThread = SpectrumThread(self)
        self.spectrumThread.start()

        self.modificationLock.release()

        for c in self.clients:
            c.onSdrAvailable()

    def isAvailable(self):
        return self.monitor is not None

    def stop(self):
        for c in self.clients:
            c.onSdrUnavailable()

        self.modificationLock.acquire()

        if self.spectrumThread is not None:
            self.spectrumThread.stop()

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

    def sleepOnRestart(self):
        pass

    def addClient(self, c):
        self.clients.append(c)
        self.start()
    def removeClient(self, c):
        try:
            self.clients.remove(c)
        except ValueError:
            pass
        if not self.clients:
            self.stop()

    def addSpectrumClient(self, c):
        self.spectrumClients.append(c)

    def removeSpectrumClient(self, c):
        try:
            self.spectrumClients.remove(c)
        except ValueError:
            pass

    def writeSpectrumData(self, data):
        for c in self.spectrumClients:
            c.write_spectrum_data(data)


class RtlSdrSource(SdrSource):
    def __init__(self, props, port):
        super().__init__(props, port)
        self.command = "rtl_sdr -s {samp_rate} -f {center_freq} -p {ppm} -g {rf_gain} -"
        self.format_conversion = "csdr convert_u8_f"

class HackrfSource(SdrSource):
    def __init__(self, props, port):
        super().__init__(props, port)
        self.command = "hackrf_transfer -s {samp_rate} -f {center_freq} -g {rf_gain} -l{lna_gain} -a{rf_amp} -r-"
        self.format_conversion =  "csdr convert_s8_f"

class SdrplaySource(SdrSource):
    def __init__(self, props, port):
        super().__init__(props, port)
        self.command = "rx_sdr -F CF32 -s {samp_rate} -f {center_freq} -p {ppm} -g {rf_gain} -"
        self.format_conversion = None

    def sleepOnRestart(self):
        time.sleep(1)

class SpectrumThread(threading.Thread):
    def __init__(self, sdrSource):
        self.doRun = True
        self.sdrSource = sdrSource
        super().__init__()

    def run(self):
        props = self.sdrSource.props.collect(
            "samp_rate", "fft_size", "fft_fps", "fft_voverlap_factor", "fft_compression",
            "csdr_dynamic_bufsize", "csdr_print_bufsizes", "csdr_through"
        ).defaults(PropertyManager.getSharedInstance())

        self.dsp = dsp = csdr.dsp()
        dsp.nc_port = self.sdrSource.getPort()
        dsp.set_demodulator("fft")
        props.getProperty("samp_rate").wire(dsp.set_samp_rate)
        props.getProperty("fft_size").wire(dsp.set_fft_size)
        props.getProperty("fft_fps").wire(dsp.set_fft_fps)
        props.getProperty("fft_compression").wire(dsp.set_fft_compression)

        def set_fft_averages(key, value):
            samp_rate = props["samp_rate"]
            fft_size = props["fft_size"]
            fft_fps = props["fft_fps"]
            fft_voverlap_factor = props["fft_voverlap_factor"]

            dsp.set_fft_averages(int(round(1.0 * samp_rate / fft_size / fft_fps / (1.0 - fft_voverlap_factor))) if fft_voverlap_factor>0 else 0)
        props.collect("samp_rate", "fft_size", "fft_fps", "fft_voverlap_factor").wire(set_fft_averages)
        set_fft_averages(None, None)

        dsp.csdr_dynamic_bufsize = props["csdr_dynamic_bufsize"]
        dsp.csdr_print_bufsizes = props["csdr_print_bufsizes"]
        dsp.csdr_through = props["csdr_through"]
        logger.debug("Spectrum thread initialized successfully.")
        dsp.start()
        if props["csdr_dynamic_bufsize"]:
            dsp.read(8) #dummy read to skip bufsize & preamble
            logger.debug("Note: CSDR_DYNAMIC_BUFSIZE_ON = 1")
        logger.debug("Spectrum thread started.")
        bytes_to_read=int(dsp.get_fft_bytes_to_read())
        while self.doRun:
            data=dsp.read(bytes_to_read)
            if len(data) == 0:
                time.sleep(1)
            else:
                self.sdrSource.writeSpectrumData(data)

        dsp.stop()
        logger.debug("spectrum thread shut down")

        self.thread = None
        self.sdrSource.removeClient(self)

    def stop(self):
        logger.debug("stopping spectrum thread")
        self.doRun = False

class DspManager(object):
    def __init__(self, handler, sdrSource):
        self.doRun = False
        self.handler = handler
        self.sdrSource = sdrSource
        self.dsp = None
        self.sdrSource.addClient(self)

        self.localProps = self.sdrSource.getProps().collect(
            "audio_compression", "fft_compression", "digimodes_fft_size", "csdr_dynamic_bufsize",
            "csdr_print_bufsizes", "csdr_through", "digimodes_enable", "samp_rate"
        ).defaults(PropertyManager.getSharedInstance())

        self.dsp = csdr.dsp()
        #dsp_initialized=False
        self.localProps.getProperty("audio_compression").wire(self.dsp.set_audio_compression)
        self.localProps.getProperty("fft_compression").wire(self.dsp.set_fft_compression)
        self.dsp.set_offset_freq(0)
        self.dsp.set_bpf(-4000,4000)
        self.localProps.getProperty("digimodes_fft_size").wire(self.dsp.set_secondary_fft_size)

        self.dsp.nc_port = self.sdrSource.getPort()
        self.dsp.csdr_dynamic_bufsize = self.localProps["csdr_dynamic_bufsize"]
        self.dsp.csdr_print_bufsizes = self.localProps["csdr_print_bufsizes"]
        self.dsp.csdr_through = self.localProps["csdr_through"]

        self.localProps.getProperty("samp_rate").wire(self.dsp.set_samp_rate)

        self.localProps.getProperty("output_rate").wire(self.dsp.set_output_rate)
        self.localProps.getProperty("offset_freq").wire(self.dsp.set_offset_freq)
        self.localProps.getProperty("squelch_level").wire(self.dsp.set_squelch_level)

        def set_low_cut(cut):
            bpf = self.dsp.get_bpf()
            bpf[0] = cut
            self.dsp.set_bpf(*bpf)
        self.localProps.getProperty("low_cut").wire(set_low_cut)

        def set_high_cut(cut):
            bpf = self.dsp.get_bpf()
            bpf[1] = cut
            self.dsp.set_bpf(*bpf)
        self.localProps.getProperty("high_cut").wire(set_high_cut)

        self.localProps.getProperty("mod").wire(self.dsp.set_demodulator)

        if (self.localProps["digimodes_enable"]):
            def set_secondary_mod(mod):
                if mod == False: mod = None
                if self.dsp.get_secondary_demodulator() == mod: return
                self.stopSecondaryThreads()
                self.dsp.stop()
                self.dsp.set_secondary_demodulator(mod)
                if mod is not None:
                    self.handler.write_secondary_dsp_config({
                        "secondary_fft_size":self.localProps["digimodes_fft_size"],
                        "if_samp_rate":self.dsp.if_samp_rate(),
                        "secondary_bw":self.dsp.secondary_bw()
                    })
                self.dsp.start()

                if mod:
                    self.startSecondaryThreads()

            self.localProps.getProperty("secondary_mod").wire(set_secondary_mod)

            self.localProps.getProperty("secondary_offset_freq").wire(self.dsp.set_secondary_offset_freq)

        super().__init__()

    def start(self):
        self.doRun = self.sdrSource.isAvailable()
        if self.doRun:
            self.dsp.start()
            threading.Thread(target = self.readDspOutput).start()
            threading.Thread(target = self.readSMeterOutput).start()

    def startSecondaryThreads(self):
        self.runSecondary = True
        self.secondaryDemodThread = threading.Thread(target = self.readSecondaryDemod)
        self.secondaryDemodThread.start()
        self.secondaryFftThread = threading.Thread(target = self.readSecondaryFft)
        self.secondaryFftThread.start()

    def stopSecondaryThreads(self):
        self.runSecondary = False
        self.secondaryDemodThread = None
        self.secondaryFftThread = None

    def readDspOutput(self):
        while (self.doRun):
            data = self.dsp.read(256)
            if len(data) != 256:
                time.sleep(1)
            else:
                self.handler.write_dsp_data(data)

    def readSMeterOutput(self):
        while (self.doRun):
            level = self.dsp.get_smeter_level()
            self.handler.write_s_meter_level(level)

    def readSecondaryDemod(self):
        while (self.runSecondary):
            data = self.dsp.read_secondary_demod(1)
            self.handler.write_secondary_demod(data)

    def readSecondaryFft(self):
        while (self.runSecondary):
            data = self.dsp.read_secondary_fft(int(self.dsp.get_secondary_fft_bytes_to_read()))
            self.handler.write_secondary_fft(data)

    def stop(self):
        self.doRun = False
        self.runSecondary = False
        self.dsp.stop()
        self.sdrSource.removeClient(self)

    def setProperty(self, prop, value):
        self.localProps.getProperty(prop).setValue(value)

    def onSdrAvailable(self):
        logger.debug("received onSdrAvailable, attempting DspSource restart")
        if not self.doRun:
            self.doRun = True
        if self.dsp is not None:
            self.dsp.start()
            threading.Thread(target = self.readDspOutput).start()
            threading.Thread(target = self.readSMeterOutput).start()

    def onSdrUnavailable(self):
        logger.debug("received onSdrUnavailable, shutting down DspSource")
        if self.dsp is not None:
            self.dsp.stop()

class CpuUsageThread(threading.Thread):
    sharedInstance = None
    @staticmethod
    def getSharedInstance():
        if CpuUsageThread.sharedInstance is None:
            CpuUsageThread.sharedInstance = CpuUsageThread()
            CpuUsageThread.sharedInstance.start()
        return CpuUsageThread.sharedInstance

    def __init__(self):
        self.clients = []
        self.doRun = True
        self.last_worktime = 0
        self.last_idletime = 0
        super().__init__()

    def run(self):
        while self.doRun:
            try:
                cpu_usage = self.get_cpu_usage()
            except:
                cpu_usage = 0
            for c in self.clients:
                c.write_cpu_usage(cpu_usage)
            time.sleep(3)
        logger.debug("cpu usage thread shut down")

    def get_cpu_usage(self):
        try:
            f = open("/proc/stat","r")
        except:
            return 0 #Workaround, possibly we're on a Mac
        line = ""
        while not "cpu " in line: line=f.readline()
        f.close()
        spl = line.split(" ")
        worktime = int(spl[2]) + int(spl[3]) + int(spl[4])
        idletime = int(spl[5])
        dworktime = (worktime - self.last_worktime)
        didletime = (idletime - self.last_idletime)
        rate = float(dworktime) / (didletime+dworktime)
        self.last_worktime = worktime
        self.last_idletime = idletime
        if (self.last_worktime==0): return 0
        return rate

    def add_client(self, c):
        self.clients.append(c)

    def remove_client(self, c):
        try:
            self.clients.remove(c)
        except ValueError:
            pass
        if not self.clients:
            self.shutdown()

    def shutdown(self):
        if self.doRun:
            if CpuUsageThread.sharedInstance == self:
                CpuUsageThread.sharedInstance = None
            self.doRun = False

class TooManyClientsException(Exception):
    pass

class ClientReporterThread(threading.Thread):
    sharedInstance = None
    @staticmethod
    def getSharedInstance():
        if ClientReporterThread.sharedInstance is None:
            ClientReporterThread.sharedInstance = ClientReporterThread()
            ClientReporterThread.sharedInstance.start()
        ClientReporterThread.sharedInstance.doRun = True
        return ClientReporterThread.sharedInstance

    def __init__(self):
        self.doRun = True
        self.clients = []
        super().__init__()

    def run(self):
        while (self.doRun):
            n = self.clientCount()
            for c in self.clients:
                c.write_clients(n)
            time.sleep(3)
        ClientReporterThread.sharedInstance = None

    def addClient(self, client):
        pm = PropertyManager.getSharedInstance()
        if len(self.clients) >= pm["max_clients"]:
            raise TooManyClientsException()
        self.clients.append(client)

    def clientCount(self):
        return len(self.clients)

    def removeClient(self, client):
        try:
            self.clients.remove(client)
        except ValueError:
            pass
        if not self.clients:
            self.doRun = False