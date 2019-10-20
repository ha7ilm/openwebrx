class OwrxAudioProcessor extends AudioWorkletProcessor {
    constructor(options){
        super(options);
        this.maxLength = options.processorOptions.maxLength;
        // initialize ringbuffer, make sure it aligns with the expected buffer size of 128
        this.bufferSize = Math.round(sampleRate * this.maxLength / 128) * 128
        this.audioBuffer = new Float32Array(this.bufferSize);
        this.inPos = 0;
        this.outPos = 0;
        this.port.addEventListener('message', (m) => {
            if (typeof(m.data) === 'string') {
                const json = JSON.parse(m.data);
                if (json.cmd && json.cmd == 'getBuffers') {
                    this.reportBuffers();
                }
            } else {
                // the ringbuffer size is aligned to the output buffer size, which means that the input buffers might
                // need to wrap around the end of the ringbuffer, back to the start.
                // it is better to have this processing here instead of in the time-critical process function.
                if (this.inPos + m.data.length <= this.bufferSize) {
                    // we have enough space, so just copy data over.
                    this.audioBuffer.set(m.data, this.inPos);
                } else {
                    // we don't have enough space, so we need to split the data.
                    const remaining = this.bufferSize - this.inPos;
                    this.audioBuffer.set(m.data.subarray(0, remaining), this.inPos);
                    this.audioBuffer.set(m.data.subarray(remaining));
                }
                this.inPos = (this.inPos + m.data.length) % this.bufferSize;
            }
        });
        this.port.addEventListener('messageerror', console.error);
        this.port.start();
    }
    process(inputs, outputs, parameters) {
        const samples = Math.min(128, this.remaining());
        outputs[0].forEach((output) => {
            output.set(this.audioBuffer.subarray(this.outPos, this.outPos + samples));
        });
        this.outPos = (this.outPos + samples) % this.bufferSize;
        return true;
    }
    remaining() {
        const mod = (this.inPos - this.outPos) % this.bufferSize;
        if (mod >= 0) return mod;
        return mod + this.bufferSize;
    }
    reportBuffers() {
        this.port.postMessage(JSON.stringify({buffersize: this.remaining()}));
    }
}

registerProcessor('openwebrx-audio-processor', OwrxAudioProcessor);