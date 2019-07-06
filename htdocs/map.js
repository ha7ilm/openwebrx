(function(){
    var protocol = 'ws';
    if (window.location.toString().startsWith('https://')) {
        protocol = 'wss';
    }

    var query = window.location.search.replace(/^\?/, '').split('&').map(function(v){
        var s = v.split('=');
        r = {}
        r[s[0]] = s.slice(1).join('=')
        return r;
    }).reduce(function(a, b){
        return a.assign(b);
    });

    var expectedCallsign;
    if (query.callsign) expectedCallsign = query.callsign;

    var ws_url = protocol + "://" + (window.location.origin.split("://")[1]) + "/ws/";
    if (!("WebSocket" in window)) return;

    var ws = new WebSocket(ws_url);
    ws.onopen = function(){
        ws.send("SERVER DE CLIENT client=map.js type=map");
    };

    var map;
    var markers = {};
    var rectangles = {};
    var updateQueue = [];

    var processUpdates = function(updates) {
        if (!map) {
            updateQueue = updateQueue.concat(updates);
            return;
        }
        updates.forEach(function(update){

            switch (update.location.type) {
                case 'latlon':
                    var pos = new google.maps.LatLng(update.location.lat, update.location.lon)
                    if (markers[update.callsign]) {
                        markers[update.callsign].setPosition(pos);
                    } else {
                        markers[update.callsign] = new google.maps.Marker({
                            position: pos,
                            map: map,
                            title: update.callsign
                        });
                    }

                    // TODO the trim should happen on the server side
                    if (expectedCallsign && expectedCallsign == update.callsign.trim()) {
                        map.panTo(pos);
                        delete(expectedCallsign);
                    }
                break;
                case 'locator':
                    var loc = update.location.locator;
                    var lat = (loc.charCodeAt(1) - 65 - 9) * 10 + Number(loc[3]);
                    var lon = (loc.charCodeAt(0) - 65 - 9) * 20 + Number(loc[2]) * 2;
                    var rectangle;
                    if (rectangles[update.callsign]) {
                        rectangle = rectangles[update.callsign];
                    } else {
                        rectangle = new google.maps.Rectangle();
                        rectangles[update.callsign] = rectangle;
                    }
                    rectangle.setOptions({
                        strokeColor: '#FF0000',
                        strokeOpacity: 0.8,
                        strokeWeight: 2,
                        fillColor: '#FF0000',
                        fillOpacity: 0.35,
                        map: map,
                        bounds:{
                            north: lat,
                            south: lat + 1,
                            west: lon,
                            east: lon + 2
                        }
                    });
                break;
            }
        });
    }

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
            json = JSON.parse(e.data);
            switch (json.type) {
                case "config":
                    var config = json.value;
                    $.getScript("https://maps.googleapis.com/maps/api/js?key=" + config.google_maps_api_key).done(function(){
                        map = new google.maps.Map($('body')[0], {
                            center: {
                                lat: config.receiver_gps[0],
                                lng: config.receiver_gps[1]
                            },
                            zoom: 5
                        });
                        processUpdates(updateQueue);
                        $.getScript("/static/nite-overlay.js").done(function(){
                            nite.init(map);
                            setInterval(function() { nite.refresh() }, 10000); // every 10s
                        });
                    })
                break
                case "update":
                    processUpdates(json.value);
                break
            }
        } catch (e) {
            // don't lose exception
            console.error(e);
        }
    };
    ws.onclose = function(){
        console.info("onclose");
    };

    window.onbeforeunload = function() { //http://stackoverflow.com/questions/4812686/closing-websocket-correctly-html5-javascript
        ws.onclose = function () {};
        ws.close();
    };
    ws.onerror = function(){
        console.info("onerror");
    };

})();