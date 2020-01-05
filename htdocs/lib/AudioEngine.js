// this controls if the new AudioWorklet API should be used if available.
// the engine will still fall back to the ScriptProcessorNode if this is set to true but not available in the browser.
var useAudioWorklets = true;

function AudioEngine(maxBufferLength, audioReporter) {
    this.audioReporter = audioReporter;
    this.initStats();
    this.resetStats();
    var ctx = window.AudioContext || window.webkitAudioContext;
    if (!ctx) {
        return;
    }
    this.audioContext = new ctx();
    this.allowed = this.audioContext.state === 'running';
    this.started = false;

    this.audioCodec = new ImaAdpcmCodec();
    this.compression = 'none';

    this.setupResampling();
    this.resampler = new sdrjs.RationalResamplerFF(this.resamplingFactor, 1);

    this.maxBufferSize = maxBufferLength * this.getSampleRate();
}

AudioEngine.prototype.start = function(callback) {
    var me = this;
    if (me.resamplingFactor === 0) return; //if failed to find a valid resampling factor...
    if (me.started) {
        if (callback) callback(false);
        return;
    }

    me.audioContext.resume().then(function(){
        me.allowed = me.audioContext.state === 'running';
        if (!me.allowed) {
            if (callback) callback(false);
            return;
        }
        me.started = true;

        me.gainNode = me.audioContext.createGain();
        me.gainNode.connect(me.audioContext.destination);

        if (useAudioWorklets && me.audioContext.audioWorklet) {
            me.audioContext.audioWorklet.addModule('static/lib/AudioProcessor.js').then(function(){
                me.audioNode = new AudioWorkletNode(me.audioContext, 'openwebrx-audio-processor', {
                    numberOfInputs: 0,
                    numberOfOutputs: 1,
                    outputChannelCount: [1],
                    processorOptions: {
                        maxBufferSize: me.maxBufferSize
                    }
                });
                me.audioNode.connect(me.gainNode);
                me.audioNode.port.addEventListener('message', function(m){
                    var json = JSON.parse(m.data);
                    if (typeof(json.buffersize) !== 'undefined') {
                        me.audioReporter({
                            buffersize: json.buffersize
                        });
                    }
                    if (typeof(json.samplesProcessed) !== 'undefined') {
                        me.audioSamples.add(json.samplesProcessed);
                    }
                });
                me.audioNode.port.start();
                if (callback) callback(true, 'AudioWorklet');
            });
        } else {
            me.audioBuffers = [];

            if (!AudioBuffer.prototype.copyToChannel) { //Chrome 36 does not have it, Firefox does
                AudioBuffer.prototype.copyToChannel = function (input, channel) //input is Float32Array
                {
                    var cd = this.getChannelData(channel);
                    for (var i = 0; i < input.length; i++) cd[i] = input[i];
                }
            }

            var bufferSize;
            if (me.audioContext.sampleRate < 44100 * 2)
                bufferSize = 4096;
            else if (me.audioContext.sampleRate >= 44100 * 2 && me.audioContext.sampleRate < 44100 * 4)
                bufferSize = 4096 * 2;
            else if (me.audioContext.sampleRate > 44100 * 4)
                bufferSize = 4096 * 4;


            function audio_onprocess(e) {
                var total = 0;
                var out = new Float32Array(bufferSize);
                while (me.audioBuffers.length) {
                    var b = me.audioBuffers.shift();
                    // not enough space to fit all data, so splice and put back in the queue
                    if (total + b.length > bufferSize) {
                        var spaceLeft  = bufferSize - total;
                        var tokeep = b.subarray(0, spaceLeft);
                        out.set(tokeep, total);
                        var tobuffer = b.subarray(spaceLeft, b.length);
                        me.audioBuffers.unshift(tobuffer);
                        total += spaceLeft;
                        break;
                    } else {
                        out.set(b, total);
                        total += b.length;
                    }
                }

                e.outputBuffer.copyToChannel(out, 0);
                me.audioSamples.add(total);

            }

            //on Chrome v36, createJavaScriptNode has been replaced by createScriptProcessor
            var method = 'createScriptProcessor';
            if (me.audioContext.createJavaScriptNode) {
                method = 'createJavaScriptNode';
            }
            me.audioNode = me.audioContext[method](bufferSize, 0, 1);
            me.audioNode.onaudioprocess = audio_onprocess;
            me.audioNode.connect(me.gainNode);
            if (callback) callback(true, 'ScriptProcessorNode');
        }

        setInterval(me.reportStats.bind(me), 1000);
    });
};

AudioEngine.prototype.isAllowed = function() {
    return this.allowed;
};

AudioEngine.prototype.reportStats = function() {
    if (this.audioNode.port) {
        this.audioNode.port.postMessage(JSON.stringify({cmd:'getStats'}));
    } else {
        this.audioReporter({
            buffersize: this.getBuffersize()
        });
    }
};

