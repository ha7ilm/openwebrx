class OwrxAudioProcessor extends AudioWorkletProcessor {
    constructor(options){
        super(options);
        this.maxLength = options.processorOptions.maxLength;
        this.reduceToLength = options.processorOptions.reduceToLength;
        this.audio_buffers = [];
        this.port.addEventListener('message', (m) => {
            if (typeof(m.data) === 'string') {
                const json = JSON.parse(m.data);
                if (json.cmd && json.cmd == 'getBuffers') {
                    this.reportBuffers();
                }
            } else {
                this.audio_buffers.push(new Float32Array(m.data));
            }
        });
        this.port.addEventListener('messageerror', console.error);
        this.port.start();
    }
    process(inputs, outputs, parameters) {
        //console.time('audio::process');
        outputs[0].forEach((output) => {
            let total = 0;
            while (this.audio_buffers.length) {
                const b = this.audio_buffers.shift();
                const newLength = total + b.length;
                const ol = output.length;
                // not enough space to fit all data, so splice and put back in the queue
                if (newLength > ol) {
                    const tokeep = b.slice(0, ol - total);
                    output.set(tokeep, total);
                    const tobuffer = b.slice(ol - total, b.length);
                    this.audio_buffers.unshift(tobuffer);
                    break;
                } else {
                    output.set(b, total);
                }
                total = newLength;
            }
        });
        //console.timeEnd('audio::process');
        return true;
    }
    bufferLength() {
        return this.audio_buffers.map(function(b){ return b.length; }).reduce(function(a, b){ return a + b; }, 0);
    }
    reportBuffers() {
        var we_have_more_than = (sec) => {
            return sec * sampleRate < this.bufferLength();
        };
        if (we_have_more_than(this.maxLength)) while (we_have_more_than(this.reduceToLength)) {
            this.audio_buffers.shift();
        }

        this.port.postMessage(JSON.stringify({buffersize: this.bufferLength()}));
    }
}

registerProcessor('openwebrx-audio-processor', OwrxAudioProcessor);