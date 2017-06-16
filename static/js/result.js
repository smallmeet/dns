/**
 * result.html
 * author: clloz
 * date: 2017/4/18
 */
var isBrute = GetQueryString("dictionary") === "true",
    isFirst = GetQueryString("dictionary") === "true",
    since_brute = 0,
    myChart,
    chartData = {}
    chartData.nodes = new Array()
    chartData.links = new Array()
    chartData.nodes[0] = {
        "id": "0",
        "name": GetQueryString("content"),
        "itemStyle": {
            "normal": {
                "color": "rgb(235,81,72)"
            }
        },
        "symbolSize": 100,
        "x": 0,
        "y": 0,
        "attributes": {
            "modularity_class": 0
        }
    }
// console.log(chartData)
$(document).ready(function () {
    var domain = GetQueryString("content"),
        since = 0,
        limit = 30

    var checkArr = [GetQueryString("https"),GetQueryString("searchEngine"),GetQueryString("domain"),GetQueryString("dictionary")]

    $("input[type='checkbox']").removeAttr("checked")
    for (var i = 0; i < checkArr.length; i++) {
        if(checkArr[i] === 'true') {
            $("input[type='checkbox']:eq(" + i +")").attr("checked", 'true')
        }
    }

    $(".search-input").val(domain)

//    myChart = echarts.init($('#echarts').get(0),'infographic');
//    myChart.showLoading();
//    initChart(chartData)

    getHeader(domain);
    getSubDomain(domain, since, limit);
    // getIpInfo();
    getDomainInfo();
    getWhois(domain);

    $('.deep-search button').click(function () {
        $('.deep-search').css("display", "none")
        $('.load-animate').css("display", "block")
        $('.load-animate .load-span').css("display", "none");
        $('.load-animate .progress-wrap').css("display", "block");
        // setTimeout(searchFinish, 3000)
        getBrute(domain, since_brute, limit)
        window['moduleBruteProgress'].start();
    })


    $(".ana").click(function () {
        var URL = $(".search-input").val()
        if (URL) {
            if (checkIp(URL)) {
                window.location.href = "/reverse_ip_lookup?target=" + $(".search-input").val();
            } else if(checkeURL(URL)) {
                var checkArr2 = [$("input[value='https']").is(':checked'), $("input[value='searchEngine']").is(':checked'), $("input[value='domain']").is(':checked'), $("input[value='dictionary']").is(':checked')]
                console.log(checkArr.toString() === checkArr2.toString())
                if (URL === domain && checkArr.toString() === checkArr2.toString()) {
                    myalert("正在分析", "tipwrong")
                } else {
                    window.location.href = "/result?https=" + $("input[value='https']").is(':checked') +
                        "&searchEngine=" + $("input[value='searchEngine']").is(':checked') +
                        "&domain=" + $("input[value='domain']").is(':checked') +
                        "&dictionary=" + $("input[value='dictionary']").is(':checked') +
                        "&content=" + $(".search-input").val()
                }
            } else {
                myalert("请输入合法的域名", "tipwrong")
            }
        } else {
            myalert("搜索内容不能为空", "tipwrong")
        }
    })
    $('.search-input').keydown(function(e){
        if(e.keyCode==13){
            $('.ana').click()
        }
    });

    $(".more-whois").on("click", function () {
        $(".not-important").css("display", "table-row")
        $(this).css("display", "none")
    })

})

//$(window).resize(function () {
//    myChart.resize()
//})

function getHeader(domain) {
    getContent("/get_http_header","get",{"domain": domain})
        .then(data => data)
        .then(data => {
            if (!data.success) {
                setTimeout(function () {
                    getHeader(domain)
                },2000)
            } else {
                $(".banner .loading").css("display", "none")
                var headerObj = data.http_header
                // console.log(headerObj)
                for (var key in headerObj) {
                    var templateRow = `${key} : ${headerObj[key]}<br>`
                    $("#header-info").append(templateRow)
                }
                // $(".left-content").getNiceScroll().resize()
            }
        })
}

window.BEN_GLOBAL_IP_RESS = {};
window.BEN_GLOBAL_IPS = new Array();

window.BEN_GLOBAL_DOMAINS = new Array();
window.BEN_GLOBAL_DOMAIN_RESS = {};

