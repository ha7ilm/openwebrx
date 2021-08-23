from csdr.chain import Chain


class BaseDemodulatorChain(Chain):
    def getFixedIfSampleRate(self):
        return None

    def getFixedAudioRate(self):
        return None

    def supportsSquelch(self):
        return True
