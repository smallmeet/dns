(function($) {
    'use strict';

    //获取url参数
    let getQueryString = function(parm) {
        let reg = new RegExp("(^|&)"+ parm +"=([^&]*)(&|$)"),
            r = window.location.search.substr(1).match(reg);
        return r ? unescape(decodeURI(decodeURI(r[2]))) : null;
    };

    let moduleGetAsyncResult = {
        'data': [],
        'init': function() {
            console.log('init');
            this.interval = 500;
            this.isStoped = false;
            this.bindViews();
        },
        'bindViews': function() {
            this.$table = $('#domain-dl');
        },
        'startFetch': function() {
            $.get('/reverse_ip_result_async', {
                'target': getQueryString('target'),
                'last': this.data.length
            }, this.callback.bind(this), 'json');

            if (!this.isStoped) {
                this.timerId = window.setTimeout(this.startFetch.bind(this), this.interval);
            }
        },
        'stop': function() {
            this.isStoped = true;
            window.clearTimeout(this.timerId);
        },
        'callback': function(data) {
            console.log(data);
            if (2 === data['task_state'] && (!data['data'] || 0 === data['data'].length)) {
                console.log('stop');
                this.isStoped = true;
                $('.deep-bar').css('display', 'none');
            }
            data['data'] && data['data'].forEach(function(e) {
                this.data.push(e);
                if (0 !== $('[data-ip="' + e['ip'] + '"]').length) {
                    let $dt = $('[data-ip="' + e['ip'] + '"]');
                    let template = '';
                    e['data'].forEach(function(ee) {
                        if(0 === $('dd[data-domain="' + ee['domain'] + '"]')) {
                            template += `<dd data-domain="${ee['domain']}"><!--<span>${ee['domain']}</span>--><a style="padding-left: 12px;" href="${ee['url']}">${ee['url']}</a><span style="padding-left: 12px;">${ee['title']}</span></dd>`;
                        }
                    });
                    $dt.after(template);
                } else {
                    let template = `<dt data-ip="${e['ip']}"><span>${e['ip']}</span><span style="padding-left: 6px;">(${e['data'].length})</span></dt>`;
                    e['data'].forEach(function(ee) {
                        template += `<dd data-domain="${ee['domain']}"><!--<span>${ee['domain']}</span>--><a style="padding-left: 12px;" href="${ee['url']}">${ee['url']}</a><span style="padding-left: 12px;">${ee['title']}</span></dd>`;
                    });
                    this.$table.append(template);
                }
            }.bind(this));
            console.dir(this.data);
        }
    };
    moduleGetAsyncResult.init();
    moduleGetAsyncResult.startFetch();
}) (jQuery);