function getDomainInfo() {
    if(window.BEN_GLOBAL_DOMAINS.length <= 0){
        setTimeout(function () {
            getDomainInfo()
        }, 2000)

    }else{

        domain = window.BEN_GLOBAL_DOMAINS.shift()
        if (domain == "end") {
            $('.b__domain-state').each(function(){
                if(!$(this).html() || $(this).html() == '...'){
                    window.BEN_GLOBAL_DOMAINS.push($(this).attr("data-subdomain"))
                }
            })

            if(window.BEN_GLOBAL_DOMAINS.length > 0) {
                // 检查是否有未完成的ip
                window.BEN_GLOBAL_DOMAINS.push("end")
            }else{
                return
            }
        }

        if (window.BEN_GLOBAL_IP_RESS[domain]) {
            status = window.BEN_GLOBAL_IP_RESS[domain]
            $("span[data-subdomain='"+domain+"']").html(status);
        }else{
            getContent("/detect_domain","get",{"target":domain}).then(
                function(data){
                    if (0 === data['state']) {
                        stateText = '域名不存在';
                    } else if (1 === data['state']) {
                        stateText = '服务未开启';
                    } else if (2 === data['state']) {
                        stateText = '服务正常';
                    } else if (-1 === data['state']) {
                        stateText = '未知错误';
                    } else {
                        stateText = '未知错误';
                    }

                    $("span[data-subdomain='"+domain+"']").html(stateText)
                    window.BEN_GLOBAL_IP_RESS[domain] = stateText

                    setTimeout(function () {
                        getDomainInfo()
                    }, 200)

                },function(value) {
                    // failure
                    $("span[data-subdomain='"+domain+"']").html("查询超时")

                    setTimeout(function () {
                        getDomainInfo()
                    }, 200)
                }
            )
        }


    }

}


function getIpInfo() {
    if (window.BEN_GLOBAL_IPS.length <=0) {
        setTimeout(function () {
            getIpInfo()
        }, 2000)
    }else{
        ip = window.BEN_GLOBAL_IPS.shift()

        if (ip == "end") {

            $('.location').each(function(){
                if(!$(this).html()){
                    window.BEN_GLOBAL_IPS.push($(this).attr("data-ip"))
                }
            })

            if(window.BEN_GLOBAL_IPS.length > 0) {
                // 检查是否有未完成的ip
                window.BEN_GLOBAL_IPS.push("end")
            }else{
                return
            }
        }

        if (window.BEN_GLOBAL_IP_RESS[ip]) {
            ip_data = window.BEN_GLOBAL_IP_RESS[ip]
            $("td[data-ip='"+ip+"']").html(ip_data.province + " " + ip_data.city);
        }else{
            console.info("ip[%s] get ip" % ip)
            getContent("/get_ip_info","get",{"ip":ip}).then(
               data => {
                var ip_data = data.data;
                td_obj = $("td[data-ip='"+ip+"']");
                content = "未获取"
                if (ip_data && data.success) {
                    if (ip_data.country || ip_data.province || ip_data.city) {
                        if (ip_data.country == '中国' && ip_data.province && ip_data.city) {
                            content = ip_data.province + " " + ip_data.city
                        } else {
                            content = ip_data.country + " " + ip_data.province + " " + ip_data.city
                        }
                    }
                }

                td_obj.html(content);

            })
        }

        setTimeout(function () {
            getIpInfo()
        }, 300)
    }
}

