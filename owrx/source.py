import subprocess
from owrx.config import PropertyManager
import threading
import csdr
import time

class RtlNmuxSource(object):
    def __init__(self):
        pm = PropertyManager.getSharedInstance()

        nmux_bufcnt = nmux_bufsize = 0
        while nmux_bufsize < pm.getPropertyValue("samp_rate")/4: nmux_bufsize += 4096
        while nmux_bufsize * nmux_bufcnt < pm.getPropertyValue("nmux_memory") * 1e6: nmux_bufcnt += 1
        if nmux_bufcnt == 0 or nmux_bufsize == 0:
            print("[openwebrx-main] Error: nmux_bufsize or nmux_bufcnt is zero. These depend on nmux_memory and samp_rate options in config_webrx.py")
            return
        print("[openwebrx-main] nmux_bufsize = %d, nmux_bufcnt = %d" % (nmux_bufsize, nmux_bufcnt))
        cmd = pm.getPropertyValue("start_rtl_command") + "| nmux --bufsize %d --bufcnt %d --port %d --address 127.0.0.1" % (nmux_bufsize, nmux_bufcnt, pm.getPropertyValue("iq_server_port"))
        subprocess.Popen(cmd, shell=True)
        print("[openwebrx-main] Started rtl source: " + cmd)

class SpectrumThread(threading.Thread):
    sharedInstance = None
    @staticmethod
    def getSharedInstance():
        if SpectrumThread.sharedInstance is None:
            SpectrumThread.sharedInstance = SpectrumThread()
            SpectrumThread.sharedInstance.start()
        return SpectrumThread.sharedInstance

    def __init__(self):
        self.clients = []
        self.doRun = True
        super().__init__()

    def run(self):
        pm = PropertyManager.getSharedInstance()

        samp_rate = pm.getPropertyValue("samp_rate")
        fft_size = pm.getPropertyValue("fft_size")
        fft_fps = pm.getPropertyValue("fft_fps")
        fft_voverlap_factor = pm.getPropertyValue("fft_voverlap_factor")
        fft_compression = pm.getPropertyValue("fft_compression")
        format_conversion = pm.getPropertyValue("format_conversion")

        spectrum_dsp=dsp=csdr.dsp()
        dsp.nc_port = pm.getPropertyValue("iq_server_port")
        dsp.set_demodulator("fft")
        dsp.set_samp_rate(samp_rate)
        dsp.set_fft_size(fft_size)
        dsp.set_fft_fps(fft_fps)
        dsp.set_fft_averages(int(round(1.0 * samp_rate / fft_size / fft_fps / (1.0 - fft_voverlap_factor))) if fft_voverlap_factor>0 else 0)
        dsp.set_fft_compression(fft_compression)
        dsp.set_format_conversion(format_conversion)
        dsp.csdr_dynamic_bufsize = pm.getPropertyValue("csdr_dynamic_bufsize")
        dsp.csdr_print_bufsizes = pm.getPropertyValue("csdr_print_bufsizes")
        dsp.csdr_through = pm.getPropertyValue("csdr_through")
        sleep_sec=0.87/fft_fps
        print("[openwebrx-spectrum] Spectrum thread initialized successfully.")
        dsp.start()
        if pm.getPropertyValue("csdr_dynamic_bufsize"):
            dsp.read(8) #dummy read to skip bufsize & preamble
            print("[openwebrx-spectrum] Note: CSDR_DYNAMIC_BUFSIZE_ON = 1")
        print("[openwebrx-spectrum] Spectrum thread started.")
        bytes_to_read=int(dsp.get_fft_bytes_to_read())
        spectrum_thread_counter=0
        while self.doRun:
            data=dsp.read(bytes_to_read)
            #print("gotcha",len(data),"bytes of spectrum data via spectrum_thread_function()")
            if spectrum_thread_counter >= fft_fps:
                spectrum_thread_counter=0
            else: spectrum_thread_counter+=1
            for c in self.clients:
                c.write_spectrum_data(data)
            '''
            correction=0
            for i in range(0,len(clients)):
                i-=correction
                if (clients[i].ws_started):
                    if clients[i].spectrum_queue.full():
                        print "[openwebrx-spectrum] client spectrum queue full, closing it."
                        close_client(i, False)
                        correction+=1
                    else:
                        clients[i].spectrum_queue.put([data]) # add new string by "reference" to all clients
            '''

        print("spectrum thread shut down")

    def add_client(self, c):
        self.clients.append(c)

    def remove_client(self, c):
        self.clients.remove(c)
        if not self.clients:
            self.shutdown()

    def shutdown(self):
        print("shutting down spectrum thread")
        SpectrumThread.sharedInstance = None
        self.doRun = False

class DspThread(threading.Thread):
    def __init__(self, handler):
        self.doRun = True
        self.handler = handler

        pm = PropertyManager.getSharedInstance()

        self.dsp = csdr.dsp()
        #dsp_initialized=False
        self.dsp.set_audio_compression(pm.getPropertyValue("audio_compression"))
        self.dsp.set_fft_compression(pm.getPropertyValue("fft_compression")) #used by secondary chains
        self.dsp.set_format_conversion(pm.getPropertyValue("format_conversion"))
        self.dsp.set_offset_freq(0)
        self.dsp.set_bpf(-4000,4000)
        self.dsp.set_secondary_fft_size(pm.getPropertyValue("digimodes_fft_size"))
        self.dsp.nc_port=pm.getPropertyValue("iq_server_port")
        self.dsp.csdr_dynamic_bufsize = pm.getPropertyValue("csdr_dynamic_bufsize")
        self.dsp.csdr_print_bufsizes = pm.getPropertyValue("csdr_print_bufsizes")
        self.dsp.csdr_through = pm.getPropertyValue("csdr_through")
        self.dsp.set_samp_rate(pm.getPropertyValue("samp_rate"))
        #do_secondary_demod=False
        super().__init__()

    def run(self):
        self.dsp.start()
        while (self.doRun):
            data = self.dsp.read(256)
            self.handler.write_dsp_data(data)

    def stop(self):
        self.doRun = False

    def set_output_rate(self, samp_rate):
        self.dsp.set_output_rate(samp_rate)

    def set_low_cut(self, cut):
        bpf = self.dsp.get_bpf()
        bpf[0] = cut
        self.dsp.set_bpf(*bpf)

    def set_high_cut(self, cut):
        bpf = self.dsp.get_bpf()
        bpf[1] = cut
        self.dsp.set_bpf(*bpf)

    def set_offset_freq(self, freq):
        self.dsp.set_offset_freq(freq)

    def set_mod(self, mod):
        if (self.dsp.get_demodulator() == mod): return
        self.dsp.stop()
        self.dsp.set_demodulator(mod)
        self.dsp.start()
