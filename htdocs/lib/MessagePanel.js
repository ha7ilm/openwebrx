function MessagePanel(el) {
    this.el = el;
    this.render();
    this.initClearButton();
}

MessagePanel.prototype.supportsMessage = function(message) {
    return false;
};

MessagePanel.prototype.render = function() {
};

MessagePanel.prototype.pushMessage = function(message) {
};

// automatic clearing is not enabled by default. call this method from the constructor to enable
MessagePanel.prototype.initClearTimer = function() {
    var me = this;
    if (me.removalInterval) clearInterval(me.removalInterval);
    me.removalInterval = setInterval(function () {
        me.clearMessages(1000);
    }, 15000);
};

MessagePanel.prototype.clearMessages = function(toRemain) {
    var $elements = $(this.el).find('tbody tr');
    // limit to 1000 entries in the list since browsers get laggy at some point
    var toRemove = $elements.length - toRemain;
    if (toRemove <= 0) return;
    $elements.slice(0, toRemove).remove();
};

MessagePanel.prototype.initClearButton = function() {
    var me = this;
    me.clearButton = $(
        '<div class="openwebrx-button">Clear</div>'
    );
    me.clearButton.css({
        position: 'absolute',
        top: '10px',
        right: '10px'
    });
    me.clearButton.on('click', function() {
        me.clearMessages(0);
    });
    $(me.el).append(me.clearButton);
};

MessagePanel.prototype.htmlEscape = function(input) {
    return $('<div/>').text(input).html()
};

MessagePanel.prototype.scrollToBottom = function() {
    var $t = $(this.el).find('table');
    $t.scrollTop($t[0].scrollHeight);
};

function WsjtMessagePanel(el) {
    MessagePanel.call(this, el);
    this.initClearTimer();
    this.qsoModes = ['FT8', 'JT65', 'JT9', 'FT4', 'FST4', 'Q65', 'MSK144'];
    this.beaconModes = ['WSPR', 'FST4W'];
    this.modes = [].concat(this.qsoModes, this.beaconModes);
}

WsjtMessagePanel.prototype = new MessagePanel();

WsjtMessagePanel.prototype.supportsMessage = function(message) {
    return this.modes.indexOf(message['mode']) >= 0;
};

WsjtMessagePanel.prototype.render = function() {
    $(this.el).append($(
        '<table>' +
            '<thead><tr>' +
                '<th>UTC</th>' +
                '<th class="decimal">dB</th>' +
                '<th class="decimal">DT</th>' +
                '<th class="decimal freq">Freq</th>' +
                '<th class="message">Message</th>' +
            '</tr></thead>' +
            '<tbody></tbody>' +
        '</table>'
    ));
};

WsjtMessagePanel.prototype.pushMessage = function(msg) {
    var $b = $(this.el).find('tbody');
    var t = new Date(msg['timestamp']);
    var pad = function (i) {
        return ('' + i).padStart(2, "0");
    };
    var linkedmsg = msg['msg'];
    var matches;

    if (this.qsoModes.indexOf(msg['mode']) >= 0) {
        matches = linkedmsg.match(/(.*\s[A-Z0-9]+\s)([A-R]{2}[0-9]{2})$/);
        if (matches && matches[2] !== 'RR73') {
            linkedmsg = this.htmlEscape(matches[1]) + '<a href="map?locator=' + matches[2] + '" target="openwebrx-map">' + matches[2] + '</a>';
        } else {
            linkedmsg = this.htmlEscape(linkedmsg);
        }
    } else if (this.beaconModes.indexOf(msg['mode']) >= 0) {
        matches = linkedmsg.match(/([A-Z0-9]*\s)([A-R]{2}[0-9]{2})(\s[0-9]+)/);
        if (matches) {
            linkedmsg = this.htmlEscape(matches[1]) + '<a href="map?locator=' + matches[2] + '" target="openwebrx-map">' + matches[2] + '</a>' + this.htmlEscape(matches[3]);
        } else {
            linkedmsg = this.htmlEscape(linkedmsg);
        }
    }
    $b.append($(
        '<tr data-timestamp="' + msg['timestamp'] + '">' +
        '<td>' + pad(t.getUTCHours()) + pad(t.getUTCMinutes()) + pad(t.getUTCSeconds()) + '</td>' +
        '<td class="decimal">' + msg['db'] + '</td>' +
        '<td class="decimal">' + msg['dt'] + '</td>' +
        '<td class="decimal freq">' + msg['freq'] + '</td>' +
        '<td class="message">' + linkedmsg + '</td>' +
        '</tr>'
    ));
    this.scrollToBottom();
}