function getSubDomain(domain, since, limit) {
    getContent("/result_async", "get", {"domain": domain, "since": since, "limit": limit})
        .then(data => {
            // console.log(data.task_state)
            if (data.success) {
                $(".sub-domain .loading").css("display", "none")
                var subDomains = data.sub_domains
                // console.log(Math.PI)
                // console.log(radius * Math.cos(angle))
                // console.log(subDomains.length)
                for ( var i = 0; i < subDomains.length; i++) {
                    // if(subDomains[i].ip === "null" || subDomains[i].ip === "") {
                    //     subDomains[i].ip = ""
                    //     var templateRow = `<tr>
                    //                     <td>${subDomains[i].last_commit_time}</td>
                    //                     <td class="domain">${subDomains[i].subdomain}</td>
                    //                     <td>${subDomains[i].ip}</td>
                    //                     <td class="location"></td>
                    //                     <td><button class="btn btn-default btn-banner">查看banner</button></td>
                    //                 </tr>`
                    // } else {
                    //     var templateRow = `<tr>
                    //                     <td>${subDomains[i].last_commit_time}</td>
                    //                     <td class="domain">${subDomains[i].subdomain}</td>
                    //                     <td>${subDomains[i].ip}</td>
                    //                     <td data-ip=${subDomains[i].ip} class="location"></td>
                    //                     <td><button data-ip=${subDomains[i].ip} class="btn btn-default btn-banner">查看banner</button></td>
                    //                 </tr>`
                    // }
                    var ips = subDomains[i].ip.split(', ').join('<br>')
                    var locations = subDomains[i].location.split(', ').join('<br>')
                    if (!locations) {
                        locations = '无';
                    }
                    var templateRow = `<tr>
                                        <td class="td-date">${subDomains[i].last_commit_time}</td>
                                        <td class="td-domain">${subDomains[i].subdomain}</td>
                                        <td class="td-origin">${subDomains[i].origin}</td>
                                        <td class="td-ip">${ips}</td>
                                        <td data-ip=${subDomains[i].ip} class="td-location location">${locations}</td>
                                        <td class="td-state"><span class="b__domain-state" data-subdomain="${subDomains[i].subdomain}">...</td>
                                    </tr>`

                    $("#domain-table").append(templateRow)

                    window.BEN_GLOBAL_IPS.push(subDomains[i].ip)
                    window.BEN_GLOBAL_DOMAINS.push(subDomains[i].subdomain)

                    ips = subDomains[i].ip.split(",")
                    if (since < 50) {
                        for(len = 0;len<ips.length;len++){
                            if (ips[len] && subDomains[i].subdomain){
                                appendData($('.search-input').val(),[{"ip":ips[len],'subdomain':subDomains[i].subdomain}]);
                            }
                        }
                    }


//                    chartData.links.push({
//                        "id": chartData.links.length,
//                        "name": null,
//                        "source": chartData.nodes.length,
//                        "target": "0",
//                        "lineStyle": {
//                            "normal": {}
//                        }
//                    })
//                    chartData.nodes.push({
//                        "id": chartData.nodes.length,
//                        "name": subDomains[i].subdomain,
//                        "itemStyle": {
//                            "normal": {
//                                "color": "rgb(51,75,92)"
//                            }
//                        },
//                        "symbolSize": parseInt(Math.random() * 20 + 30),
//                        "x": Math.random() * 300,
//                        "y": Math.random() * 300,
//                        "attributes": {
//                            "modularity_class": parseInt(Math.random() * 8) + 1
//                        }
//                    })

                }
                // $(".left-content").getNiceScroll().resize()
//                if(chartData.nodes.length < 200 && subDomains.length) {
//                    chartData.nodes[0].symbolSize = 50
//                    myChart.showLoading();
//                    refreshChart(chartData)
//                }
                since += subDomains.length
            }
            if(!data.success || !(data.sub_domains.length !== limit && data.task_state === 2)){
                setTimeout(function () {
                    getSubDomain(domain, since, limit)
                }, 250)
            } else if (data.task_state === 2) {
                console.log(data.is_brute)
                window.BEN_GLOBAL_IPS.push("end")
                window.BEN_GLOBAL_DOMAINS.push("end")
                if (!isBrute) {
                    $('.deep-search').css("display", "block")
                    $('.load-animate').css("display", "none")
                    since_brute = since
                } else {
                    if (isFirst) {
                        getBrute(domain, since, limit)
                        since_brute = since
                        isFirst = false
                    } else {
                        $(".s-finish strong").html(since)
                        searchFinish()
                    }
                }
                window['moduleBruteProgress'].stop();
            }

            return data
        })
        // .then(data => {
        //     var elNum = 0
        //     if (!(since % 30)) {
        //         elNum = 30
        //     } else {
        //         elNum = since % 30
        //     }
        //     for (var i = since - elNum; i < since; i++) {
        //         $(".btn-banner:eq(" + i + ")").on("click", function () {
        //
        //             if ($(this).attr("data-ip")) {
        //                 $(".fullscreen").css("display", "block")
        //                 $("#banner").html("")
        //                 $.get("/get_banner",{"ip": $(this).attr("data-ip")},function (data) {
        //                     console.log(data)
        //                     $(".fullscreen").css("display", "none")
        //                     if (JSON.parse(data).success) {
        //                         var bannerInfo = JSON.parse(data).data
        //                         for (var key in bannerInfo) {
        //                             if (bannerInfo[key] !== "") {
        //                                 var templateRow = `${key} : ${bannerInfo[key]}<br>`
        //                                 $("#banner").append(templateRow)
        //                             }
        //                         }
        //                         $("#myModal").modal("show")
        //                     } else {
        //                         myalert("请求失败，请稍后重试", "tipwrong")
        //                     }
        //
        //                 })
        //             } else {
        //                 myalert("未获取IP，无法请求", "tipwrong")
        //             }
        //
        //         })
        //     }
        //     return data
        // })
        .then(data => {
            var elNum = 0
            if (!(since % 30)) {
                elNum = 30
            } else {
                elNum = since % 30
            }

//            alert(JSON.stringifywindow.ips)

//            ips.forEach(function(ip){
//                $.get("/get_ip_info",{"ip": ip},function (data) {
//                    if (JSON.parse(data).success && JSON.parse(data).data !== null) {
//                        var location = JSON.parse(data).data
//                        $("td[data-ip='"+ip+"']").html(location.province + " " + location.city);
//                    }
//                })
//            })

//            data.sub_domains.forEach(function(domain_info){
//                ip = domain_info.ip
//                subdomain = domain_info.subdomain
//


//                $.get("/get_ip_info",{"ip": $(".location:eq(" + i + ")").attr("data-ip")},function (data) {
//                    if (JSON.parse(data).success && JSON.parse(data).data !== null) {
//                        var location = JSON.parse(data).data
//                        if (location.country || location.province || location.city) {
//                            if (location.country == '中国' && location.province && location.city) {
//                                $(".location:eq(" + i + ")").html(location.province + " " + location.city)
//                            } else {
//                                $(".location:eq(" + i + ")").html(location.country + " " + location.province + " " + location.city)
//                            }
//                        } else {
//                            $(".location:eq(" + i + ")").html("未获取")
//                        }
//                    } else {
//                        $(".location:eq(" + i + ")").html("未获取")
//                    }
//                })
//            })


            // console.log(since, elNum)
            // 查询地区
//            for (var i = since - elNum; i < since; i++) {
//                (function (i) {
//                    if ($(".location:eq(" + i + ")").attr("data-ip")) {
//                        $.get("/get_ip_info",{"ip": $(".location:eq(" + i + ")").attr("data-ip")},function (data) {
//                            if (JSON.parse(data).success && JSON.parse(data).data !== null) {
//                                var location = JSON.parse(data).data
//                                if (location.country || location.province || location.city) {
//                                    if (location.country == '中国' && location.province && location.city) {
//                                        $(".location:eq(" + i + ")").html(location.province + " " + location.city)
//                                    } else {
//                                        $(".location:eq(" + i + ")").html(location.country + " " + location.province + " " + location.city)
//                                    }
////                                } else if(location.province && location.city){
////                                    $(".location:eq(" + i + ")").html(location.province + " " + location.city)
////                                } else if (location.country) {
////                                    $(".location:eq(" + i + ")").html(location.country)
//                                } else {
//                                    $(".location:eq(" + i + ")").html("未获取")
//                                }
//                            } else {
//                                $(".location:eq(" + i + ")").html("未获取")
//                            }
//                        })
//                    }
//                })(i)
//            }


            // 查询服务器状态
//            console.log('start for.');
//            for (var i = since - elNum; i < since; i++) {
//                console.log(i);
//                var $target = $(".b__domain-state:eq(" + i + ")");
//                var currentDomain = $target.attr("data-subdomain");
//                (function($target) {
//                    console.log('start ajax');
//                    $.get('/detect_domain?target=' + currentDomain, function(responseData) {
//                        console.log('ajax callback, ' + JSON.stringify(responseData));
//                        var stateText;
//                        if (0 === responseData['state']) {
//                            stateText = '域名不存在';
//                        } else if (1 === responseData['state']) {
//                            stateText = '服务未开启';
//                        } else if (2 === responseData['state']) {
//                            stateText = '服务正常';
//                        } else if (-1 === responseData['state']) {
//                            stateText = '未知错误';
//                        } else {
//                            stateText = '未知错误';
//                        }
//                        $target.text(stateText);
//                    }, 'json')
//                }) ($target);
//            }
//            console.log('end for.')
        })
}

