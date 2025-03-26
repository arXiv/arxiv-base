-- MySQL dump 10.13  Distrib 5.7.20, for Linux (x86_64)
--
-- Host: localhost    Database: arXiv
-- ------------------------------------------------------
-- Server version	5.7.20

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
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

-- SET @@GLOBAL.GTID_PURGED='2d19f914-b050-11e7-95e6-005056a34791:1-572482257';

--
-- Table structure for table `Subscription_UniversalInstitution`
--

DROP TABLE IF EXISTS `Subscription_UniversalInstitution`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Subscription_UniversalInstitution` (
  `resolver_URL` varchar(255) DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `label` varchar(255) DEFAULT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `alt_text` varchar(255) DEFAULT NULL,
  `link_icon` varchar(255) DEFAULT NULL,
  `note` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Subscription_UniversalInstitutionContact`
--

DROP TABLE IF EXISTS `Subscription_UniversalInstitutionContact`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Subscription_UniversalInstitutionContact` (
  `email` varchar(255) DEFAULT NULL,
  `sid` int(11) NOT NULL,
  `active` tinyint(4) DEFAULT '0',
  `contact_name` varchar(255) DEFAULT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `phone` varchar(255) DEFAULT NULL,
  `note` varchar(2048) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `sid` (`sid`),
  CONSTRAINT `Subscription_Institution_Contact_Universal` FOREIGN KEY (`sid`) REFERENCES `Subscription_UniversalInstitution` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Subscription_UniversalInstitutionIP`
--

DROP TABLE IF EXISTS `Subscription_UniversalInstitutionIP`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Subscription_UniversalInstitutionIP` (
  `sid` int(11) NOT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `exclude` tinyint(4) DEFAULT '0',
  `end` bigint(20) NOT NULL,
  `start` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `sid` (`sid`),
  KEY `ip` (`start`,`end`),
  KEY `end` (`end`),
  KEY `start` (`start`),
  CONSTRAINT `Subscription_Institution_IP_Universal` FOREIGN KEY (`sid`) REFERENCES `Subscription_UniversalInstitution` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_admin_log`
--