$.fn.wsjtMessagePanel = function(){
    if (!this.data('panel')) {
        this.data('panel', new WsjtMessagePanel(this));
    }
    return this.data('panel');
};

function PacketMessagePanel(el) {
    MessagePanel.call(this, el);
    this.initClearTimer();
}

PacketMessagePanel.prototype = new MessagePanel();

PacketMessagePanel.prototype.supportsMessage = function(message) {
    return message['mode'] === 'APRS';
};

PacketMessagePanel.prototype.render = function() {
    $(this.el).append($(
        '<table>' +
            '<thead><tr>' +
                '<th>UTC</th>' +
                '<th class="callsign">Callsign</th>' +
                '<th class="coord">Coord</th>' +
                '<th class="message">Comment</th>' +
            '</tr></thead>' +
            '<tbody></tbody>' +
        '</table>'
    ));
};

PacketMessagePanel.prototype.pushMessage = function(msg) {
    var $b = $(this.el).find('tbody');
    var pad = function (i) {
        return ('' + i).padStart(2, "0");
    };

    if (msg.type && msg.type === 'thirdparty' && msg.data) {
        msg = msg.data;
    }

    var source = msg.source;
    var callsign;
    if ('object' in source) {
        callsign = source.object;
    } else if ('item' in source) {
        callsign = source.item;
    } else {
        callsign = source.callsign;
        if ('ssid' in source) {
            callsign += '-' + source.ssid;
        }
    }

    var timestamp = '';
    if (msg.timestamp) {
        var t = new Date(msg.timestamp);
        timestamp = pad(t.getUTCHours()) + pad(t.getUTCMinutes()) + pad(t.getUTCSeconds())
    }

    var link = '';
    var classes = [];
    var styles = {};
    var overlay = '';
    var stylesToString = function (s) {
        return $.map(s, function (value, key) {
            return key + ':' + value + ';'
        }).join('')
    };
    if (msg.symbol) {
        classes.push('aprs-symbol');
        classes.push('aprs-symboltable-' + (msg.symbol.table === '/' ? 'normal' : 'alternate'));
        styles['background-position-x'] = -(msg.symbol.index % 16) * 15 + 'px';
        styles['background-position-y'] = -Math.floor(msg.symbol.index / 16) * 15 + 'px';
        if (msg.symbol.table !== '/' && msg.symbol.table !== '\\') {
            var s = {};
            s['background-position-x'] = -(msg.symbol.tableindex % 16) * 15 + 'px';
            s['background-position-y'] = -Math.floor(msg.symbol.tableindex / 16) * 15 + 'px';
            overlay = '<div class="aprs-symbol aprs-symboltable-overlay" style="' + stylesToString(s) + '"></div>';
        }
    } else if (msg.lat && msg.lon) {
        classes.push('openwebrx-maps-pin');
        overlay = '<svg viewBox="0 0 20 35"><use xlink:href="static/gfx/svg-defs.svg#maps-pin"></use></svg>';
    }
    var attrs = [
        'class="' + classes.join(' ') + '"',
        'style="' + stylesToString(styles) + '"'
    ].join(' ');
    if (msg.lat && msg.lon) {
        link = '<a ' + attrs + ' href="map?' + new URLSearchParams(source).toString() + '" target="openwebrx-map">' + overlay + '</a>';
    } else {
        link = '<div ' + attrs + '>' + overlay + '</div>'
    }

    $b.append($(
        '<tr>' +
        '<td>' + timestamp + '</td>' +
        '<td class="callsign">' + callsign + '</td>' +
        '<td class="coord">' + link + '</td>' +
        '<td class="message">' + this.htmlEscape(msg.comment || msg.message || '') + '</td>' +
        '</tr>'
    ));
    this.scrollToBottom();
};

$.fn.packetMessagePanel = function() {
    if (!this.data('panel')) {
        this.data('panel', new PacketMessagePanel(this));
    }
    return this.data('panel');
};

PocsagMessagePanel = function(el) {
    MessagePanel.call(this, el);
    this.initClearTimer();
}

PocsagMessagePanel.prototype = new MessagePanel();

