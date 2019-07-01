(function(){
    var protocol = 'ws';
    if (window.location.toString().startsWith('https://')) {
        protocol = 'wss';
    }

    var ws_url = protocol + "://" + (window.location.origin.split("://")[1]) + "/ws/";
    if (!("WebSocket" in window)) return;

    var ws = new WebSocket(ws_url);
    ws.onopen = function(){
        ws.send("SERVER DE CLIENT client=map.js type=map");
    };

    var map;
    var markers = {};
    var updateQueue = [];

    var processUpdates = function(updates) {
        if (!map) {
            updateQueue = updateQueue.concat(updates);
            return;
        }
        updates.forEach(function(update){
            // TODO maidenhead locator implementation
            if (update.location.type != 'latlon') return;
            var pos = new google.maps.LatLng(update.location.lat, update.location.lon)
            if (markers[update.callsign]) {
                console.info("updating");
                markers[update.callsign].setPosition(pos);
            } else {
                console.info("initializing");
                markers[update.callsign] = new google.maps.Marker({
                    position: pos,
                    map: map,
                    title: update.callsign
                });
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
                            zoom: 8
                        });
                        processUpdates(updateQueue);
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