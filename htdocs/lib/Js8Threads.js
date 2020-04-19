Js8Thread = function(el){
    this.messages = [];
    this.el = el;
}

Js8Thread.prototype.getAverageFrequency = function(){
    var total = this.messages.map(function(message){
        return message.freq;
    }).reduce(function(t, f){
        return t + f;
    }, 0);
    return total / this.messages.length;
}

Js8Thread.prototype.pushMessage = function(message) {
    this.messages.push(message);
    this.render();
}

Js8Thread.prototype.render = function() {
    this.el.html(
        '<td>' + this.renderTimestamp(this.getLatestTimestamp()) + '</td>' +
        '<td class="decimal freq">' + Math.round(this.getAverageFrequency()) + '</td>' +
        '<td class="message">' + this.renderMessages() + '</td>'
    );
}

Js8Thread.prototype.getLatestTimestamp() {
    return this.messages(this.messages.length - 1).timestamp;
}

Js8Thread.prototype.renderMessages = function() {
    res = []
    for (var i = 0; i < this.messages.length; i++) {
        var msg = this.messages[i];
        if (msg.thread_type & 1) {
            res.push('[ ');
        } else if (i > 0 && msg.timestamp - this.messages[i - 1].timestamp > 15000) {
            res.push(' ... ');
        }
        res.push(msg.msg);
        if (msg.thread_type & 2) {
            res.push(' ]');
        }
    }
    return res.join('');
}

Js8Thread.prototype.renderTimestamp = function(timestamp) {
    var t = new Date(timestamp);
    var pad = function (i) {
        return ('' + i).padStart(2, "0");
    };
    return pad(t.getUTCHours()) + pad(t.getUTCMinutes()) + pad(t.getUTCSeconds());
}

Js8Threader = function(el){
    this.threads = [];
    this.tbody = $(el).find('tbody');
    console.info(this.tbody);
};

Js8Threader.prototype.findThread = function(freq) {
    var matching = this.threads.filter(function(thread) {
        return Math.abs(thread.getAverageFrequency() - freq) <= 5;
    });
    return matching[0] || false;
}

Js8Threader.prototype.pushMessage = function(message) {
    var thread = this.findThread(message.freq);
    if (!thread) {
        var line = $("<tr></tr>")
        this.tbody.append(line);
        var thread = new Js8Thread(line);
        this.threads.push(thread);
    }
    thread.pushMessage(message);
}

$.fn.js8 = function() {
    if (!this.data('threader')) {
        this.data('threader', new Js8Threader(this));
    }
    return this.data('threader');
}