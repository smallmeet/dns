$(function () {
    var domainData = {}
    setMap()

    //获取url参数
    let getQueryString = function (parm) {
        let reg = new RegExp("(^|&)" + parm + "=([^&]*)(&|$)"),
            r = window.location.search.substr(1).match(reg);
        return r ? unescape(decodeURI(decodeURI(r[2]))) : null;
    };

    var whois_info = {
        "domain_name": "域名",
        "whois_server": "Whois 服务器",
        "name_servers": "域名服务器",
        "status": "状态",
        "name": "名字",
        "emails": "邮箱",
        "country": "国家",
        "state": "州 / 省",
        "city": "城市",
        "address": "地址",
        "zipcode": "邮政编码",
        "org": "组织",
        "dnssec": "DNS安全扩展",
        "creation_date": "创建时间",
        "updated_date": "更新时间",
        "expiration_date": "过期时间",
        "registrar": "注册商",
        "referral_url": "推广 Url"
    }

    $(window).scroll(function () {
        if ($(window).scrollTop() > 200)
            $('.go-top').show();
        else
            $('.go-top').hide();
    });
    $('.go-top').click(function () {
        $('html, body').animate({ scrollTop: 0 }, 300);
    });

    $("#download").click(function () {
        $(".table2excel").table2excel({
            exclude: ".noExl",
            name: "Excel Document Name",
            filename: "myFileName",
            exclude_img: true,
            exclude_links: true,
            exclude_inputs: true
        });
    });

    //webscoket
    // 192.168.1.172:8888/result_ws
    // var wsURI = 'ws://' + window.location.host + '/result_ws'
    var wsURI = 'ws://192.168.0.112:8888/result_ws_test'
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
            // console.log(event.data)
            var data = JSON.parse(event.data)
            var type = data.type;
            switch (type) {
                case 'domain_detail': //whois ns mx
                    // console.log(JSON.stringify(data))
                    whois(data)
                    paint(data)
                    break;
                case 'ip_history':  //历史解析记录
                    // console.log(data)
                    ip_his(data)
                    break;
                case 'sub_domain':   //子域名
                    console.log(JSON.stringify(data))
                    subdomain(data)
                    break;
                case 'domain_state': //子域名状态
                    status(data)
                    break;
                case 'scan_info':  //端口扫描信息
                    scanRes(data)
                    break;
                case 'task_over':
                    console.log("连接结束")
                    if (!$(".filter").hasClass("complete")) $(".filter").addClass("complete")
                    if (!$(".sort").hasClass("complete")) $(".sort").addClass("complete")
                    break;

            }
            $("[data-toggle='tooltip']").tooltip();
        };
    };

    function start() {
        //向服务器发送请求  
        // var obj = { "domain": getQueryString("domain") }
        var obj = { "domain": "kq88.com" }
        webSocket.send(JSON.stringify(obj));
    }

    function ip_his(data) {
        var his = data.history
        for (var i = 0; i < his.length; i++) {
            var templateRow = `
                                <tr>
                                    <td class="col-md-3">${his[i].ip}</td>
                                    <td class="col-md-3">${his[i].start_date}</td>
                                    <td class="col-md-3">${his[i].end_date}</td>
                                </tr>
                            `
            $(".ip-histroy tbody").append(templateRow)
        }
    }

    function whois(data) {
        var whois = data.whois;
        for (var key in whois) {
            if (whois[key] !== "null" && whois[key] !== null) {
                var templateRow = `
                    <tr>
                        <td>${whois_info[key] ? whois_info[key] : key}</td>
                        <td>${whois[key]}</td>
                    </tr>
                `
                $(".table-whois tbody").append(templateRow)
            }
        }
        if ($(".table-whois tbody").find("tr").length === 0) {
            $(".table-whois").css("display", "none")
            $(".nowhois").css("display", "block")
        }
    }

    function subdomain(data) {
        var subdomain = data.sub_domains
        var refreshData = {}
        var ipArr = []
        for (var i = 0; i < subdomain.length; i++) {
            // normal table
            var templateRow = `
                <tr>
                    <td data-select="${subdomain[i].sub_domain}" class="col-md-3">${subdomain[i].sub_domain} ${subdomain[i].location === "" ? `` : `<span class="flag flag-${subdomain[i].location.toLocaleLowerCase()}"></span>`}<br></td>
                    <td>${subdomain[i].last_commit_time}</td>
                    <td>${modalStr(subdomain[i].ip, subdomain[i].sub_domain)}</td>
                    <td><div data-domain=${subdomain[i].sub_domain}></div></td>
                </tr>
            `
            $(".domain tbody").append(templateRow)
            if (subdomain[i].location !== "") {
                refreshData[subdomain[i].location] ? refreshData[subdomain[i].location] += 1 : refreshData[subdomain[i].location] = 1
            }

            //ip sort table
            if (subdomain[i].ip !== "") {
                var ip_l = subdomain[i].ip.split(",")
                for (var j = 0; j < ip_l.length; j++) {
                    if ($.inArray(ip_l[j], ipArr) === -1) {
                        ipArr.push(ip_l[j])
                        var sortTempRow = `
                        <tr data-sort-ip=${subdomain[i].ip}>
                            <td><i data-toggle='tooltip' title='端口扫描' data-parent="${subdomain[i].sub_domain}" data-ip="${ip_l[j]}" class='fa fa-eye'></i> <span data-search-ip="${ip_l[j]}">${ip_l[j]}</span><br></td>
                            <td>${subdomain[i].last_commit_time}</td>
                            <td data-select="${subdomain[i].sub_domain}" class="col-md-3">${subdomain[i].sub_domain} ${subdomain[i].location === "" ? `` : `<span class="flag flag-${subdomain[i].location.toLocaleLowerCase()}"></span>`}<br></td>
                            <td><div data-domain=${subdomain[i].sub_domain}></div></td>
                        </tr>
                    `
                        $(".sort-table tbody").append(sortTempRow)
                    } else {
                        $($("[data-sort-ip='" + subdomain[i].ip + "']").find("td").get(2)).append(`${subdomain[i].sub_domain} ${subdomain[i].location === "" ? `` : `<span class="flag flag-${subdomain[i].location.toLocaleLowerCase()}"></span>`}<br>`)
                        $($("[data-sort-ip='" + subdomain[i].ip + "']").find("td").get(3)).append(`<div data-domain=${subdomain[i].sub_domain}></div>`)
                    }
                }
            }

            ips = subdomain[i].ip.split(",")
            for (len = 0; len < ips.length; len++) {
                if (ips[len] && subdomain[i].sub_domain) {
                    console.log(123)
                    appendData("kq88.com", [{ "ip": ips[len], 'subdomain': subdomain[i].sub_domain }]);
                }
            }
        }
        // console.log(refreshData)
        refresh(refreshData)
        domainSelect()
    }

    function status(data) {
        switch (data.state) {
            case -1:
            case 1:
            case 2:
            case 3:
                $("[data-domain='" + data.domain + "']").append(`<span class="label label-warning"><i class="fa  fa-unlink"></i> 服务器无法访问</span>`)
                break;
            case 0:
                $("[data-domain='" + data.domain + "']").append(`<span class="label label-danger"><i class="fa  fa-ban"></i> 域名不存在</span>`)
                break;
            case 4:
                $("[data-domain='" + data.domain + "']").append(`<span class="label label-primary"><i class="fa  fa-send"></i> 正常</span>`)
                break;
        }
    }

    function setMap() {
        $('#world-map').vectorMap({
            map: 'world_mill_en',
            backgroundColor: '#333333',
            zoomButtons: false,
            series: {
                regions: [{
                    values: domainData,
                    scale: ['#C8EEFF', '#0071A4'],
                    normalizeFunction: 'polynomial'
                }]
            },
            onRegionTipShow: function (e, el, code) {
                if (typeof domainData[code] !== "undefined") {
                    el.html(el.html() + ' <br>服务器 : ' + domainData[code]);
                }
            }
        });
    }

    function refresh(data) {
        var mapObject = $('#world-map').vectorMap('get', 'mapObject');
        for (key in data) {
            if (domainData[key]) {
                domainData[key] += data[key]
            } else {
                domainData[key] = data[key]
            }
        }
        // mapObject.series.regions[0].setValues(domainData);
        // mapObject.series.regions[0].setScale(['#C8EEFF', '#0071A4']);
        mapObject.remove()
        setMap();
    }

    function modalStr(ip, domain) {
        if (ip === "") {
            return "无"
        } else {
            var ip_l = ip.split(",")
            var str = ""
            for (var i = 0; i < ip_l.length; i++) {
                str += "<i data-toggle='tooltip' title='端口扫描' data-parent=" + domain + " data-ip=" + ip_l[i] + " class='fa fa-eye'></i> <span data-search-ip='" + ip_l[i] + "'>" + ip_l[i] + "</span><br>"
            }
            return str
        }
    }

    //点击端口扫描
    $(document).on('click', "[data-parent]", function () {
        console.log($(this).attr("data-parent"), $(this).attr("data-ip"))
        if (!$(this).hasClass("fa-spin") && !$(this).hasClass("port-success")) {
            var portInfo = {
                "type": "scan",
                "domain": $(this).attr("data-parent"),
                "ip": $(this).attr("data-ip")
            }
            $(this).removeClass("fa-eye").addClass("fa-spin fa-spinner")
            webSocket.send(JSON.stringify(portInfo));
        }
    })

    function scanRes(data) {

        $("[data-parent='" + data.domain_info.domain + "'][data-ip='" + data.ip_info.ip.ip + "']").removeClass("fa-spin fa-spinner").addClass("fa-eye port-success")
        // $("[data-parent='mail.kq88.com'][data-ip='183.61.38.175']").removeClass("fa-spin fa-spinner").addClass("fa-eye port-success")
        localStorage[data.domain_info.domain + " " + data.ip_info.ip.ip] = JSON.stringify(data)
        // console.log(localStorage['mail.kq88.com 183.61.38.175'])
    }

    //点击查看端口信息
    $(document).on("click", ".port-success", function () {
        var data = JSON.parse(localStorage[$(this).attr("data-parent") + " " + $(this).attr("data-ip")])
        console.log(data)
        $(".port-info").empty()
        $(".more-info").empty()
        var portInfo_temp = `
            <p>IP地址: ${data.ip_info.ip.ip} <a href="${data.ip_info.ip.ip}"><i class="fa fa-external-link" style="color:lightblue;"></i></a></p>
                    <p>协议: ${data.domain_info.cms.cms}</p>
                    <p>CMS信息: ${data.ip_info.ip.web_info.product}</p>
                    <p>产品: ${data.ip_info.ip.web_info.name}</p>
                    <p>产品名: ${data.ip_info.ip.web_info.extrainfo}</p>
                    <p>版本号: ${data.ip_info.ip.web_info.version}</p>
                    <p>更新时间: ${data.domain_info.sync_time}</p>
        `
        $(".port-info").append(portInfo_temp)

        var moreInfo_temp = `
            <pre>${data.ip_info.ip.port_info}</pre>
        `
        $(".more-info").append(moreInfo_temp)
        $("#port").modal("show")
    })

    //绘制svg
    function paint(data) {
        // console.log(data)
        var svgJson = {
            "name": "domain",
            "children": [
                {
                    "name": "NS",
                    "children": []
                },
                {
                    "name": "MX",
                    "children": []
                },
                {
                    "name": "site",
                    "children": []
                }
            ]
        }
        var ns_record = data.ns_records
        var mx_record = data.mx_records
        var site_record = data.other_site

        var nsObj = {}
        var mxObj = {}
        var siteObj = {}
        if (ns_record) {
            for (var i = 0; i < ns_record.length; i++) {
                nsObj['name'] = ns_record[i].ip + " " + ns_record[i].name
                svgJson.children[0].children.push(nsObj)
            }
        }

        if (mx_record) {
            for (var i = 0; i < mx_record.length; i++) {
                mxObj['name'] = mx_record[i].ip + " " + mx_record[i].name
                svgJson.children[1].children.push(mxObj)
            }
        }

        if (site_record) {
            for (var j = 0; j < site_record.length; j++) {
                for (var key in site_record[j]) {
                    siteObj['name'] = key
                    siteObj['children'] = []
                    for (var i = 0; i < site_record[j][key].length; i++) {
                        var childObj = {}
                        childObj['name'] = site_record[j][key][i].domain + " " + site_record[j][key][i].title
                        siteObj['children'].push(childObj)
                    }
                }
            }
            console.log(siteObj)
            svgJson.children[2].children.push(siteObj)
        }

        // console.log(svgJson)
        svgPaint(JSON.stringify(svgJson))
    }

    //ip 反查
    $(document).on("click", "[data-search-ip]", function () {
        window.location.href = "/reverse_ip_lookup_new?ip=" + $(this).attr("data-search-ip")
    })

    //域名 url title
    //筛选域名
    function domainSelect(str) {
        // str = "0."
        var reg_format = /[\s_\u4E00-\u9FA5\uF900-\uFA2D]/
        if (reg_format.test(str)) {
            myalert("域名不能包含空格、下划线和中文")
            return;
        }
        var reg = new RegExp(str)
        var tr_l = $(".domain tbody tr")
        var mark = 0
        for (var i = 0; i < tr_l.length; i++) {
            // console.log($(tr_l[i]).find("td").get(0))
            if (str === "") {
                $(tr_l[i]).css("display", "table-row")
                if (!$(".sort").hasClass("complete")) { $(".sort").addClass("complete") }
            } else {
                if ($(".sort").hasClass("complete")) { $(".sort").removeClass("complete") }
                if (!reg.test($(tr_l[i]).find("td").get(0).getAttribute("data-select"))) {
                    $(tr_l[i]).css("display", "none")
                    mark++
                } else {
                    $(tr_l[i]).css("display", "table-row")
                }
            }
        }
        if (mark === tr_l.length) {
            $(".nofilter").css("display", "block")
        } else {
            $(".nofilter").css("display", "none")
        }
    }

    //点击筛选按钮
    $(document).on("click", ".filter.complete", function () {
        domainSelect($("#filter_text").val())
    })

    $("#filter_text").on("keydown", function (e) {
        if (e.keyCode == 13) {
            $('.filter.complete').click()
        }
    })
    //reverse_ip_result_ws
    //按ip重组
    function sort() {
        $(".domain").css("display") === "table" ? ($(".domain").css("display", "none"), $(".sort-table").css("display", "table"), $(".filter").removeClass("complete")) : ($(".domain").css("display", "table"), $(".sort-table").css("display", "none"), $(".filter").addClass("complete"))
    }

    //点击排序按钮
    $(document).on("click", ".sort.complete", function () {
        sort()
    })
});


