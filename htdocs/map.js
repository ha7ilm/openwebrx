$(function(){
    var query = new URLSearchParams(window.location.search);

    var expectedCallsign;
    if (query.has('callsign')) {
        expectedCallsign = Object.fromEntries(query.entries());
    }
    var expectedLocator;
    if (query.has('locator')) expectedLocator = query.get('locator');
    var expectedIcao;
    if (query.has('icao')) expectedIcao = query.get('icao');

    var protocol = window.location.protocol.match(/https/) ? 'wss' : 'ws';

    var href = window.location.href;
    var index = href.lastIndexOf('/');
    if (index > 0) {
        href = href.substr(0, index + 1);
    }
    href = href.split("://")[1];
    href = protocol + "://" + href;
    if (!href.endsWith('/')) {
        href += '/';
    }
    var ws_url = href + "ws/";

    var map;
    var markers = {};
    var rectangles = {};
    var receiverMarker;
    var updateQueue = [];

    // reasonable default; will be overriden by server
    var retention_time = 2 * 60 * 60 * 1000;
    var strokeOpacity = 0.8;
    var fillOpacity = 0.35;
    var callsign_service;

    var colorKeys = {};
    var colorScale = chroma.scale(['red', 'blue', 'green']).mode('hsl');
    var getColor = function(id){
        if (!id) return "#000000";
        if (!colorKeys[id]) {
            var keys = Object.keys(colorKeys);
            keys.push(id);
            keys.sort(function(a, b) {
                var pa = parseFloat(a);
                var pb = parseFloat(b);
                if (isNaN(pa) || isNaN(pb)) return a.localeCompare(b);
                return pa - pb;
            });
            var colors = colorScale.colors(keys.length);
            colorKeys = {};
            keys.forEach(function(key, index) {
                colorKeys[key] = colors[index];
            });
            reColor();
            updateLegend();
        }
        return colorKeys[id];
    }

    // when the color palette changes, update all grid squares with new color
    var reColor = function() {
        $.each(rectangles, function(_, r) {
            var color = getColor(colorAccessor(r));
            r.setOptions({
                strokeColor: color,
                fillColor: color
            });
        });
    }

    var colorMode = 'byband';
    var colorAccessor = function(r) {
        switch (colorMode) {
            case 'byband':
                return r.band;
            case 'bymode':
                return r.mode;
        }
    };

    $(function(){
        $('#openwebrx-map-colormode').on('change', function(){
            colorMode = $(this).val();
            colorKeys = {};
            filterRectangles(allRectangles);
            reColor();
            updateLegend();
        });
    });

    var updateLegend = function() {
        var lis = $.map(colorKeys, function(value, key) {
            // fake rectangle to test if the filter would match
            var fakeRectangle = Object.fromEntries([[colorMode.slice(2), key]]);
            var disabled = rectangleFilter(fakeRectangle) ? '' : ' disabled';
            return '<li class="square' + disabled + '" data-selector="' + key + '"><span class="illustration" style="background-color:' + chroma(value).alpha(fillOpacity) + ';border-color:' + chroma(value).alpha(strokeOpacity) + ';"></span>' + key + '</li>';
        });
        $(".openwebrx-map-legend .content").html('<ul>' + lis.join('') + '</ul>');
    };

    var shallowEquals = function(obj1, obj2) {
        // basic shallow object comparison
        return Object.entries(obj1).sort().toString() === Object.entries(obj2).sort().toString();
    }

    var processUpdates = function(updates) {
        if (typeof(AprsMarker) == 'undefined') {
            updateQueue = updateQueue.concat(updates);
            return;
        }
        updates.forEach(function(update){
            var key = sourceToKey(update.source);

            switch (update.location.type) {
                case 'latlon':
                    var pos = false;
                    if (update.location.lat && update.location.lon) {
                        pos = new google.maps.LatLng(update.location.lat, update.location.lon);
                    }
                    var marker;
                    var markerClass = google.maps.Marker;
                    var aprsOptions = {}
                    if (update.location.symbol) {
                        markerClass = AprsMarker;
                        aprsOptions.symbol = update.location.symbol;
                        aprsOptions.course = update.location.course;
                        aprsOptions.speed = update.location.speed;
                    } else if (update.source.icao) {
                        markerClass = PlaneMarker;
                        aprsOptions = update.location;
                    }
                    if (markers[key]) {
                        marker = markers[key];
                        if (!pos) {
                            delete markers[key];
                            marker.setMap();
                            return;
                        }
                    } else {
                        if (pos) {
                            marker = new markerClass();
                            marker.addListener('click', function () {
                                showMarkerInfoWindow(update.source, pos);
                            });
                            marker.setMap(map);
                            markers[key] = marker;
                        }
                    }
                    if (!marker) return;
                    marker.setOptions($.extend({
                        position: pos,
                        title: sourceToString(update.source)
                    }, aprsOptions, getMarkerOpacityOptions(update.lastseen) ));
                    marker.source = update.source;
                    marker.lastseen = update.lastseen;
                    marker.mode = update.mode;
                    marker.band = update.band;
                    marker.comment = update.location.comment;

                    if (expectedCallsign && shallowEquals(expectedCallsign, update.source))  {
                        map.panTo(pos);
                        showMarkerInfoWindow(update.source, pos);
                        expectedCallsign = false;
                    }

                    if (expectedIcao && expectedIcao === update.source.icao) {
                        map.panTo(pos);
                        showMarkerInfoWindow(update.source, pos);
                        expectedIcao = false;
                    }

                    if (infowindow && infowindow.source && shallowEquals(infowindow.source, update.source)) {
                        showMarkerInfoWindow(infowindow.source, pos);
                    }
                break;
                case 'locator':
                    var loc = update.location.locator;
                    var lat = (loc.charCodeAt(1) - 65 - 9) * 10 + Number(loc[3]);
                    var lon = (loc.charCodeAt(0) - 65 - 9) * 20 + Number(loc[2]) * 2;
                    var center = new google.maps.LatLng({lat: lat + .5, lng: lon + 1});
                    var rectangle;
                    // the accessor is designed to work on the rectangle... but it should work on the update object, too
                    var color = getColor(colorAccessor(update));
                    if (rectangles[key]) {
                        rectangle = rectangles[key];
                    } else {
                        rectangle = new google.maps.Rectangle();
                        rectangle.addListener('click', function(){
                            showLocatorInfoWindow(this.locator, this.center);
                        });
                        rectangles[key] = rectangle;
                    }
                    rectangle.source = update.source;
                    rectangle.lastseen = update.lastseen;
                    rectangle.locator = update.location.locator;
                    rectangle.mode = update.mode;
                    rectangle.band = update.band;
                    rectangle.center = center;

                    rectangle.setOptions($.extend({
                        strokeColor: color,
                        strokeWeight: 2,
                        fillColor: color,
                        map: rectangleFilter(rectangle) ? map : undefined,
                        bounds:{
                            north: lat,
                            south: lat + 1,
                            west: lon,
                            east: lon + 2
                        }
                    }, getRectangleOpacityOptions(update.lastseen) ));

                    if (expectedLocator && expectedLocator === update.location.locator) {
                        map.panTo(center);
                        showLocatorInfoWindow(expectedLocator, center);
                        expectedLocator = false;
                    }

                    if (infowindow && infowindow.locator && infowindow.locator === update.location.locator) {
                        showLocatorInfoWindow(infowindow.locator, center);
                    }
                break;
            }
        });
    };

    var clearMap = function(){
        var reset = function(_, item) { item.setMap(); };
        $.each(markers, reset);
        $.each(rectangles, reset);
        receiverMarker.setMap();
        markers = {};
        rectangles = {};
    };

    var reconnect_timeout = false;

    var config = {}

    var connect = function(){
        var ws = new WebSocket(ws_url);
        ws.onopen = function(){
            ws.send("SERVER DE CLIENT client=map.js type=map");
            reconnect_timeout = false
        };

        ws.onmessage = function(e){
            if (typeof e.data != 'string') {
                console.error("unsupported binary data on websocket; ignoring");
                return
            }
            if (e.data.substr(0, 16) == "CLIENT DE SERVER") {
                return
            }
            try {
                var json = JSON.parse(e.data);
                switch (json.type) {
                    case "config":
                        Object.assign(config, json.value);
                        if ('receiver_gps' in config) {
                            var receiverPos = {
                                lat: config.receiver_gps.lat,
                                lng: config.receiver_gps.lon
                            };
                            if (!map) $.getScript("https://maps.googleapis.com/maps/api/js?key=" + config.google_maps_api_key).done(function(){
                                map = new google.maps.Map($('.openwebrx-map')[0], {
                                    center: receiverPos,
                                    zoom: 5,
                                });

                                $.getScript("static/lib/nite-overlay.js").done(function(){
                                    nite.init(map);
                                    setInterval(function() { nite.refresh() }, 10000); // every 10s
                                });
                                $.when(
                                    $.getScript('static/lib/AprsMarker.js'),
                                    $.getScript('static/lib/PlaneMarker.js')
                                ).done(function(){
                                    processUpdates(updateQueue);
                                    updateQueue = [];
                                });

                                var $legend = $(".openwebrx-map-legend");
                                setupLegendFilters($legend);
                                map.controls[google.maps.ControlPosition.LEFT_BOTTOM].push($legend[0]);

                                if (!receiverMarker) {
                                    receiverMarker = new google.maps.Marker();
                                    receiverMarker.addListener('click', function() {
                                        showReceiverInfoWindow(receiverMarker);
                                    });
                                }
                                receiverMarker.setOptions({
                                    map: map,
                                    position: receiverPos,
                                    title: config['receiver_name'],
                                    config: config
                                });
                            }); else {
                                receiverMarker.setOptions({
                                    map: map,
                                    position: receiverPos,
                                    config: config
                                });
                            }
                        }
                        if ('receiver_name' in config && receiverMarker) {
                            receiverMarker.setOptions({
                                title: config['receiver_name']
                            });
                        }
                        if ('map_position_retention_time' in config) {
                            retention_time = config.map_position_retention_time * 1000;
                        }
                        if ('callsign_service' in config) {
                            callsign_service = config['callsign_service'];
                        }
                    break;
                    case "update":
                        processUpdates(json.value);
                    break;
                    case 'receiver_details':
                        $('.webrx-top-container').header().setDetails(json['value']);
                    break;
                    default:
                        console.warn('received message of unknown type: ' + json['type']);
                }
            } catch (e) {
                // don't lose exception
                console.error(e);
            }
        };
        ws.onclose = function(){
            clearMap();
            if (reconnect_timeout) {
                // max value: roundabout 8 and a half minutes
                reconnect_timeout = Math.min(reconnect_timeout * 2, 512000);
            } else {
                // initial value: 1s
                reconnect_timeout = 1000;
            }
            setTimeout(connect, reconnect_timeout);
        };

        window.onbeforeunload = function() { //http://stackoverflow.com/questions/4812686/closing-websocket-correctly-html5-javascript
            ws.onclose = function () {};
            ws.close();
        };

        /*
        ws.onerror = function(){
            console.info("websocket error");
        };
        */
    };

    connect();

    var getInfoWindow = function() {
        if (!infowindow) {
            infowindow = new google.maps.InfoWindow();
            google.maps.event.addListener(infowindow, 'closeclick', function() {
                delete infowindow.locator;
                delete infowindow.source;
            });
        }
        delete infowindow.locator;
        delete infowindow.source;
        return infowindow;
    };

    var sourceToKey = function(source) {
        // special treatment for special entities
        // not just for display but also in key treatment in order not to overlap with other locations sent by the same callsign
        if ('item' in source) return source['item'];
        if ('object' in source) return source['object'];
        if ('icao' in source) return source['icao'];
        var key = source.callsign;
        if ('ssid' in source) key += '-' + source.ssid;
        return key;
    };

    // we can reuse the same logic for displaying and indexing
    var sourceToString = sourceToKey;

    var linkifySource = function(source) {
        var callsignString = sourceToString(source);
        switch (callsign_service) {
            case "qrzcq":
                return '<a target="callsign_info" href="https://www.qrzcq.com/call/' + source.callsign + '">' + callsignString + '</a>';
            case "qrz":
                return '<a target="callsign_info" href="https://www.qrz.com/db/' + source.callsign + '">' + callsignString + '</a>';
            case 'aprsfi':
                var callWithSsid = sourceToKey(source);
                return '<a target="callsign_info" href="https://aprs.fi/info/a/' + callWithSsid + '">' + callsignString + '</a>';
            default:
                return callsignString;
        }
    };

    var distanceKm = function(p1, p2) {
        // Earth radius in km
        var R = 6371.0;
        // Convert degrees to radians
        var rlat1 = p1.lat() * (Math.PI/180);
        var rlat2 = p2.lat() * (Math.PI/180);
        // Compute difference in radians
        var difflat = rlat2-rlat1;
        var difflon = (p2.lng()-p1.lng()) * (Math.PI/180);
        // Compute distance
        d = 2 * R * Math.asin(Math.sqrt(
            Math.sin(difflat/2) * Math.sin(difflat/2) +
            Math.cos(rlat1) * Math.cos(rlat2) * Math.sin(difflon/2) * Math.sin(difflon/2)
        ));
        return Math.round(d);
    };

    var infowindow;
    var showLocatorInfoWindow = function(locator, pos) {
        var infowindow = getInfoWindow();
        infowindow.locator = locator;
        var inLocator = Object.values(rectangles).filter(rectangleFilter).filter(function(d) {
            return d.locator === locator;
        }).sort(function(a, b){
            return b.lastseen - a.lastseen;
        });
        var distance = receiverMarker?
            " at " + distanceKm(receiverMarker.position, pos) + " km" : "";
        infowindow.setContent(
            '<h3>Locator: ' + locator + distance + '</h3>' +
            '<div>Active Callsigns:</div>' +
            '<ul>' +
                inLocator.map(function(i){
                    var timestring = moment(i.lastseen).fromNow();
                    var message = linkifySource(i.source) + ' (' + timestring + ' using ' + i.mode;
                    if (i.band) message += ' on ' + i.band;
                    message += ')';
                    return '<li>' + message + '</li>'
                }).join("") +
            '</ul>'
        );
        infowindow.setPosition(pos);
        infowindow.open(map);
    };

    var showMarkerInfoWindow = function(source, pos) {
        var infowindow = getInfoWindow();
        infowindow.source = source;
        var marker = markers[sourceToKey(source)];
        var timestring = moment(marker.lastseen).fromNow();
        var commentString = "";
        var distance = "";
        if (marker.comment) {
            commentString = '<div>' + marker.comment + '</div>';
        }
        if (receiverMarker) {
            distance = " at " + distanceKm(receiverMarker.position, marker.position) + " km";
        }
        var title;
        if (marker.icao) {
            title = marker.identification || marker.icao;
            if ('altitude' in marker) {
                commentString += '<div>Altitude: ' + marker.altitude + ' ft</div>';
            }
            if ('groundspeed' in marker) {
                commentString += '<div>Speed: ' + Math.round(marker.groundspeed) + ' kt</div>';
            }
            if ('verticalspeed' in marker) {
                commentString += '<div>V/S: ' + marker.verticalspeed + ' ft/min</div>';
            }
        } else {
            linkifySource(source);
        }
        infowindow.setContent(
            '<h3>' + title + distance + '</h3>' +
            '<div>' + timestring + ' using ' + marker.mode + ( marker.band ? ' on ' + marker.band : '' ) + '</div>' +
            commentString
        );
        infowindow.open(map, marker);
    };

    var showReceiverInfoWindow = function(marker) {
        var infowindow = getInfoWindow()
        infowindow.setContent(
            '<h3>' + marker.config['receiver_name'] + '</h3>' +
            '<div>Receiver location</div>'
        );
        infowindow.open(map, marker);
    };

    var getScale = function(lastseen) {
        var age = new Date().getTime() - lastseen;
        var scale = 1;
        if (age >= retention_time / 2) {
            scale = (retention_time - age) / (retention_time / 2);
        }
        return Math.max(0, Math.min(1, scale));
    };

    var getRectangleOpacityOptions = function(lastseen) {
        var scale = getScale(lastseen);
        return {
            strokeOpacity: strokeOpacity * scale,
            fillOpacity: fillOpacity * scale
        };
    };

    var getMarkerOpacityOptions = function(lastseen) {
        var scale = getScale(lastseen);
        return {
            opacity: scale
        };
    };

    // fade out / remove positions after time
    setInterval(function(){
        var now = new Date().getTime();
        Object.values(rectangles).forEach(function(m){
            var age = now - m.lastseen;
            if (age > retention_time) {
                delete rectangles[sourceToKey(m.source)];
                m.setMap();
                return;
            }
            m.setOptions(getRectangleOpacityOptions(m.lastseen));
        });
        Object.values(markers).forEach(function(m) {
            var age = now - m.lastseen;
            if (age > retention_time || (m.ttl && age > m.ttl)) {
                delete markers[sourceToKey(m.source)];
                m.setMap();
                return;
            }
            m.setOptions(getMarkerOpacityOptions(m.lastseen));
        });
    }, 1000);

    var rectangleFilter = allRectangles = function() { return true; };

    var filterRectangles = function(filter) {
        rectangleFilter = filter;
        $.each(rectangles, function(_, r) {
            r.setMap(rectangleFilter(r) ? map : undefined);
        });
    };

    var setupLegendFilters = function($legend) {
        $content = $legend.find('.content');
        $content.on('click', 'li', function() {
            var $el = $(this);
            $lis = $content.find('li');
            if ($lis.hasClass('disabled') && !$el.hasClass('disabled')) {
                $lis.removeClass('disabled');
                filterRectangles(allRectangles);
            } else {
                $el.removeClass('disabled');
                $lis.filter(function() {
                    return this != $el[0]
                }).addClass('disabled');

                var key = colorMode.slice(2);
                var selector = $el.data('selector');
                filterRectangles(function(r) {
                    return r[key] === selector;
                });
            }
        });
    }

});
