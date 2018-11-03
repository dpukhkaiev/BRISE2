
const _conf = {
    'workerService': 'http://localhost:49153',
    'mainNode': 'http://localhost:49152',
}




$(document).ready(function () {

    console.log(":: Front-end lift off ::")

    // init conection
    var socket = io.connect(_conf.mainNode);

    socket.on('connect', function () {
        socket.send('User has connected!');
        console.log('Connect');
    });
    socket.on('disconnect', function () {
        socket.send('User has disconnected!');
        console.log('disconnect');
    });
    // --------------------------------------- New events

    socket.on('task', function (msg) {
        $("#task").append('<li class="collection-item">' + JSON.stringify(msg) + '</li>');
        console.log('Task:', msg);
    })
    socket.on('experiment', function (msg) {
        $("#experiment").append('<li class="collection-item">' + JSON.stringify(msg) + '</li>');
        console.log('Experiment:', msg);
    })

    socket.on('log', function (msg) {
        $("#log").append('<li class="collection-item">' + JSON.stringify(msg) + '</li>');
        console.log('Log:', msg);
    });

    //---------------------------------------- Old events
    socket.on('main_config', function (msg) {
        $("#others").append('<li class="collection-item">' + JSON.stringify(msg) + '</li>');
        console.log('--main_config:', msg);
    })
    socket.on('info', function (msg) {
        $("#others").append('<li class="collection-item">' + 'info:' + JSON.stringify(msg) + '</li>');
        console.log('--info:', msg);
    })
    socket.on('task result', function (msg) {
        $("#others").append('<li class="collection-item">' + JSON.stringify(msg) + '</li>');
        console.log('--task result:', msg);
    });

    socket.on('regression', function (msg) {
        $("#others").append('<li class="collection-item">' + JSON.stringify(msg) + '</li>');
        console.log('--regression', msg);
    });
    socket.on('best point', function (msg) {
        $("#others").append('<li class="collection-item">' + JSON.stringify(msg) + '</li>');
        console.log('--best point:', msg);
    });
    socket.on('default conf', function (msg) {
        $("#others").append('<li class="collection-item">' + JSON.stringify(msg) + '</li>');
        console.log('--default conf:', msg);
    });

    // -------------------------------------- Start/Stop main
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            document.getElementById("main-response").innerHTML = this.responseText;
        }
    };

    function startMain() {
        xhttp.open("GET", (_conf.mainNode + '/main_start'), true);
        xhttp.send();
    };
    function stopMain() {
        xhttp.open("GET", (_conf.mainNode + '/main_stop'), true);
        xhttp.send();
    };

    $('#start').click(function () {
        startMain()
    });
    $('#stop').click(function () {
        stopMain()
    });
});