子域名前后端接口
======

只有一个接口
------
```
/result_async
```

参数
------
- `domain` 目标域名
- `type` 类型，候选词如下：
	- `sub_domain` 子域名结果
	- `domain_state` 域名服务状态
	- `domain_detail` 域名详情
	- `ip_history` 历史 Ip 解析记录

返回值
------

### 子域名结果
```json
{
	"type": "sub_domain",
	"domain": 域名,
	"task_state": 任务状态 0 排队 | 1 正在运行 | 2 运行结束,
	"sub_domains": [
		{
			"sub_domain": 子域名,
			"ip": 子域名对应 IP,
			"location": IP 对应地理位置,
			"origin": 结果来源
		},
		...
	]
}
```

### 域名服务状态
```json
{
	"type": "domain_state",
	"domain": 域名,
	"state": -1 未知错误 | 0 没有 A 记录 | 1 端口未开启 | 2 连接超时 | 3 非 HTTP 服务 | 4 服务正常
}
```

### 域名详情
```json
{
	"type": "domain_detail",
	"domain": 域名,
	"ns_records": [
		{
			"name": Name Server 名称,
			"ip": Name Server Ip
		},
		...
	],
	"mx_records": [
		{
			"name": Mail Exchanger 记录名称,
			"ip": Mail Exchanger 服务器 Ip
		},
		...
	}],
	"whois": {
		"domain_name": 域名,
		"whois_server": Whois 服务器,
		"name_servers": 域名服务器,
		"status": 状态,
		"name": 名字,
		"emails": 邮箱,
		"country": 国家,
		"state": 州 / 省,
		"city": 城市,
		"address": 地址,
		"zipcode": 邮政编码,
		"org": 组织,
		"dnssec": DNS安全扩展,
		"creation_date": 创建时间,
		"updated_date": 更新时间,
		"expiration_date": 过期时间,
		"registrar": 注册商,
		"referral_url": 推广 Url
	}
}
```

### 历史解析记录
```json
{
	"type": "ip_history",
	"domain": 域名,
	"history": [
		{
			"ip": ip,
			"start_date": 开始年月日,
			"end_date": 结束年月日
		},
		...
	]
}
```


### 扫描信息

```

{
	'type':'scan_info',
    "domain_info":{
        "domain":"hy2.kq88.com",
        "cms":{
            "url":"www.jinwulab.com",
            "md5":"1870a829d9bc69abf500eca6f00241fe",
            "cms":"wordpress", // cms信息
            "error":"no"
        },
        "sync_time":"2017-06-14-17"
    },
    "ip_info":{
        "ip":{
            "ip":"42.121.57.135",
            "web_info":{
                "product":"Apache httpd", //产品
                "name":"http",            //协议
                "extrainfo":"(CentOS) PHP/5.6.29", //产品名
                "reason":"syn-ack",
                "cpe":"cpe:/a:apache:http_server:2.4.6",
                "state":"open",
                "version":"2.4.6",  //版本号
                "conf":"10"
            },
            "port_info":"{"source": "hackertarget", "dataset": "PORT STATE SERVICE VERSION\n80/tcp open http Apache httpd 2.4.6 ((CentOS) PHP/5.6.29)"}"
        }
    },
    "type":"scan_info"
}


```