PocsagMessagePanel.prototype.supportsMessage = function(message) {
    return message['mode'] === 'Pocsag';
};

PocsagMessagePanel.prototype.render = function() {
    $(this.el).append($(
        '<table>' +
            '<thead><tr>' +
                '<th class="address">Address</th>' +
                '<th class="message">Message</th>' +
            '</tr></thead>' +
            '<tbody></tbody>' +
        '</table>'
    ));
};

PocsagMessagePanel.prototype.pushMessage = function(msg) {
    var $b = $(this.el).find('tbody');
    $b.append($(
        '<tr>' +
            '<td class="address">' + msg.address + '</td>' +
            '<td class="message">' + this.htmlEscape(msg.message) + '</td>' +
        '</tr>'
    ));
    this.scrollToBottom();
};

$.fn.pocsagMessagePanel = function() {
    if (!this.data('panel')) {
        this.data('panel', new PocsagMessagePanel(this));
    }
    return this.data('panel');
};

AdsbMessagePanel = function(el) {
    MessagePanel.call(this, el);
    this.aircraft = {}
    this.aircraftTrackingService = false;
    this.initClearTimer();
}

AdsbMessagePanel.prototype = new MessagePanel();

AdsbMessagePanel.prototype.supportsMessage = function(message) {
    return message["mode"] === "ADSB";
};

AdsbMessagePanel.prototype.render = function() {
    $(this.el).append($(
        '<table>' +
            '<thead><tr>' +
                '<th class="address">ICAO</th>' +
                '<th class="callsign">Flight</th>' +
                '<th class="altitude">Altitude</th>' +
                '<th class="speed">Speed</th>' +
                '<th class="track">Track</th>' +
                '<th class="verticalspeed">V/S</th>' +
                '<th class="position">Position</th>' +
                '<th class="messages">Messages</th>' +
            '</tr></thead>' +
            '<tbody></tbody>' +
        '</table>'
    ));
};


AdsbMessagePanel.prototype.pushMessage = function(message) {
    if (!('icao' in message)) return;
    if (!(message.icao in this.aircraft)) {
        var el = $("<tr>");
        $(this.el).find('tbody').append(el);
        this.aircraft[message.icao] = {
            el: el,
            messages: 0
        }
    }
    var state = this.aircraft[message.icao];
    Object.assign(state, message);
    state.lastSeen = Date.now();
    state.messages += 1;

    var ifDefined = function(input, formatter) {
        if (typeof(input) !== 'undefined') {
            if (formatter) return formatter(input);
            return input;
        }
        return "";
    }

    var coordRound = function(i) {
        return Math.round(i * 1000) / 1000;
    }

    var getPosition = function(state) {
        if (!('lat' in state) || !('lon') in state) return '';
        return '<a href="map?icao=' + state.icao + '" target="openwebrx-map">' + coordRound(state.lat) + ', ' + coordRound(state.lon) + '</a>';
    }

    state.el.html(
        '<td>' + this.linkify(state, state.icao) + '</td>' +
        '<td>' + this.linkify(state, ifDefined(state.identification)) + '</td>' +
        '<td>' + ifDefined(state.altitude) + '</td>' +
        '<td>' + ifDefined(state.groundspeed || state.IAS || state.TAS, Math.round) + '</td>' +
        '<td>' + ifDefined(state.groundtrack || state.heading, Math.round) + '</td>' +
        '<td>' + ifDefined(state.verticalspeed) + '</td>' +
        '<td>' + getPosition(state) + '</td>' +
        '<td>' + state.messages + '</td>'
    );
};

AdsbMessagePanel.prototype.clearMessages = function(toRemain) {
    var now = Date.now();
    var me = this;
    Object.entries(this.aircraft).forEach(function(e) {
        if (now - e[1].lastSeen > toRemain) {
            delete me.aircraft[e[0]];
            e[1].el.remove();
        }
    })
};

AdsbMessagePanel.prototype.initClearTimer = function() {
    var me = this;
    if (me.removalInterval) clearInterval(me.removalInterval);
    me.removalInterval = setInterval(function () {
        me.clearMessages(30000);
    }, 15000);
};

AdsbMessagePanel.prototype.setAircraftTrackingService = function(service) {
    this.aircraftTrackingService = service;
};