// add_brute_task domain
function getBrute(domain, since, limit) {
    getContent("/add_brute_task", "post", {domain: domain})
        .then(data => {
            if (data.success) {
                isBrute = true
                console.log(since)
                getSubDomain(domain, since, limit)
            }
        })
}

function getWhois(domain) {
    getContent("/get_whois", "get", {"domain": domain})
        .then(data => {
            if (!data.success || isEmptyObject(data.whois)) {
                setTimeout(function () {
                    getWhois(domain)
                }, 2000)
            } else {
                $(".domain .loading").css("display", "none")
                // console.log(data.whois)
                var whoisInfo = data.whois
                for (var key in whoisInfo) {
                    if(whoisInfo[key] !== null) {
                        if (key === "updated_date" || key === "expiration_date" || key === "address" || key === "whois_server" || key === "name_servers" || key === "emails") {
                            var templateRow = `<tr>
                                            <td>${key}</td>
                                            <td>${whoisInfo[key]}</td>
                                        </tr>`
                        } else {
                            var templateRow = `<tr class="not-important">
                                            <td>${key}</td>
                                            <td>${whoisInfo[key]}</td>
                                        </tr>`
                        }

                        $("#header-table").append(templateRow)
                    }
                }
                // $(".left-content").getNiceScroll().resize()
            }
        })
}

