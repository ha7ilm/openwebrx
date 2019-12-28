ProgressBar = function(el) {
    this.$el = $(el);
    this.$innerText = this.$el.find('.openwebrx-progressbar-text');
    this.$innerBar = this.$el.find('.openwebrx-progressbar-bar');
    this.$innerBar.css('width', '0%');
};

ProgressBar.prototype.set = function(val, text, over) {
    this.setValue(val);
    this.setText(text);
    this.setOver(over);
};

ProgressBar.prototype.setValue = function(val) {
    if (val < 0) val = 0;
    if (val > 1) val = 1;
    this.$innerBar.stop().animate({width: val * 100 + '%'}, 700);
};

ProgressBar.prototype.setText = function(text) {
    this.$innerText.html(text);
};

ProgressBar.prototype.setOver = function(over) {
    this.$innerBar.css('backgroundColor', (over) ? "#ff6262" : "#00aba6");
};

AudioBufferProgressBar = function(el, sampleRate) {
    ProgressBar.call(this, el);
    this.sampleRate = sampleRate;
};

AudioBufferProgressBar.prototype = new ProgressBar();

AudioBufferProgressBar.prototype.setBuffersize = function(buffersize) {
    var audio_buffer_value = buffersize / this.sampleRate;
    var overrun = audio_buffer_value > audio_buffer_maximal_length_sec;
    var underrun = audio_buffer_value === 0;
    var text = "buffer";
    if (overrun) {
        text = "overrun";
    }
    if (underrun) {
        text = "underrun";
    }
    this.set(audio_buffer_value, "Audio " + text + " [" + (audio_buffer_value).toFixed(1) + " s]", overrun || underrun);
};


NetworkSpeedProgressBar = function(el) {
    ProgressBar.call(this, el);
};

NetworkSpeedProgressBar.prototype = new ProgressBar();

NetworkSpeedProgressBar.prototype.setSpeed = function(speed) {
    var speedInKilobits = speed * 8 / 1000;
    this.set(speedInKilobits / 2000, "Network usage [" + speedInKilobits.toFixed(1) + " kbps]", false);
};

AudioSpeedProgressBar = function(el) {
    ProgressBar.call(this, el);
};

AudioSpeedProgressBar.prototype = new ProgressBar();

AudioSpeedProgressBar.prototype.setSpeed = function(speed) {
    this.set(speed / 500000, "Audio stream [" + (speed / 1000).toFixed(0) + " kbps]", false);
};

AudioOutputProgressBar = function(el, sampleRate) {
    ProgressBar.call(this, el);
    this.maxRate = sampleRate * 1.25;
    this.minRate = sampleRate * .25;
};

AudioOutputProgressBar.prototype = new ProgressBar();

AudioOutputProgressBar.prototype.setAudioRate = function(audioRate) {
    this.set(audioRate / this.maxRate, "Audio output [" + (audioRate / 1000).toFixed(1) + " ksps]", audioRate > this.maxRate || audioRate < this.minRate);
};

ClientsProgressBar = function(el) {
    ProgressBar.call(this, el);
    this.clients = 0;
    this.maxClients = 0;
};

ClientsProgressBar.prototype = new ProgressBar();

ClientsProgressBar.prototype.setClients = function(clients) {
    this.clients = clients;
    this.render();
};

ClientsProgressBar.prototype.setMaxClients = function(maxClients) {
    this.maxClients = maxClients;
    this.render();
};

ClientsProgressBar.prototype.render = function() {
    this.set(this.clients / this.maxClients, "Clients [" + this.clients + "]", this.clients > this.maxClients * 0.85);
};

CpuProgressBar = function(el) {
    ProgressBar.call(this, el);
};

CpuProgressBar.prototype = new ProgressBar();

CpuProgressBar.prototype.setUsage = function(usage) {
    this.set(usage, "Server CPU [" + Math.round(usage * 100) + "%]", usage > .85);
};