AdsbMessagePanel.prototype.linkify = function(state, text) {
    var link = false;
    switch (this.aircraftTrackingService) {
        case 'flightaware':
            link = 'https://flightaware.com/live/modes/' + state.icao;
            if (state.identification) link += "/ident/" + state.identification
            link += '/redirect';
            break;
        case 'planefinder':
            if (state.identification) link = 'https://planefinder.net/flight/' + state.identification;
            break;
    }
    if (link) {
        return '<a target="_blank" href="' + link + '">' + text + '</a>';
    }
    return text;

};

$.fn.adsbMessagePanel = function () {
    if (!this.data('panel')) {
        this.data('panel', new AdsbMessagePanel(this));
    }
    return this.data('panel');
};

IsmMessagePanel = function(el) {
    MessagePanel.call(this, el);
    this.initClearTimer();
};

IsmMessagePanel.prototype = new MessagePanel();

IsmMessagePanel.prototype.supportsMessage = function(message) {
    return message['mode'] === 'ISM';
};

IsmMessagePanel.prototype.render = function() {
    $(this.el).append($(
        '<table>' +
            '<thead><tr>' +
                '<th class="model">Model</th>' +
                '<th class="id">ID</th>' +
                '<th class="channel">Channel</th>' +
                '<th class="data">Data</th>' +
            '</tr></thead>' +
            '<tbody></tbody>' +
        '</table>'
    ));

};

IsmMessagePanel.prototype.pushMessage = function(message) {
    var $b = $(this.el).find('tbody');

    var ifDefined = function(input, formatter) {
        if (typeof(input) !== 'undefined') {
            if (formatter) return formatter(input);
            return input;
        }
        return "";
    }

    var mergeRemainingMessage = function(input, exclude) {
        return Object.entries(input).map(function(entry) {
            if (exclude.includes(entry[0])) return '';
            return entry[0] + ': ' + entry[1] + ';';
        }).join(' ');
    }

    $b.append($(
        '<tr>' +
            '<td class="model">' + ifDefined(message.model) + '</td>' +
            '<td class="id">' + ifDefined(message.id) + '</td>' +
            '<td class="channel">' + ifDefined(message.channel) + '</td>' +
            '<td class="data">' + this.htmlEscape(mergeRemainingMessage(message, ['model', 'id', 'channel', 'mode', 'time'])) + '</td>' +
        '</tr>'
    ));
    this.scrollToBottom();
};

$.fn.ismMessagePanel = function() {
    if (!this.data('panel')) {
        this.data('panel', new IsmMessagePanel(this));
    }
    return this.data('panel');
};

HfdlMessagePanel = function(el) {
    MessagePanel.call(this, el);
    this.initClearTimer();
}

HfdlMessagePanel.prototype = new MessagePanel();

HfdlMessagePanel.prototype.render = function() {
    $(this.el).append($(
        '<table>' +
            '<thead><tr>' +
                '<th class="source">Source</th>' +
                '<th class="destination">Destination</th>' +
                '<th class="details">Details</th>' +
            '</tr></thead>' +
            '<tbody></tbody>' +
        '</table>'
    ));
};

HfdlMessagePanel.prototype.supportsMessage = function(message) {
    return message['mode'] === 'HFDL';
};