AudioEngine.prototype.initStats = function() {
    var me = this;
    var buildReporter = function(key) {
        return function(v){
            var report = {};
            report[key] = v;
            me.audioReporter(report);
        }

    };

    this.audioBytes = new Measurement();
    this.audioBytes.report(10000, 1000, buildReporter('audioByteRate'));

    this.audioSamples = new Measurement();
    this.audioSamples.report(10000, 1000, buildReporter('audioRate'));
};

AudioEngine.prototype.resetStats = function() {
    this.audioBytes.reset();
    this.audioSamples.reset();
};

AudioEngine.prototype.setupResampling = function() { //both at the server and the client
    var output_range_max = 12000;
    var output_range_min = 8000;
    var targetRate = this.audioContext.sampleRate;
    var i = 1;
    while (true) {
        var audio_server_output_rate = Math.floor(targetRate / i);
        if (audio_server_output_rate < output_range_min) {
            this.resamplingFactor = 0;
            this.outputRate = 0;
            divlog('Your audio card sampling rate (' + targetRate + ') is not supported.<br />Please change your operating system default settings in order to fix this.', 1);
            break;
        } else if (audio_server_output_rate >= output_range_min && audio_server_output_rate <= output_range_max) {
            this.resamplingFactor = i;
            this.outputRate = audio_server_output_rate;
            break; //okay, we're done
        }
        i++;
    }
};

AudioEngine.prototype.getOutputRate = function() {
    return this.outputRate;
};

AudioEngine.prototype.getSampleRate = function() {
    return this.audioContext.sampleRate;
};

AudioEngine.prototype.pushAudio = function(data) {
    if (!this.audioNode) return;
    this.audioBytes.add(data.byteLength);
    var buffer;
    if (this.compression === "adpcm") {
        //resampling & ADPCM
        buffer = this.audioCodec.decode(new Uint8Array(data));
    } else {
        buffer = new Int16Array(data);
    }
    buffer = this.resampler.process(sdrjs.ConvertI16_F(buffer));
    if (this.audioNode.port) {
        // AudioWorklets supported
        this.audioNode.port.postMessage(buffer);
    } else {
        // silently drop excess samples
        if (this.getBuffersize() + buffer.length <= this.maxBufferSize) {
            this.audioBuffers.push(buffer);
        }
    }
};

AudioEngine.prototype.setCompression = function(compression) {
    this.compression = compression;
};

AudioEngine.prototype.setVolume = function(volume) {
    this.gainNode.gain.value = volume;
};

AudioEngine.prototype.getBuffersize = function() {
    // only available when using ScriptProcessorNode
    if (!this.audioBuffers) return 0;
    return this.audioBuffers.map(function(b){ return b.length; }).reduce(function(a, b){ return a + b; }, 0);
};

function ImaAdpcmCodec() {
    this.stepIndex = 0;
    this.predictor = 0;
    this.step = 0;
}

ImaAdpcmCodec.imaIndexTable = [ -1, -1, -1, -1, 2, 4, 6, 8, -1, -1, -1, -1, 2, 4, 6, 8 ];

ImaAdpcmCodec.imaStepTable = [
                               7, 8, 9, 10, 11, 12, 13, 14, 16, 17,
                               19, 21, 23, 25, 28, 31, 34, 37, 41, 45,
                               50, 55, 60, 66, 73, 80, 88, 97, 107, 118,
                               130, 143, 157, 173, 190, 209, 230, 253, 279, 307,
                               337, 371, 408, 449, 494, 544, 598, 658, 724, 796,
                               876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066,
                               2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428, 4871, 5358,
                               5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899,
                               15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767
                             ];

ImaAdpcmCodec.prototype.decode = function(data) {
    var output = new Int16Array(data.length * 2);
    for (var i = 0; i < data.length; i++) {
        output[i * 2] = this.decodeNibble(data[i] & 0x0F);
        output[i * 2 + 1] = this.decodeNibble((data[i] >> 4) & 0x0F);
    }
    return output;
};

ImaAdpcmCodec.prototype.decodeNibble = function(nibble) {
    this.stepIndex += ImaAdpcmCodec.imaIndexTable[nibble];
    this.stepIndex = Math.min(Math.max(this.stepIndex, 0), 88);

    var diff = this.step >> 3;
    if (nibble & 1) diff += this.step >> 2;
    if (nibble & 2) diff += this.step >> 1;
    if (nibble & 4) diff += this.step;
    if (nibble & 8) diff = -diff;

    this.predictor += diff;
    this.predictor = Math.min(Math.max(this.predictor, -32768), 32767);

    this.step = ImaAdpcmCodec.imaStepTable[this.stepIndex];

    return this.predictor;
};