var getContent = function (url, type, data) {
    var promise = new Promise(function (resolve, reject) {
        $.ajax({
            type: type,
            url: url,
            data: data,
            dataType: "json",
            timeout : 10000,
            success: function (data) {
                resolve(data)
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                reject(data)
            }
        })
    })
    return promise
}

function isEmptyObject(obj) {
    for (var key in obj) {
        return false;
    }
    return true;
}

function project(x, y) {
    var angle = (x - 90) / 180 * Math.PI, radius = y;
    return [radius * Math.cos(angle), radius * Math.sin(angle)];
}

//function refreshChart(data) {
//    if (!myChart) {
//        return
//    } else {
//            if (data.nodes.length) {
//                data.nodes.forEach(function (node) {
//                    node.itemStyle = null;
//                    node.value = node.symbolSize;
//                    node.symbolSize /= 1.5;
//                    node.label = {
//                        normal: {
//                            show: node.symbolSize > 10
//                        }
//                    };
//                    node.category = node.attributes.modularity_class;
//                });
//            }
//            var option = myChart.getOption();
//            // console.log(option)
//            option.series[0].data = data.nodes;
//            option.series[0].links = data.links;
//            // console.log(option)
//            myChart.hideLoading()
//            myChart.setOption(option);
//    }
//}

//function initChart(data) {
//        myChart.hideLoading();
//        // console.log(data)
//        var categories = [];
//        for (var i = 0; i < 9; i++) {
//            if (i === 0) {
//                categories[i] = {
//                    name: '主域名'
//                };
//            } else {
//                categories[i] = {
//                    name: '子域名' + i
//                };
//            }
//
//        }
//        if (data.nodes) {
//            data.nodes.forEach(function (node) {
//                node.itemStyle = null;
//                node.value = node.symbolSize;
//                node.symbolSize /= 1.5;
//                node.label = {
//                    normal: {
//                        show: node.symbolSize > 10
//                    }
//                };
//                node.category = node.attributes.modularity_class;
//            });
//        }
//        var option = {
//            title: {
//                text: '域名关系表',
//                subtext: 'Default layout',
//                top: 'bottom',
//                left: 'right'
//            },
//            tooltip: {},
//            legend: [{
//                // selectedMode: 'single',
//                data: categories.map(function (a) {
//                    return a.name;
//                })
//            }],
//            animationDurationUpdate: 1500,
//            animationEasingUpdate: 'quinticInOut',
//            series : [
//                {
//                    name: '域名关系',
//                    type: 'graph',
//                    layout: 'circular',
//                    circular: {
//                        rotateLabel: true
//                    },
//                    data: data.nodes,
//                    links: data.links,
//                    categories: categories,
//                    roam: true,
//                    label: {
//                        normal: {
//                            position: 'right',
//                            formatter: '{b}'
//                        }
//                    },
//                    lineStyle: {
//                        normal: {
//                            color: 'source',
//                            curveness: 0.3
//                        }
//                    }
//                }
//            ]
//        };
//        myChart.setOption(option);
//}

//获取url参数
function GetQueryString(parm)
{
    var reg = new RegExp("(^|&)"+ parm +"=([^&]*)(&|$)");
    var r = window.location.search.substr(1).match(reg);
    if(r!=null)return  unescape(decodeURI(decodeURI(r[2]))); return null;
}

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

function searchFinish() {
    $('.load-animate').css("display", "none")
    $('.s-finish').css("display", "block")
}
