(function(){
    var protocol = 'ws';
    if (window.location.toString().startsWith('https://')) {
        protocol = 'wss';
    }

    var query = window.location.search.replace(/^\?/, '').split('&').map(function(v){
        var s = v.split('=');
        var r = {};
        r[s[0]] = s.slice(1).join('=');
        return r;
    }).reduce(function(a, b){
        return a.assign(b);
    });

    var expectedCallsign;
    if (query.callsign) expectedCallsign = query.callsign;
    var expectedLocator;
    if (query.locator) expectedLocator = query.locator;

    var ws_url = protocol + "://" + (window.location.origin.split("://")[1]) + "/ws/";
    if (!("WebSocket" in window)) return;

    var map;
    var markers = {};
    var rectangles = {};
    var updateQueue = [];

    // reasonable default; will be overriden by server
    var retention_time = 2 * 60 * 60 * 1000;
    var strokeOpacity = 0.8;
    var fillOpacity = 0.35;

    var processUpdates = function(updates) {
        if (!map) {
            updateQueue = updateQueue.concat(updates);
            return;
        }
        updates.forEach(function(update){

            switch (update.location.type) {
                case 'latlon':
                    var pos = new google.maps.LatLng(update.location.lat, update.location.lon);
                    var marker;
                    if (markers[update.callsign]) {
                        marker = markers[update.callsign];
                    } else {
                        marker = new google.maps.Marker();
                        marker.addListener('click', function(){
                            showMarkerInfoWindow(update.callsign, pos);
                        });
                        markers[update.callsign] = marker;
                    }
                    marker.setOptions($.extend({
                        position: pos,
                        map: map,
                        title: update.callsign
                    }, getMarkerOpacityOptions(update.lastseen) ));
                    marker.lastseen = update.lastseen;
                    marker.mode = update.mode;

                    // TODO the trim should happen on the server side
                    if (expectedCallsign && expectedCallsign == update.callsign.trim()) {
                        map.panTo(pos);
                        showMarkerInfoWindow(update.callsign, pos);
                        delete(expectedCallsign);
                    }
                break;
                case 'locator':
                    var loc = update.location.locator;
                    var lat = (loc.charCodeAt(1) - 65 - 9) * 10 + Number(loc[3]);
                    var lon = (loc.charCodeAt(0) - 65 - 9) * 20 + Number(loc[2]) * 2;
                    var center = new google.maps.LatLng({lat: lat + .5, lng: lon + 1});
                    var rectangle;
                    if (rectangles[update.callsign]) {
                        rectangle = rectangles[update.callsign];
                    } else {
                        rectangle = new google.maps.Rectangle();
                        rectangle.addListener('click', function(){
                            showLocatorInfoWindow(update.location.locator, center);
                        });
                        rectangles[update.callsign] = rectangle;
                    }
                    rectangle.setOptions($.extend({
                        strokeColor: '#FF0000',
                        strokeWeight: 2,
                        fillColor: '#FF0000',
                        map: map,
                        bounds:{
                            north: lat,
                            south: lat + 1,
                            west: lon,
                            east: lon + 2
                        }
                    }, getRectangleOpacityOptions(update.lastseen) ));
                    rectangle.lastseen = update.lastseen;
                    rectangle.locator = update.location.locator;
                    rectangle.mode = update.mode;

                    if (expectedLocator && expectedLocator == update.location.locator) {
                        map.panTo(center);
                        showLocatorInfoWindow(expectedLocator, center);
                        delete(expectedLocator);
                    }
                break;
            }
        });
    };

    var clearMap = function(){
        var reset = function(callsign, item) { item.setMap(); };
        $.each(markers, reset);
        $.each(rectangles, reset);
        markers = {};
        rectangles = {};
    };

    var reconnect_timeout = false;

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
                console.log("Server acknowledged WebSocket connection.");
                return
            }
            try {
                var json = JSON.parse(e.data);
                switch (json.type) {
                    case "config":
                        var config = json.value;
                        if (!map) $.getScript("https://maps.googleapis.com/maps/api/js?key=" + config.google_maps_api_key).done(function(){
                            map = new google.maps.Map($('.openwebrx-map')[0], {
                                center: {
                                    lat: config.receiver_gps[0],
                                    lng: config.receiver_gps[1]
                                },
                                zoom: 5
                            });
                            processUpdates(updateQueue);
                            updateQueue = [];
                            $.getScript("/static/lib/nite-overlay.js").done(function(){
                                nite.init(map);
                                setInterval(function() { nite.refresh() }, 10000); // every 10s
                            });
                        });
                        retention_time = config.map_position_retention_time * 1000;
                    break;
                    case "update":
                        processUpdates(json.value);
                    break;
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

    var infowindow;
    var showLocatorInfoWindow = function(locator, pos) {
        if (!infowindow) infowindow = new google.maps.InfoWindow();
        var inLocator = $.map(rectangles, function(r, callsign) {
            return {callsign: callsign, locator: r.locator, lastseen: r.lastseen, mode: r.mode}
        }).filter(function(d) {
            return d.locator == locator;
        }).sort(function(a, b){
            return b.lastseen - a.lastseen;
        });
        infowindow.setContent(
            '<h3>Locator: ' + locator + '</h3>' +
            '<div>Active Callsigns:</div>' +
            '<ul>' +
                inLocator.map(function(i){
                    var timestring = moment(i.lastseen).fromNow();
                    return '<li>' + i.callsign + ' (' + timestring + ' using ' + i.mode + ')</li>'
                }).join("") +
            '</ul>'
        );
        infowindow.setPosition(pos);
        infowindow.open(map);
    };

    var showMarkerInfoWindow = function(callsign, pos) {
        if (!infowindow) infowindow = new google.maps.InfoWindow();
        var marker = markers[callsign];
        var timestring = moment(marker.lastseen).fromNow();
        infowindow.setContent(
            '<h3>' + callsign + '</h3>' +
            '<div>' + timestring + ' using ' + marker.mode + '</div>'
        );
        infowindow.open(map, marker);
    }

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
        $.each(rectangles, function(callsign, m) {
            var age = now - m.lastseen;
            if (age > retention_time) {
                delete rectangles[callsign];
                m.setMap();
                return;
            }
            m.setOptions(getRectangleOpacityOptions(m.lastseen));
        });
        $.each(markers, function(callsign, m) {
            var age = now - m.lastseen;
            if (age > retention_time) {
                delete markers[callsign];
                m.setMap();
                return;
            }
            m.setOptions(getMarkerOpacityOptions(m.lastseen));
        });
    }, 1000);

})();