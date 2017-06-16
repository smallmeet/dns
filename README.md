子域名查询系统
======

Overview
------

查询各级子域名（通常是二级域名）。查询方式为：调接口、页面爬虫、https证书、爆破。  
现有接口：
- alexa
- ilinks
- ip138
- crt.sh
- sitedossier (有验证码)
- threatcrowd
- threatminer
- bugbank
- hack_target
- netcraft
- juanluo
- 百度
- bing

Installation
-------

> sudo apt-get install mysql-server  
> sudo apt-get install redis-server  
> sudo apt-get install python-setuptools  
> sudo apt-get install libmysqlclient-dev  
> sudo apt-get install python-dev  
> sudo easy_install pip

MySQL 导入表结构
> mysql -uUSER -pPASS -e "drop database if exists subdomain; create database subdomain;"  
> mysql -uUSER -pPASS subdomain < data/subdomain.sql

Python 包
> sudo pip install -r requirements.txt

Usage
------

手动启动，worker 可启动多个。
> python server.py  
> python utils/worker.log

脚本启动
> ./launch.sh

Package structure
------

- api  原来子域名命令行版本
	- config 配置文件
	- dict 爆破字典
	- utils 各种接口，接口文件命名规则为 aaa_bbb.py，类名为 AaaBbb
- config Web 系统的配置文件
- data 数据库导出文件
- handlers 处理 Http 请求的类
- static 静态文件目录
	- css
	- fonts
	- imgs
	- js
- templates HTML 模板目录
- utils 一些工具
	- banner.py 获取一个 Ip 的指定端口 banner 信息
	- config.py 读取配置类
	- g.py 多线程全局锁
	- identicon.py 用来生成头像
	- iplookup.py 查询 Ip 的地理位置信息
    - taskloader.py 任务加载器
	- worker.py 任务执行器，从队列中取任务，并执行
	- utils.py 一些工具

Worker flow chart
------

![描述](http://oq2vxplra.bkt.clouddn.com/flow_chart%20%281%29.png)