HfdlMessagePanel.prototype.pushMessage = function(message) {
    var $b = $(this.el).find('tbody');

    var src = '';
    var dst = '';
    var details = JSON.stringify(message);

    var renderAddress = function(a) {
        return a['id'];
    }

    // TODO remove safety net once parsing is complete
    try {
        var payload = message['hfdl'];
        if ('spdu' in payload) {
            var spdu = payload['spdu'];
            src = renderAddress(spdu['src']);
            details = '<h4>HFDL Squitter message</h4>'
            details += '<div>Systable version: ' + spdu['systable_version'] + '</div>';

            if ('gs_status' in spdu) {
                details += spdu['gs_status'].map(function(gs){
                    return '<div>Ground station ' + gs['gs']['id'] + ' is operating on frequency ids ' + gs['freqs'].map(function(f) {return f['id']; }).join(', ') + '</div>';
                }).join('')
            }
        } else if ('lpdu' in payload) {
            var lpdu = payload['lpdu'];
            src = renderAddress(lpdu['src']);
            dst = renderAddress(lpdu['dst']);
            if (lpdu['type']['id'] === 13 || lpdu['type']['id'] === 29) {
                // unnumbered data
                var hfnpdu = lpdu['hfnpdu'];
                if (hfnpdu['type']['id'] === 209) {
                    // performance data
                    details = '<h4>Performance data</h4>';
                    details += '<div>Flight: ' + hfnpdu['flight_id'] + '</div>';
                    if ('pos' in hfnpdu) {
                        var pos = hfnpdu['pos'];
                        var lat = pos['lat'] || 180;
                        var lon = pos['lon'] || 180;
                        if (Math.abs(lat) <= 90 && Math.abs(lon) <= 180) {
                            details += '<div>Position: ' + pos['lat'] + ', ' + pos['lon'] + '</div>';
                        }
                    }
                } else if (hfnpdu['type']['id'] === 255) {
                    // enveloped data
                    if ('acars' in hfnpdu) {
                        var acars = hfnpdu['acars'];
                        details = '<h4>ACARS message</h4>';
                        details += '<div>Flight: ' + acars['flight'] + '</div>';
                        details += '<div>Registration: ' + acars['reg'] + '</div>';
                        details += '<div class="acars_message">' + acars['msg_text'] + '</div>';
                    }
                }
            } else if (lpdu['type']['id'] === 47) {
                // logon denied
                details = '<h4>Logon denied</h4>';
            } else if (lpdu['type']['id'] === 63) {
                details = '<h4>Logoff request</h4>';
                if (lpdu['ac_info'] && lpdu['ac_info']['icao']) {
                    details += '<div>ICAO: ' + lpdu['ac_info']['icao'];
                }
            } else if (lpdu['type']['id'] === 79) {
                details = '<h4>Logon resume</h4>';
                if (lpdu['ac_info'] && lpdu['ac_info']['icao']) {
                    details += '<div>ICAO: ' + lpdu['ac_info']['icao'];
                }
            } else if (lpdu['type']['id'] === 95) {
                details = '<h4>Logon resume confirmation</h4>';
            } else if (lpdu['type']['id'] === 143) {
                details = '<h4>Logon request</h4>';
                if (lpdu['ac_info'] && lpdu['ac_info']['icao']) {
                    details += '<div>ICAO: ' + lpdu['ac_info']['icao'];
                }
            } else if (lpdu['type']['id'] === 159) {
                details = '<h4>Logon confirmation</h4>';
                if (lpdu['ac_info'] && lpdu['ac_info']['icao']) {
                    details += '<div>ICAO: ' + lpdu['ac_info']['icao'];
                }
                if (lpdu['assigned_ac_id']) {
                    details += '<div>Assigned aircraft ID: ' + lpdu['assigned_ac_id'] + '</div>';
                }
            } else if (lpdu['type']['id'] === 191) {
                details = '<h4>Logon request (DLS)</h4>';
                if (lpdu['ac_info'] && lpdu['ac_info']['icao']) {
                    details += '<div>ICAO: ' + lpdu['ac_info']['icao'];
                }
            }
        }
    } catch (e) {
        console.error(e, e.stack);
    }

    $b.append($(
        '<tr>' +
            '<td class="source">' + src + '</td>' +
            '<td class="destination">' + dst + '</td>' +
            '<td class="details">' + details + '</td>' +
        '</tr>'
    ));
    this.scrollToBottom();
};

$.fn.hfdlMessagePanel = function() {
    if (!this.data('panel')) {
        this.data('panel', new HfdlMessagePanel(this));
    }
    return this.data('panel');
};

Vdl2MessagePanel = function(el) {
    MessagePanel.apply(this, el);
    this.initClearTimer();
}

Vdl2MessagePanel.prototype = new MessagePanel();

Vdl2MessagePanel.prototype.render = function() {
    $(this.el).append($(
        '<table>' +
            '<thead><tr>' +
                '<th class="todo">TODO</th>' +
                '</tr></thead>' +
            '<tbody></tbody>' +
        '</table>'
    ));
};

Vdl2MessagePanel.prototype.supportsMessage = function(message) {
    return message['mode'] === 'VDL2';
};

Vdl2MessagePanel.prototype.pushMessage = function(message) {
    var $b = $(this.el).find('tbody');
    $b.append($(
        '<tr>' +
            '<td class="todo">' + JSON.stringify(message) + '</td>' +
        '</tr>'
    ));
    this.scrollToBottom();
};

$.fn.vdl2MessagePanel = function() {
    if (!this.data('panel')) {
        this.data('panel', new Vdl2MessagePanel(this));
    }
    return this.data('panel');
};