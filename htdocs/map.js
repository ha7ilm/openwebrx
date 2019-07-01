(function(){
    var protocol = 'ws';
    if (window.location.toString().startsWith('https://')) {
        protocol = 'wss';
    }

    var ws_url = protocol + "://" + (window.location.origin.split("://")[1]) + "/ws/";
    if (!("WebSocket" in window)) return;

    var ws = new WebSocket(ws_url);
    ws.onopen = function(){
        console.info("onopen");
        ws.send("SERVER DE CLIENT client=map.js type=map");
    };
    ws.onmessage = function(){
        console.info("onmessage");
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