/**
 * home.html
 * author: clloz
 * date: 2017/4/18
 */
var _xsrf = $("input[name='_xsrf']").attr('value');
$(document).ready(function () {
    $(".history").niceScroll();

    $(".search-input").focus(function () {
        // $(".history").css("display", "block")
        $(".search-bar").addClass("bar-shadow")
    })
    $(".search-input").blur(function (e) {
        // if(e.relatedTarget !== $('.history')[0]){
        //     $(".history").css("display", "none")
        // }
        $(".search-bar").removeClass("bar-shadow")
    })

    $('.list-group-item').click(function () {
        // console.log("html",$(this).html())
        $(".search-input").val($(this).html())
        $(".history").css("display", "none")
    })

    // var username = cookie.getCookie('current_username');
    // // console.log(username)
    // if (username) {
    //     var imgsrc = "../static/img/" + username + ".png"
    //     $("img").attr("src", imgsrc)
    //     $("img").css("display", "block")
    // }

    $('.fa-cogs').click(function () {
        $(this).css('display', 'none')
        $('.ana-check').css('display', 'block')
    })

    $('.fa-remove').click(function () {
        $('.ana-check').css('display', 'none')
        $('.fa-cogs').css('display', 'block')
    })

    $('#ana').click(function () {
        var URL = $(".search-input").val()
        if (URL) {
            if(checkeURL(URL)) {
                window.location.href = "/result?https=" + $("input[value='https']").is(':checked') +
                    "&searchEngine=" + $("input[value='searchEngine']").is(':checked') +
                    "&domain=" + $("input[value='domain']").is(':checked') +
                    "&dictionary=" + $("input[value='dictionary']").is(':checked') +
                    "&content=" + $(".search-input").val()
            } else {
                myalert("请输入合法的域名", "tipwrong")
            }

        } else {
            myalert("搜索内容不能为空")
        }

    })

    $('#logout').click(function () {
        cookie.delCookie('logStatus')
        window.location.href = '/logout'
    })

    $('body').keydown(function(e){
        if(e.keyCode==13){
            $('#ana').click()
        }
    });
})

function checkeURL(URL){
    var str=URL;
    var reg = /((https|http|ftp|rtsp|mms):\/\/)?(([0-9a-z_!~*'().&=+$%-]+:)?[0-9a-z_!~*'().&=+$%-]+@)?(([0-9]{1,3}\.){3}[0-9]{1,3}|([0-9a-z_!~*'()-]+\.)*([0-9a-z][0-9a-z-]{0,61})?[0-9a-z]\.[a-z]{2,6})(:[0-9]{1,4})?((\/?)|(\/[0-9a-z_!~*'().;?:@&=+$,%#-]+)+\/?)/g;
    var objExp=new RegExp(reg);
    if (objExp.test(str)) {
        return true
    } else {
        return false
    }
}
