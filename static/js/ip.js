$(document).ready(function () {
    //获取url参数
    let getQueryString = function (parm) {
        let reg = new RegExp("(^|&)" + parm + "=([^&]*)(&|$)"),
            r = window.location.search.substr(1).match(reg);
        return r ? unescape(decodeURI(decodeURI(r[2]))) : null;
    };

    $(window).scroll(function () {
        if ($(window).scrollTop() > 200)
            $('.go-top').show();
        else
            $('.go-top').hide();
    });
    $('.go-top').click(function () {
        $('html, body').animate({ scrollTop: 0 }, 300);
    });

    if (getQueryString("ip")) { $(".result span").html(getQueryString("ip")) }

    //webscoket
    // 192.168.1.172:8888/result_ws
    // var wsURI = 'ws://' + window.location.host + '/result_ws'
    var wsURI = 'ws://192.168.0.112:8888/reverse_ip_result_ws'
    var webSocket = new WebSocket(wsURI);
    webSocket.onerror = function (event) {
        console.log(event.data);
    };
    //与WebSocket建立连接  
    webSocket.onopen = function (event) {
        console.log('与服务器端建立连接');
        start();

        //处理服务器返回的信息  
        webSocket.onmessage = function (event) {
            var data = JSON.parse(event.data)[getQueryString("ip")]
            console.log(data)
            for (var i = 0; i < data.length; i++) {
                var templateRow = `
                    <tr>
                        <td>${data[i].domain}</td>
                        <td>${data[i].url}</td>
                        <td>${data[i].title}</td>
                    </tr>
                `
                $(".table-ip tbody").append(templateRow)
            }

            if (!data.length) {
                $(".table-ip").css("display", "none")
                $(".nodomain").css("display", "block")
            }
            
        };
    };

    function start() {
        //向服务器发送请求  
        var obj = { "ip": getQueryString("ip") }
        webSocket.send(JSON.stringify(obj));
    }
})
