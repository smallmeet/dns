-- MySQL dump 10.13  Distrib 5.7.17, for Linux (x86_64)
--
-- Host: localhost    Database: subdomain
-- ------------------------------------------------------
-- Server version	5.7.17-0ubuntu0.16.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `system_admin_user`
--

DROP TABLE IF EXISTS `system_admin_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `system_admin_user` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `group_id` tinyint(1) NOT NULL DEFAULT '2' COMMENT '组id 0超级管理员 1管理员, 2用户',
  `username` varchar(128)  DEFAULT NULL COMMENT '用户名,最长20个中文',
  `password` char(32) DEFAULT NULL COMMENT '密码,md5',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `lastlogin_time` datetime DEFAULT NULL COMMENT '最后登录时间',
  `login_ip` char(32) DEFAULT NULL COMMENT '登录ip',
  `avatar` char(64) DEFAULT '' COMMENT '头像路径',
  `comment` char(255) DEFAULT '' COMMENT '备注',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
ALTER TABLE `subdomain`.`system_admin_user`
ADD UNIQUE INDEX `username_UNIQUE` (`username` ASC);

--
-- Dumping data for table `system_admin_user`
--

LOCK TABLES `system_admin_user` WRITE;
/*!40000 ALTER TABLE `system_admin_user` DISABLE KEYS */;
INSERT INTO `system_admin_user` VALUES (1,1,'admin','21232f297a57a5a743894a0e4a801fc3','2017-04-20 13:42:38','2017-04-20 13:42:38',NULL, '', ''),(2,0,'root','63a9f0ea7bb98050796b649e85481845','2017-04-20 13:42:38','2017-04-20 13:42:38',NULL,'', ''),(3,2,'tom','34b7da764b21d298ef307d04d8152dc5','2017-04-20 13:42:38','2017-04-20 13:42:38',NULL,'', '');
/*!40000 ALTER TABLE `system_admin_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `system_domain`
--

DROP TABLE IF EXISTS `system_domain`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `system_domain` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT COMMENT '域名id',
  `domain` varchar(64) NOT NULL COMMENT '域名',
  `domain_whois` text DEFAULT '' COMMENT '域名whois信息',
  `ns_records` text DEFAULT '' COMMENT 'NS 记录',
  `mx_records` text DEFAULT '' COMMENT 'MX 记录',
  PRIMARY KEY (`id`),
  UNIQUE (`domain`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_domain`
--

LOCK TABLES `system_domain` WRITE;
/*!40000 ALTER TABLE `system_domain` DISABLE KEYS */;
/*!40000 ALTER TABLE `system_domain` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `system_httphead`
--

DROP TABLE IF EXISTS `system_httphead`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `system_httphead` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `ip` int(4) unsigned NOT NULL COMMENT 'ip',
  `httphead` text NOT NULL COMMENT '域名banner',
  `pz` text COMMENT '旁站',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_httphead`
--

LOCK TABLES `system_httphead` WRITE;
/*!40000 ALTER TABLE `system_httphead` DISABLE KEYS */;
/*!40000 ALTER TABLE `system_httphead` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `system_subdomain_result`
--

DROP TABLE IF EXISTS `system_subdomain_result`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `system_subdomain_result` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `domain_id` int(10) NOT NULL,
  `subdomain` varchar(255) NOT NULL COMMENT '子域名',
  `ip` text NOT NULL COMMENT '子域名对应ip,可能多个结果',
  `location` text COMMENT '地理位置',
  `last_commit_time` datetime NOT NULL COMMENT '最后修改时间',
  `origin` varchar(32) NOT NULL COMMENT '来源',
  PRIMARY KEY (`id`),
--  KEY `system_domain` (`domain_id`),
  UNIQUE (`subdomain`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

/* 新增子域名状态字段 */
alter table `system_subdomain_result` add `state` varchar(10) default '';

--
-- Table structure for table `system_task_records`
--

DROP TABLE IF EXISTS `system_task_records`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `system_task_records` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `keywords` varchar(64) DEFAULT NULL COMMENT '任务关键字',
  `create_time` datetime DEFAULT NULL COMMENT '任务创建时间',
  `finish_time` datetime DEFAULT NULL COMMENT '完成时间',
  `state` int(1) unsigned NOT NULL DEFAULT '0' COMMENT '0 未取出, 1 已经取出未完成, 2 完成',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;


DROP TABLE IF EXISTS `system_domains`;
CREATE TABLE `system_domains` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT COMMENT '域名id',
  `domain` varchar(64) NOT NULL COMMENT '域名',
  PRIMARY KEY (`id`),
  UNIQUE (`domain`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `system_ips`;
CREATE TABLE `system_ips` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT COMMENT 'ip id',
  `ip` bigint(20) NOT NULL COMMENT 'ip',
  `web_info` varchar(1000) NOT NULL DEFAULT '' COMMENT 'web信息',
  `sync_time` datetime DEFAULT NULL COMMENT '同步时间,方便做阈值控制',
  `port_info` varchar(1000) NOT NULL DEFAULT '' COMMENT '端口信息',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `ipv4` varchar(128) NOT NULL DEFAULT '' COMMENT 'ip信息',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ip` (`ip`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `system_domain_and_ip`;
CREATE TABLE `system_domain_and_ip`(
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `ip_id` int(10) NOT NULL COMMENT 'ip id',
  `domain_id` int(10) NOT NULL COMMENT '域名 id',
  `url` text COMMENT '取出时的 url',
  `title` text COMMENT 'url 对应的 title',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE (`ip_id`, `domain_id`)
)ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
--
-- Dumping data for table `system_task_records`
--


/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2017-04-24 13:53:43


DROP TABLE IF EXISTS `system_events`;
CREATE TABLE `system_events` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `ip` bigint(20) NOT NULL DEFAULT 0 COMMENT 'ip的int信息',
  `ipv4` varchar(128) NOT NULL DEFAULT '' COMMENT 'ip信息',
  `domain` varchar(1000) NOT NULL DEFAULT '' COMMENT '域名信息',
  `state` tinyint(4) DEFAULT 0 COMMENT '状态,0:待开始，1:执行中，2:完成，-1:失败',
  `type_id` tinyint(4) DEFAULT 0 COMMENT '1:查询子域名信息 2:ip反查 3:域名及端口信息查询(包括端口,cms识别,head信息获取)',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `finish_time` datetime DEFAULT NULL COMMENT '完成时间',
  `is_delete` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否删除',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;





alter table system_domains add column cms varchar(200) not null default '' comment 'cms信息';
alter table system_domains add column head_info varchar(5000) not null default '' comment '头部信息';
alter table system_domains add column sync_time datetime default null comment '同步时间,方便做阈值控制';
alter table system_domains add column create_time datetime default null comment '创建时间';