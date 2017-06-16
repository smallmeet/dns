/**
 * Created by Administrator on 2017/4/20.
 */
var _xsrf = $("input[name='_xsrf']").attr('value');
$(document).ready(function () {
    var accountInfo = cookie.getCookie('accountInfo');
    var logStatus = cookie.getCookie('logStatus')

    // if (logStatus) {
    //     console.log('已登录')
    //     window.location.href = '/search'
    // }
    // console.log(accountInfo)

    //如果cookie里没有账号信息
    if(Boolean(accountInfo) === false){
        console.log('cookie中没有检测到账号信息！');
        // return false;
    }
    else{
        //如果cookie里有账号信息
        console.log('cookie中检测到账号信息！现在开始预填写！');
        var userName = "";
        var passWord = "";
        var index = accountInfo.indexOf("&");

        userName = accountInfo.substring(0,index);
        passWord = accountInfo.substring(index+1);

        $('#username').val(userName)
        $('#password').val(passWord)
        $("input[value='remember-me']").attr("checked", true)
    }


    $('#login').click(function () {
        $.post('/login',{
            '_xsrf': _xsrf,
            'username': $('#username').val(),
            'password': $('#password').val(),
            'log_status': $("input[value='set-log']").is(':checked')
        },function (data) {
            console.log(JSON.parse(data))
            var data = JSON.parse(data)
            switch (Number(data.code)) {
                case 0:
                    myalert('服务器出错',"tipwrong")
                    break;
                case 1:
                    var rememberStatus = $("input[value='remember-me']").is(':checked');
                    var logStatus = $("input[value='set-log']").is(':checked');
                    console.log(rememberStatus)
                    var accountInfo = "";
                    accountInfo = $('#username').val() + "&" + $('#password').val();
                    cookie.setCookie('current_username', $('#username').val(), 1440*3)
                    if (rememberStatus) {
                        console.log("cookie")
                        cookie.setCookie('accountInfo', accountInfo, 1440*3)
                    } else {
                        cookie.delCookie('accountInfo')
                    }
                    if (logStatus) {
                        cookie.setCookie('logStatus', logStatus, 1440*3)
                    } else {
                        cookie.delCookie('logStatus')
                    }
                    window.location.href = "/search"
                    break;
                case 2:
                    myalert('用户名密码错误',"tipwrong")
                    break;
                case 3:
                    myalert('用户名密码不能为空',"tipwrong")
                    break;
            }
        })
    })

    $('body').keydown(function(e){
        if(e.keyCode==13){
            $('#login').click()
        }
    });
})