DROP TABLE IF EXISTS `arXiv_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `logtime` varchar(24) DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `paper_id` varchar(20) DEFAULT NULL,
  `username` varchar(20) DEFAULT NULL,
  `host` varchar(64) DEFAULT NULL,
  `program` varchar(20) DEFAULT NULL,
  `command` varchar(20) DEFAULT NULL,
  `logtext` text,
  `document_id` mediumint(8) unsigned DEFAULT NULL,
  `submission_id` int(11) DEFAULT NULL,
  `notify` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `arXiv_admin_log_idx_submission_id` (`submission_id`),
  KEY `arXiv_admin_log_idx_command` (`command`),
  KEY `arXiv_admin_log_idx_paper_id` (`paper_id`),
  KEY `arXiv_admin_log_idx_username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_admin_metadata`
--

DROP TABLE IF EXISTS `arXiv_admin_metadata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_admin_metadata` (
  `metadata_id` int(11) NOT NULL AUTO_INCREMENT,
  `document_id` mediumint(8) unsigned DEFAULT NULL,
  `paper_id` varchar(64) DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `updated` datetime DEFAULT NULL,
  `submitter_name` varchar(64) DEFAULT NULL,
  `submitter_email` varchar(64) DEFAULT NULL,
  `history` text,
  `source_size` int(11) DEFAULT NULL,
  `source_type` varchar(12) DEFAULT NULL,
  `title` text,
  `authors` text,
  `category_string` varchar(255) DEFAULT NULL,
  `comments` text,
  `proxy` varchar(255) DEFAULT NULL,
  `report_num` text,
  `msc_class` varchar(255) DEFAULT NULL,
  `acm_class` varchar(255) DEFAULT NULL,
  `journal_ref` text,
  `doi` varchar(255) DEFAULT NULL,
  `abstract` text,
  `license` varchar(255) DEFAULT NULL,
  `version` int(11) NOT NULL DEFAULT '1',
  `modtime` int(10) DEFAULT NULL,
  `is_current` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`metadata_id`),
  UNIQUE KEY `pidv` (`paper_id`,`version`),
  KEY `id` (`metadata_id`),
  KEY `document_id` (`document_id`),
  CONSTRAINT `meta_doc_fk` FOREIGN KEY (`document_id`) REFERENCES `arXiv_documents` (`document_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_admin_state`
--

DROP TABLE IF EXISTS `arXiv_admin_state`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_admin_state` (
  `document_id` int(11) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `abs_timestamp` int(11) DEFAULT NULL,
  `src_timestamp` int(11) DEFAULT NULL,
  `state` enum('pending','ok','bad') NOT NULL DEFAULT 'pending',
  `admin` varchar(32) DEFAULT NULL,
  `comment` varchar(255) DEFAULT NULL,
  UNIQUE KEY `document_id` (`document_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_archive_category`
--

DROP TABLE IF EXISTS `arXiv_archive_category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_archive_category` (
  `archive_id` varchar(16) NOT NULL DEFAULT '',
  `category_id` varchar(32) NOT NULL,
  PRIMARY KEY (`archive_id`,`category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_archive_def`
--

DROP TABLE IF EXISTS `arXiv_archive_def`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_archive_def` (
  `archive` varchar(16) NOT NULL DEFAULT '',
  `name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`archive`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_archive_group`
--

DROP TABLE IF EXISTS `arXiv_archive_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_archive_group` (
  `archive_id` varchar(16) NOT NULL DEFAULT '',
  `group_id` varchar(16) NOT NULL DEFAULT '',
  PRIMARY KEY (`archive_id`,`group_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_archives`
--

DROP TABLE IF EXISTS `arXiv_archives`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_archives` (
  `archive_id` varchar(16) NOT NULL DEFAULT '',
  `in_group` varchar(16) NOT NULL DEFAULT '',
  `archive_name` varchar(255) NOT NULL DEFAULT '',
  `start_date` varchar(4) NOT NULL DEFAULT '',
  `end_date` varchar(4) NOT NULL DEFAULT '',
  `subdivided` int(1) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`archive_id`),
  KEY `in_group` (`in_group`),
  CONSTRAINT `0_576` FOREIGN KEY (`in_group`) REFERENCES `arXiv_groups` (`group_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_author_ids`
--

DROP TABLE IF EXISTS `arXiv_author_ids`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_author_ids` (
  `user_id` int(4) unsigned NOT NULL,
  `author_id` varchar(50) NOT NULL,
  `updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  KEY `author_id` (`author_id`),
  CONSTRAINT `arXiv_author_ids_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_aws_config`
--

DROP TABLE IF EXISTS `arXiv_aws_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_aws_config` (
  `domain` varchar(75) NOT NULL,
  `keyname` varchar(60) NOT NULL,
  `value` varchar(150) DEFAULT NULL,
  PRIMARY KEY (`domain`,`keyname`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_aws_files`
--

DROP TABLE IF EXISTS `arXiv_aws_files`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_aws_files` (
  `type` varchar(10) NOT NULL DEFAULT '',
  `filename` varchar(100) NOT NULL DEFAULT '',
  `md5sum` varchar(50) DEFAULT NULL,
  `content_md5sum` varchar(50) DEFAULT NULL,
  `size` int(11) DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL,
  `yymm` varchar(4) DEFAULT NULL,
  `seq_num` int(11) DEFAULT NULL,
  `first_item` varchar(20) DEFAULT NULL,
  `last_item` varchar(20) DEFAULT NULL,
  `num_items` int(11) DEFAULT NULL,
  PRIMARY KEY (`filename`),
  KEY `type` (`type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_bad_pw`
--

DROP TABLE IF EXISTS `arXiv_bad_pw`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_bad_pw` (
  `user_id` int(10) unsigned NOT NULL DEFAULT '0',
  KEY `user_id` (`user_id`),
  CONSTRAINT `0_601` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_bib_feeds`
--

DROP TABLE IF EXISTS `arXiv_bib_feeds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_bib_feeds` (
  `bib_id` mediumint(8) NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL DEFAULT '',
  `priority` tinyint(1) NOT NULL DEFAULT '0',
  `uri` varchar(255) DEFAULT NULL,
  `identifier` varchar(255) DEFAULT NULL,
  `version` varchar(255) DEFAULT NULL,
  `strip_journal_ref` tinyint(1) NOT NULL DEFAULT '0',
  `concatenate_dupes` int(11) DEFAULT NULL,
  `max_updates` int(11) DEFAULT NULL,
  `email_errors` varchar(255) DEFAULT NULL,
  `prune_ids` text,
  `prune_regex` text,
  `enabled` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`bib_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_bib_updates`
--

DROP TABLE IF EXISTS `arXiv_bib_updates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_bib_updates` (
  `update_id` mediumint(8) NOT NULL AUTO_INCREMENT,
  `document_id` mediumint(8) NOT NULL DEFAULT '0',
  `bib_id` mediumint(8) NOT NULL DEFAULT '0',
  `updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `journal_ref` text,
  `doi` text,
  PRIMARY KEY (`update_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_black_email`
--

DROP TABLE IF EXISTS `arXiv_black_email`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_black_email` (
  `pattern` varchar(64) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_block_email`
--

DROP TABLE IF EXISTS `arXiv_block_email`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_block_email` (
  `pattern` varchar(64) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_bogus_countries`
--

DROP TABLE IF EXISTS `arXiv_bogus_countries`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_bogus_countries` (
  `user_id` int(10) unsigned NOT NULL DEFAULT '0',
  `country_name` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_bogus_subject_class`
--

DROP TABLE IF EXISTS `arXiv_bogus_subject_class`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_bogus_subject_class` (
  `document_id` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `category_name` varchar(255) NOT NULL DEFAULT '',
  KEY `document_id` (`document_id`),
  CONSTRAINT `0_604` FOREIGN KEY (`document_id`) REFERENCES `arXiv_documents` (`document_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_categories`
--

DROP TABLE IF EXISTS `arXiv_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_categories` (
  `archive` varchar(16) NOT NULL DEFAULT '',
  `subject_class` varchar(16) NOT NULL DEFAULT '',
  `definitive` int(1) NOT NULL DEFAULT '0',
  `active` int(1) NOT NULL DEFAULT '0',
  `category_name` varchar(255) DEFAULT NULL,
  `endorse_all` enum('y','n','d') NOT NULL DEFAULT 'd',
  `endorse_email` enum('y','n','d') NOT NULL DEFAULT 'd',
  `papers_to_endorse` smallint(5) unsigned NOT NULL DEFAULT '0',
  `endorsement_domain` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`archive`,`subject_class`),
  KEY `endorsement_domain` (`endorsement_domain`),
  CONSTRAINT `0_578` FOREIGN KEY (`archive`) REFERENCES `arXiv_archives` (`archive_id`),
  CONSTRAINT `0_753` FOREIGN KEY (`endorsement_domain`) REFERENCES `arXiv_endorsement_domains` (`endorsement_domain`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_category_def`
--

DROP TABLE IF EXISTS `arXiv_category_def`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_category_def` (
  `category` varchar(32) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_check_responses`
--

DROP TABLE IF EXISTS `arXiv_check_responses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_check_responses` (
  `check_response_id` int(11) NOT NULL AUTO_INCREMENT,
  `check_result_id` int(11) NOT NULL,
  `user_id` int(10) unsigned NOT NULL,
  `ok` tinyint(1) NOT NULL,
  `persist_response` tinyint(1) NOT NULL DEFAULT '0',
  `created` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `message` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`check_response_id`),
  KEY `check_responses_result_index` (`check_result_id`),
  KEY `check_responses_user_index` (`user_id`),
  CONSTRAINT `check_responses_results_fk` FOREIGN KEY (`check_result_id`) REFERENCES `arXiv_check_results` (`check_result_id`),
  CONSTRAINT `check_responses_user_fk` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_check_result_views`
--

DROP TABLE IF EXISTS `arXiv_check_result_views`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_check_result_views` (
  `check_result_view_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(40) NOT NULL,
  `description` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`check_result_view_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_check_results`
--

DROP TABLE IF EXISTS `arXiv_check_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_check_results` (
  `check_result_id` int(11) NOT NULL AUTO_INCREMENT,
  `submission_id` int(11) NOT NULL,
  `data_version` int(11) NOT NULL DEFAULT '0',
  `metadata_version` int(11) NOT NULL DEFAULT '0',
  `check_id` int(11) NOT NULL,
  `user_id` int(10) unsigned NOT NULL,
  `ok` tinyint(1) NOT NULL,
  `created` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `message` varchar(40) DEFAULT NULL,
  `data` varchar(2000) DEFAULT NULL,
  PRIMARY KEY (`check_result_id`),
  KEY `check_results_submission_index` (`submission_id`),
  KEY `check_results_check_index` (`check_id`),
  KEY `check_results_user_index` (`user_id`),
  CONSTRAINT `check_results_checks_fk` FOREIGN KEY (`check_id`) REFERENCES `arXiv_checks` (`check_id`),
  CONSTRAINT `check_results_sub_fk` FOREIGN KEY (`submission_id`) REFERENCES `arXiv_submissions` (`submission_id`),
  CONSTRAINT `check_results_user_fk` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_check_roles`
--

DROP TABLE IF EXISTS `arXiv_check_roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_check_roles` (
  `check_role_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(40) NOT NULL,
  `description` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`check_role_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_check_targets`
--

DROP TABLE IF EXISTS `arXiv_check_targets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_check_targets` (
  `check_target_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(40) NOT NULL,
  `description` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`check_target_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_checks`
--

DROP TABLE IF EXISTS `arXiv_checks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_checks` (
  `check_id` int(11) NOT NULL AUTO_INCREMENT,
  `check_target_id` int(11) NOT NULL,
  `check_role_id` int(11) NOT NULL,
  `check_result_view_id` int(11) NOT NULL DEFAULT '1',
  `name` varchar(40) NOT NULL,
  `description` varchar(200) DEFAULT NULL,
  `enable_check` tinyint(1) NOT NULL DEFAULT '0',
  `enable_hold` tinyint(1) NOT NULL DEFAULT '0',
  `enable_queue` tinyint(1) NOT NULL DEFAULT '0',
  `retry_minutes` smallint(6) NOT NULL DEFAULT '0',
  `optional` tinyint(1) NOT NULL DEFAULT '1',
  `persist_response` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`check_id`),
  KEY `checks_content_fk` (`check_target_id`),
  KEY `checks_roles_fk` (`check_role_id`),
  KEY `checks_result_views_fk` (`check_result_view_id`),
  CONSTRAINT `checks_content_fk` FOREIGN KEY (`check_target_id`) REFERENCES `arXiv_check_targets` (`check_target_id`),
  CONSTRAINT `checks_result_views_fk` FOREIGN KEY (`check_result_view_id`) REFERENCES `arXiv_check_result_views` (`check_result_view_id`),
  CONSTRAINT `checks_roles_fk` FOREIGN KEY (`check_role_id`) REFERENCES `arXiv_check_roles` (`check_role_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_control_holds`
--

DROP TABLE IF EXISTS `arXiv_control_holds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_control_holds` (
  `hold_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `control_id` int(10) unsigned NOT NULL DEFAULT '0',
  `hold_type` enum('submission','cross','jref') NOT NULL DEFAULT 'submission',
  `hold_status` enum('held','extended','accepted','rejected') NOT NULL DEFAULT 'held',
  `hold_reason` varchar(255) NOT NULL DEFAULT '',
  `hold_data` varchar(255) NOT NULL DEFAULT '',
  `origin` enum('auto','user','admin','moderator') NOT NULL DEFAULT 'auto',
  `placed_by` int(10) unsigned DEFAULT NULL,
  `last_changed_by` int(10) unsigned DEFAULT NULL,
  PRIMARY KEY (`hold_id`),
  UNIQUE KEY `control_id` (`control_id`,`hold_type`),
  KEY `hold_type` (`hold_type`),
  KEY `hold_status` (`hold_status`),
  KEY `hold_reason` (`hold_reason`),
  KEY `origin` (`origin`),
  KEY `placed_by` (`placed_by`),
  KEY `last_changed_by` (`last_changed_by`),
  CONSTRAINT `arXiv_control_holds_ibfk_1` FOREIGN KEY (`placed_by`) REFERENCES `tapir_users` (`user_id`),
  CONSTRAINT `arXiv_control_holds_ibfk_2` FOREIGN KEY (`last_changed_by`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_cross_control`
--

DROP TABLE IF EXISTS `arXiv_cross_control`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_cross_control` (
  `control_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `document_id` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `version` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `desired_order` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `user_id` int(10) unsigned NOT NULL DEFAULT '0',
  `status` enum('new','frozen','published','rejected') NOT NULL DEFAULT 'new',
  `flag_must_notify` enum('0','1') DEFAULT '1',
  `archive` varchar(16) NOT NULL DEFAULT '',
  `subject_class` varchar(16) NOT NULL DEFAULT '',
  `request_date` int(10) unsigned NOT NULL DEFAULT '0',
  `freeze_date` int(10) unsigned NOT NULL DEFAULT '0',
  `publish_date` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`control_id`),
  KEY `status` (`status`),
  KEY `freeze_date` (`freeze_date`),
  KEY `document_id` (`document_id`,`version`),
  KEY `archive` (`archive`,`subject_class`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `arXiv_cross_control_ibfk_1` FOREIGN KEY (`document_id`) REFERENCES `arXiv_documents` (`document_id`),
  CONSTRAINT `arXiv_cross_control_ibfk_2` FOREIGN KEY (`archive`, `subject_class`) REFERENCES `arXiv_categories` (`archive`, `subject_class`),
  CONSTRAINT `arXiv_cross_control_ibfk_3` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_datacite_dois`
--

DROP TABLE IF EXISTS `arXiv_datacite_dois`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_datacite_dois` (
  `doi` varchar(255) NOT NULL,
  `account` enum('test','prod') DEFAULT NULL,
  `metadata_id` int(11) NOT NULL,
  `paper_id` varchar(64) NOT NULL,
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`doi`),
  UNIQUE KEY `account_paper_id` (`account`,`paper_id`),
  KEY `metadata_id` (`metadata_id`),
  CONSTRAINT `arXiv_datacite_dois_ibfk_1` FOREIGN KEY (`metadata_id`) REFERENCES `arXiv_metadata` (`metadata_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_dblp`
--

DROP TABLE IF EXISTS `arXiv_dblp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_dblp` (
  `document_id` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `url` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`document_id`),
  CONSTRAINT `arXiv_DBLP_cdfk1` FOREIGN KEY (`document_id`) REFERENCES `arXiv_documents` (`document_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_dblp_authors`
--

DROP TABLE IF EXISTS `arXiv_dblp_authors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_dblp_authors` (
  `author_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`author_id`),
  UNIQUE KEY `author_id` (`author_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_dblp_document_authors`
--

DROP TABLE IF EXISTS `arXiv_dblp_document_authors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_dblp_document_authors` (
  `document_id` mediumint(8) unsigned NOT NULL,
  `author_id` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `position` tinyint(4) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`document_id`,`author_id`),
  KEY `document_id` (`document_id`),
  KEY `author_id` (`author_id`),
  CONSTRAINT `arXiv_DBLP_abfk1` FOREIGN KEY (`document_id`) REFERENCES `arXiv_documents` (`document_id`),
  CONSTRAINT `arXiv_DBLP_ibfk2` FOREIGN KEY (`author_id`) REFERENCES `arXiv_dblp_authors` (`author_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_demographics`
--

DROP TABLE IF EXISTS `arXiv_demographics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_demographics` (
  `user_id` int(10) unsigned NOT NULL DEFAULT '0',
  `country` char(2) NOT NULL DEFAULT '',
  `affiliation` varchar(255) NOT NULL DEFAULT '',
  `url` varchar(255) NOT NULL DEFAULT '',
  `type` smallint(5) unsigned DEFAULT NULL,
  `archive` varchar(16) DEFAULT NULL,
  `subject_class` varchar(16) DEFAULT NULL,
  `original_subject_classes` varchar(255) NOT NULL DEFAULT '',
  `flag_group_physics` int(1) unsigned DEFAULT NULL,
  `flag_group_math` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_group_cs` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_group_nlin` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_proxy` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_journal` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_xml` int(1) unsigned NOT NULL DEFAULT '0',
  `dirty` int(1) unsigned NOT NULL DEFAULT '2',
  `flag_group_test` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_suspect` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_group_q_bio` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_group_q_fin` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_group_stat` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_group_eess` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_group_econ` int(1) unsigned NOT NULL DEFAULT '0',
  `veto_status` enum('ok','no-endorse','no-upload','no-replace') NOT NULL DEFAULT 'ok',
  PRIMARY KEY (`user_id`),
  KEY `country` (`country`),
  KEY `type` (`type`),
  KEY `archive` (`archive`,`subject_class`),
  KEY `flag_group_physics` (`flag_group_physics`),
  KEY `flag_group_math` (`flag_group_math`),
  KEY `flag_group_cs` (`flag_group_cs`),
  KEY `flag_group_nlin` (`flag_group_nlin`),
  KEY `flag_proxy` (`flag_proxy`),
  KEY `flag_journal` (`flag_journal`),
  KEY `flag_xml` (`flag_xml`),
  KEY `flag_group_stat` (`flag_group_stat`),
  KEY `flag_group_q_bio` (`flag_group_q_bio`),
  KEY `flag_group_q_fin` (`flag_group_q_fin`),
  KEY `flag_suspect` (`flag_suspect`),
  KEY `flag_group_eess` (`flag_group_eess`),
  KEY `flag_group_econ` (`flag_group_econ`),
  CONSTRAINT `0_587` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`),
  CONSTRAINT `0_588` FOREIGN KEY (`archive`, `subject_class`) REFERENCES `arXiv_categories` (`archive`, `subject_class`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_document_category`
--

DROP TABLE IF EXISTS `arXiv_document_category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_document_category` (
  `document_id` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `category` varchar(32) NOT NULL,
  `is_primary` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`document_id`,`category`),
  KEY `document_id` (`document_id`),
  KEY `category` (`category`),
  CONSTRAINT `doc_cat_cat` FOREIGN KEY (`category`) REFERENCES `arXiv_category_def` (`category`),
  CONSTRAINT `doc_cat_doc` FOREIGN KEY (`document_id`) REFERENCES `arXiv_documents` (`document_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_documents`
--

DROP TABLE IF EXISTS `arXiv_documents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_documents` (
  `document_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `paper_id` varchar(20) NOT NULL DEFAULT '',
  `title` varchar(255) NOT NULL DEFAULT '',
  `authors` text,
  `submitter_email` varchar(64) NOT NULL DEFAULT '',
  `submitter_id` int(10) unsigned DEFAULT NULL,
  `dated` int(10) unsigned NOT NULL DEFAULT '0',
  `primary_subject_class` varchar(16) DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  PRIMARY KEY (`document_id`),
  UNIQUE KEY `paper_id` (`paper_id`),
  KEY `dated` (`dated`),
  KEY `title` (`title`),
  KEY `submitter_id` (`submitter_id`),
  KEY `submitter_email` (`submitter_email`),
  CONSTRAINT `0_580` FOREIGN KEY (`submitter_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_duplicates`
--

DROP TABLE IF EXISTS `arXiv_duplicates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_duplicates` (
  `user_id` int(10) unsigned NOT NULL DEFAULT '0',
  `email` varchar(255) DEFAULT NULL,
  `username` varchar(255) DEFAULT NULL,
  KEY `user_id` (`user_id`),
  CONSTRAINT `0_599` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_endorsement_domains`
--

DROP TABLE IF EXISTS `arXiv_endorsement_domains`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_endorsement_domains` (
  `endorsement_domain` varchar(32) NOT NULL DEFAULT '',
  `endorse_all` enum('y','n') NOT NULL DEFAULT 'n',
  `mods_endorse_all` enum('y','n') NOT NULL DEFAULT 'n',
  `endorse_email` enum('y','n') NOT NULL DEFAULT 'y',
  `papers_to_endorse` smallint(5) unsigned NOT NULL DEFAULT '4',
  PRIMARY KEY (`endorsement_domain`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_endorsement_requests`
--

DROP TABLE IF EXISTS `arXiv_endorsement_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_endorsement_requests` (
  `request_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `endorsee_id` int(10) unsigned NOT NULL DEFAULT '0',
  `archive` varchar(16) NOT NULL DEFAULT '',
  `subject_class` varchar(16) NOT NULL DEFAULT '',
  `secret` varchar(16) NOT NULL DEFAULT '',
  `flag_valid` int(1) unsigned NOT NULL DEFAULT '0',
  `issued_when` int(10) unsigned NOT NULL DEFAULT '0',
  `point_value` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`request_id`),
  UNIQUE KEY `secret` (`secret`),
  UNIQUE KEY `endorsee_id_2` (`endorsee_id`,`archive`,`subject_class`),
  KEY `endorsee_id` (`endorsee_id`),
  KEY `archive` (`archive`,`subject_class`),
  CONSTRAINT `0_722` FOREIGN KEY (`endorsee_id`) REFERENCES `tapir_users` (`user_id`),
  CONSTRAINT `0_723` FOREIGN KEY (`archive`, `subject_class`) REFERENCES `arXiv_categories` (`archive`, `subject_class`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_endorsement_requests_audit`
--

DROP TABLE IF EXISTS `arXiv_endorsement_requests_audit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_endorsement_requests_audit` (
  `request_id` int(10) unsigned NOT NULL DEFAULT '0',
  `session_id` int(10) unsigned NOT NULL DEFAULT '0',
  `remote_addr` varchar(16) DEFAULT NULL,
  `remote_host` varchar(255) DEFAULT NULL,
  `tracking_cookie` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`request_id`),
  CONSTRAINT `0_725` FOREIGN KEY (`request_id`) REFERENCES `arXiv_endorsement_requests` (`request_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_endorsements`
--

DROP TABLE IF EXISTS `arXiv_endorsements`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_endorsements` (
  `endorsement_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `endorser_id` int(10) unsigned DEFAULT NULL,
  `endorsee_id` int(10) unsigned NOT NULL DEFAULT '0',
  `archive` varchar(16) NOT NULL DEFAULT '',
  `subject_class` varchar(16) NOT NULL DEFAULT '',
  `flag_valid` int(1) unsigned NOT NULL DEFAULT '0',
  `type` enum('user','admin','auto') DEFAULT NULL,
  `point_value` int(1) unsigned NOT NULL DEFAULT '0',
  `issued_when` int(10) unsigned NOT NULL DEFAULT '0',
  `request_id` int(10) unsigned DEFAULT NULL,
  PRIMARY KEY (`endorsement_id`),
  UNIQUE KEY `endorser_id_2` (`endorser_id`,`endorsee_id`,`archive`,`subject_class`),
  KEY `endorser_id` (`endorser_id`),
  KEY `endorsee_id` (`endorsee_id`),
  KEY `archive` (`archive`,`subject_class`),
  KEY `request_id` (`request_id`),
  CONSTRAINT `0_727` FOREIGN KEY (`endorser_id`) REFERENCES `tapir_users` (`user_id`),
  CONSTRAINT `0_728` FOREIGN KEY (`endorsee_id`) REFERENCES `tapir_users` (`user_id`),
  CONSTRAINT `0_729` FOREIGN KEY (`archive`, `subject_class`) REFERENCES `arXiv_categories` (`archive`, `subject_class`),
  CONSTRAINT `0_730` FOREIGN KEY (`request_id`) REFERENCES `arXiv_endorsement_requests` (`request_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_endorsements_audit`
--

DROP TABLE IF EXISTS `arXiv_endorsements_audit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_endorsements_audit` (
  `endorsement_id` int(10) unsigned NOT NULL DEFAULT '0',
  `session_id` int(10) unsigned NOT NULL DEFAULT '0',
  `remote_addr` varchar(16) NOT NULL DEFAULT '',
  `remote_host` varchar(255) NOT NULL DEFAULT '',
  `tracking_cookie` varchar(255) NOT NULL DEFAULT '',
  `flag_knows_personally` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_seen_paper` int(1) unsigned NOT NULL DEFAULT '0',
  `comment` text,
  PRIMARY KEY (`endorsement_id`),
  CONSTRAINT `0_732` FOREIGN KEY (`endorsement_id`) REFERENCES `arXiv_endorsements` (`endorsement_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_freeze_log`
--

DROP TABLE IF EXISTS `arXiv_freeze_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_freeze_log` (
  `date` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_group_def`
--

DROP TABLE IF EXISTS `arXiv_group_def`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_group_def` (
  `archive_group` varchar(16) NOT NULL DEFAULT '',
  `name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`archive_group`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_groups`
--

DROP TABLE IF EXISTS `arXiv_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_groups` (
  `group_id` varchar(16) NOT NULL DEFAULT '',
  `group_name` varchar(255) NOT NULL DEFAULT '',
  `start_year` varchar(4) NOT NULL DEFAULT '',
  PRIMARY KEY (`group_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_in_category`
--

DROP TABLE IF EXISTS `arXiv_in_category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_in_category` (
  `document_id` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `archive` varchar(16) NOT NULL DEFAULT '',
  `subject_class` varchar(16) NOT NULL DEFAULT '',
  `is_primary` tinyint(1) NOT NULL DEFAULT '0',
  UNIQUE KEY `archive` (`archive`,`subject_class`,`document_id`),
  KEY `document_id` (`document_id`),
  KEY `arXiv_in_category_mp` (`archive`,`subject_class`),
  CONSTRAINT `0_582` FOREIGN KEY (`document_id`) REFERENCES `arXiv_documents` (`document_id`),
  CONSTRAINT `0_583` FOREIGN KEY (`archive`, `subject_class`) REFERENCES `arXiv_categories` (`archive`, `subject_class`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_jref_control`
--

DROP TABLE IF EXISTS `arXiv_jref_control`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_jref_control` (
  `control_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `document_id` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `version` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `user_id` int(10) unsigned NOT NULL DEFAULT '0',
  `status` enum('new','frozen','published','rejected') NOT NULL DEFAULT 'new',
  `flag_must_notify` enum('0','1') DEFAULT '1',
  `jref` varchar(255) NOT NULL DEFAULT '',
  `request_date` int(10) unsigned NOT NULL DEFAULT '0',
  `freeze_date` int(10) unsigned NOT NULL DEFAULT '0',
  `publish_date` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`control_id`),
  UNIQUE KEY `document_id` (`document_id`,`version`),
  KEY `freeze_date` (`freeze_date`),
  KEY `status` (`status`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `arXiv_jref_control_ibfk_1` FOREIGN KEY (`document_id`) REFERENCES `arXiv_documents` (`document_id`),
  CONSTRAINT `arXiv_jref_control_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_licenses`
--

DROP TABLE IF EXISTS `arXiv_licenses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_licenses` (
  `name` varchar(255) NOT NULL,
  `label` varchar(255) DEFAULT NULL,
  `active` tinyint(1) DEFAULT '1',
  `note` varchar(400) DEFAULT NULL,
  `sequence` tinyint(4) DEFAULT NULL,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_log_positions`
--

DROP TABLE IF EXISTS `arXiv_log_positions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_log_positions` (
  `id` varchar(255) NOT NULL DEFAULT '',
  `position` int(10) unsigned DEFAULT NULL,
  `date` int(10) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_metadata`
--

DROP TABLE IF EXISTS `arXiv_metadata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_metadata` (
  `metadata_id` int(11) NOT NULL AUTO_INCREMENT,
  `document_id` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `paper_id` varchar(64) NOT NULL,
  `created` datetime DEFAULT NULL,
  `updated` datetime DEFAULT NULL,
  `submitter_id` int(4) unsigned DEFAULT NULL,
  `submitter_name` varchar(64) NOT NULL,
  `submitter_email` varchar(64) NOT NULL,
  `source_size` int(11) DEFAULT NULL,
  `source_format` varchar(12) DEFAULT NULL,
  `source_flags` varchar(12) DEFAULT NULL,
  `title` text,
  `authors` text,
  `abs_categories` varchar(255) DEFAULT NULL,
  `comments` text,
  `proxy` varchar(255) DEFAULT NULL,
  `report_num` text,
  `msc_class` varchar(255) DEFAULT NULL,
  `acm_class` varchar(255) DEFAULT NULL,
  `journal_ref` text,
  `doi` varchar(255) DEFAULT NULL,
  `abstract` text,
  `license` varchar(255) DEFAULT NULL,
  `version` int(4) NOT NULL DEFAULT '1',
  `modtime` int(11) DEFAULT NULL,
  `is_current` tinyint(1) DEFAULT '1',
  `is_withdrawn` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`metadata_id`),
  UNIQUE KEY `pidv` (`paper_id`,`version`),
  KEY `arXiv_metadata_idx_document_id` (`document_id`),
  KEY `arXiv_metadata_idx_license` (`license`),
  KEY `arXiv_metadata_idx_submitter_id` (`submitter_id`),
  CONSTRAINT `arXiv_metadata_fk_document_id` FOREIGN KEY (`document_id`) REFERENCES `arXiv_documents` (`document_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `arXiv_metadata_fk_license` FOREIGN KEY (`license`) REFERENCES `arXiv_licenses` (`name`),
  CONSTRAINT `arXiv_metadata_fk_submitter_id` FOREIGN KEY (`submitter_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_mirror_list`
--

DROP TABLE IF EXISTS `arXiv_mirror_list`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_mirror_list` (
  `mirror_list_id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime DEFAULT NULL,
  `updated` datetime DEFAULT NULL,
  `document_id` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `version` int(4) NOT NULL DEFAULT '1',
  `write_source` tinyint(1) NOT NULL DEFAULT '0',
  `write_abs` tinyint(1) NOT NULL DEFAULT '0',
  `is_written` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`mirror_list_id`),
  KEY `arXiv_mirror_list_idx_document_id` (`document_id`),
  CONSTRAINT `arXiv_mirror_list_fk_document_id` FOREIGN KEY (`document_id`) REFERENCES `arXiv_documents` (`document_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_moderator_api_key`
--

DROP TABLE IF EXISTS `arXiv_moderator_api_key`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_moderator_api_key` (
  `user_id` int(4) unsigned NOT NULL DEFAULT '0',
  `secret` varchar(32) NOT NULL DEFAULT '',
  `valid` int(1) NOT NULL DEFAULT '1',
  `issued_when` int(4) unsigned NOT NULL DEFAULT '0',
  `issued_to` varchar(16) NOT NULL DEFAULT '',
  `remote_host` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`user_id`,`secret`),
  CONSTRAINT `arXiv_moderator_api_key_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_moderators`
--

DROP TABLE IF EXISTS `arXiv_moderators`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_moderators` (
  `user_id` int(10) unsigned NOT NULL DEFAULT '0',
  `archive` varchar(16) NOT NULL DEFAULT '',
  `subject_class` varchar(16) NOT NULL DEFAULT '',
  `is_public` tinyint(4) NOT NULL DEFAULT '0',
  `no_email` tinyint(1) DEFAULT '0',
  `no_web_email` tinyint(1) DEFAULT '0',
  `no_reply_to` tinyint(1) DEFAULT '0',
  `daily_update` tinyint(1) DEFAULT '0',
  UNIQUE KEY `user_id` (`archive`,`subject_class`,`user_id`),
  KEY `user_id_2` (`user_id`),
  KEY `arXiv_moderators_idx_no_email` (`no_email`),
  KEY `arXiv_moderators_idx_no_web_email` (`no_web_email`),
  KEY `arXiv_moderators_idx_no_reply_to` (`no_reply_to`),
  CONSTRAINT `0_590` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`),
  CONSTRAINT `0_591` FOREIGN KEY (`archive`, `subject_class`) REFERENCES `arXiv_categories` (`archive`, `subject_class`),
  CONSTRAINT `fk_archive_id` FOREIGN KEY (`archive`) REFERENCES `arXiv_archive_group` (`archive_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_monitor_klog`
--

DROP TABLE IF EXISTS `arXiv_monitor_klog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_monitor_klog` (
  `t` int(10) unsigned NOT NULL DEFAULT '0',
  `sent` int(10) unsigned DEFAULT NULL,
  PRIMARY KEY (`t`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_monitor_mailq`
--

DROP TABLE IF EXISTS `arXiv_monitor_mailq`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_monitor_mailq` (
  `t` int(10) unsigned NOT NULL DEFAULT '0',
  `main_q` int(10) unsigned NOT NULL DEFAULT '0',
  `local_q` int(10) unsigned NOT NULL DEFAULT '0',
  `local_host_map` int(10) unsigned NOT NULL DEFAULT '0',
  `local_timeout` int(10) unsigned NOT NULL DEFAULT '0',
  `local_refused` int(10) unsigned NOT NULL DEFAULT '0',
  `local_in_flight` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`t`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_monitor_mailsent`
--

DROP TABLE IF EXISTS `arXiv_monitor_mailsent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_monitor_mailsent` (
  `t` int(10) unsigned NOT NULL DEFAULT '0',
  `sent` int(10) unsigned DEFAULT NULL,
  PRIMARY KEY (`t`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_next_mail`
--

DROP TABLE IF EXISTS `arXiv_next_mail`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_next_mail` (
  `next_mail_id` int(11) NOT NULL AUTO_INCREMENT,
  `submission_id` int(11) NOT NULL,
  `document_id` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `paper_id` varchar(20) DEFAULT NULL,
  `version` int(4) NOT NULL DEFAULT '1',
  `type` varchar(255) NOT NULL DEFAULT 'new',
  `extra` varchar(255) DEFAULT NULL,
  `mail_id` char(6) DEFAULT NULL,
  `is_written` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`next_mail_id`),
  KEY `arXiv_next_mail_idx_document_id` (`document_id`),
  KEY `arXiv_next_mail_idx_document_id_version` (`document_id`,`version`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_orcid_config`
--

DROP TABLE IF EXISTS `arXiv_orcid_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_orcid_config` (
  `domain` varchar(75) NOT NULL,
  `keyname` varchar(60) NOT NULL,
  `value` varchar(150) DEFAULT NULL,
  PRIMARY KEY (`domain`,`keyname`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_orcid_ids`
--

DROP TABLE IF EXISTS `arXiv_orcid_ids`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_orcid_ids` (
  `user_id` int(4) unsigned NOT NULL,
  `orcid` varchar(19) NOT NULL,
  `authenticated` tinyint(1) NOT NULL DEFAULT '0',
  `updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  KEY `orcid` (`orcid`),
  CONSTRAINT `arXiv_orcid_ids_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_ownership_requests`
--

DROP TABLE IF EXISTS `arXiv_ownership_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_ownership_requests` (
  `request_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(10) unsigned NOT NULL DEFAULT '0',
  `endorsement_request_id` int(10) unsigned DEFAULT NULL,
  `workflow_status` enum('pending','accepted','rejected') NOT NULL DEFAULT 'pending',
  PRIMARY KEY (`request_id`),
  KEY `user_id` (`user_id`),
  KEY `endorsement_request_id` (`endorsement_request_id`),
  CONSTRAINT `0_734` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`),
  CONSTRAINT `0_735` FOREIGN KEY (`endorsement_request_id`) REFERENCES `arXiv_endorsement_requests` (`request_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_ownership_requests_audit`
--

DROP TABLE IF EXISTS `arXiv_ownership_requests_audit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_ownership_requests_audit` (
  `request_id` int(10) unsigned NOT NULL DEFAULT '0',
  `session_id` int(10) unsigned NOT NULL DEFAULT '0',
  `remote_addr` varchar(16) NOT NULL DEFAULT '',
  `remote_host` varchar(255) NOT NULL DEFAULT '',
  `tracking_cookie` varchar(255) NOT NULL DEFAULT '',
  `date` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`request_id`),
  CONSTRAINT `0_737` FOREIGN KEY (`request_id`) REFERENCES `arXiv_ownership_requests` (`request_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_ownership_requests_papers`
--

DROP TABLE IF EXISTS `arXiv_ownership_requests_papers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_ownership_requests_papers` (
  `request_id` int(10) unsigned NOT NULL DEFAULT '0',
  `document_id` int(10) unsigned NOT NULL DEFAULT '0',
  UNIQUE KEY `request_id` (`request_id`,`document_id`),
  KEY `document_id` (`document_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_paper_owners`
--

DROP TABLE IF EXISTS `arXiv_paper_owners`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_paper_owners` (
  `document_id` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `user_id` int(10) unsigned NOT NULL DEFAULT '0',
  `date` int(10) unsigned NOT NULL DEFAULT '0',
  `added_by` int(10) unsigned NOT NULL DEFAULT '0',
  `remote_addr` varchar(16) NOT NULL DEFAULT '',
  `remote_host` varchar(255) NOT NULL DEFAULT '',
  `tracking_cookie` varchar(32) NOT NULL DEFAULT '',
  `valid` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_author` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_auto` int(1) unsigned NOT NULL DEFAULT '1',
  UNIQUE KEY `document_id` (`document_id`,`user_id`),
  KEY `user_id` (`user_id`),
  KEY `added_by` (`added_by`),
  CONSTRAINT `0_593` FOREIGN KEY (`document_id`) REFERENCES `arXiv_documents` (`document_id`),
  CONSTRAINT `0_594` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`),
  CONSTRAINT `0_595` FOREIGN KEY (`added_by`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_paper_pw`
--

DROP TABLE IF EXISTS `arXiv_paper_pw`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_paper_pw` (
  `document_id` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `password_storage` int(1) unsigned DEFAULT NULL,
  `password_enc` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`document_id`),
  CONSTRAINT `0_585` FOREIGN KEY (`document_id`) REFERENCES `arXiv_documents` (`document_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_paper_sessions`
--

DROP TABLE IF EXISTS `arXiv_paper_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_paper_sessions` (
  `paper_session_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `paper_id` varchar(16) NOT NULL DEFAULT '',
  `start_time` int(10) unsigned NOT NULL DEFAULT '0',
  `end_time` int(10) unsigned NOT NULL DEFAULT '0',
  `ip_name` varchar(16) NOT NULL DEFAULT '',
  PRIMARY KEY (`paper_session_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_pilot_datasets`
--

DROP TABLE IF EXISTS `arXiv_pilot_datasets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_pilot_datasets` (
  `submission_id` int(11) NOT NULL,
  `numfiles` smallint(4) unsigned DEFAULT '0',
  `feed_url` varchar(256) DEFAULT NULL,
  `manifestation` varchar(256) DEFAULT NULL,
  `published` tinyint(1) DEFAULT '0',
  `created` datetime NOT NULL,
  `last_checked` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`submission_id`),
  CONSTRAINT `arXiv_pilot_datasets_cdfk3` FOREIGN KEY (`submission_id`) REFERENCES `arXiv_submissions` (`submission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_pilot_files`
--

DROP TABLE IF EXISTS `arXiv_pilot_files`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_pilot_files` (
  `file_id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `submission_id` int(11) NOT NULL,
  `filename` varchar(256) DEFAULT '',
  `entity_url` varchar(256) DEFAULT NULL,
  `description` varchar(80) DEFAULT NULL,
  `byRef` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`file_id`),
  KEY `arXiv_pilot_files_cdfk3` (`submission_id`),
  CONSTRAINT `arXiv_pilot_files_cdfk3` FOREIGN KEY (`submission_id`) REFERENCES `arXiv_submissions` (`submission_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_publish_log`
--

DROP TABLE IF EXISTS `arXiv_publish_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_publish_log` (
  `date` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_questionable_categories`
--

DROP TABLE IF EXISTS `arXiv_questionable_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_questionable_categories` (
  `archive` varchar(16) NOT NULL DEFAULT '',
  `subject_class` varchar(16) NOT NULL DEFAULT '',
  PRIMARY KEY (`archive`,`subject_class`),
  CONSTRAINT `0_756` FOREIGN KEY (`archive`, `subject_class`) REFERENCES `arXiv_categories` (`archive`, `subject_class`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_queue_view`
--

DROP TABLE IF EXISTS `arXiv_queue_view`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_queue_view` (
  `user_id` int(4) unsigned NOT NULL DEFAULT '0',
  `last_view` datetime DEFAULT NULL,
  `second_last_view` datetime DEFAULT NULL,
  `total_views` int(3) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`user_id`),
  CONSTRAINT `arXiv_queue_view_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_refresh_list`
--

DROP TABLE IF EXISTS `arXiv_refresh_list`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_refresh_list` (
  `filename` varchar(255) DEFAULT NULL,
  `mtime` int(10) unsigned DEFAULT NULL,
  KEY `arXiv_refresh_list_mtime` (`mtime`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_reject_session_usernames`
--

DROP TABLE IF EXISTS `arXiv_reject_session_usernames`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_reject_session_usernames` (
  `username` varchar(64) NOT NULL DEFAULT '',
  PRIMARY KEY (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_sciencewise_pings`
--

DROP TABLE IF EXISTS `arXiv_sciencewise_pings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_sciencewise_pings` (
  `paper_id_v` varchar(32) NOT NULL,
  `updated` datetime DEFAULT NULL,
  PRIMARY KEY (`paper_id_v`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_show_email_requests`
--

DROP TABLE IF EXISTS `arXiv_show_email_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_show_email_requests` (
  `document_id` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `user_id` int(10) unsigned NOT NULL DEFAULT '0',
  `session_id` int(10) unsigned NOT NULL DEFAULT '0',
  `dated` int(10) unsigned NOT NULL DEFAULT '0',
  `flag_allowed` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `remote_addr` varchar(16) NOT NULL DEFAULT '',
  `remote_host` varchar(255) NOT NULL DEFAULT '',
  `tracking_cookie` varchar(255) NOT NULL DEFAULT '',
  `request_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`request_id`),
  KEY `document_id` (`document_id`),
  KEY `user_id` (`user_id`,`dated`),
  KEY `dated` (`dated`),
  KEY `remote_addr` (`remote_addr`),
  CONSTRAINT `arXiv_show_email_requests_ibfk_1` FOREIGN KEY (`document_id`) REFERENCES `arXiv_documents` (`document_id`),
  CONSTRAINT `arXiv_show_email_requests_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_state`
--

DROP TABLE IF EXISTS `arXiv_state`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_state` (
  `id` int(11) NOT NULL,
  `name` varchar(24) DEFAULT NULL,
  `value` varchar(24) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_stats_hourly`
--

DROP TABLE IF EXISTS `arXiv_stats_hourly`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_stats_hourly` (
  `ymd` date NOT NULL,
  `hour` tinyint(3) unsigned NOT NULL,
  `node_num` tinyint(3) unsigned NOT NULL,
  `access_type` char(1) NOT NULL,
  `connections` int(4) unsigned NOT NULL,
  KEY `arXiv_stats_hourly_idx_ymd` (`ymd`),
  KEY `arXiv_stats_hourly_idx_hour` (`hour`),
  KEY `arXiv_stats_hourly_idx_node_num` (`node_num`),
  KEY `arXiv_stats_hourly_idx_access_type` (`access_type`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_stats_monthly_downloads`
--

DROP TABLE IF EXISTS `arXiv_stats_monthly_downloads`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_stats_monthly_downloads` (
  `ym` date NOT NULL,
  `downloads` int(10) unsigned NOT NULL,
  PRIMARY KEY (`ym`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_stats_monthly_submissions`
--

DROP TABLE IF EXISTS `arXiv_stats_monthly_submissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_stats_monthly_submissions` (
  `ym` date NOT NULL DEFAULT '0000-00-00',
  `num_submissions` smallint(5) unsigned NOT NULL,
  `historical_delta` tinyint(4) NOT NULL DEFAULT '0',
  PRIMARY KEY (`ym`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_submission_abs_classifier_data`
--

DROP TABLE IF EXISTS `arXiv_submission_abs_classifier_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_submission_abs_classifier_data` (
  `submission_id` int(11) NOT NULL DEFAULT '0',
  `json` text,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `status` enum('processing','success','failed','no connection') DEFAULT NULL,
  `message` text,
  `is_oversize` tinyint(1) DEFAULT '0',
  `suggested_primary` text,
  `suggested_reason` text,
  `autoproposal_primary` text,
  `autoproposal_reason` text,
  `classifier_service_version` text,
  `classifier_model_version` text,
  PRIMARY KEY (`submission_id`),
  CONSTRAINT `arXiv_submission_abs_classifier_data_ibfk_1` FOREIGN KEY (`submission_id`) REFERENCES `arXiv_submissions` (`submission_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_submission_agreements`
--

DROP TABLE IF EXISTS `arXiv_submission_agreements`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_submission_agreements` (
  `agreement_id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `effective_date` datetime DEFAULT CURRENT_TIMESTAMP,
  `commit_ref` varchar(255) NOT NULL,
  `content` text,
  PRIMARY KEY (`agreement_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_submission_category`
--

DROP TABLE IF EXISTS `arXiv_submission_category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_submission_category` (
  `submission_id` int(11) NOT NULL,
  `category` varchar(32) NOT NULL DEFAULT '',
  `is_primary` tinyint(1) NOT NULL DEFAULT '0',
  `is_published` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`submission_id`,`category`),
  KEY `arXiv_submission_category_idx_category` (`category`),
  KEY `arXiv_submission_category_idx_submission_id` (`submission_id`),
  KEY `arXiv_submission_category_idx_is_primary` (`is_primary`),
  KEY `arXiv_submission_category_idx_is_published` (`is_published`),
  CONSTRAINT `arXiv_submission_category_fk_category` FOREIGN KEY (`category`) REFERENCES `arXiv_category_def` (`category`),
  CONSTRAINT `arXiv_submission_category_fk_submission_id` FOREIGN KEY (`submission_id`) REFERENCES `arXiv_submissions` (`submission_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_submission_category_proposal`
--

DROP TABLE IF EXISTS `arXiv_submission_category_proposal`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_submission_category_proposal` (
  `proposal_id` int(11) NOT NULL AUTO_INCREMENT,
  `submission_id` int(11) NOT NULL,
  `category` varchar(32) CHARACTER SET latin1 NOT NULL,
  `is_primary` tinyint(1) NOT NULL DEFAULT '0',
  `proposal_status` int(11) DEFAULT '0',
  `user_id` int(4) unsigned NOT NULL,
  `updated` datetime DEFAULT NULL,
  `proposal_comment_id` int(11) DEFAULT NULL,
  `response_comment_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`proposal_id`,`submission_id`,`category`,`is_primary`),
  KEY `arXiv_submission_category_proposal_idx_key` (`proposal_id`),
  KEY `arXiv_submission_category_proposal_idx_category` (`category`),
  KEY `arXiv_submission_category_proposal_idx_submission_id` (`submission_id`),
  KEY `arXiv_submission_category_proposal_idx_is_primary` (`is_primary`),
  KEY `arXiv_submission_category_proposal_fk_user_id` (`user_id`),
  KEY `arXiv_submission_category_proposal_fk_prop_comment_id` (`proposal_comment_id`),
  KEY `arXiv_submission_category_proposal_fk_resp_comment_id` (`response_comment_id`),
  CONSTRAINT `arXiv_submission_category_proposal_fk_category` FOREIGN KEY (`category`) REFERENCES `arXiv_category_def` (`category`),
  CONSTRAINT `arXiv_submission_category_proposal_fk_prop_comment_id` FOREIGN KEY (`proposal_comment_id`) REFERENCES `arXiv_admin_log` (`id`),
  CONSTRAINT `arXiv_submission_category_proposal_fk_resp_comment_id` FOREIGN KEY (`response_comment_id`) REFERENCES `arXiv_admin_log` (`id`),
  CONSTRAINT `arXiv_submission_category_proposal_fk_submission_id` FOREIGN KEY (`submission_id`) REFERENCES `arXiv_submissions` (`submission_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `arXiv_submission_category_proposal_fk_user_id` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_submission_classifier_data`
--

DROP TABLE IF EXISTS `arXiv_submission_classifier_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_submission_classifier_data` (
  `submission_id` int(11) NOT NULL DEFAULT '0',
  `json` text,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `status` enum('processing','success','failed','no connection') DEFAULT NULL,
  `message` text,
  `is_oversize` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`submission_id`),
  CONSTRAINT `arXiv_submission_classifier_data_ibfk_1` FOREIGN KEY (`submission_id`) REFERENCES `arXiv_submissions` (`submission_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_submission_control`
--

DROP TABLE IF EXISTS `arXiv_submission_control`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_submission_control` (
  `control_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `document_id` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `version` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `pending_paper_id` varchar(20) NOT NULL DEFAULT '',
  `user_id` int(10) unsigned NOT NULL DEFAULT '0',
  `status` enum('new','frozen','published','rejected') NOT NULL DEFAULT 'new',
  `flag_must_notify` enum('0','1') DEFAULT '1',
  `request_date` int(10) unsigned NOT NULL DEFAULT '0',
  `freeze_date` int(10) unsigned NOT NULL DEFAULT '0',
  `publish_date` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`control_id`),
  UNIQUE KEY `document_id` (`document_id`,`version`),
  KEY `pending_paper_id` (`pending_paper_id`),
  KEY `status` (`status`),
  KEY `request_date` (`request_date`),
  KEY `freeze_date` (`freeze_date`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `arXiv_submission_control_ibfk_1` FOREIGN KEY (`document_id`) REFERENCES `arXiv_documents` (`document_id`),
  CONSTRAINT `arXiv_submission_control_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_submission_flag`
--

DROP TABLE IF EXISTS `arXiv_submission_flag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_submission_flag` (
  `flag_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(4) unsigned NOT NULL DEFAULT '0',
  `submission_id` int(11) NOT NULL,
  `flag` tinyint(4) NOT NULL DEFAULT '0',
  `updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `flag_pdf_opened` smallint(6) NOT NULL DEFAULT '0',
  PRIMARY KEY (`flag_id`),
  UNIQUE KEY `uniq_one_flag_per_mod` (`submission_id`,`user_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `arXiv_submission_flag_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `arXiv_submission_flag_ibfk_2` FOREIGN KEY (`submission_id`) REFERENCES `arXiv_submissions` (`submission_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_submission_hold_reason`
--

DROP TABLE IF EXISTS `arXiv_submission_hold_reason`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_submission_hold_reason` (
  `reason_id` int(11) NOT NULL AUTO_INCREMENT,
  `submission_id` int(11) NOT NULL,
  `user_id` int(4) unsigned NOT NULL,
  `reason` varchar(30) DEFAULT NULL,
  `type` varchar(30) DEFAULT NULL,
  `comment_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`reason_id`,`user_id`),
  KEY `submission_id` (`submission_id`),
  KEY `user_id` (`user_id`),
  KEY `comment_id` (`comment_id`),
  CONSTRAINT `arXiv_submission_hold_reason_ibfk_1` FOREIGN KEY (`submission_id`) REFERENCES `arXiv_submissions` (`submission_id`) ON DELETE CASCADE,
  CONSTRAINT `arXiv_submission_hold_reason_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `arXiv_submission_hold_reason_ibfk_3` FOREIGN KEY (`comment_id`) REFERENCES `arXiv_admin_log` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_submission_locks`
--

DROP TABLE IF EXISTS `arXiv_submission_locks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_submission_locks` (
  `submission_lock_id` int(11) NOT NULL AUTO_INCREMENT,
  `submission_id` int(11) NOT NULL,
  `user_id` int(4) unsigned NOT NULL,
  `lock_type` varchar(20) NOT NULL,
  `expires` datetime NOT NULL,
  `updated` datetime NOT NULL,
  `released` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`submission_lock_id`),
  UNIQUE KEY `arxiv_submission_locks_sub_index` (`submission_id`,`lock_type`),
  KEY `arxiv_submission_locks_user_index` (`user_id`),
  CONSTRAINT `arxiv_submission_locks_sub_fk` FOREIGN KEY (`submission_id`) REFERENCES `arXiv_submissions` (`submission_id`),
  CONSTRAINT `arxiv_submission_locks_user_fk` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_submission_near_duplicates`
--

DROP TABLE IF EXISTS `arXiv_submission_near_duplicates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_submission_near_duplicates` (
  `submission_id` int(11) NOT NULL DEFAULT '0',
  `matching_id` int(11) NOT NULL DEFAULT '0',
  `similarity` decimal(2,1) unsigned NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`submission_id`,`matching_id`),
  UNIQUE KEY `match` (`submission_id`,`matching_id`),
  CONSTRAINT `arXiv_submission_near_duplicates_ibfk_1` FOREIGN KEY (`submission_id`) REFERENCES `arXiv_submissions` (`submission_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_submission_qa_reports`
--

DROP TABLE IF EXISTS `arXiv_submission_qa_reports`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_submission_qa_reports` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `submission_id` int(11) NOT NULL,
  `report_key_name` varchar(64) NOT NULL,
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `num_flags` smallint(6) NOT NULL DEFAULT '0',
  `report` json NOT NULL,
  `report_uri` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `submission_id` (`submission_id`),
  KEY `report_key_name` (`report_key_name`),
  CONSTRAINT `arXiv_submission_qa_reports_ibfk_1` FOREIGN KEY (`submission_id`) REFERENCES `arXiv_submissions` (`submission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_submission_view_flag`
--

DROP TABLE IF EXISTS `arXiv_submission_view_flag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_submission_view_flag` (
  `submission_id` int(11) NOT NULL,
  `flag` tinyint(1) DEFAULT '0',
  `user_id` int(4) unsigned NOT NULL,
  `updated` datetime DEFAULT NULL,
  PRIMARY KEY (`submission_id`,`user_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `arXiv_submission_view_flag_ibfk_1` FOREIGN KEY (`submission_id`) REFERENCES `arXiv_submissions` (`submission_id`) ON DELETE CASCADE,
  CONSTRAINT `arXiv_submission_view_flag_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_submissions`
--

DROP TABLE IF EXISTS `arXiv_submissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_submissions` (
  `submission_id` int(11) NOT NULL AUTO_INCREMENT,
  `document_id` mediumint(8) unsigned DEFAULT NULL,
  `doc_paper_id` varchar(20) CHARACTER SET latin1 DEFAULT NULL,
  `sword_id` int(8) unsigned DEFAULT NULL,
  `userinfo` tinyint(4) DEFAULT '0',
  `is_author` tinyint(1) NOT NULL DEFAULT '0',
  `agree_policy` tinyint(1) DEFAULT '0',
  `viewed` tinyint(1) DEFAULT '0',
  `stage` int(11) DEFAULT '0',
  `submitter_id` int(4) unsigned DEFAULT NULL,
  `submitter_name` varchar(64) DEFAULT NULL,
  `submitter_email` varchar(64) DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `updated` datetime DEFAULT NULL,
  `status` int(11) NOT NULL DEFAULT '0',
  `sticky_status` int(11) DEFAULT NULL,
  `must_process` tinyint(1) DEFAULT '1',
  `submit_time` datetime DEFAULT NULL,
  `release_time` datetime DEFAULT NULL,
  `source_size` int(11) DEFAULT '0',
  `source_format` varchar(12) CHARACTER SET latin1 DEFAULT NULL,
  `source_flags` varchar(12) CHARACTER SET latin1 DEFAULT NULL,
  `has_pilot_data` tinyint(1) DEFAULT NULL,
  `is_withdrawn` tinyint(1) NOT NULL DEFAULT '0',
  `title` text,
  `authors` text,
  `comments` text,
  `proxy` varchar(255) CHARACTER SET latin1 DEFAULT NULL,
  `report_num` text,
  `msc_class` varchar(255) DEFAULT NULL,
  `acm_class` varchar(255) DEFAULT NULL,
  `journal_ref` text,
  `doi` varchar(255) DEFAULT NULL,
  `abstract` text,
  `license` varchar(255) CHARACTER SET latin1 DEFAULT NULL,
  `version` int(4) NOT NULL DEFAULT '1',
  `type` char(8) CHARACTER SET latin1 DEFAULT NULL,
  `is_ok` tinyint(1) DEFAULT NULL,
  `admin_ok` tinyint(1) DEFAULT NULL,
  `allow_tex_produced` tinyint(1) DEFAULT '0',
  `is_oversize` tinyint(1) DEFAULT '0',
  `remote_addr` varchar(16) CHARACTER SET latin1 NOT NULL DEFAULT '',
  `remote_host` varchar(255) CHARACTER SET latin1 NOT NULL DEFAULT '',
  `package` varchar(255) CHARACTER SET latin1 NOT NULL DEFAULT '',
  `rt_ticket_id` int(8) unsigned DEFAULT NULL,
  `auto_hold` tinyint(1) DEFAULT '0',
  `is_locked` int(1) unsigned NOT NULL DEFAULT '0',
  `agreement_id` smallint(5) unsigned DEFAULT NULL,
  `data_version` smallint(6) NOT NULL DEFAULT '1',
  `metadata_version` smallint(6) NOT NULL DEFAULT '1',
  `data_needed` smallint(6) NOT NULL DEFAULT '0',
  `data_version_queued` smallint(6) NOT NULL DEFAULT '0',
  `metadata_version_queued` smallint(6) NOT NULL DEFAULT '0',
  `data_queued_time` datetime DEFAULT NULL,
  `metadata_queued_time` datetime DEFAULT NULL,
  PRIMARY KEY (`submission_id`),
  KEY `arXiv_submissions_idx_document_id` (`document_id`),
  KEY `arXiv_submissions_idx_license` (`license`),
  KEY `arXiv_submissions_idx_submitter_id` (`submitter_id`),
  KEY `arXiv_submissions_idx_sword_id` (`sword_id`),
  KEY `arXiv_submissions_idx_status` (`status`),
  KEY `arXiv_submissions_idx_type` (`type`),
  KEY `arXiv_submissions_idx_is_ok` (`is_ok`),
  KEY `arXiv_submissions_idx_doc_paper_id` (`doc_paper_id`),
  KEY `arXiv_submissions_idx_rt_ticket_id` (`rt_ticket_id`),
  KEY `arXiv_submissions_idx_is_locked` (`is_locked`),
  KEY `agreement_fk` (`agreement_id`),
  CONSTRAINT `agreement_fk` FOREIGN KEY (`agreement_id`) REFERENCES `arXiv_submission_agreements` (`agreement_id`),
  CONSTRAINT `arXiv_submissions_fk_document_id` FOREIGN KEY (`document_id`) REFERENCES `arXiv_documents` (`document_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `arXiv_submissions_fk_license` FOREIGN KEY (`license`) REFERENCES `arXiv_licenses` (`name`) ON UPDATE CASCADE,
  CONSTRAINT `arXiv_submissions_fk_submitter_id` FOREIGN KEY (`submitter_id`) REFERENCES `tapir_users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `arXiv_submissions_fk_sword_id` FOREIGN KEY (`sword_id`) REFERENCES `arXiv_tracking` (`sword_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_submitter_flags`
--

DROP TABLE IF EXISTS `arXiv_submitter_flags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_submitter_flags` (
  `flag_id` int(11) NOT NULL,
  `comment` varchar(255) DEFAULT NULL,
  `pattern` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`flag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_suspect_emails`
--

DROP TABLE IF EXISTS `arXiv_suspect_emails`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_suspect_emails` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `type` varchar(10) NOT NULL,
  `pattern` text NOT NULL,
  `comment` text NOT NULL,
  `updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_suspicious_names`
--

DROP TABLE IF EXISTS `arXiv_suspicious_names`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_suspicious_names` (
  `user_id` int(10) unsigned NOT NULL DEFAULT '0',
  `full_name` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`user_id`),
  CONSTRAINT `0_606` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_sword_licenses`
--

DROP TABLE IF EXISTS `arXiv_sword_licenses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_sword_licenses` (
  `user_id` int(4) unsigned NOT NULL,
  `license` varchar(127) DEFAULT NULL,
  `updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  CONSTRAINT `user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_titles`
--

DROP TABLE IF EXISTS `arXiv_titles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_titles` (
  `paper_id` varchar(64) NOT NULL,
  `title` varchar(255) DEFAULT NULL,
  `report_num` varchar(255) DEFAULT NULL,
  `date` date DEFAULT NULL,
  PRIMARY KEY (`paper_id`),
  KEY `arXiv_titles_idx` (`title`),
  KEY `arXiv_repno_idx` (`report_num`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_top_papers`
--

DROP TABLE IF EXISTS `arXiv_top_papers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_top_papers` (
  `from_week` date NOT NULL DEFAULT '0000-00-00',
  `class` char(1) NOT NULL DEFAULT '',
  `rank` smallint(5) unsigned NOT NULL DEFAULT '0',
  `document_id` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `viewers` mediumint(8) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`from_week`,`class`,`rank`),
  KEY `document_id` (`document_id`),
  CONSTRAINT `arXiv_top_papers_ibfk_1` FOREIGN KEY (`document_id`) REFERENCES `arXiv_documents` (`document_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_trackback_pings`
--

DROP TABLE IF EXISTS `arXiv_trackback_pings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_trackback_pings` (
  `trackback_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `document_id` mediumint(8) unsigned DEFAULT NULL,
  `title` varchar(255) NOT NULL DEFAULT '',
  `excerpt` varchar(255) NOT NULL DEFAULT '',
  `url` varchar(255) NOT NULL DEFAULT '',
  `blog_name` varchar(255) NOT NULL DEFAULT '',
  `remote_host` varchar(255) NOT NULL DEFAULT '',
  `remote_addr` varchar(16) NOT NULL DEFAULT '',
  `posted_date` int(10) unsigned NOT NULL DEFAULT '0',
  `is_stale` tinyint(4) NOT NULL DEFAULT '0',
  `approved_by_user` mediumint(9) NOT NULL DEFAULT '0',
  `approved_time` int(11) NOT NULL DEFAULT '0',
  `status` enum('pending','pending2','accepted','rejected','spam') NOT NULL DEFAULT 'pending',
  `site_id` int(10) unsigned DEFAULT NULL,
  PRIMARY KEY (`trackback_id`),
  KEY `arXiv_trackback_pings__document_id` (`document_id`),
  KEY `arXiv_trackback_pings__url` (`url`),
  KEY `arXiv_trackback_pings__posted_date` (`posted_date`),
  KEY `arXiv_trackback_pings__status` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_trackback_sites`
--

DROP TABLE IF EXISTS `arXiv_trackback_sites`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_trackback_sites` (
  `pattern` varchar(255) NOT NULL DEFAULT '',
  `site_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `action` enum('neutral','accept','reject','spam') NOT NULL DEFAULT 'neutral',
  PRIMARY KEY (`site_id`),
  KEY `arXiv_trackback_sites__pattern` (`pattern`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_tracking`
--

DROP TABLE IF EXISTS `arXiv_tracking`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_tracking` (
  `tracking_id` int(11) NOT NULL AUTO_INCREMENT,
  `sword_id` int(8) unsigned zerofill NOT NULL DEFAULT '00000000',
  `paper_id` varchar(32) NOT NULL,
  `submission_errors` text,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`tracking_id`),
  UNIQUE KEY `sword_id` (`sword_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_updates`
--

DROP TABLE IF EXISTS `arXiv_updates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_updates` (
  `document_id` int(11) DEFAULT NULL,
  `version` int(4) NOT NULL DEFAULT '1',
  `date` date DEFAULT NULL,
  `action` enum('new','replace','absonly','cross','repcro') DEFAULT NULL,
  `archive` varchar(20) DEFAULT NULL,
  `category` varchar(20) DEFAULT NULL,
  UNIQUE KEY `document_id` (`document_id`,`date`,`action`,`category`),
  KEY `date_index` (`date`),
  KEY `archive_index` (`archive`),
  KEY `category_index` (`category`),
  KEY `document_id_index` (`document_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_updates_tmp`
--

DROP TABLE IF EXISTS `arXiv_updates_tmp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_updates_tmp` (
  `document_id` int(11) DEFAULT NULL,
  `date` date DEFAULT NULL,
  `action` enum('new','replace','absonly','cross','repcro') DEFAULT NULL,
  `category` varchar(20) DEFAULT NULL,
  UNIQUE KEY `document_id` (`document_id`,`date`,`action`,`category`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_versions`
--

DROP TABLE IF EXISTS `arXiv_versions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_versions` (
  `document_id` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `version` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `request_date` int(10) unsigned NOT NULL DEFAULT '0',
  `freeze_date` int(10) unsigned NOT NULL DEFAULT '0',
  `publish_date` int(10) unsigned NOT NULL DEFAULT '0',
  `flag_current` mediumint(8) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`document_id`,`version`),
  KEY `request_date` (`request_date`),
  KEY `freeze_date` (`freeze_date`),
  KEY `publish_date` (`publish_date`),
  CONSTRAINT `arXiv_versions_ibfk_1` FOREIGN KEY (`document_id`) REFERENCES `arXiv_documents` (`document_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_versions_checksum`
--

DROP TABLE IF EXISTS `arXiv_versions_checksum`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_versions_checksum` (
  `document_id` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `version` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `flag_abs_present` int(10) unsigned NOT NULL DEFAULT '0',
  `abs_size` int(10) unsigned NOT NULL DEFAULT '0',
  `abs_md5sum` binary(16) DEFAULT NULL,
  `flag_src_present` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `src_size` int(10) unsigned NOT NULL DEFAULT '0',
  `src_md5sum` binary(16) DEFAULT NULL,
  PRIMARY KEY (`document_id`,`version`),
  KEY `abs_size` (`abs_size`),
  KEY `abs_md5sum` (`abs_md5sum`),
  KEY `src_size` (`src_size`),
  KEY `src_md5sum` (`src_md5sum`),
  CONSTRAINT `arXiv_versions_checksum_ibfk_1` FOREIGN KEY (`document_id`, `version`) REFERENCES `arXiv_versions` (`document_id`, `version`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_white_email`
--

DROP TABLE IF EXISTS `arXiv_white_email`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_white_email` (
  `pattern` varchar(64) DEFAULT NULL,
  UNIQUE KEY `uc_pattern` (`pattern`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `arXiv_xml_notifications`
--

DROP TABLE IF EXISTS `arXiv_xml_notifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `arXiv_xml_notifications` (
  `control_id` int(10) unsigned DEFAULT NULL,
  `type` enum('submission','cross','jref') DEFAULT NULL,
  `queued_date` int(10) unsigned NOT NULL DEFAULT '0',
  `sent_date` int(10) unsigned NOT NULL DEFAULT '0',
  `status` enum('unsent','sent','failed') DEFAULT NULL,
  KEY `control_id` (`control_id`),
  KEY `status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dbix_class_schema_versions`
--

DROP TABLE IF EXISTS `dbix_class_schema_versions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dbix_class_schema_versions` (
  `version` varchar(10) NOT NULL,
  `installed` varchar(20) NOT NULL,
  PRIMARY KEY (`version`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `demographics_backup`
--

DROP TABLE IF EXISTS `demographics_backup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `demographics_backup` (
  `user_id` int(10) unsigned NOT NULL DEFAULT '0',
  `country` char(2) NOT NULL DEFAULT '',
  `affiliation` varchar(255) NOT NULL DEFAULT '',
  `url` varchar(255) NOT NULL DEFAULT '',
  `type` smallint(5) unsigned DEFAULT NULL,
  `os` smallint(5) unsigned DEFAULT NULL,
  `archive` varchar(16) DEFAULT NULL,
  `subject_class` varchar(16) DEFAULT NULL,
  `original_subject_classes` varchar(255) NOT NULL DEFAULT '',
  `flag_group_physics` int(1) unsigned DEFAULT NULL,
  `flag_group_math` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_group_cs` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_group_nlin` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_proxy` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_journal` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_xml` int(1) unsigned NOT NULL DEFAULT '0',
  `dirty` int(1) unsigned NOT NULL DEFAULT '2',
  `flag_group_test` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_suspect` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_group_q_bio` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_no_upload` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_no_endorse` int(1) unsigned NOT NULL DEFAULT '0',
  `veto_status` enum('ok','no-endorse','no-upload') DEFAULT 'ok'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `membership_institutions`
--

DROP TABLE IF EXISTS `membership_institutions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `membership_institutions` (
  `sid` int(11) NOT NULL,
  `name` varchar(256) DEFAULT NULL,
  `country` varchar(40) DEFAULT NULL,
  `country_code` varchar(10) DEFAULT NULL,
  `consortia_code` varchar(20) DEFAULT NULL,
  `member_type` varchar(20) DEFAULT NULL,
  `ror_id` varchar(50) DEFAULT NULL,
  `is_consortium` tinyint(4) DEFAULT NULL,
  `label` varchar(256) DEFAULT NULL,
  `comment` text,
  `is_active` tinyint(4) NOT NULL DEFAULT '1',
  PRIMARY KEY (`sid`),
  KEY `membership_Institution_name_index` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `membership_users`
--

DROP TABLE IF EXISTS `membership_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `membership_users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sid` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sessions`
--

DROP TABLE IF EXISTS `sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sessions` (
  `id` char(72) NOT NULL,
  `session_data` text,
  `expires` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_address`
--

DROP TABLE IF EXISTS `tapir_address`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_address` (
  `user_id` int(4) unsigned NOT NULL DEFAULT '0',
  `address_type` int(1) NOT NULL DEFAULT '0',
  `company` varchar(80) NOT NULL DEFAULT '',
  `line1` varchar(80) NOT NULL DEFAULT '',
  `line2` varchar(80) NOT NULL DEFAULT '',
  `city` varchar(50) NOT NULL DEFAULT '',
  `state` varchar(50) NOT NULL DEFAULT '',
  `postal_code` varchar(16) NOT NULL DEFAULT '',
  `country` char(2) NOT NULL DEFAULT '',
  `share_addr` int(1) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`user_id`,`address_type`),
  KEY `country` (`country`),
  KEY `city` (`city`),
  KEY `postal_code` (`postal_code`),
  KEY `address_type` (`address_type`),
  CONSTRAINT `0_522` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`),
  CONSTRAINT `0_523` FOREIGN KEY (`country`) REFERENCES `tapir_countries` (`digraph`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_admin_audit`
--

DROP TABLE IF EXISTS `tapir_admin_audit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_admin_audit` (
  `log_date` int(10) unsigned NOT NULL DEFAULT '0',
  `session_id` int(4) unsigned DEFAULT NULL,
  `ip_addr` varchar(16) NOT NULL DEFAULT '',
  `remote_host` varchar(255) NOT NULL DEFAULT '',
  `admin_user` int(4) unsigned DEFAULT NULL,
  `affected_user` int(4) unsigned NOT NULL DEFAULT '0',
  `tracking_cookie` varchar(255) NOT NULL DEFAULT '',
  `action` varchar(32) NOT NULL DEFAULT '',
  `data` text NOT NULL,
  `comment` text NOT NULL,
  `entry_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`entry_id`),
  KEY `log_date` (`log_date`),
  KEY `session_id` (`session_id`),
  KEY `ip_addr` (`ip_addr`),
  KEY `admin_user` (`admin_user`),
  KEY `affected_user` (`affected_user`),
  KEY `data` (`data`(32)),
  KEY `data_2` (`data`(32)),
  KEY `data_3` (`data`(32)),
  CONSTRAINT `0_553` FOREIGN KEY (`session_id`) REFERENCES `tapir_sessions` (`session_id`),
  CONSTRAINT `0_554` FOREIGN KEY (`admin_user`) REFERENCES `tapir_users` (`user_id`),
  CONSTRAINT `0_555` FOREIGN KEY (`affected_user`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_countries`
--

DROP TABLE IF EXISTS `tapir_countries`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_countries` (
  `digraph` char(2) NOT NULL DEFAULT '',
  `country_name` varchar(255) NOT NULL DEFAULT '',
  `rank` int(1) unsigned NOT NULL DEFAULT '255',
  PRIMARY KEY (`digraph`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_demographics`
--

DROP TABLE IF EXISTS `tapir_demographics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_demographics` (
  `user_id` int(4) unsigned NOT NULL DEFAULT '0',
  `gender` int(1) NOT NULL DEFAULT '0',
  `share_gender` int(1) unsigned NOT NULL DEFAULT '16',
  `birthday` date DEFAULT NULL,
  `share_birthday` int(1) unsigned NOT NULL DEFAULT '16',
  `country` char(2) NOT NULL DEFAULT '',
  `share_country` int(1) unsigned NOT NULL DEFAULT '16',
  `postal_code` varchar(16) NOT NULL DEFAULT '',
  PRIMARY KEY (`user_id`),
  KEY `country` (`country`),
  KEY `postal_code` (`postal_code`),
  KEY `birthday` (`birthday`),
  CONSTRAINT `0_517` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`),
  CONSTRAINT `0_518` FOREIGN KEY (`country`) REFERENCES `tapir_countries` (`digraph`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_email_change_tokens`
--

DROP TABLE IF EXISTS `tapir_email_change_tokens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_email_change_tokens` (
  `user_id` int(4) unsigned NOT NULL DEFAULT '0',
  `old_email` varchar(255) DEFAULT NULL,
  `new_email` varchar(255) DEFAULT NULL,
  `secret` varchar(32) NOT NULL DEFAULT '',
  `tapir_dest` varchar(255) NOT NULL DEFAULT '',
  `issued_when` int(10) unsigned NOT NULL DEFAULT '0',
  `issued_to` varchar(16) NOT NULL DEFAULT '',
  `remote_host` varchar(16) NOT NULL DEFAULT '',
  `tracking_cookie` varchar(255) NOT NULL DEFAULT '',
  `used` int(1) unsigned NOT NULL DEFAULT '0',
  `session_id` int(4) unsigned NOT NULL DEFAULT '0',
  `consumed_when` int(10) unsigned DEFAULT NULL,
  `consumed_from` varchar(16) DEFAULT NULL,
  PRIMARY KEY (`user_id`,`secret`),
  KEY `secret` (`secret`),
  CONSTRAINT `0_535` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_email_change_tokens_used`
--

DROP TABLE IF EXISTS `tapir_email_change_tokens_used`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_email_change_tokens_used` (
  `user_id` int(4) unsigned NOT NULL DEFAULT '0',
  `secret` varchar(32) NOT NULL DEFAULT '',
  `used_when` int(10) unsigned NOT NULL DEFAULT '0',
  `used_from` varchar(16) NOT NULL DEFAULT '',
  `remote_host` varchar(255) NOT NULL DEFAULT '',
  `session_id` int(4) unsigned NOT NULL DEFAULT '0',
  KEY `user_id` (`user_id`),
  KEY `session_id` (`session_id`),
  CONSTRAINT `0_537` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`),
  CONSTRAINT `0_538` FOREIGN KEY (`session_id`) REFERENCES `tapir_sessions` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_email_headers`
--

DROP TABLE IF EXISTS `tapir_email_headers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_email_headers` (
  `template_id` int(10) unsigned NOT NULL DEFAULT '0',
  `header_name` varchar(32) NOT NULL DEFAULT '',
  `header_content` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`template_id`,`header_name`),
  CONSTRAINT `0_563` FOREIGN KEY (`template_id`) REFERENCES `tapir_email_templates` (`template_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_email_log`
--

DROP TABLE IF EXISTS `tapir_email_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_email_log` (
  `mail_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `reference_type` char(1) DEFAULT NULL,
  `reference_id` int(4) unsigned DEFAULT NULL,
  `sent_date` int(10) unsigned NOT NULL DEFAULT '0',
  `email` varchar(255) DEFAULT NULL,
  `flag_bounced` int(1) unsigned DEFAULT NULL,
  `mailing_id` int(10) unsigned DEFAULT NULL,
  `template_id` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`mail_id`),
  KEY `mailing_id` (`mailing_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_email_mailings`
--

DROP TABLE IF EXISTS `tapir_email_mailings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_email_mailings` (
  `mailing_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `template_id` int(10) unsigned DEFAULT NULL,
  `created_by` int(10) unsigned DEFAULT NULL,
  `sent_by` int(10) unsigned DEFAULT NULL,
  `created_date` int(10) unsigned DEFAULT NULL,
  `sent_date` int(10) unsigned DEFAULT NULL,
  `complete_date` int(10) unsigned DEFAULT NULL,
  `mailing_name` varchar(255) DEFAULT NULL,
  `comment` text,
  PRIMARY KEY (`mailing_id`),
  KEY `created_by` (`created_by`),
  KEY `sent_by` (`sent_by`),
  KEY `template_id` (`template_id`),
  CONSTRAINT `0_565` FOREIGN KEY (`created_by`) REFERENCES `tapir_users` (`user_id`),
  CONSTRAINT `0_566` FOREIGN KEY (`sent_by`) REFERENCES `tapir_users` (`user_id`),
  CONSTRAINT `0_567` FOREIGN KEY (`template_id`) REFERENCES `tapir_email_templates` (`template_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_email_templates`
--

DROP TABLE IF EXISTS `tapir_email_templates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_email_templates` (
  `template_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `short_name` varchar(32) NOT NULL DEFAULT '',
  `lang` char(2) NOT NULL DEFAULT 'en',
  `long_name` varchar(255) NOT NULL DEFAULT '',
  `data` text NOT NULL,
  `sql_statement` text NOT NULL,
  `update_date` int(10) unsigned NOT NULL DEFAULT '0',
  `created_by` int(4) unsigned NOT NULL DEFAULT '0',
  `updated_by` int(4) unsigned NOT NULL DEFAULT '0',
  `workflow_status` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_system` int(1) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`template_id`),
  UNIQUE KEY `short_name` (`short_name`,`lang`),
  KEY `created_by` (`created_by`),
  KEY `updated_by` (`updated_by`),
  KEY `update_date` (`update_date`),
  CONSTRAINT `0_560` FOREIGN KEY (`created_by`) REFERENCES `tapir_users` (`user_id`),
  CONSTRAINT `0_561` FOREIGN KEY (`updated_by`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_email_tokens`
--

DROP TABLE IF EXISTS `tapir_email_tokens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_email_tokens` (
  `user_id` int(4) unsigned NOT NULL DEFAULT '0',
  `secret` varchar(32) NOT NULL DEFAULT '',
  `tapir_dest` varchar(255) NOT NULL DEFAULT '',
  `issued_when` int(10) unsigned NOT NULL DEFAULT '0',
  `issued_to` varchar(16) NOT NULL DEFAULT '',
  `remote_host` varchar(255) NOT NULL DEFAULT '',
  `tracking_cookie` varchar(255) NOT NULL DEFAULT '',
  `wants_perm_token` int(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`user_id`,`secret`),
  KEY `secret` (`secret`),
  CONSTRAINT `0_530` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_email_tokens_used`
--

DROP TABLE IF EXISTS `tapir_email_tokens_used`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_email_tokens_used` (
  `user_id` int(4) unsigned NOT NULL DEFAULT '0',
  `secret` varchar(32) NOT NULL DEFAULT '',
  `used_when` int(10) unsigned NOT NULL DEFAULT '0',
  `used_from` varchar(16) NOT NULL DEFAULT '',
  `remote_host` varchar(255) NOT NULL DEFAULT '',
  `session_id` int(4) unsigned NOT NULL DEFAULT '0',
  KEY `user_id` (`user_id`),
  KEY `session_id` (`session_id`),
  CONSTRAINT `0_532` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`),
  CONSTRAINT `0_533` FOREIGN KEY (`session_id`) REFERENCES `tapir_sessions` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_error_log`
--

DROP TABLE IF EXISTS `tapir_error_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_error_log` (
  `error_date` int(4) unsigned NOT NULL DEFAULT '0',
  `user_id` int(4) unsigned DEFAULT NULL,
  `session_id` int(4) unsigned DEFAULT NULL,
  `ip_addr` varchar(16) NOT NULL DEFAULT '',
  `remote_host` varchar(255) NOT NULL DEFAULT '',
  `tracking_cookie` varchar(32) NOT NULL DEFAULT '',
  `message` varchar(32) NOT NULL DEFAULT '',
  `url` varchar(255) NOT NULL DEFAULT '',
  `error_url` varchar(255) NOT NULL DEFAULT '',
  KEY `error_date` (`error_date`),
  KEY `user_id` (`user_id`),
  KEY `session_id` (`session_id`),
  KEY `ip_addr` (`ip_addr`),
  KEY `tracking_cookie` (`tracking_cookie`),
  KEY `message` (`message`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_integer_variables`
--

DROP TABLE IF EXISTS `tapir_integer_variables`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_integer_variables` (
  `variable_id` varchar(32) NOT NULL DEFAULT '',
  `value` int(4) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`variable_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_nicknames`
--

DROP TABLE IF EXISTS `tapir_nicknames`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_nicknames` (
  `nick_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `nickname` varchar(20) NOT NULL DEFAULT '',
  `user_id` int(4) unsigned NOT NULL DEFAULT '0',
  `user_seq` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_valid` int(1) unsigned NOT NULL DEFAULT '0',
  `role` int(10) unsigned NOT NULL DEFAULT '0',
  `policy` int(10) unsigned NOT NULL DEFAULT '0',
  `flag_primary` int(1) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`nick_id`),
  UNIQUE KEY `user_id` (`user_id`,`user_seq`),
  UNIQUE KEY `nickname` (`nickname`),
  KEY `flag_valid` (`flag_valid`),
  KEY `role` (`role`),
  KEY `policy` (`policy`),
  CONSTRAINT `0_570` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_nicknames_audit`
--

DROP TABLE IF EXISTS `tapir_nicknames_audit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_nicknames_audit` (
  `nick_id` int(10) unsigned NOT NULL DEFAULT '0',
  `creation_date` int(10) unsigned NOT NULL DEFAULT '0',
  `creation_ip_num` varchar(16) NOT NULL DEFAULT '',
  `remote_host` varchar(255) NOT NULL DEFAULT '',
  `tracking_cookie` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`nick_id`),
  KEY `creation_date` (`creation_date`),
  KEY `creation_ip_num` (`creation_ip_num`),
  KEY `tracking_cookie` (`tracking_cookie`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_no_cookies`
--

DROP TABLE IF EXISTS `tapir_no_cookies`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_no_cookies` (
  `log_date` int(10) unsigned NOT NULL DEFAULT '0',
  `ip_addr` varchar(16) NOT NULL DEFAULT '',
  `remote_host` varchar(255) NOT NULL DEFAULT '',
  `tracking_cookie` varchar(255) NOT NULL DEFAULT '',
  `session_data` varchar(255) NOT NULL DEFAULT '',
  `user_agent` varchar(255) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_periodic_tasks_log`
--

DROP TABLE IF EXISTS `tapir_periodic_tasks_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_periodic_tasks_log` (
  `t` int(4) unsigned NOT NULL DEFAULT '0',
  `entry` text,
  KEY `tapir_periodic_tasks_log_1` (`t`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_permanent_tokens`
--

DROP TABLE IF EXISTS `tapir_permanent_tokens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_permanent_tokens` (
  `user_id` int(4) unsigned NOT NULL DEFAULT '0',
  `secret` varchar(32) NOT NULL DEFAULT '',
  `valid` int(1) NOT NULL DEFAULT '1',
  `issued_when` int(4) unsigned NOT NULL DEFAULT '0',
  `issued_to` varchar(16) NOT NULL DEFAULT '',
  `remote_host` varchar(255) NOT NULL DEFAULT '',
  `session_id` int(4) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`user_id`,`secret`),
  KEY `session_id` (`session_id`),
  CONSTRAINT `0_540` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`),
  CONSTRAINT `0_541` FOREIGN KEY (`session_id`) REFERENCES `tapir_sessions` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_permanent_tokens_used`
--

DROP TABLE IF EXISTS `tapir_permanent_tokens_used`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_permanent_tokens_used` (
  `user_id` int(4) unsigned DEFAULT NULL,
  `secret` varchar(32) NOT NULL DEFAULT '',
  `used_when` int(4) unsigned DEFAULT NULL,
  `used_from` varchar(16) DEFAULT NULL,
  `remote_host` varchar(255) NOT NULL DEFAULT '',
  `session_id` int(4) unsigned NOT NULL DEFAULT '0',
  KEY `user_id` (`user_id`),
  KEY `session_id` (`session_id`),
  CONSTRAINT `0_543` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`),
  CONSTRAINT `0_544` FOREIGN KEY (`session_id`) REFERENCES `tapir_sessions` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_phone`
--

DROP TABLE IF EXISTS `tapir_phone`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_phone` (
  `user_id` int(4) unsigned NOT NULL DEFAULT '0',
  `phone_type` int(1) NOT NULL DEFAULT '0',
  `phone_number` varchar(32) DEFAULT NULL,
  `share_phone` int(1) unsigned NOT NULL DEFAULT '16',
  PRIMARY KEY (`user_id`,`phone_type`),
  KEY `phone_number` (`phone_number`),
  KEY `phone_type` (`phone_type`),
  CONSTRAINT `0_520` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_policy_classes`
--

DROP TABLE IF EXISTS `tapir_policy_classes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_policy_classes` (
  `class_id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL DEFAULT '',
  `description` text NOT NULL,
  `password_storage` int(1) unsigned NOT NULL DEFAULT '0',
  `recovery_policy` int(1) unsigned NOT NULL DEFAULT '0',
  `permanent_login` int(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`class_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_presessions`
--

DROP TABLE IF EXISTS `tapir_presessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_presessions` (
  `presession_id` int(4) unsigned NOT NULL AUTO_INCREMENT,
  `ip_num` varchar(16) NOT NULL DEFAULT '',
  `remote_host` varchar(255) NOT NULL DEFAULT '',
  `tracking_cookie` varchar(255) NOT NULL DEFAULT '',
  `created_at` int(4) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`presession_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_recovery_tokens`
--

DROP TABLE IF EXISTS `tapir_recovery_tokens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_recovery_tokens` (
  `user_id` int(4) unsigned NOT NULL DEFAULT '0',
  `secret` varchar(32) NOT NULL DEFAULT '',
  `valid` int(1) NOT NULL DEFAULT '1',
  `tapir_dest` varchar(255) NOT NULL DEFAULT '',
  `issued_when` int(10) unsigned NOT NULL DEFAULT '0',
  `issued_to` varchar(16) NOT NULL DEFAULT '',
  `remote_host` varchar(255) NOT NULL DEFAULT '',
  `tracking_cookie` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`user_id`,`secret`),
  KEY `secret` (`secret`),
  CONSTRAINT `0_546` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_recovery_tokens_used`
--

DROP TABLE IF EXISTS `tapir_recovery_tokens_used`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_recovery_tokens_used` (
  `user_id` int(4) unsigned NOT NULL DEFAULT '0',
  `secret` varchar(32) NOT NULL DEFAULT '',
  `used_when` int(4) unsigned DEFAULT NULL,
  `used_from` varchar(16) DEFAULT NULL,
  `remote_host` varchar(255) NOT NULL DEFAULT '',
  `session_id` int(4) unsigned DEFAULT NULL,
  PRIMARY KEY (`user_id`,`secret`),
  KEY `session_id` (`session_id`),
  CONSTRAINT `0_548` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`),
  CONSTRAINT `0_549` FOREIGN KEY (`session_id`) REFERENCES `tapir_sessions` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_save_post_variables`
--

DROP TABLE IF EXISTS `tapir_save_post_variables`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_save_post_variables` (
  `presession_id` int(4) unsigned NOT NULL DEFAULT '0',
  `name` varchar(255) DEFAULT NULL,
  `value` mediumtext NOT NULL,
  `seq` int(4) unsigned NOT NULL DEFAULT '0',
  KEY `presession_id` (`presession_id`),
  CONSTRAINT `0_558` FOREIGN KEY (`presession_id`) REFERENCES `tapir_presessions` (`presession_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_sessions`
--

DROP TABLE IF EXISTS `tapir_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_sessions` (
  `session_id` int(4) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(4) unsigned NOT NULL DEFAULT '0',
  `last_reissue` int(11) NOT NULL DEFAULT '0',
  `start_time` int(11) NOT NULL DEFAULT '0',
  `end_time` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`session_id`),
  KEY `user_id` (`user_id`),
  KEY `start_time` (`start_time`),
  KEY `end_time` (`end_time`),
  CONSTRAINT `0_525` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_sessions_audit`
--

DROP TABLE IF EXISTS `tapir_sessions_audit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_sessions_audit` (
  `session_id` int(4) unsigned NOT NULL DEFAULT '0',
  `ip_addr` varchar(16) NOT NULL DEFAULT '',
  `remote_host` varchar(255) NOT NULL DEFAULT '',
  `tracking_cookie` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`session_id`),
  KEY `ip_addr` (`ip_addr`),
  KEY `tracking_cookie` (`tracking_cookie`),
  CONSTRAINT `0_527` FOREIGN KEY (`session_id`) REFERENCES `tapir_sessions` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_string_variables`
--

DROP TABLE IF EXISTS `tapir_string_variables`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_string_variables` (
  `variable_id` varchar(32) NOT NULL DEFAULT '',
  `value` text NOT NULL,
  PRIMARY KEY (`variable_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_strings`
--

DROP TABLE IF EXISTS `tapir_strings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_strings` (
  `name` varchar(32) NOT NULL DEFAULT '',
  `module` varchar(32) NOT NULL DEFAULT '',
  `language` varchar(32) NOT NULL DEFAULT 'en',
  `string` text NOT NULL,
  PRIMARY KEY (`module`,`name`,`language`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_users`
--

DROP TABLE IF EXISTS `tapir_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_users` (
  `user_id` int(4) unsigned NOT NULL AUTO_INCREMENT,
  `first_name` varchar(50) DEFAULT NULL,
  `last_name` varchar(50) DEFAULT NULL,
  `suffix_name` varchar(50) DEFAULT NULL,
  `share_first_name` int(1) unsigned NOT NULL DEFAULT '1',
  `share_last_name` int(1) unsigned NOT NULL DEFAULT '1',
  `email` varchar(255) NOT NULL DEFAULT '',
  `share_email` int(1) unsigned NOT NULL DEFAULT '8',
  `email_bouncing` int(1) unsigned NOT NULL DEFAULT '0',
  `policy_class` smallint(5) unsigned NOT NULL DEFAULT '0',
  `joined_date` int(10) unsigned NOT NULL DEFAULT '0',
  `joined_ip_num` varchar(16) DEFAULT NULL,
  `joined_remote_host` varchar(255) NOT NULL DEFAULT '',
  `flag_internal` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_edit_users` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_edit_system` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_email_verified` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_approved` int(1) unsigned NOT NULL DEFAULT '1',
  `flag_deleted` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_banned` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_wants_email` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_html_email` int(1) unsigned NOT NULL DEFAULT '0',
  `tracking_cookie` varchar(255) NOT NULL DEFAULT '',
  `flag_allow_tex_produced` int(1) unsigned NOT NULL DEFAULT '0',
  `flag_can_lock` int(1) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`),
  KEY `policy_class` (`policy_class`),
  KEY `first_name` (`first_name`),
  KEY `last_name` (`last_name`),
  KEY `tracking_cookie` (`tracking_cookie`),
  KEY `joined_date` (`joined_date`),
  KEY `flag_internal` (`flag_internal`),
  KEY `flag_edit_users` (`flag_edit_users`),
  KEY `flag_approved` (`flag_approved`),
  KEY `flag_deleted` (`flag_deleted`),
  KEY `flag_banned` (`flag_banned`),
  KEY `joined_ip_num` (`joined_ip_num`),
  KEY `flag_can_lock` (`flag_can_lock`),
  CONSTRAINT `0_510` FOREIGN KEY (`policy_class`) REFERENCES `tapir_policy_classes` (`class_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_users_hot`
--

DROP TABLE IF EXISTS `tapir_users_hot`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_users_hot` (
  `user_id` int(4) unsigned NOT NULL DEFAULT '0',
  `last_login` int(4) unsigned NOT NULL DEFAULT '0',
  `second_last_login` int(4) unsigned NOT NULL DEFAULT '0',
  `number_sessions` int(4) NOT NULL DEFAULT '0',
  PRIMARY KEY (`user_id`),
  KEY `last_login` (`last_login`),
  KEY `second_last_login` (`second_last_login`),
  KEY `number_sessions` (`number_sessions`),
  CONSTRAINT `0_514` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tapir_users_password`
--

DROP TABLE IF EXISTS `tapir_users_password`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tapir_users_password` (
  `user_id` int(4) unsigned NOT NULL DEFAULT '0',
  `password_storage` int(1) unsigned NOT NULL DEFAULT '0',
  `password_enc` varchar(50) NOT NULL DEFAULT '',
  PRIMARY KEY (`user_id`),
  CONSTRAINT `0_512` FOREIGN KEY (`user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-11-21 10:44:33
