$(function () {
    // console.log(config)
    var domainData = {}
    var statusFilter = 0;//当前用户选择状态
    var isFilter = false;//当前数据是否过滤
    var reg_domain = ""//domain table过滤正则str
    var reg_sort = ""//sort table过滤正则str
    var label_status = ["label-success", "label-warning", "label-danger"]
    setMap()

    //获取url参数
    var getQueryString = function (parm) {
        var reg = new RegExp("(^|&)" + parm + "=([^&]*)(&|$)"),
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
        var date = new Date()
        $(".table2excel").table2excel({
            exclude: ".noExl",
            name: "Excel Document Name",
            filename: "domains_" + date.getFullYear() + "-" + (date.getMouth + 1) + "-" + date.getDate(),
            exclude_img: true,
            exclude_links: true,
            exclude_inputs: true
        });
    });

    //webscoket
    // 192.168.1.172:8888/result_ws
    // var wsURI = 'ws://' + window.location.host + '/result_ws'
    var wsURI = env_config.sub_domain_result_ws
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
                    // console.log(JSON.stringify(data))
                    $("#subdomain").css("display", "block")
                    $("#download").css("display", "block")
                    $("#chart").css("display", "block")
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
                    // if (!$(".sort").hasClass("complete")) $(".sort").addClass("complete")
                    $(".pageloader3").css("display", "none")
                    break;

            }
            $("[data-toggle='tooltip']").tooltip();
        };
    };

    function start() {
        //向服务器发送请求  
        // var obj = { "domain": getQueryString("domain") }
        // console.log(config.test.domain)
        webSocket.send(JSON.stringify(env_config.domain));
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
                    <tr class="${isImportant(key)}">
                        <td>${whois_info[key] ? whois_info[key] : key}</td>
                        <td>${whois[key]}</td>
                    </tr>
                `
                $(".table-whois tbody").append(templateRow)
            }
        }
        if ($(".table-whois tbody").find("tr").length === 0) {
            $(".table-whois").css("display", "none")
            $(".more").css("display", "none")
            $(".nowhois").css("display", "block")
        }
    }

    function subdomain(data) {
        var subdomain = data.sub_domains
        var refreshData = {}
        var ipArr = []
        // if (!subdomain.length) {
        //     $(".table2excel").css("display", "none")
        //     $(".input-group").css("display", "none")
        //     $(".nofilter").css("display", "block")
        // }
        for (var i = 0; i < subdomain.length; i++) {
            // normal table
            var isShow = true
            if (isFilter) {
                var reg = new RegExp(reg_domain)
                if (!reg.test(subdomain[i].sub_domain)) isShow = false
            }
            var templateRow = `
                <tr style="display:${isShow ? 'table-row' : 'none'}">
                    <td data-select="${subdomain[i].sub_domain}" class="col-md-3">${subdomain[i].sub_domain}<br><span class="cms cms-server" data-toggle="tooltip" title="查看CMS">Nginx</span> <span class="cms cms-pdt" data-toggle="tooltip" title="查看CMS">thinkphp</span> <br></td>
                    <td>${subdomain[i].last_commit_time}</td>
                    <td>${modalStr(subdomain[i].ip, subdomain[i].sub_domain, subdomain[i].location.toLocaleLowerCase())}</td>
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
                            <td><i data-toggle='tooltip' title='端口扫描' data-parent="${subdomain[i].sub_domain}" data-ip="${ip_l[j]}" class='fa fa-eye'></i> <span data-search-ip="${ip_l[j]}">${ip_l[j]}</span> ${subdomain[i].location === "" ? `` : `<span class="flag flag-${subdomain[i].location.split(",")[j].toLocaleLowerCase()}"></span>`}<br></td>
                            <td>${subdomain[i].last_commit_time}</td>
                            <td data-select="${subdomain[i].sub_domain}" class="col-md-3"><span class="sort-domain">${subdomain[i].sub_domain}</span></td>
                            <td><div data-domain=${subdomain[i].sub_domain}></div></td>
                        </tr>
                    `
                        $(".sort-table tbody").append(sortTempRow)
                    } else {
                        $($("[data-sort-ip='" + subdomain[i].ip + "']").find("td").get(2)).append(`<span  class="sort-domain">${subdomain[i].sub_domain}</span>`)
                        $($("[data-sort-ip='" + subdomain[i].ip + "']").find("td").get(3)).append(`<div data-domain=${subdomain[i].sub_domain}></div>`)
                    }
                }
            }
        }
        // console.log(refreshData)
        refresh(refreshData)
        // domainSelect()
    }

    function status(data) {
        switch (data.state) {
            case -1:
            case 1:
            case 2:
            case 3:
                $("[data-domain='" + data.domain + "']").append(`<span class="label label-warning server-status" data-toggle="tooltip" title="无法访问"><i class="fa  fa-unlink"></i></span>`)

                break;
            case 0:
                $("[data-domain='" + data.domain + "']").append(`<span class="label label-danger server-status" data-toggle="tooltip" title="不存在"><i class="fa  fa-ban"></i></span>`)

                break;
            case 4:
                $("[data-domain='" + data.domain + "']").append(`<span class="label label-success server-status" data-toggle="tooltip" title="正常"><i class="fa  fa-check"></i></span>`)

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

    function modalStr(ip, domain, location) {
        if (ip === "") {
            return "无"
        } else {
            var ip_l = ip.split(",")
            var location_l = location.split(",")
            // console.log(locat)
            var str = ""
            for (var i = 0; i < ip_l.length; i++) {
                str += "<i data-toggle='tooltip' title='端口扫描' data-parent=" + domain + " data-ip=" + ip_l[i] + " class='fa fa-eye'></i> <span data-search-ip='" + ip_l[i] + "'>" + ip_l[i] + "</span> <span class='flag flag-" + location_l[i] + "'></span><br>"
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
        // console.log(data)
        $(".port-info").empty()
        $(".more-info").empty()

        var portInfo_temp = `
            <p>IP地址: ${data.ip_info.ip.ip} <a href="${data.ip_info.ip.ip}"><i class="fa fa-external-link" style="color:lightblue;"></i></a></p>
                    <p>协议: ${data.domain_info.cms ? data.domain_info.cms.cms : ``}</p>
                    <p>CMS信息: ${data.ip_info.web_info ? data.ip_info.ip.web_info.product : ``}</p>
                    <p>产品: ${data.ip_info.web_info ? data.ip_info.ip.web_info.name : ``}</p>
                    <p>产品名: ${data.ip_info.web_info ? data.ip_info.ip.web_info.extrainfo : ``}</p>
                    <p>版本号: ${data.ip_info.web_info ? data.ip_info.ip.web_info.version : ``}</p>
                    <p>更新时间: ${data.ip_info.sync_time ? data.domain_info.sync_time : ``}</p>
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
            // console.log(siteObj)
            svgJson.children[2].children.push(siteObj)
        }

        // console.log(JSON.stringify(svgJson))
        svgPaint(JSON.stringify(svgJson))
    }

    //ip 反查
    $(document).on("click", "[data-search-ip]", function () {
        window.location.href = "/reverse_ip_lookup_new?ip=" + $(this).attr("data-search-ip")
    })

    //域名 url title
    //筛选域名
    function domainSelect(str) {
        if ($(".domain").css("display") !== "none") {
            console.log(1)
            statusFilter = 0
            trigger_status()
            str === "" ? isFilter = false : isFilter = true
            var reg_format = /[\s_\u4E00-\u9FA5\uF900-\uFA2D]/
            if (reg_format.test(str)) {
                myalert("域名不能包含空格、下划线和中文", "tipwrong")
                return;
            }
        } else {
            console.log(2)
            var reg_format = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])(\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])){3}$/
            if (str !== "" && !reg_format.test(str)) {
                myalert("请输入合法的域名", "tipwrong")
                return;
            }
        }
        filter(str)
    }

    //点击筛选按钮
    $(document).on("click", ".filter.complete", function () {
        if ($(".domain").css("display") !== "none") {
            reg_domain = $("#filter_text").val()
        } else {
            reg_sort = $("#filter_text").val()
        }
        
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
        $(".domain").css("display") === "table" ? ($(".domain").css("display", "none"), $(".sort-table").css("display", "table"), $("#filter_text").attr("placeholder", "请输入要查询的IP"), $("#filter_text").val(reg_sort)) : ($(".domain").css("display", "table"), $(".sort-table").css("display", "none"), $("#filter_text").attr("placeholder", "请输入域名允许的字符"), $("#filter_text").val(reg_domain))
    }

    //点击排序按钮
    $(document).on("click", ".sort.complete", function () {
        sort()
    })

    //whois important
    function isImportant(key) {
        if (key === "updated_date" || key === "expiration_date" || key === "address" || key === "whois_server" || key === "name_servers" || key === "emails") {
            // return "important"
        } else {
            return "not-important"
        }
    }

    //more whois 
    $(".more").on("click", function () {
        $(".not-important").removeClass("not-important")
        $(".more").css("display", "none")
    })

    //查看图片
    $("#chart").on("click", function () {
        var obj = {
            "name": env_config.domain.domain,
            "children": []
        }

        var ip_list = $("[data-sort-ip]")

        for (var i = 0; i < ip_list.length; i++) {
            var ipObj = {
                "name": $(ip_list[i]).attr("data-sort-ip"),
                "children": []
            }
            var domainDOM = $(ip_list[i]).find("div")
            for (var j = 0; j < domainDOM.length; j++) {
                var tempObj = {
                    "name": $(domainDOM[j]).attr("data-domain")
                }
                ipObj.children.push(tempObj)
            }
            obj.children.push(ipObj)
        }
        window.localStorage["chartObj"] = JSON.stringify(obj)
    })

    //domain status
    $("#domain-status").on("click", function () {
        isFilter ? filter(reg_domain, statusFilter) : filter("", statusFilter)
        if (statusFilter === 3) {
            statusFilter = 0
        } else {
            statusFilter++
        }
        trigger_status()
    })

    //filter rules 
    function filter(str, status) {
        console.log(str)
        var mark = 0;
        var reg = new RegExp(str)
        if ($(".domain").css("display") !== "none") {
            var tr_domain = $(".domain tbody tr")

            for (var i = 0; i < tr_domain.length; i++) {
                if (reg.test($(tr_domain[i]).find("td").get(0).getAttribute("data-select"))) {
                    // console.log(status === undefined)
                    if (status !== undefined) {
                        if (status === 3) {
                            $(tr_domain[i]).css("display", "table-row")
                            mark++
                        } else {
                            if (!$(tr_domain[i]).find(".server-status").hasClass(label_status[status])) {
                                $(tr_domain[i]).css("display", "none")
                            } else {
                                $(tr_domain[i]).css("display", "table-row")
                                mark++
                            }
                        }
                    } else {
                        $(tr_domain[i]).css("display", "table-row")
                        mark++
                    }
                } else {
                    $(tr_domain[i]).css("display", "none")
                }
            }
        } else {
            var tr_sort = $(".sort-table tbody tr")

            for (var i = 0; i < tr_sort.length; i++) {
                if (str === "") {
                    $(tr_sort[i]).css("display", "table-row")
                    mark++
                } else {
                    if (reg.test($(tr_sort[i]).attr("data-sort-ip"))) {
                        $(tr_sort[i]).css("display", "table-row")
                        mark++
                    } else {
                        $(tr_sort[i]).css("display", "none")
                    }
                }
            }
        }
        if (mark === 0) {
            $(".nofilter").css("display", "block")
        } else {
            $(".nofilter").css("display", "none")
        }
    }

    //修改表头状态
    function trigger_status() {
        switch (statusFilter) {
            case 0:
                $(".status-info").html(" 全部")
                $(".status-info").css("color", "white")
                break;
            case 1:
                $(".status-info").html(" 正常")
                $(".status-info").css("color", "#5cb85c")
                break;
            case 2:
                $(".status-info").html(" 连接失败")
                $(".status-info").css("color", "#f0ad4e")
                break;
            case 3:
                $(".status-info").html(" 不存在")
                $(".status-info").css("color", "#d9534f")
                break;
        }
    }
});


