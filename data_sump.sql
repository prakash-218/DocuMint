CREATE DATABASE  IF NOT EXISTS `invoice_generator` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `invoice_generator`;
-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: localhost    Database: invoice_generator
-- ------------------------------------------------------
-- Server version	8.4.6

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `customer`
--

DROP TABLE IF EXISTS `customer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customer` (
  `customer_id` char(36) NOT NULL,
  `org_id` char(36) NOT NULL,
  `name` varchar(255) NOT NULL,
  `tax_id` varchar(50) DEFAULT NULL,
  `street_address` varchar(255) DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `state` varchar(100) DEFAULT NULL,
  `zip_code` varchar(20) DEFAULT NULL,
  `country` varchar(100) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `is_archived` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`customer_id`),
  KEY `idx_customer_org_id` (`org_id`),
  KEY `idx_customer_archived` (`org_id`,`is_archived`),
  CONSTRAINT `customer_ibfk_1` FOREIGN KEY (`org_id`) REFERENCES `organization` (`org_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customer`
--

LOCK TABLES `customer` WRITE;
/*!40000 ALTER TABLE `customer` DISABLE KEYS */;
INSERT INTO `customer` VALUES ('b15d0c5b-d119-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','Nike Inc','Tx-1202','123 Jackson Boulevard','Boston','Massachusets','12345','USA','2025-12-04 14:01:12',1);
/*!40000 ALTER TABLE `customer` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `customer_contact_assignment`
--

DROP TABLE IF EXISTS `customer_contact_assignment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customer_contact_assignment` (
  `customer_id` char(36) NOT NULL,
  `person_id` char(36) NOT NULL,
  `role` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`customer_id`,`person_id`),
  KEY `person_id` (`person_id`),
  CONSTRAINT `customer_contact_assignment_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`) ON DELETE CASCADE,
  CONSTRAINT `customer_contact_assignment_ibfk_2` FOREIGN KEY (`person_id`) REFERENCES `person` (`person_id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customer_contact_assignment`
--

LOCK TABLES `customer_contact_assignment` WRITE;
/*!40000 ALTER TABLE `customer_contact_assignment` DISABLE KEYS */;
/*!40000 ALTER TABLE `customer_contact_assignment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `customer_user`
--

DROP TABLE IF EXISTS `customer_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customer_user` (
  `customer_user_id` char(36) NOT NULL,
  `customer_id` char(36) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`customer_user_id`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_customer_user_customer` (`customer_id`),
  KEY `idx_customer_user_email` (`email`),
  CONSTRAINT `customer_user_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customer_user`
--

LOCK TABLES `customer_user` WRITE;
/*!40000 ALTER TABLE `customer_user` DISABLE KEYS */;
INSERT INTO `customer_user` VALUES ('f84c694d-d11f-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','test@test.com','$2b$12$rEUcUVOgJFnF/tDu6mD/K.aE9NPr2PLEuU26DPJsp3/3LzndVjX1e','2025-12-04 14:46:08');
/*!40000 ALTER TABLE `customer_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `field`
--

DROP TABLE IF EXISTS `field`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `field` (
  `field_id` char(36) NOT NULL,
  `section_id` char(36) NOT NULL,
  `name` varchar(100) NOT NULL,
  `display_name` varchar(100) DEFAULT NULL,
  `label` varchar(100) DEFAULT NULL,
  `data_type` varchar(20) NOT NULL,
  `is_required` tinyint(1) DEFAULT '0',
  `is_currency` tinyint(1) DEFAULT '0',
  `ordinal` int DEFAULT NULL,
  `calculation_formula` text,
  PRIMARY KEY (`field_id`),
  KEY `idx_field_section` (`section_id`),
  CONSTRAINT `field_ibfk_1` FOREIGN KEY (`section_id`) REFERENCES `section` (`section_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `field`
--

LOCK TABLES `field` WRITE;
/*!40000 ALTER TABLE `field` DISABLE KEYS */;
INSERT INTO `field` VALUES ('89618cfa-d119-11f0-a496-e40d36ebc7e6','896059a4-d119-11f0-a496-e40d36ebc7e6','name','name','name','string',1,0,1,NULL),('89632a6c-d119-11f0-a496-e40d36ebc7e6','896059a4-d119-11f0-a496-e40d36ebc7e6','qty','qty','qty','number',1,0,2,NULL),('89656ae7-d119-11f0-a496-e40d36ebc7e6','896059a4-d119-11f0-a496-e40d36ebc7e6','price','price','price','number',0,1,3,NULL),('8966dcf1-d119-11f0-a496-e40d36ebc7e6','896059a4-d119-11f0-a496-e40d36ebc7e6','total','total','total','number',0,1,4,'this.price * this.qty'),('8969d52a-d119-11f0-a496-e40d36ebc7e6','896816f5-d119-11f0-a496-e40d36ebc7e6','Total','Total','Total','number',0,1,1,'sum(Items.amount)'),('896b3cc4-d119-11f0-a496-e40d36ebc7e6','896816f5-d119-11f0-a496-e40d36ebc7e6','Tax','Tax','Tax','number',0,1,2,'Total * 0.1'),('896cc593-d119-11f0-a496-e40d36ebc7e6','896816f5-d119-11f0-a496-e40d36ebc7e6','Grand_Total','Grand Total','Grand Total','number',0,1,3,'Total + Tax'),('8d1887cb-d120-11f0-a496-e40d36ebc7e6','8d0d20bd-d120-11f0-a496-e40d36ebc7e6','name','name','name','string',1,0,1,NULL),('8d1ea15c-d120-11f0-a496-e40d36ebc7e6','8d0d20bd-d120-11f0-a496-e40d36ebc7e6','qty','qty','qty','number',1,0,2,NULL),('8d24c05d-d120-11f0-a496-e40d36ebc7e6','8d0d20bd-d120-11f0-a496-e40d36ebc7e6','price','price','price','number',1,1,3,NULL),('8d291313-d120-11f0-a496-e40d36ebc7e6','8d0d20bd-d120-11f0-a496-e40d36ebc7e6','total','total','total','number',0,1,4,'this.price * this.qty'),('8d2ca1d4-d120-11f0-a496-e40d36ebc7e6','8d2b1eed-d120-11f0-a496-e40d36ebc7e6','Total','Total','Total','number',0,1,1,'sum(Items.total)'),('8d2e2279-d120-11f0-a496-e40d36ebc7e6','8d2b1eed-d120-11f0-a496-e40d36ebc7e6','Tax','Tax','Tax','number',0,1,2,'Total * 0.1'),('8d2fb217-d120-11f0-a496-e40d36ebc7e6','8d2b1eed-d120-11f0-a496-e40d36ebc7e6','Grand_Total','Grand Total','Grand Total','number',0,1,3,'Total + Tax'),('998a4fd7-d11d-11f0-a496-e40d36ebc7e6','998893ab-d11d-11f0-a496-e40d36ebc7e6','name','name','name','string',1,0,1,NULL),('998c6397-d11d-11f0-a496-e40d36ebc7e6','998893ab-d11d-11f0-a496-e40d36ebc7e6','qty','qty','qty','number',1,0,2,NULL),('998e5586-d11d-11f0-a496-e40d36ebc7e6','998893ab-d11d-11f0-a496-e40d36ebc7e6','price','price','price','number',0,1,3,NULL),('99907bf2-d11d-11f0-a496-e40d36ebc7e6','998893ab-d11d-11f0-a496-e40d36ebc7e6','total','total','total','number',0,1,4,'this.price * this.qty'),('99951375-d11d-11f0-a496-e40d36ebc7e6','9992ac33-d11d-11f0-a496-e40d36ebc7e6','Total','Total','Total','number',0,1,1,'sum(Items.amount)'),('9996fed6-d11d-11f0-a496-e40d36ebc7e6','9992ac33-d11d-11f0-a496-e40d36ebc7e6','Tax','Tax','Tax','number',0,1,2,'Total * 0.1'),('9998eb31-d11d-11f0-a496-e40d36ebc7e6','9992ac33-d11d-11f0-a496-e40d36ebc7e6','Grand_Total','Grand Total','Grand Total','number',0,1,3,'Total + Tax'),('ca3715e0-d11d-11f0-a496-e40d36ebc7e6','ca370422-d11d-11f0-a496-e40d36ebc7e6','name','name','name','string',1,0,1,NULL),('ca37164f-d11d-11f0-a496-e40d36ebc7e6','ca370422-d11d-11f0-a496-e40d36ebc7e6','qty','qty','qty','number',1,0,2,NULL),('ca37167e-d11d-11f0-a496-e40d36ebc7e6','ca370422-d11d-11f0-a496-e40d36ebc7e6','price','price','price','number',0,0,3,NULL),('ca3716fa-d11d-11f0-a496-e40d36ebc7e6','ca370422-d11d-11f0-a496-e40d36ebc7e6','total','total','total','number',0,0,4,'this.price * this.qty'),('ca37184e-d11d-11f0-a496-e40d36ebc7e6','ca370463-d11d-11f0-a496-e40d36ebc7e6','Total','Total','Total','number',0,0,1,'sum(Items.total)'),('ca371884-d11d-11f0-a496-e40d36ebc7e6','ca370463-d11d-11f0-a496-e40d36ebc7e6','Tax','Tax','Tax','number',0,0,2,'Total * 0.1'),('ca3718a6-d11d-11f0-a496-e40d36ebc7e6','ca370463-d11d-11f0-a496-e40d36ebc7e6','Grand_Total','Grand Total','Grand Total','number',0,0,3,'Total + Tax');
/*!40000 ALTER TABLE `field` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `invoice`
--

DROP TABLE IF EXISTS `invoice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `invoice` (
  `invoice_id` char(36) NOT NULL,
  `org_id` char(36) NOT NULL,
  `customer_id` char(36) NOT NULL,
  `template_id` char(36) DEFAULT NULL,
  `template_version` int DEFAULT NULL,
  `issue_date` date DEFAULT NULL,
  `due_date` date DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `total_amount` decimal(15,4) DEFAULT '0.0000',
  PRIMARY KEY (`invoice_id`),
  KEY `idx_invoice_org_id` (`org_id`),
  KEY `idx_invoice_customer_id` (`customer_id`),
  KEY `idx_invoice_status` (`status`),
  KEY `idx_invoice_template` (`template_id`,`template_version`),
  CONSTRAINT `invoice_ibfk_1` FOREIGN KEY (`org_id`) REFERENCES `organization` (`org_id`) ON DELETE CASCADE,
  CONSTRAINT `invoice_ibfk_2` FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`) ON DELETE RESTRICT,
  CONSTRAINT `invoice_ibfk_3` FOREIGN KEY (`template_id`, `template_version`) REFERENCES `template` (`template_id`, `version`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `invoice`
--

LOCK TABLES `invoice` WRITE;
/*!40000 ALTER TABLE `invoice` DISABLE KEYS */;
INSERT INTO `invoice` VALUES ('a7408add-d11d-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',1,'2025-12-04',NULL,'draft',0.0000),('aa1e1c32-d120-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','8d06b26e-d120-11f0-a496-e40d36ebc7e6',1,'2025-12-04',NULL,'pending',21000.0000),('c3a01c95-d11e-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'2025-10-18','2025-11-13','paid',5592.4000),('c3db46f5-d11e-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'2025-11-07','2025-12-13','pending',18654.9000),('c40bd4ff-d11e-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'2025-12-17','2026-01-07','pending',5852.0000),('c42a9814-d11e-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'2025-10-05','2025-11-04','draft',17339.3000),('c456bd67-d11e-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'2025-12-18','2026-01-14','pending',5717.8000),('c47ea693-d11e-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'2025-10-21','2025-11-29','paid',11116.6000),('c4aa7e43-d11e-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'2025-09-14','2025-10-28','paid',6355.8000),('c4dda99b-d11e-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'2025-11-03','2025-12-05','draft',14159.2000),('c51d4a4c-d11e-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'2025-08-22','2025-10-01','draft',5351.5000),('c54eb9dc-d11e-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'2025-08-14','2025-09-26','pending',7585.6000),('c5768987-d11e-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'2025-12-03','2026-01-05','pending',7491.0000),('c5950a4f-d11e-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'2025-10-24','2025-12-08','paid',13774.2000),('c5d27f09-d11e-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'2025-09-02','2025-09-30','pending',4517.7000),('c5f76d6d-d11e-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'2025-09-27','2025-10-28','pending',7871.6000),('c633a9ca-d11e-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'2025-11-10','2025-12-12','draft',9815.3000),('c6690dab-d11e-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'2025-08-24','2025-10-07','draft',9603.0000),('c68df805-d11e-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'2025-09-02','2025-10-02','pending',5017.1000),('c6bc2949-d11e-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'2025-11-27','2026-01-01','paid',6135.8000),('c6e3ce30-d11e-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'2025-08-11','2025-09-10','pending',3540.9000),('cf090d0e-d119-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','895ef75d-d119-11f0-a496-e40d36ebc7e6',1,'2025-12-04','2026-01-04','draft',0.0000),('e0c04dd1-d11d-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','b15d0c5b-d119-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'2025-12-04',NULL,'pending',3300.0000);
/*!40000 ALTER TABLE `invoice` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `invoice_value`
--

DROP TABLE IF EXISTS `invoice_value`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `invoice_value` (
  `value_id` char(36) NOT NULL,
  `invoice_id` char(36) NOT NULL,
  `field_id` char(36) DEFAULT NULL,
  `val_string` text,
  `val_number` decimal(15,4) DEFAULT NULL,
  `val_date` date DEFAULT NULL,
  `val_boolean` tinyint(1) DEFAULT NULL,
  `ordinal` int DEFAULT '0',
  PRIMARY KEY (`value_id`),
  KEY `idx_invoice_value_invoice` (`invoice_id`),
  KEY `idx_invoice_value_field` (`field_id`),
  CONSTRAINT `invoice_value_ibfk_1` FOREIGN KEY (`invoice_id`) REFERENCES `invoice` (`invoice_id`) ON DELETE CASCADE,
  CONSTRAINT `invoice_value_ibfk_2` FOREIGN KEY (`field_id`) REFERENCES `field` (`field_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `invoice_value`
--

LOCK TABLES `invoice_value` WRITE;
/*!40000 ALTER TABLE `invoice_value` DISABLE KEYS */;
INSERT INTO `invoice_value` VALUES ('a741dad3-d11d-11f0-a496-e40d36ebc7e6','a7408add-d11d-11f0-a496-e40d36ebc7e6','998a4fd7-d11d-11f0-a496-e40d36ebc7e6','test',NULL,NULL,NULL,0),('a743126a-d11d-11f0-a496-e40d36ebc7e6','a7408add-d11d-11f0-a496-e40d36ebc7e6','998c6397-d11d-11f0-a496-e40d36ebc7e6',NULL,1.0000,NULL,NULL,0),('a7440adf-d11d-11f0-a496-e40d36ebc7e6','a7408add-d11d-11f0-a496-e40d36ebc7e6','998e5586-d11d-11f0-a496-e40d36ebc7e6',NULL,12.0000,NULL,NULL,0),('a744fce0-d11d-11f0-a496-e40d36ebc7e6','a7408add-d11d-11f0-a496-e40d36ebc7e6','99907bf2-d11d-11f0-a496-e40d36ebc7e6',NULL,12.0000,NULL,NULL,0),('a74603f3-d11d-11f0-a496-e40d36ebc7e6','a7408add-d11d-11f0-a496-e40d36ebc7e6','998a4fd7-d11d-11f0-a496-e40d36ebc7e6','new',NULL,NULL,NULL,1),('a74706e2-d11d-11f0-a496-e40d36ebc7e6','a7408add-d11d-11f0-a496-e40d36ebc7e6','998c6397-d11d-11f0-a496-e40d36ebc7e6',NULL,2.0000,NULL,NULL,1),('a7481623-d11d-11f0-a496-e40d36ebc7e6','a7408add-d11d-11f0-a496-e40d36ebc7e6','998e5586-d11d-11f0-a496-e40d36ebc7e6',NULL,12.0000,NULL,NULL,1),('a7491775-d11d-11f0-a496-e40d36ebc7e6','a7408add-d11d-11f0-a496-e40d36ebc7e6','99907bf2-d11d-11f0-a496-e40d36ebc7e6',NULL,24.0000,NULL,NULL,1),('a74a1993-d11d-11f0-a496-e40d36ebc7e6','a7408add-d11d-11f0-a496-e40d36ebc7e6','99951375-d11d-11f0-a496-e40d36ebc7e6',NULL,0.0000,NULL,NULL,0),('a74b0377-d11d-11f0-a496-e40d36ebc7e6','a7408add-d11d-11f0-a496-e40d36ebc7e6','9996fed6-d11d-11f0-a496-e40d36ebc7e6',NULL,0.0000,NULL,NULL,0),('a74c1316-d11d-11f0-a496-e40d36ebc7e6','a7408add-d11d-11f0-a496-e40d36ebc7e6','9998eb31-d11d-11f0-a496-e40d36ebc7e6',NULL,0.0000,NULL,NULL,0),('aa1fb104-d120-11f0-a496-e40d36ebc7e6','aa1e1c32-d120-11f0-a496-e40d36ebc7e6','8d1887cb-d120-11f0-a496-e40d36ebc7e6','shoe',NULL,NULL,NULL,0),('aa20c626-d120-11f0-a496-e40d36ebc7e6','aa1e1c32-d120-11f0-a496-e40d36ebc7e6','8d1ea15c-d120-11f0-a496-e40d36ebc7e6',NULL,100.0000,NULL,NULL,0),('aa21d669-d120-11f0-a496-e40d36ebc7e6','aa1e1c32-d120-11f0-a496-e40d36ebc7e6','8d24c05d-d120-11f0-a496-e40d36ebc7e6',NULL,200.0000,NULL,NULL,0),('aa230bd9-d120-11f0-a496-e40d36ebc7e6','aa1e1c32-d120-11f0-a496-e40d36ebc7e6','8d291313-d120-11f0-a496-e40d36ebc7e6',NULL,20000.0000,NULL,NULL,0),('aa241720-d120-11f0-a496-e40d36ebc7e6','aa1e1c32-d120-11f0-a496-e40d36ebc7e6','8d1887cb-d120-11f0-a496-e40d36ebc7e6','socks',NULL,NULL,NULL,1),('aa2575fe-d120-11f0-a496-e40d36ebc7e6','aa1e1c32-d120-11f0-a496-e40d36ebc7e6','8d1ea15c-d120-11f0-a496-e40d36ebc7e6',NULL,200.0000,NULL,NULL,1),('aa26a847-d120-11f0-a496-e40d36ebc7e6','aa1e1c32-d120-11f0-a496-e40d36ebc7e6','8d24c05d-d120-11f0-a496-e40d36ebc7e6',NULL,5.0000,NULL,NULL,1),('aa27c574-d120-11f0-a496-e40d36ebc7e6','aa1e1c32-d120-11f0-a496-e40d36ebc7e6','8d291313-d120-11f0-a496-e40d36ebc7e6',NULL,1000.0000,NULL,NULL,1),('aa2923a3-d120-11f0-a496-e40d36ebc7e6','aa1e1c32-d120-11f0-a496-e40d36ebc7e6','8d2ca1d4-d120-11f0-a496-e40d36ebc7e6',NULL,21000.0000,NULL,NULL,0),('aa2a4c17-d120-11f0-a496-e40d36ebc7e6','aa1e1c32-d120-11f0-a496-e40d36ebc7e6','8d2e2279-d120-11f0-a496-e40d36ebc7e6',NULL,2100.0000,NULL,NULL,0),('aa2b7143-d120-11f0-a496-e40d36ebc7e6','aa1e1c32-d120-11f0-a496-e40d36ebc7e6','8d2fb217-d120-11f0-a496-e40d36ebc7e6',NULL,23100.0000,NULL,NULL,0),('c3a47d6c-d11e-11f0-a496-e40d36ebc7e6','c3a01c95-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Quality Assurance',NULL,NULL,NULL,1),('c3a6acef-d11e-11f0-a496-e40d36ebc7e6','c3a01c95-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,36.0000,NULL,NULL,1),('c3a89550-d11e-11f0-a496-e40d36ebc7e6','c3a01c95-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,64.0000,NULL,NULL,1),('c3aa7781-d11e-11f0-a496-e40d36ebc7e6','c3a01c95-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Maintenance Contract',NULL,NULL,NULL,2),('c3acc8c7-d11e-11f0-a496-e40d36ebc7e6','c3a01c95-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,12.0000,NULL,NULL,2),('c3aedc4d-d11e-11f0-a496-e40d36ebc7e6','c3a01c95-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,178.0000,NULL,NULL,2),('c3b0ce17-d11e-11f0-a496-e40d36ebc7e6','c3a01c95-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Documentation',NULL,NULL,NULL,3),('c3b2d8ac-d11e-11f0-a496-e40d36ebc7e6','c3a01c95-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,4.0000,NULL,NULL,3),('c3b50b66-d11e-11f0-a496-e40d36ebc7e6','c3a01c95-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,122.0000,NULL,NULL,3),('c3b70115-d11e-11f0-a496-e40d36ebc7e6','c3a01c95-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,4),('c3b92fc9-d11e-11f0-a496-e40d36ebc7e6','c3a01c95-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,1.0000,NULL,NULL,4),('c3bb701e-d11e-11f0-a496-e40d36ebc7e6','c3a01c95-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,156.0000,NULL,NULL,4),('c3cb9958-d11e-11f0-a496-e40d36ebc7e6','c3a01c95-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,2304.0000,NULL,NULL,1),('c3cda370-d11e-11f0-a496-e40d36ebc7e6','c3a01c95-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,2136.0000,NULL,NULL,2),('c3cff14b-d11e-11f0-a496-e40d36ebc7e6','c3a01c95-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,488.0000,NULL,NULL,3),('c3d24cc2-d11e-11f0-a496-e40d36ebc7e6','c3a01c95-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,156.0000,NULL,NULL,4),('c3d42362-d11e-11f0-a496-e40d36ebc7e6','c3a01c95-d11e-11f0-a496-e40d36ebc7e6','ca37184e-d11d-11f0-a496-e40d36ebc7e6',NULL,5084.0000,NULL,NULL,0),('c3d57f8b-d11e-11f0-a496-e40d36ebc7e6','c3a01c95-d11e-11f0-a496-e40d36ebc7e6','ca371884-d11d-11f0-a496-e40d36ebc7e6',NULL,508.4000,NULL,NULL,0),('c3d6cea9-d11e-11f0-a496-e40d36ebc7e6','c3a01c95-d11e-11f0-a496-e40d36ebc7e6','ca3718a6-d11d-11f0-a496-e40d36ebc7e6',NULL,5592.4000,NULL,NULL,0),('c3df5907-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Maintenance Contract',NULL,NULL,NULL,1),('c3e125e3-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,17.0000,NULL,NULL,1),('c3e2c177-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,187.0000,NULL,NULL,1),('c3e3f6f5-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Design Work',NULL,NULL,NULL,2),('c3e53718-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,22.0000,NULL,NULL,2),('c3e6a5e5-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,176.0000,NULL,NULL,2),('c3e80301-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Software Development',NULL,NULL,NULL,3),('c3e92d20-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,27.0000,NULL,NULL,3),('c3ea7fc4-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,178.0000,NULL,NULL,3),('c3eda57b-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,4),('c3ef1e30-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,37.0000,NULL,NULL,4),('c3f0a66c-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,88.0000,NULL,NULL,4),('c3f216a9-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Web Development Services',NULL,NULL,NULL,5),('c3f3b399-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,13.0000,NULL,NULL,5),('c3f540ab-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,142.0000,NULL,NULL,5),('c3fcac64-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,3179.0000,NULL,NULL,1),('c3fe39c5-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,3872.0000,NULL,NULL,2),('c3fff4c7-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,4806.0000,NULL,NULL,3),('c4018ed7-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,3256.0000,NULL,NULL,4),('c4031fca-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,1846.0000,NULL,NULL,5),('c40481d7-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca37184e-d11d-11f0-a496-e40d36ebc7e6',NULL,16959.0000,NULL,NULL,0),('c405dae3-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca371884-d11d-11f0-a496-e40d36ebc7e6',NULL,1695.9000,NULL,NULL,0),('c407d470-d11e-11f0-a496-e40d36ebc7e6','c3db46f5-d11e-11f0-a496-e40d36ebc7e6','ca3718a6-d11d-11f0-a496-e40d36ebc7e6',NULL,18654.9000,NULL,NULL,0),('c40efa04-d11e-11f0-a496-e40d36ebc7e6','c40bd4ff-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Maintenance Contract',NULL,NULL,NULL,1),('c4103754-d11e-11f0-a496-e40d36ebc7e6','c40bd4ff-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,22.0000,NULL,NULL,1),('c411b82e-d11e-11f0-a496-e40d36ebc7e6','c40bd4ff-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,102.0000,NULL,NULL,1),('c4134fe9-d11e-11f0-a496-e40d36ebc7e6','c40bd4ff-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Training Services',NULL,NULL,NULL,2),('c414ea38-d11e-11f0-a496-e40d36ebc7e6','c40bd4ff-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,6.0000,NULL,NULL,2),('c41671fd-d11e-11f0-a496-e40d36ebc7e6','c40bd4ff-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,74.0000,NULL,NULL,2),('c418208e-d11e-11f0-a496-e40d36ebc7e6','c40bd4ff-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Documentation',NULL,NULL,NULL,3),('c419af3f-d11e-11f0-a496-e40d36ebc7e6','c40bd4ff-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,28.0000,NULL,NULL,3),('c41b2389-d11e-11f0-a496-e40d36ebc7e6','c40bd4ff-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,94.0000,NULL,NULL,3),('c420e2b2-d11e-11f0-a496-e40d36ebc7e6','c40bd4ff-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,2244.0000,NULL,NULL,1),('c42258d0-d11e-11f0-a496-e40d36ebc7e6','c40bd4ff-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,444.0000,NULL,NULL,2),('c4239de7-d11e-11f0-a496-e40d36ebc7e6','c40bd4ff-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,2632.0000,NULL,NULL,3),('c4252c9e-d11e-11f0-a496-e40d36ebc7e6','c40bd4ff-d11e-11f0-a496-e40d36ebc7e6','ca37184e-d11d-11f0-a496-e40d36ebc7e6',NULL,5320.0000,NULL,NULL,0),('c4269620-d11e-11f0-a496-e40d36ebc7e6','c40bd4ff-d11e-11f0-a496-e40d36ebc7e6','ca371884-d11d-11f0-a496-e40d36ebc7e6',NULL,532.0000,NULL,NULL,0),('c427fc5b-d11e-11f0-a496-e40d36ebc7e6','c40bd4ff-d11e-11f0-a496-e40d36ebc7e6','ca3718a6-d11d-11f0-a496-e40d36ebc7e6',NULL,5852.0000,NULL,NULL,0),('c42dc795-d11e-11f0-a496-e40d36ebc7e6','c42a9814-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Web Development Services',NULL,NULL,NULL,1),('c42f4bba-d11e-11f0-a496-e40d36ebc7e6','c42a9814-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,4.0000,NULL,NULL,1),('c4312897-d11e-11f0-a496-e40d36ebc7e6','c42a9814-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,166.0000,NULL,NULL,1),('c432a810-d11e-11f0-a496-e40d36ebc7e6','c42a9814-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Quality Assurance',NULL,NULL,NULL,2),('c4346b5d-d11e-11f0-a496-e40d36ebc7e6','c42a9814-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,39.0000,NULL,NULL,2),('c4367964-d11e-11f0-a496-e40d36ebc7e6','c42a9814-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,180.0000,NULL,NULL,2),('c438d2a1-d11e-11f0-a496-e40d36ebc7e6','c42a9814-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Web Development Services',NULL,NULL,NULL,3),('c43b92f9-d11e-11f0-a496-e40d36ebc7e6','c42a9814-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,15.0000,NULL,NULL,3),('c43e0d33-d11e-11f0-a496-e40d36ebc7e6','c42a9814-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,102.0000,NULL,NULL,3),('c4408b79-d11e-11f0-a496-e40d36ebc7e6','c42a9814-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Maintenance Contract',NULL,NULL,NULL,4),('c4430758-d11e-11f0-a496-e40d36ebc7e6','c42a9814-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,37.0000,NULL,NULL,4),('c4455c04-d11e-11f0-a496-e40d36ebc7e6','c42a9814-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,177.0000,NULL,NULL,4),('c44cf203-d11e-11f0-a496-e40d36ebc7e6','c42a9814-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,664.0000,NULL,NULL,1),('c44e5867-d11e-11f0-a496-e40d36ebc7e6','c42a9814-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,7020.0000,NULL,NULL,2),('c44f9b34-d11e-11f0-a496-e40d36ebc7e6','c42a9814-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,1530.0000,NULL,NULL,3),('c450e702-d11e-11f0-a496-e40d36ebc7e6','c42a9814-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,6549.0000,NULL,NULL,4),('c4526cd5-d11e-11f0-a496-e40d36ebc7e6','c42a9814-d11e-11f0-a496-e40d36ebc7e6','ca37184e-d11d-11f0-a496-e40d36ebc7e6',NULL,15763.0000,NULL,NULL,0),('c453d0d5-d11e-11f0-a496-e40d36ebc7e6','c42a9814-d11e-11f0-a496-e40d36ebc7e6','ca371884-d11d-11f0-a496-e40d36ebc7e6',NULL,1576.3000,NULL,NULL,0),('c455205f-d11e-11f0-a496-e40d36ebc7e6','c42a9814-d11e-11f0-a496-e40d36ebc7e6','ca3718a6-d11d-11f0-a496-e40d36ebc7e6',NULL,17339.3000,NULL,NULL,0),('c4598868-d11e-11f0-a496-e40d36ebc7e6','c456bd67-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Web Development Services',NULL,NULL,NULL,1),('c45ab4e6-d11e-11f0-a496-e40d36ebc7e6','c456bd67-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,31.0000,NULL,NULL,1),('c45c2e35-d11e-11f0-a496-e40d36ebc7e6','c456bd67-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,58.0000,NULL,NULL,1),('c45deaab-d11e-11f0-a496-e40d36ebc7e6','c456bd67-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Quality Assurance',NULL,NULL,NULL,2),('c4600d11-d11e-11f0-a496-e40d36ebc7e6','c456bd67-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,20.0000,NULL,NULL,2),('c46211d3-d11e-11f0-a496-e40d36ebc7e6','c456bd67-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,170.0000,NULL,NULL,2),('c47094be-d11e-11f0-a496-e40d36ebc7e6','c456bd67-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,1798.0000,NULL,NULL,1),('c4733017-d11e-11f0-a496-e40d36ebc7e6','c456bd67-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,3400.0000,NULL,NULL,2),('c4757400-d11e-11f0-a496-e40d36ebc7e6','c456bd67-d11e-11f0-a496-e40d36ebc7e6','ca37184e-d11d-11f0-a496-e40d36ebc7e6',NULL,5198.0000,NULL,NULL,0),('c4776ef8-d11e-11f0-a496-e40d36ebc7e6','c456bd67-d11e-11f0-a496-e40d36ebc7e6','ca371884-d11d-11f0-a496-e40d36ebc7e6',NULL,519.8000,NULL,NULL,0),('c4797194-d11e-11f0-a496-e40d36ebc7e6','c456bd67-d11e-11f0-a496-e40d36ebc7e6','ca3718a6-d11d-11f0-a496-e40d36ebc7e6',NULL,5717.8000,NULL,NULL,0),('c482fd56-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Maintenance Contract',NULL,NULL,NULL,1),('c484b707-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,22.0000,NULL,NULL,1),('c4865f3a-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,192.0000,NULL,NULL,1),('c487a142-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Quality Assurance',NULL,NULL,NULL,2),('c488eb60-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,28.0000,NULL,NULL,2),('c48a730a-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,52.0000,NULL,NULL,2),('c48bed87-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,3),('c48d3793-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,4.0000,NULL,NULL,3),('c48ea27d-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,119.0000,NULL,NULL,3),('c49003d6-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Web Development Services',NULL,NULL,NULL,4),('c4914360-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,29.0000,NULL,NULL,4),('c492bf9e-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,53.0000,NULL,NULL,4),('c4941add-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Training Services',NULL,NULL,NULL,5),('c495caf7-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,19.0000,NULL,NULL,5),('c4978546-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,127.0000,NULL,NULL,5),('c49d6bd7-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,4224.0000,NULL,NULL,1),('c49ea5a6-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,1456.0000,NULL,NULL,2),('c49ff334-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,476.0000,NULL,NULL,3),('c4a166e2-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,1537.0000,NULL,NULL,4),('c4a2ce9f-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,2413.0000,NULL,NULL,5),('c4a428e2-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca37184e-d11d-11f0-a496-e40d36ebc7e6',NULL,10106.0000,NULL,NULL,0),('c4a594f3-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca371884-d11d-11f0-a496-e40d36ebc7e6',NULL,1010.6000,NULL,NULL,0),('c4a6e6ec-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6','ca3718a6-d11d-11f0-a496-e40d36ebc7e6',NULL,11116.6000,NULL,NULL,0),('c4ad576b-d11e-11f0-a496-e40d36ebc7e6','c4aa7e43-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Design Work',NULL,NULL,NULL,1),('c4aecab4-d11e-11f0-a496-e40d36ebc7e6','c4aa7e43-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,10.0000,NULL,NULL,1),('c4b0003e-d11e-11f0-a496-e40d36ebc7e6','c4aa7e43-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,80.0000,NULL,NULL,1),('c4b17d08-d11e-11f0-a496-e40d36ebc7e6','c4aa7e43-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,2),('c4b2ae97-d11e-11f0-a496-e40d36ebc7e6','c4aa7e43-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,10.0000,NULL,NULL,2),('c4b4207f-d11e-11f0-a496-e40d36ebc7e6','c4aa7e43-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,170.0000,NULL,NULL,2),('c4b57249-d11e-11f0-a496-e40d36ebc7e6','c4aa7e43-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Web Development Services',NULL,NULL,NULL,3),('c4b73907-d11e-11f0-a496-e40d36ebc7e6','c4aa7e43-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,17.0000,NULL,NULL,3),('c4b8c12f-d11e-11f0-a496-e40d36ebc7e6','c4aa7e43-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,66.0000,NULL,NULL,3),('c4ba72ae-d11e-11f0-a496-e40d36ebc7e6','c4aa7e43-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Software Development',NULL,NULL,NULL,4),('c4bc5090-d11e-11f0-a496-e40d36ebc7e6','c4aa7e43-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,22.0000,NULL,NULL,4),('c4be252a-d11e-11f0-a496-e40d36ebc7e6','c4aa7e43-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,98.0000,NULL,NULL,4),('c4ceb103-d11e-11f0-a496-e40d36ebc7e6','c4aa7e43-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,800.0000,NULL,NULL,1),('c4d08620-d11e-11f0-a496-e40d36ebc7e6','c4aa7e43-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,1700.0000,NULL,NULL,2),('c4d2050e-d11e-11f0-a496-e40d36ebc7e6','c4aa7e43-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,1122.0000,NULL,NULL,3),('c4d3f14c-d11e-11f0-a496-e40d36ebc7e6','c4aa7e43-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,2156.0000,NULL,NULL,4),('c4d5cc81-d11e-11f0-a496-e40d36ebc7e6','c4aa7e43-d11e-11f0-a496-e40d36ebc7e6','ca37184e-d11d-11f0-a496-e40d36ebc7e6',NULL,5778.0000,NULL,NULL,0),('c4d76d12-d11e-11f0-a496-e40d36ebc7e6','c4aa7e43-d11e-11f0-a496-e40d36ebc7e6','ca371884-d11d-11f0-a496-e40d36ebc7e6',NULL,577.8000,NULL,NULL,0),('c4d8da82-d11e-11f0-a496-e40d36ebc7e6','c4aa7e43-d11e-11f0-a496-e40d36ebc7e6','ca3718a6-d11d-11f0-a496-e40d36ebc7e6',NULL,6355.8000,NULL,NULL,0),('c4e1dc37-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Project Management',NULL,NULL,NULL,1),('c4e3e823-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,12.0000,NULL,NULL,1),('c4e5a99b-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,73.0000,NULL,NULL,1),('c4e78b3c-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Software Development',NULL,NULL,NULL,2),('c4e99192-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,9.0000,NULL,NULL,2),('c4eb6b85-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,187.0000,NULL,NULL,2),('c4edc9c8-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Design Work',NULL,NULL,NULL,3),('c4efe62c-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,35.0000,NULL,NULL,3),('c4f1f87a-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,92.0000,NULL,NULL,3),('c4f3dfd2-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Design Work',NULL,NULL,NULL,4),('c4f5f3a8-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,28.0000,NULL,NULL,4),('c4f7e2e6-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,178.0000,NULL,NULL,4),('c4f93a53-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Software Development',NULL,NULL,NULL,5),('c4fa98c3-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,37.0000,NULL,NULL,5),('c4fbfc33-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,57.0000,NULL,NULL,5),('c50d023a-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,876.0000,NULL,NULL,1),('c50f31ce-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,1683.0000,NULL,NULL,2),('c5110c5b-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,3220.0000,NULL,NULL,3),('c512eb11-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,4984.0000,NULL,NULL,4),('c51515ce-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,2109.0000,NULL,NULL,5),('c5177fee-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca37184e-d11d-11f0-a496-e40d36ebc7e6',NULL,12872.0000,NULL,NULL,0),('c519833f-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca371884-d11d-11f0-a496-e40d36ebc7e6',NULL,1287.2000,NULL,NULL,0),('c51b3388-d11e-11f0-a496-e40d36ebc7e6','c4dda99b-d11e-11f0-a496-e40d36ebc7e6','ca3718a6-d11d-11f0-a496-e40d36ebc7e6',NULL,14159.2000,NULL,NULL,0),('c5219ca4-d11e-11f0-a496-e40d36ebc7e6','c51d4a4c-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Quality Assurance',NULL,NULL,NULL,1),('c523978b-d11e-11f0-a496-e40d36ebc7e6','c51d4a4c-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,7.0000,NULL,NULL,1),('c525aced-d11e-11f0-a496-e40d36ebc7e6','c51d4a4c-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,83.0000,NULL,NULL,1),('c527adce-d11e-11f0-a496-e40d36ebc7e6','c51d4a4c-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,2),('c5297358-d11e-11f0-a496-e40d36ebc7e6','c51d4a4c-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,23.0000,NULL,NULL,2),('c52b49d0-d11e-11f0-a496-e40d36ebc7e6','c51d4a4c-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,100.0000,NULL,NULL,2),('c52deb3f-d11e-11f0-a496-e40d36ebc7e6','c51d4a4c-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Design Work',NULL,NULL,NULL,3),('c530ff29-d11e-11f0-a496-e40d36ebc7e6','c51d4a4c-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,31.0000,NULL,NULL,3),('c533f319-d11e-11f0-a496-e40d36ebc7e6','c51d4a4c-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,64.0000,NULL,NULL,3),('c54319ae-d11e-11f0-a496-e40d36ebc7e6','c51d4a4c-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,581.0000,NULL,NULL,1),('c5451519-d11e-11f0-a496-e40d36ebc7e6','c51d4a4c-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,2300.0000,NULL,NULL,2),('c546fe29-d11e-11f0-a496-e40d36ebc7e6','c51d4a4c-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,1984.0000,NULL,NULL,3),('c548bb45-d11e-11f0-a496-e40d36ebc7e6','c51d4a4c-d11e-11f0-a496-e40d36ebc7e6','ca37184e-d11d-11f0-a496-e40d36ebc7e6',NULL,4865.0000,NULL,NULL,0),('c54a7811-d11e-11f0-a496-e40d36ebc7e6','c51d4a4c-d11e-11f0-a496-e40d36ebc7e6','ca371884-d11d-11f0-a496-e40d36ebc7e6',NULL,486.5000,NULL,NULL,0),('c54c44fd-d11e-11f0-a496-e40d36ebc7e6','c51d4a4c-d11e-11f0-a496-e40d36ebc7e6','ca3718a6-d11d-11f0-a496-e40d36ebc7e6',NULL,5351.5000,NULL,NULL,0),('c5524caa-d11e-11f0-a496-e40d36ebc7e6','c54eb9dc-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Quality Assurance',NULL,NULL,NULL,1),('c553af3d-d11e-11f0-a496-e40d36ebc7e6','c54eb9dc-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,24.0000,NULL,NULL,1),('c5552318-d11e-11f0-a496-e40d36ebc7e6','c54eb9dc-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,162.0000,NULL,NULL,1),('c55691aa-d11e-11f0-a496-e40d36ebc7e6','c54eb9dc-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Design Work',NULL,NULL,NULL,2),('c5580f41-d11e-11f0-a496-e40d36ebc7e6','c54eb9dc-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,18.0000,NULL,NULL,2),('c55951c6-d11e-11f0-a496-e40d36ebc7e6','c54eb9dc-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,106.0000,NULL,NULL,2),('c55a8b11-d11e-11f0-a496-e40d36ebc7e6','c54eb9dc-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Web Development Services',NULL,NULL,NULL,3),('c55bc896-d11e-11f0-a496-e40d36ebc7e6','c54eb9dc-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,2.0000,NULL,NULL,3),('c55d15e9-d11e-11f0-a496-e40d36ebc7e6','c54eb9dc-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,178.0000,NULL,NULL,3),('c55eb45f-d11e-11f0-a496-e40d36ebc7e6','c54eb9dc-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,4),('c56017f1-d11e-11f0-a496-e40d36ebc7e6','c54eb9dc-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,4.0000,NULL,NULL,4),('c56152dc-d11e-11f0-a496-e40d36ebc7e6','c54eb9dc-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,186.0000,NULL,NULL,4),('c5662f26-d11e-11f0-a496-e40d36ebc7e6','c54eb9dc-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,3888.0000,NULL,NULL,1),('c5676274-d11e-11f0-a496-e40d36ebc7e6','c54eb9dc-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,1908.0000,NULL,NULL,2),('c568e20a-d11e-11f0-a496-e40d36ebc7e6','c54eb9dc-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,356.0000,NULL,NULL,3),('c56a934d-d11e-11f0-a496-e40d36ebc7e6','c54eb9dc-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,744.0000,NULL,NULL,4),('c56caf4d-d11e-11f0-a496-e40d36ebc7e6','c54eb9dc-d11e-11f0-a496-e40d36ebc7e6','ca37184e-d11d-11f0-a496-e40d36ebc7e6',NULL,6896.0000,NULL,NULL,0),('c56f01fe-d11e-11f0-a496-e40d36ebc7e6','c54eb9dc-d11e-11f0-a496-e40d36ebc7e6','ca371884-d11d-11f0-a496-e40d36ebc7e6',NULL,689.6000,NULL,NULL,0),('c5716f67-d11e-11f0-a496-e40d36ebc7e6','c54eb9dc-d11e-11f0-a496-e40d36ebc7e6','ca3718a6-d11d-11f0-a496-e40d36ebc7e6',NULL,7585.6000,NULL,NULL,0),('c57bc403-d11e-11f0-a496-e40d36ebc7e6','c5768987-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Web Development Services',NULL,NULL,NULL,1),('c57df73f-d11e-11f0-a496-e40d36ebc7e6','c5768987-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,30.0000,NULL,NULL,1),('c5802284-d11e-11f0-a496-e40d36ebc7e6','c5768987-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,77.0000,NULL,NULL,1),('c581fbaf-d11e-11f0-a496-e40d36ebc7e6','c5768987-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Web Development Services',NULL,NULL,NULL,2),('c58366ca-d11e-11f0-a496-e40d36ebc7e6','c5768987-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,36.0000,NULL,NULL,2),('c584c8f7-d11e-11f0-a496-e40d36ebc7e6','c5768987-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,125.0000,NULL,NULL,2),('c588edea-d11e-11f0-a496-e40d36ebc7e6','c5768987-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,2310.0000,NULL,NULL,1),('c58a4cfe-d11e-11f0-a496-e40d36ebc7e6','c5768987-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,4500.0000,NULL,NULL,2),('c58b7451-d11e-11f0-a496-e40d36ebc7e6','c5768987-d11e-11f0-a496-e40d36ebc7e6','ca37184e-d11d-11f0-a496-e40d36ebc7e6',NULL,6810.0000,NULL,NULL,0),('c58cfb60-d11e-11f0-a496-e40d36ebc7e6','c5768987-d11e-11f0-a496-e40d36ebc7e6','ca371884-d11d-11f0-a496-e40d36ebc7e6',NULL,681.0000,NULL,NULL,0),('c58eef63-d11e-11f0-a496-e40d36ebc7e6','c5768987-d11e-11f0-a496-e40d36ebc7e6','ca3718a6-d11d-11f0-a496-e40d36ebc7e6',NULL,7491.0000,NULL,NULL,0),('c59a0335-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Software Development',NULL,NULL,NULL,1),('c59c7505-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,31.0000,NULL,NULL,1),('c59eb918-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,174.0000,NULL,NULL,1),('c5a0f179-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Documentation',NULL,NULL,NULL,2),('c5a33db8-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,4.0000,NULL,NULL,2),('c5a621ff-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,184.0000,NULL,NULL,2),('c5a8297b-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Maintenance Contract',NULL,NULL,NULL,3),('c5aa4c82-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,4.0000,NULL,NULL,3),('c5acbcaf-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,58.0000,NULL,NULL,3),('c5afb929-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Project Management',NULL,NULL,NULL,4),('c5b21a43-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,35.0000,NULL,NULL,4),('c5b3ebe7-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,125.0000,NULL,NULL,4),('c5b5631b-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Documentation',NULL,NULL,NULL,5),('c5b6b75c-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,17.0000,NULL,NULL,5),('c5b7e68e-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,105.0000,NULL,NULL,5),('c5c2dac6-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,5394.0000,NULL,NULL,1),('c5c4fd68-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,736.0000,NULL,NULL,2),('c5c73ff5-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,232.0000,NULL,NULL,3),('c5c8e1ee-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,4375.0000,NULL,NULL,4),('c5ca4978-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,1785.0000,NULL,NULL,5),('c5cbd1ef-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca37184e-d11d-11f0-a496-e40d36ebc7e6',NULL,12522.0000,NULL,NULL,0),('c5cd8c91-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca371884-d11d-11f0-a496-e40d36ebc7e6',NULL,1252.2000,NULL,NULL,0),('c5ced37e-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6','ca3718a6-d11d-11f0-a496-e40d36ebc7e6',NULL,13774.2000,NULL,NULL,0),('c5d53cca-d11e-11f0-a496-e40d36ebc7e6','c5d27f09-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Maintenance Contract',NULL,NULL,NULL,1),('c5d70d34-d11e-11f0-a496-e40d36ebc7e6','c5d27f09-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,1.0000,NULL,NULL,1),('c5d96c05-d11e-11f0-a496-e40d36ebc7e6','c5d27f09-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,123.0000,NULL,NULL,1),('c5db371b-d11e-11f0-a496-e40d36ebc7e6','c5d27f09-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Maintenance Contract',NULL,NULL,NULL,2),('c5dd93a3-d11e-11f0-a496-e40d36ebc7e6','c5d27f09-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,24.0000,NULL,NULL,2),('c5df76a4-d11e-11f0-a496-e40d36ebc7e6','c5d27f09-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,166.0000,NULL,NULL,2),('c5ec9018-d11e-11f0-a496-e40d36ebc7e6','c5d27f09-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,123.0000,NULL,NULL,1),('c5eed12f-d11e-11f0-a496-e40d36ebc7e6','c5d27f09-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,3984.0000,NULL,NULL,2),('c5f0a7b6-d11e-11f0-a496-e40d36ebc7e6','c5d27f09-d11e-11f0-a496-e40d36ebc7e6','ca37184e-d11d-11f0-a496-e40d36ebc7e6',NULL,4107.0000,NULL,NULL,0),('c5f21aee-d11e-11f0-a496-e40d36ebc7e6','c5d27f09-d11e-11f0-a496-e40d36ebc7e6','ca371884-d11d-11f0-a496-e40d36ebc7e6',NULL,410.7000,NULL,NULL,0),('c5f3e404-d11e-11f0-a496-e40d36ebc7e6','c5d27f09-d11e-11f0-a496-e40d36ebc7e6','ca3718a6-d11d-11f0-a496-e40d36ebc7e6',NULL,4517.7000,NULL,NULL,0),('c5fa2d37-d11e-11f0-a496-e40d36ebc7e6','c5f76d6d-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Documentation',NULL,NULL,NULL,1),('c5fb8e41-d11e-11f0-a496-e40d36ebc7e6','c5f76d6d-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,30.0000,NULL,NULL,1),('c5fcda0b-d11e-11f0-a496-e40d36ebc7e6','c5f76d6d-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,183.0000,NULL,NULL,1),('c5fe301c-d11e-11f0-a496-e40d36ebc7e6','c5f76d6d-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,2),('c5ffcf3c-d11e-11f0-a496-e40d36ebc7e6','c5f76d6d-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,1.0000,NULL,NULL,2),('c601ae42-d11e-11f0-a496-e40d36ebc7e6','c5f76d6d-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,124.0000,NULL,NULL,2),('c6032d1b-d11e-11f0-a496-e40d36ebc7e6','c5f76d6d-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Project Management',NULL,NULL,NULL,3),('c6093745-d11e-11f0-a496-e40d36ebc7e6','c5f76d6d-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,9.0000,NULL,NULL,3),('c60b34da-d11e-11f0-a496-e40d36ebc7e6','c5f76d6d-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,120.0000,NULL,NULL,3),('c60d7343-d11e-11f0-a496-e40d36ebc7e6','c5f76d6d-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Training Services',NULL,NULL,NULL,4),('c60f1904-d11e-11f0-a496-e40d36ebc7e6','c5f76d6d-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,3.0000,NULL,NULL,4),('c610e3e5-d11e-11f0-a496-e40d36ebc7e6','c5f76d6d-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,154.0000,NULL,NULL,4),('c621af72-d11e-11f0-a496-e40d36ebc7e6','c5f76d6d-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,5490.0000,NULL,NULL,1),('c623abe0-d11e-11f0-a496-e40d36ebc7e6','c5f76d6d-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,124.0000,NULL,NULL,2),('c625e466-d11e-11f0-a496-e40d36ebc7e6','c5f76d6d-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,1080.0000,NULL,NULL,3),('c6282a5e-d11e-11f0-a496-e40d36ebc7e6','c5f76d6d-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,462.0000,NULL,NULL,4),('c62a9df6-d11e-11f0-a496-e40d36ebc7e6','c5f76d6d-d11e-11f0-a496-e40d36ebc7e6','ca37184e-d11d-11f0-a496-e40d36ebc7e6',NULL,7156.0000,NULL,NULL,0),('c62ce9da-d11e-11f0-a496-e40d36ebc7e6','c5f76d6d-d11e-11f0-a496-e40d36ebc7e6','ca371884-d11d-11f0-a496-e40d36ebc7e6',NULL,715.6000,NULL,NULL,0),('c62f0c80-d11e-11f0-a496-e40d36ebc7e6','c5f76d6d-d11e-11f0-a496-e40d36ebc7e6','ca3718a6-d11d-11f0-a496-e40d36ebc7e6',NULL,7871.6000,NULL,NULL,0),('c638216b-d11e-11f0-a496-e40d36ebc7e6','c633a9ca-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Design Work',NULL,NULL,NULL,1),('c63a2435-d11e-11f0-a496-e40d36ebc7e6','c633a9ca-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,3.0000,NULL,NULL,1),('c63baef3-d11e-11f0-a496-e40d36ebc7e6','c633a9ca-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,74.0000,NULL,NULL,1),('c63d0cd3-d11e-11f0-a496-e40d36ebc7e6','c633a9ca-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,2),('c63e6baa-d11e-11f0-a496-e40d36ebc7e6','c633a9ca-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,21.0000,NULL,NULL,2),('c63fb019-d11e-11f0-a496-e40d36ebc7e6','c633a9ca-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,77.0000,NULL,NULL,2),('c6410f6f-d11e-11f0-a496-e40d36ebc7e6','c633a9ca-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Quality Assurance',NULL,NULL,NULL,3),('c64258f1-d11e-11f0-a496-e40d36ebc7e6','c633a9ca-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,19.0000,NULL,NULL,3),('c643c2c5-d11e-11f0-a496-e40d36ebc7e6','c633a9ca-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,196.0000,NULL,NULL,3),('c645261e-d11e-11f0-a496-e40d36ebc7e6','c633a9ca-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Training Services',NULL,NULL,NULL,4),('c6468aef-d11e-11f0-a496-e40d36ebc7e6','c633a9ca-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,20.0000,NULL,NULL,4),('c6481668-d11e-11f0-a496-e40d36ebc7e6','c633a9ca-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,168.0000,NULL,NULL,4),('c658b267-d11e-11f0-a496-e40d36ebc7e6','c633a9ca-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,222.0000,NULL,NULL,1),('c65ad9c2-d11e-11f0-a496-e40d36ebc7e6','c633a9ca-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,1617.0000,NULL,NULL,2),('c65ce9a9-d11e-11f0-a496-e40d36ebc7e6','c633a9ca-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,3724.0000,NULL,NULL,3),('c65f30ed-d11e-11f0-a496-e40d36ebc7e6','c633a9ca-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,3360.0000,NULL,NULL,4),('c661ae33-d11e-11f0-a496-e40d36ebc7e6','c633a9ca-d11e-11f0-a496-e40d36ebc7e6','ca37184e-d11d-11f0-a496-e40d36ebc7e6',NULL,8923.0000,NULL,NULL,0),('c664484d-d11e-11f0-a496-e40d36ebc7e6','c633a9ca-d11e-11f0-a496-e40d36ebc7e6','ca371884-d11d-11f0-a496-e40d36ebc7e6',NULL,892.3000,NULL,NULL,0),('c666700c-d11e-11f0-a496-e40d36ebc7e6','c633a9ca-d11e-11f0-a496-e40d36ebc7e6','ca3718a6-d11d-11f0-a496-e40d36ebc7e6',NULL,9815.3000,NULL,NULL,0),('c66bea66-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Training Services',NULL,NULL,NULL,1),('c66d44dd-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,10.0000,NULL,NULL,1),('c66e757e-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,80.0000,NULL,NULL,1),('c66fbd2a-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Training Services',NULL,NULL,NULL,2),('c6711dee-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,35.0000,NULL,NULL,2),('c6729e5a-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,94.0000,NULL,NULL,2),('c674604d-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Software Development',NULL,NULL,NULL,3),('c675da68-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,20.0000,NULL,NULL,3),('c6774637-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,60.0000,NULL,NULL,3),('c678a347-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,4),('c679beb0-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,4.0000,NULL,NULL,4),('c67af557-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,200.0000,NULL,NULL,4),('c67c336d-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Project Management',NULL,NULL,NULL,5),('c67dc0c9-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,20.0000,NULL,NULL,5),('c67ef8ef-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,132.0000,NULL,NULL,5),('c683e8ba-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,800.0000,NULL,NULL,1),('c68514e8-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,3290.0000,NULL,NULL,2),('c6864187-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,1200.0000,NULL,NULL,3),('c68784ba-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,800.0000,NULL,NULL,4),('c688a50c-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,2640.0000,NULL,NULL,5),('c689dc50-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca37184e-d11d-11f0-a496-e40d36ebc7e6',NULL,8730.0000,NULL,NULL,0),('c68b0a0f-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca371884-d11d-11f0-a496-e40d36ebc7e6',NULL,873.0000,NULL,NULL,0),('c68c4460-d11e-11f0-a496-e40d36ebc7e6','c6690dab-d11e-11f0-a496-e40d36ebc7e6','ca3718a6-d11d-11f0-a496-e40d36ebc7e6',NULL,9603.0000,NULL,NULL,0),('c6907305-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Project Management',NULL,NULL,NULL,1),('c691c822-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,17.0000,NULL,NULL,1),('c692dcc4-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,64.0000,NULL,NULL,1),('c694a0fc-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Design Work',NULL,NULL,NULL,2),('c695f114-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,10.0000,NULL,NULL,2),('c6979283-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,64.0000,NULL,NULL,2),('c6997e39-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,3),('c69b4238-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,3.0000,NULL,NULL,3),('c69d29b0-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,110.0000,NULL,NULL,3),('c69f00ad-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,4),('c6a0ab78-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,9.0000,NULL,NULL,4),('c6a2598b-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,138.0000,NULL,NULL,4),('c6a41c6f-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Software Development',NULL,NULL,NULL,5),('c6a5ab54-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,13.0000,NULL,NULL,5),('c6a71493-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,97.0000,NULL,NULL,5),('c6ad62ee-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,1088.0000,NULL,NULL,1),('c6aed93d-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,640.0000,NULL,NULL,2),('c6b0504a-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,330.0000,NULL,NULL,3),('c6b1acfb-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,1242.0000,NULL,NULL,4),('c6b31d06-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,1261.0000,NULL,NULL,5),('c6b486b2-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca37184e-d11d-11f0-a496-e40d36ebc7e6',NULL,4561.0000,NULL,NULL,0),('c6b629e7-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca371884-d11d-11f0-a496-e40d36ebc7e6',NULL,456.1000,NULL,NULL,0),('c6b7aac2-d11e-11f0-a496-e40d36ebc7e6','c68df805-d11e-11f0-a496-e40d36ebc7e6','ca3718a6-d11d-11f0-a496-e40d36ebc7e6',NULL,5017.1000,NULL,NULL,0),('c6c02454-d11e-11f0-a496-e40d36ebc7e6','c6bc2949-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Web Development Services',NULL,NULL,NULL,1),('c6c22a73-d11e-11f0-a496-e40d36ebc7e6','c6bc2949-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,23.0000,NULL,NULL,1),('c6c39010-d11e-11f0-a496-e40d36ebc7e6','c6bc2949-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,64.0000,NULL,NULL,1),('c6c4ff6f-d11e-11f0-a496-e40d36ebc7e6','c6bc2949-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Quality Assurance',NULL,NULL,NULL,2),('c6c62fc5-d11e-11f0-a496-e40d36ebc7e6','c6bc2949-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,2.0000,NULL,NULL,2),('c6c76bfd-d11e-11f0-a496-e40d36ebc7e6','c6bc2949-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,93.0000,NULL,NULL,2),('c6c8ab76-d11e-11f0-a496-e40d36ebc7e6','c6bc2949-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,3),('c6c9eb7d-d11e-11f0-a496-e40d36ebc7e6','c6bc2949-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,40.0000,NULL,NULL,3),('c6cb78f3-d11e-11f0-a496-e40d36ebc7e6','c6bc2949-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,98.0000,NULL,NULL,3),('c6d7c979-d11e-11f0-a496-e40d36ebc7e6','c6bc2949-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,1472.0000,NULL,NULL,1),('c6d99a50-d11e-11f0-a496-e40d36ebc7e6','c6bc2949-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,186.0000,NULL,NULL,2),('c6db8d95-d11e-11f0-a496-e40d36ebc7e6','c6bc2949-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,3920.0000,NULL,NULL,3),('c6ddaa59-d11e-11f0-a496-e40d36ebc7e6','c6bc2949-d11e-11f0-a496-e40d36ebc7e6','ca37184e-d11d-11f0-a496-e40d36ebc7e6',NULL,5578.0000,NULL,NULL,0),('c6df1571-d11e-11f0-a496-e40d36ebc7e6','c6bc2949-d11e-11f0-a496-e40d36ebc7e6','ca371884-d11d-11f0-a496-e40d36ebc7e6',NULL,557.8000,NULL,NULL,0),('c6e0417a-d11e-11f0-a496-e40d36ebc7e6','c6bc2949-d11e-11f0-a496-e40d36ebc7e6','ca3718a6-d11d-11f0-a496-e40d36ebc7e6',NULL,6135.8000,NULL,NULL,0),('c6e8503e-d11e-11f0-a496-e40d36ebc7e6','c6e3ce30-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,1),('c6e9f92c-d11e-11f0-a496-e40d36ebc7e6','c6e3ce30-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,15.0000,NULL,NULL,1),('c6ebfe69-d11e-11f0-a496-e40d36ebc7e6','c6e3ce30-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,97.0000,NULL,NULL,1),('c6ee2152-d11e-11f0-a496-e40d36ebc7e6','c6e3ce30-d11e-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','Training Services',NULL,NULL,NULL,2),('c6f020b5-d11e-11f0-a496-e40d36ebc7e6','c6e3ce30-d11e-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,12.0000,NULL,NULL,2),('c6f2335e-d11e-11f0-a496-e40d36ebc7e6','c6e3ce30-d11e-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,147.0000,NULL,NULL,2),('c6fbb5f9-d11e-11f0-a496-e40d36ebc7e6','c6e3ce30-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,1455.0000,NULL,NULL,1),('c6fd30f3-d11e-11f0-a496-e40d36ebc7e6','c6e3ce30-d11e-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,1764.0000,NULL,NULL,2),('c6fecc37-d11e-11f0-a496-e40d36ebc7e6','c6e3ce30-d11e-11f0-a496-e40d36ebc7e6','ca37184e-d11d-11f0-a496-e40d36ebc7e6',NULL,3219.0000,NULL,NULL,0),('c7005079-d11e-11f0-a496-e40d36ebc7e6','c6e3ce30-d11e-11f0-a496-e40d36ebc7e6','ca371884-d11d-11f0-a496-e40d36ebc7e6',NULL,321.9000,NULL,NULL,0),('c7015f8c-d11e-11f0-a496-e40d36ebc7e6','c6e3ce30-d11e-11f0-a496-e40d36ebc7e6','ca3718a6-d11d-11f0-a496-e40d36ebc7e6',NULL,3540.9000,NULL,NULL,0),('cf0abcc1-d119-11f0-a496-e40d36ebc7e6','cf090d0e-d119-11f0-a496-e40d36ebc7e6','89618cfa-d119-11f0-a496-e40d36ebc7e6','Shoes',NULL,NULL,NULL,0),('cf0c0e0a-d119-11f0-a496-e40d36ebc7e6','cf090d0e-d119-11f0-a496-e40d36ebc7e6','89632a6c-d119-11f0-a496-e40d36ebc7e6',NULL,100.0000,NULL,NULL,0),('cf0d9300-d119-11f0-a496-e40d36ebc7e6','cf090d0e-d119-11f0-a496-e40d36ebc7e6','89656ae7-d119-11f0-a496-e40d36ebc7e6',NULL,20.0000,NULL,NULL,0),('cf0f285c-d119-11f0-a496-e40d36ebc7e6','cf090d0e-d119-11f0-a496-e40d36ebc7e6','8966dcf1-d119-11f0-a496-e40d36ebc7e6',NULL,2000.0000,NULL,NULL,0),('cf102cd9-d119-11f0-a496-e40d36ebc7e6','cf090d0e-d119-11f0-a496-e40d36ebc7e6','89618cfa-d119-11f0-a496-e40d36ebc7e6','socks',NULL,NULL,NULL,1),('cf1139ed-d119-11f0-a496-e40d36ebc7e6','cf090d0e-d119-11f0-a496-e40d36ebc7e6','89632a6c-d119-11f0-a496-e40d36ebc7e6',NULL,200.0000,NULL,NULL,1),('cf128b69-d119-11f0-a496-e40d36ebc7e6','cf090d0e-d119-11f0-a496-e40d36ebc7e6','89656ae7-d119-11f0-a496-e40d36ebc7e6',NULL,5.0000,NULL,NULL,1),('cf139db4-d119-11f0-a496-e40d36ebc7e6','cf090d0e-d119-11f0-a496-e40d36ebc7e6','8966dcf1-d119-11f0-a496-e40d36ebc7e6',NULL,1000.0000,NULL,NULL,1),('cf14acec-d119-11f0-a496-e40d36ebc7e6','cf090d0e-d119-11f0-a496-e40d36ebc7e6','8969d52a-d119-11f0-a496-e40d36ebc7e6',NULL,0.0000,NULL,NULL,0),('cf15d2cc-d119-11f0-a496-e40d36ebc7e6','cf090d0e-d119-11f0-a496-e40d36ebc7e6','896b3cc4-d119-11f0-a496-e40d36ebc7e6',NULL,0.0000,NULL,NULL,0),('cf16f97d-d119-11f0-a496-e40d36ebc7e6','cf090d0e-d119-11f0-a496-e40d36ebc7e6','896cc593-d119-11f0-a496-e40d36ebc7e6',NULL,0.0000,NULL,NULL,0),('e0c19245-d11d-11f0-a496-e40d36ebc7e6','e0c04dd1-d11d-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','shoe',NULL,NULL,NULL,0),('e0c28a1e-d11d-11f0-a496-e40d36ebc7e6','e0c04dd1-d11d-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,100.0000,NULL,NULL,0),('e0c38e27-d11d-11f0-a496-e40d36ebc7e6','e0c04dd1-d11d-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,20.0000,NULL,NULL,0),('e0c4766d-d11d-11f0-a496-e40d36ebc7e6','e0c04dd1-d11d-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,2000.0000,NULL,NULL,0),('e0c56994-d11d-11f0-a496-e40d36ebc7e6','e0c04dd1-d11d-11f0-a496-e40d36ebc7e6','ca3715e0-d11d-11f0-a496-e40d36ebc7e6','sock',NULL,NULL,NULL,1),('e0c65233-d11d-11f0-a496-e40d36ebc7e6','e0c04dd1-d11d-11f0-a496-e40d36ebc7e6','ca37164f-d11d-11f0-a496-e40d36ebc7e6',NULL,200.0000,NULL,NULL,1),('e0c749cb-d11d-11f0-a496-e40d36ebc7e6','e0c04dd1-d11d-11f0-a496-e40d36ebc7e6','ca37167e-d11d-11f0-a496-e40d36ebc7e6',NULL,5.0000,NULL,NULL,1),('e0c83125-d11d-11f0-a496-e40d36ebc7e6','e0c04dd1-d11d-11f0-a496-e40d36ebc7e6','ca3716fa-d11d-11f0-a496-e40d36ebc7e6',NULL,1000.0000,NULL,NULL,1),('e0c8fe39-d11d-11f0-a496-e40d36ebc7e6','e0c04dd1-d11d-11f0-a496-e40d36ebc7e6','ca37184e-d11d-11f0-a496-e40d36ebc7e6',NULL,3000.0000,NULL,NULL,0),('e0c9e78e-d11d-11f0-a496-e40d36ebc7e6','e0c04dd1-d11d-11f0-a496-e40d36ebc7e6','ca371884-d11d-11f0-a496-e40d36ebc7e6',NULL,300.0000,NULL,NULL,0),('e0cad3ea-d11d-11f0-a496-e40d36ebc7e6','e0c04dd1-d11d-11f0-a496-e40d36ebc7e6','ca3718a6-d11d-11f0-a496-e40d36ebc7e6',NULL,3300.0000,NULL,NULL,0);
/*!40000 ALTER TABLE `invoice_value` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `organization`
--

DROP TABLE IF EXISTS `organization`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `organization` (
  `org_id` char(36) NOT NULL,
  `domain` varchar(100) NOT NULL,
  `name` varchar(100) NOT NULL,
  `street_address` varchar(255) DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `state` varchar(100) DEFAULT NULL,
  `zip_code` varchar(20) DEFAULT NULL,
  `country` varchar(100) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`org_id`),
  UNIQUE KEY `unique_name_domain` (`name`,`domain`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `organization`
--

LOCK TABLES `organization` WRITE;
/*!40000 ALTER TABLE `organization` DISABLE KEYS */;
INSERT INTO `organization` VALUES ('192c3ffd-d11a-11f0-a496-e40d36ebc7e6','test.com','o2',NULL,NULL,NULL,NULL,NULL,'2025-12-04 14:04:07'),('39c1312b-d119-11f0-a496-e40d36ebc7e6','test.com','NEU','123 Jackson Boulevard','Boston','Massachusets','12345','USA','2025-12-04 13:57:52');
/*!40000 ALTER TABLE `organization` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payment`
--

DROP TABLE IF EXISTS `payment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payment` (
  `payment_id` char(36) NOT NULL,
  `invoice_id` char(36) NOT NULL,
  `amount` decimal(15,4) NOT NULL,
  `method` varchar(50) DEFAULT NULL,
  `reference_number` varchar(100) DEFAULT NULL,
  `payment_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`payment_id`),
  KEY `idx_payment_invoice` (`invoice_id`),
  CONSTRAINT `payment_ibfk_1` FOREIGN KEY (`invoice_id`) REFERENCES `invoice` (`invoice_id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payment`
--

LOCK TABLES `payment` WRITE;
/*!40000 ALTER TABLE `payment` DISABLE KEYS */;
INSERT INTO `payment` VALUES ('c3d95ccc-d11e-11f0-a496-e40d36ebc7e6','c3a01c95-d11e-11f0-a496-e40d36ebc7e6',5592.4000,'Credit Card','REF-696281','2025-12-04 14:37:31'),('c4a8ec6b-d11e-11f0-a496-e40d36ebc7e6','c47ea693-d11e-11f0-a496-e40d36ebc7e6',11116.6000,'Credit Card','REF-905434','2025-12-04 14:37:32'),('c4db93a4-d11e-11f0-a496-e40d36ebc7e6','c4aa7e43-d11e-11f0-a496-e40d36ebc7e6',6355.8000,'Credit Card','REF-723664','2025-12-04 14:37:33'),('c5d10d68-d11e-11f0-a496-e40d36ebc7e6','c5950a4f-d11e-11f0-a496-e40d36ebc7e6',13774.2000,'Bank Transfer','REF-919583','2025-12-04 14:37:34'),('c6e1e1d9-d11e-11f0-a496-e40d36ebc7e6','c6bc2949-d11e-11f0-a496-e40d36ebc7e6',6135.8000,'Bank Transfer','REF-220756','2025-12-04 14:37:36');
/*!40000 ALTER TABLE `payment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `person`
--

DROP TABLE IF EXISTS `person`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `person` (
  `person_id` char(36) NOT NULL,
  `email` varchar(255) NOT NULL,
  `full_name` varchar(100) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`person_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `person`
--

LOCK TABLES `person` WRITE;
/*!40000 ALTER TABLE `person` DISABLE KEYS */;
/*!40000 ALTER TABLE `person` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `section`
--

DROP TABLE IF EXISTS `section`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `section` (
  `section_id` char(36) NOT NULL,
  `template_id` char(36) NOT NULL,
  `template_version` int NOT NULL,
  `name` varchar(100) NOT NULL,
  `display_name` varchar(100) DEFAULT NULL,
  `title` varchar(100) DEFAULT NULL,
  `ordinal` int DEFAULT NULL,
  `section_type` enum('normal','line_item') DEFAULT 'normal',
  PRIMARY KEY (`section_id`),
  KEY `idx_section_template` (`template_id`,`template_version`),
  CONSTRAINT `section_ibfk_1` FOREIGN KEY (`template_id`, `template_version`) REFERENCES `template` (`template_id`, `version`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `section`
--

LOCK TABLES `section` WRITE;
/*!40000 ALTER TABLE `section` DISABLE KEYS */;
INSERT INTO `section` VALUES ('896059a4-d119-11f0-a496-e40d36ebc7e6','895ef75d-d119-11f0-a496-e40d36ebc7e6',1,'Items','Items','Items',1,'line_item'),('896816f5-d119-11f0-a496-e40d36ebc7e6','895ef75d-d119-11f0-a496-e40d36ebc7e6',1,'Total','Total','Total',2,'normal'),('8d0d20bd-d120-11f0-a496-e40d36ebc7e6','8d06b26e-d120-11f0-a496-e40d36ebc7e6',1,'Items','Items','Items',1,'line_item'),('8d2b1eed-d120-11f0-a496-e40d36ebc7e6','8d06b26e-d120-11f0-a496-e40d36ebc7e6',1,'Total','Total','Total',2,'normal'),('998893ab-d11d-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',1,'Items','Items','Items',1,'line_item'),('9992ac33-d11d-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',1,'Total','Total','Total',2,'normal'),('ca370422-d11d-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'Items','Items','Items',1,'line_item'),('ca370463-d11d-11f0-a496-e40d36ebc7e6','9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'Total','Total','Total',2,'normal');
/*!40000 ALTER TABLE `section` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `template`
--

DROP TABLE IF EXISTS `template`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `template` (
  `template_id` char(36) NOT NULL,
  `version` int NOT NULL,
  `org_id` char(36) NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `currency_code` char(3) NOT NULL,
  `total_field_id` char(36) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `is_archived` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`template_id`,`version`),
  KEY `idx_template_total_field` (`total_field_id`),
  KEY `idx_template_org_id` (`org_id`),
  KEY `idx_template_latest` (`template_id`,`version` DESC),
  KEY `idx_template_archived` (`org_id`,`is_archived`),
  CONSTRAINT `template_ibfk_1` FOREIGN KEY (`org_id`) REFERENCES `organization` (`org_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `template`
--

LOCK TABLES `template` WRITE;
/*!40000 ALTER TABLE `template` DISABLE KEYS */;
INSERT INTO `template` VALUES ('895ef75d-d119-11f0-a496-e40d36ebc7e6',1,'39c1312b-d119-11f0-a496-e40d36ebc7e6','Standard Invoice','USD','8969d52a-d119-11f0-a496-e40d36ebc7e6','2025-12-04 14:00:05',0),('8d06b26e-d120-11f0-a496-e40d36ebc7e6',1,'39c1312b-d119-11f0-a496-e40d36ebc7e6','Premium','USD','8d2ca1d4-d120-11f0-a496-e40d36ebc7e6','2025-12-04 14:50:18',0),('9986e8ba-d11d-11f0-a496-e40d36ebc7e6',1,'39c1312b-d119-11f0-a496-e40d36ebc7e6','Test','USD','99951375-d11d-11f0-a496-e40d36ebc7e6','2025-12-04 14:29:10',1),('9986e8ba-d11d-11f0-a496-e40d36ebc7e6',2,'39c1312b-d119-11f0-a496-e40d36ebc7e6','Test','USD','ca3718a6-d11d-11f0-a496-e40d36ebc7e6','2025-12-04 14:30:32',1);
/*!40000 ALTER TABLE `template` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_organization`
--

DROP TABLE IF EXISTS `user_organization`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_organization` (
  `user_id` char(36) NOT NULL,
  `org_id` char(36) NOT NULL,
  `role` varchar(50) DEFAULT 'member',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`,`org_id`),
  KEY `idx_user_org_user` (`user_id`),
  KEY `idx_user_org_org` (`org_id`),
  CONSTRAINT `user_organization_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `user_organization_ibfk_2` FOREIGN KEY (`org_id`) REFERENCES `organization` (`org_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_organization`
--

LOCK TABLES `user_organization` WRITE;
/*!40000 ALTER TABLE `user_organization` DISABLE KEYS */;
INSERT INTO `user_organization` VALUES ('13838994-d11f-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','member','2025-12-04 14:39:45'),('39c29420-d119-11f0-a496-e40d36ebc7e6','192c3ffd-d11a-11f0-a496-e40d36ebc7e6','owner','2025-12-04 14:04:07'),('39c29420-d119-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','owner','2025-12-04 13:57:52'),('ae4e13c2-d11f-11f0-a496-e40d36ebc7e6','192c3ffd-d11a-11f0-a496-e40d36ebc7e6','member','2025-12-04 14:44:22'),('ae4e13c2-d11f-11f0-a496-e40d36ebc7e6','39c1312b-d119-11f0-a496-e40d36ebc7e6','member','2025-12-04 14:44:04');
/*!40000 ALTER TABLE `user_organization` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` char(36) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES ('13838994-d11f-11f0-a496-e40d36ebc7e6','prakash@test.com','$2b$12$9TS7IdFyLfii/PsIPJTovu1p38uaFh9HrrbwevGkDyYDDVDN5PZcq','2025-12-04 14:39:45'),('39c29420-d119-11f0-a496-e40d36ebc7e6','test@test.com','$2b$12$eAD.p3aL1e1bM6wTSdvDXeN2SoMgU1LHVGWLrOyxcNYd5//7/Zif2','2025-12-04 13:57:52'),('ae4e13c2-d11f-11f0-a496-e40d36ebc7e6','kavinn@test.com','$2b$12$40Gs8sqvSDuuVFrAL0aOhuVxP2z9dwG.KbeO8qP8p6HJqk2EtNisq','2025-12-04 14:44:04');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping events for database 'invoice_generator'
--

--
-- Dumping routines for database 'invoice_generator'
--
/*!50003 DROP PROCEDURE IF EXISTS `sp_add_template_field` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_add_template_field`(
    IN p_section_id CHAR(36),
    IN p_name VARCHAR(100),
    IN p_display_name VARCHAR(100),
    IN p_data_type VARCHAR(20),
    IN p_is_required BOOLEAN,
    IN p_is_currency BOOLEAN,
    IN p_ordinal INT,
    IN p_calculation_formula TEXT,
    OUT p_field_id CHAR(36)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    IF NOT EXISTS (SELECT 1 FROM section WHERE section_id = p_section_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Section does not exist';
    END IF;
    
    IF p_data_type NOT IN ('string', 'number', 'date', 'boolean') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid data type. Must be: string, number, date, or boolean';
    END IF;
    
    IF p_name IS NULL OR p_name = '' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Field name is required and cannot contain spaces';
    END IF;
    
    IF p_name LIKE '% %' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Field name cannot contain spaces';
    END IF;
    
    SET p_field_id = UUID();
    
    INSERT INTO field (field_id, section_id, name, display_name, data_type, is_required, is_currency, ordinal, calculation_formula)
    VALUES (p_field_id, p_section_id, p_name, p_display_name, p_data_type, IFNULL(p_is_required, FALSE), IFNULL(p_is_currency, FALSE), IFNULL(p_ordinal, 0), p_calculation_formula);
    
    
    SELECT p_field_id AS field_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_archive_customer` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_archive_customer`(
    IN p_customer_id CHAR(36),
    IN p_org_id CHAR(36)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    IF NOT EXISTS (SELECT 1 FROM customer WHERE customer_id = p_customer_id AND org_id = p_org_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Customer does not exist or does not belong to organization';
    END IF;
    
    UPDATE customer
    SET is_archived = TRUE
    WHERE customer_id = p_customer_id AND org_id = p_org_id;
    
    SELECT ROW_COUNT() AS rows_affected;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_archive_template` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_archive_template`(
    IN p_template_id CHAR(36),
    IN p_org_id CHAR(36)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    IF NOT EXISTS (SELECT 1 FROM template WHERE template_id = p_template_id AND org_id = p_org_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Template does not exist or does not belong to organization';
    END IF;
    
    UPDATE template
    SET is_archived = TRUE
    WHERE template_id = p_template_id AND org_id = p_org_id;
    
    SELECT ROW_COUNT() AS rows_affected;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_assign_user_to_org` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_assign_user_to_org`(
    IN p_user_id CHAR(36),
    IN p_org_id CHAR(36),
    IN p_role VARCHAR(50)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    IF NOT EXISTS (SELECT 1 FROM users WHERE user_id = p_user_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'User does not exist';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM organization WHERE org_id = p_org_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Organization does not exist';
    END IF;
    
    INSERT INTO user_organization (user_id, org_id, role)
    VALUES (p_user_id, p_org_id, IFNULL(p_role, 'member'))
    ON DUPLICATE KEY UPDATE role = IFNULL(p_role, role);
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_authenticate_customer` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_authenticate_customer`(
    IN p_email VARCHAR(255),
    IN p_password_hash VARCHAR(255)
)
BEGIN
    DECLARE v_customer_user_id CHAR(36);
    DECLARE v_customer_id CHAR(36);
    DECLARE v_password_hash VARCHAR(255);
    
    SELECT customer_user_id, customer_id, password_hash 
    INTO v_customer_user_id, v_customer_id, v_password_hash
    FROM customer_user
    WHERE email = p_email;
    
    IF v_customer_user_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid email or password';
    END IF;
    
    IF v_password_hash != p_password_hash THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid email or password';
    END IF;
    
    
    SELECT 
        cu.customer_user_id,
        cu.customer_id,
        cu.email,
        c.name AS customer_name,
        c.org_id
    FROM customer_user cu
    JOIN customer c ON cu.customer_id = c.customer_id
    WHERE cu.customer_user_id = v_customer_user_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_authenticate_user` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_authenticate_user`(
    IN p_email VARCHAR(255),
    IN p_password_hash VARCHAR(255),
    OUT p_user_id CHAR(36),
    OUT p_email_out VARCHAR(255)
)
BEGIN
    DECLARE v_user_id CHAR(36);
    DECLARE v_password_hash VARCHAR(255);
    
    SELECT user_id, password_hash INTO v_user_id, v_password_hash
    FROM users
    WHERE email = p_email;
    
    IF v_user_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid email or password';
    END IF;
    
    IF v_password_hash != p_password_hash THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid email or password';
    END IF;
    
    SET p_user_id = v_user_id;
    SET p_email_out = p_email;
    
    
    SELECT v_user_id AS user_id, p_email AS email;
    
    
    SELECT uo.org_id, o.name, o.domain, uo.role
    FROM user_organization uo
    JOIN organization o ON uo.org_id = o.org_id
    WHERE uo.user_id = v_user_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_check_template_version_has_invoices` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_check_template_version_has_invoices`(
    IN p_template_id CHAR(36),
    IN p_template_version INT,
    IN p_org_id CHAR(36)
)
BEGIN
    DECLARE v_count INT DEFAULT 0;
    DECLARE v_has_invoices BOOLEAN DEFAULT FALSE;
    
    SELECT COUNT(*) INTO v_count
    FROM invoice
    WHERE template_id = p_template_id
      AND template_version = p_template_version
      AND org_id = p_org_id;
    
    SET v_has_invoices = IF(v_count > 0, TRUE, FALSE);
    
    
    SELECT v_has_invoices AS has_invoices, v_count AS invoice_count;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_create_customer` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_create_customer`(
    IN p_org_id CHAR(36),
    IN p_name VARCHAR(255),
    IN p_tax_id VARCHAR(50),
    IN p_street_address VARCHAR(255),
    IN p_city VARCHAR(100),
    IN p_state VARCHAR(100),
    IN p_zip_code VARCHAR(20),
    IN p_country VARCHAR(100),
    OUT p_customer_id CHAR(36)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    IF NOT EXISTS (SELECT 1 FROM organization WHERE org_id = p_org_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Organization does not exist';
    END IF;
    
    SET p_customer_id = UUID();
    
    INSERT INTO customer (customer_id, org_id, name, tax_id, street_address, city, state, zip_code, country)
    VALUES (p_customer_id, p_org_id, p_name, p_tax_id, p_street_address, p_city, p_state, p_zip_code, p_country);
    
    
    SELECT p_customer_id AS customer_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_create_customer_user` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_create_customer_user`(
    IN p_customer_id CHAR(36),
    IN p_email VARCHAR(255),
    IN p_password_hash VARCHAR(255),
    OUT p_customer_user_id CHAR(36)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    IF NOT EXISTS (SELECT 1 FROM customer WHERE customer_id = p_customer_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Customer does not exist';
    END IF;
    
    IF EXISTS (SELECT 1 FROM customer_user WHERE email = p_email) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Email already exists';
    END IF;
    
    SET p_customer_user_id = UUID();
    
    INSERT INTO customer_user (customer_user_id, customer_id, email, password_hash)
    VALUES (p_customer_user_id, p_customer_id, p_email, p_password_hash);
    
    
    SELECT p_customer_user_id AS customer_user_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_create_invoice` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_create_invoice`(
    IN p_org_id CHAR(36),
    IN p_customer_id CHAR(36),
    IN p_template_id CHAR(36),
    OUT p_invoice_id CHAR(36),
    OUT p_template_version INT
)
BEGIN
    DECLARE v_latest_version INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    
    IF NOT EXISTS (SELECT 1 FROM organization WHERE org_id = p_org_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Organization does not exist';
    END IF;
    
    
    IF NOT EXISTS (SELECT 1 FROM customer WHERE customer_id = p_customer_id AND org_id = p_org_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Customer does not exist or does not belong to organization';
    END IF;
    
    
    SELECT MAX(version) INTO v_latest_version
    FROM template
    WHERE template_id = p_template_id
      AND org_id = p_org_id;
    
    IF v_latest_version IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Template does not exist or does not belong to organization';
    END IF;
    
    SET p_invoice_id = UUID();
    SET p_template_version = v_latest_version;
    
    INSERT INTO invoice (invoice_id, org_id, customer_id, template_id, template_version, status)
    VALUES (p_invoice_id, p_org_id, p_customer_id, p_template_id, p_template_version, 'draft');
    
    
    SELECT p_invoice_id AS invoice_id, p_template_version AS template_version;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_create_organization` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_create_organization`(
    IN p_name VARCHAR(100),
    IN p_domain VARCHAR(100),
    IN p_street_address VARCHAR(255),
    IN p_city VARCHAR(100),
    IN p_state VARCHAR(100),
    IN p_zip_code VARCHAR(20),
    IN p_country VARCHAR(100),
    OUT p_org_id CHAR(36)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    SET p_org_id = UUID();
    
    INSERT INTO organization (org_id, domain, name, street_address, city, state, zip_code, country)
    VALUES (p_org_id, p_domain, p_name, p_street_address, p_city, p_state, p_zip_code, p_country);
    
    
    SELECT p_org_id AS org_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_create_section` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_create_section`(
    IN p_template_id CHAR(36),
    IN p_template_version INT,
    IN p_name VARCHAR(100),
    IN p_display_name VARCHAR(100),
    IN p_ordinal INT,
    IN p_section_type VARCHAR(20),
    OUT p_section_id CHAR(36)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    IF NOT EXISTS (SELECT 1 FROM template WHERE template_id = p_template_id AND version = p_template_version) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Template version does not exist';
    END IF;
    
    IF p_section_type NOT IN ('normal', 'line_item') THEN
        SET p_section_type = 'normal';
    END IF;
    
    IF p_name IS NULL OR p_name = '' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Section name is required and cannot contain spaces';
    END IF;
    
    IF p_name LIKE '% %' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Section name cannot contain spaces';
    END IF;
    
    SET p_section_id = UUID();
    
    INSERT INTO section (section_id, template_id, template_version, name, display_name, ordinal, section_type)
    VALUES (p_section_id, p_template_id, p_template_version, p_name, p_display_name, IFNULL(p_ordinal, 0), IFNULL(p_section_type, 'normal'));
    
    
    SELECT p_section_id AS section_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_create_template` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_create_template`(
    IN p_org_id CHAR(36),
    IN p_name VARCHAR(100),
    IN p_currency_code CHAR(3),
    OUT p_template_id CHAR(36),
    OUT p_version INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    IF NOT EXISTS (SELECT 1 FROM organization WHERE org_id = p_org_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Organization does not exist';
    END IF;
    
    SET p_template_id = UUID();
    SET p_version = 1;
    
    INSERT INTO template (template_id, version, org_id, name, currency_code)
    VALUES (p_template_id, p_version, p_org_id, p_name, p_currency_code);
    
    
    SELECT p_template_id AS template_id, p_version AS version;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_create_template_version` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_create_template_version`(
    IN p_template_id CHAR(36),
    IN p_org_id CHAR(36),
    OUT p_new_version INT
)
BEGIN
    DECLARE v_latest_version INT;
    DECLARE v_template_name VARCHAR(100);
    DECLARE v_currency_code CHAR(3);
    DECLARE v_old_total_field_id CHAR(36);
    DECLARE v_new_total_field_id CHAR(36);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    
    IF NOT EXISTS (SELECT 1 FROM organization WHERE org_id = p_org_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Organization does not exist';
    END IF;
    
    
    SELECT MAX(version) INTO v_latest_version
    FROM template
    WHERE template_id = p_template_id
      AND org_id = p_org_id;
    
    IF v_latest_version IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Template does not exist or does not belong to organization';
    END IF;
    
    
    SELECT name, currency_code, total_field_id
    INTO v_template_name, v_currency_code, v_old_total_field_id
    FROM template
    WHERE template_id = p_template_id
      AND version = v_latest_version;
    
    
    SET p_new_version = v_latest_version + 1;
    
    
    INSERT INTO template (template_id, version, org_id, name, currency_code, total_field_id)
    VALUES (p_template_id, p_new_version, p_org_id, v_template_name, v_currency_code, NULL);
    
    
    INSERT INTO section (section_id, template_id, template_version, name, display_name, ordinal, section_type)
    SELECT UUID(), p_template_id, p_new_version, name, display_name, ordinal, section_type
    FROM section
    WHERE template_id = p_template_id
      AND template_version = v_latest_version
    ORDER BY ordinal;
    
    
    INSERT INTO field (field_id, section_id, name, display_name, data_type, is_required, is_currency, ordinal, calculation_formula)
    SELECT 
        UUID(),
        new_s.section_id,
        f.name,
        f.display_name,
        f.data_type,
        f.is_required,
        f.is_currency,
        f.ordinal,
        f.calculation_formula
    FROM field f
    JOIN section old_s ON f.section_id = old_s.section_id
    JOIN section new_s ON new_s.template_id = p_template_id
                      AND new_s.template_version = p_new_version
                      AND new_s.ordinal = old_s.ordinal
                      AND new_s.name = old_s.name
    WHERE old_s.template_id = p_template_id
      AND old_s.template_version = v_latest_version
    ORDER BY old_s.ordinal, f.ordinal;
    
    
    IF v_old_total_field_id IS NOT NULL THEN
        SELECT f_new.field_id INTO v_new_total_field_id
        FROM field f_old
        JOIN section s_old ON f_old.section_id = s_old.section_id
        JOIN section s_new ON s_new.template_id = p_template_id
                          AND s_new.template_version = p_new_version
                          AND s_new.ordinal = s_old.ordinal
                          AND s_new.title = s_old.title
        JOIN field f_new ON f_new.section_id = s_new.section_id
                         AND f_new.ordinal = f_old.ordinal
                         AND f_new.label = f_old.label
        WHERE f_old.field_id = v_old_total_field_id
        LIMIT 1;
        
        IF v_new_total_field_id IS NOT NULL THEN
            UPDATE template
            SET total_field_id = v_new_total_field_id
            WHERE template_id = p_template_id
              AND version = p_new_version;
        END IF;
    END IF;
    
    
    SELECT p_new_version AS new_version;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_create_user` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_create_user`(
    IN p_email VARCHAR(255),
    IN p_password_hash VARCHAR(255),
    OUT p_user_id CHAR(36)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    IF EXISTS (SELECT 1 FROM users WHERE email = p_email) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Email already exists';
    END IF;
    
    SET p_user_id = UUID();
    
    INSERT INTO users (user_id, email, password_hash)
    VALUES (p_user_id, p_email, p_password_hash);
    
    
    SELECT p_user_id AS user_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_delete_customer` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_delete_customer`(
    IN p_customer_id CHAR(36),
    IN p_org_id CHAR(36)
)
BEGIN
    DECLARE v_invoice_count INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    
    IF NOT EXISTS (SELECT 1 FROM customer WHERE customer_id = p_customer_id AND org_id = p_org_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Customer does not exist or does not belong to organization';
    END IF;
    
    
    SELECT COUNT(*) INTO v_invoice_count
    FROM invoice
    WHERE customer_id = p_customer_id;
    
    IF v_invoice_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot delete customer with existing invoices. Delete invoices first.';
    END IF;
    
    
    DELETE FROM customer_user WHERE customer_id = p_customer_id;
    
    
    DELETE FROM customer_contact_assignment WHERE customer_id = p_customer_id;
    
    
    DELETE FROM customer WHERE customer_id = p_customer_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_delete_field` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_delete_field`(
    IN p_field_id CHAR(36)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    IF NOT EXISTS (SELECT 1 FROM field WHERE field_id = p_field_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Field does not exist';
    END IF;
    
    
    DELETE FROM field WHERE field_id = p_field_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_delete_invoice` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_delete_invoice`(
    IN p_invoice_id CHAR(36)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    IF NOT EXISTS (SELECT 1 FROM invoice WHERE invoice_id = p_invoice_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invoice does not exist';
    END IF;
    
    
    DELETE FROM payment WHERE invoice_id = p_invoice_id;
    
    
    DELETE FROM invoice_value WHERE invoice_id = p_invoice_id;
    
    
    DELETE FROM invoice WHERE invoice_id = p_invoice_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_delete_section` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_delete_section`(
    IN p_section_id CHAR(36)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    IF NOT EXISTS (SELECT 1 FROM section WHERE section_id = p_section_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Section does not exist';
    END IF;
    
    
    DELETE FROM field WHERE section_id = p_section_id;
    
    
    DELETE FROM section WHERE section_id = p_section_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_find_organizations_by_domain` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_find_organizations_by_domain`(
    IN p_domain VARCHAR(100)
)
BEGIN
    SELECT 
        org_id,
        name,
        domain,
        created_at
    FROM organization
    WHERE domain = p_domain
    ORDER BY created_at DESC;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_find_organization_by_domain` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_find_organization_by_domain`(
    IN p_domain VARCHAR(100)
)
BEGIN
    SELECT 
        org_id,
        name,
        domain,
        created_at
    FROM organization
    WHERE domain = p_domain
    LIMIT 1;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_get_customer_details` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_customer_details`(
    IN p_customer_id CHAR(36)
)
BEGIN
    
    SELECT 
        c.customer_id,
        c.org_id,
        c.name,
        c.tax_id,
        c.street_address,
        c.city,
        c.state,
        c.zip_code,
        c.country,
        c.created_at
    FROM customer c
    WHERE c.customer_id = p_customer_id;
    
    
    SELECT 
        p.person_id,
        p.email,
        p.full_name,
        cca.role
    FROM customer_contact_assignment cca
    JOIN person p ON cca.person_id = p.person_id
    WHERE cca.customer_id = p_customer_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_get_customer_invoices` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_customer_invoices`(
    IN p_customer_id CHAR(36)
)
BEGIN
    SELECT 
        i.invoice_id,
        i.template_id,
        t.name AS template_name,
        i.issue_date,
        i.due_date,
        i.status,
        (SELECT IFNULL(SUM(payment.amount), 0) FROM payment WHERE payment.invoice_id = i.invoice_id) AS paid_amount,
        i.total_amount AS total_amount
    FROM invoice i
    LEFT JOIN template t ON i.template_id = t.template_id AND i.template_version = t.version
    WHERE i.customer_id = p_customer_id
      AND i.status IS NOT NULL
      AND i.status != 'draft'
    ORDER BY i.issue_date DESC, i.invoice_id DESC;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_get_customer_users` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_customer_users`(
    IN p_customer_id CHAR(36)
)
BEGIN
    SELECT 
        cu.customer_user_id,
        cu.customer_id,
        cu.email,
        cu.created_at
    FROM customer_user cu
    WHERE cu.customer_id = p_customer_id
    ORDER BY cu.created_at DESC;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_get_customer_user_by_email` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_customer_user_by_email`(
    IN p_email VARCHAR(255)
)
BEGIN
    SELECT 
        cu.customer_user_id,
        cu.customer_id,
        cu.email,
        cu.password_hash,
        c.name AS customer_name,
        c.org_id
    FROM customer_user cu
    JOIN customer c ON cu.customer_id = c.customer_id
    WHERE cu.email = p_email;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_get_dashboard_stats` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_dashboard_stats`(
    IN p_org_id CHAR(36)
)
BEGIN
    SELECT 
        
        (SELECT IFNULL(SUM(i.total_amount), 0)
         FROM invoice i
         WHERE i.org_id = p_org_id 
           AND i.status IN ('paid', 'pending')) AS total_revenue,
        
        
        (SELECT COUNT(*)
         FROM invoice
         WHERE org_id = p_org_id AND status = 'pending') AS pending_count,
        
        
        (SELECT COUNT(*)
         FROM invoice
         WHERE org_id = p_org_id AND status = 'paid') AS paid_count,
        
        
        (SELECT COUNT(*)
         FROM invoice
         WHERE org_id = p_org_id 
           AND status IN ('pending', 'draft')
           AND due_date < CURDATE()) AS overdue_count,
        
        
        (SELECT COUNT(*)
         FROM invoice
         WHERE org_id = p_org_id) AS total_invoices,
        
        
        (SELECT IFNULL(SUM(i.total_amount), 0)
         FROM invoice i
         WHERE i.org_id = p_org_id
           AND i.status IN ('paid', 'pending')
           AND YEAR(i.issue_date) = YEAR(CURDATE())
           AND MONTH(i.issue_date) = MONTH(CURDATE())) AS revenue_this_month,
        
        
        (SELECT IFNULL(SUM(i.total_amount), 0)
         FROM invoice i
         WHERE i.org_id = p_org_id
           AND i.status IN ('paid', 'pending')
           AND YEAR(i.issue_date) = YEAR(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
           AND MONTH(i.issue_date) = MONTH(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))) AS revenue_last_month,
        
        
        (SELECT COUNT(*)
         FROM invoice
         WHERE org_id = p_org_id
           AND YEAR(issue_date) = YEAR(CURDATE())
           AND MONTH(issue_date) = MONTH(CURDATE())) AS invoices_created_this_month,
        
        
        (SELECT IFNULL(SUM(p.amount), 0)
         FROM payment p
         JOIN invoice i ON p.invoice_id = i.invoice_id
         WHERE i.org_id = p_org_id
           AND YEAR(p.payment_date) = YEAR(CURDATE())
           AND MONTH(p.payment_date) = MONTH(CURDATE())) AS money_received_this_month,
        
        
        (SELECT IFNULL(SUM(i.total_amount), 0)
         FROM invoice i
         WHERE i.org_id = p_org_id
           AND i.status = 'pending'
           AND YEAR(i.issue_date) = YEAR(CURDATE())
           AND MONTH(i.issue_date) = MONTH(CURDATE())) AS pending_money_this_month;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_get_invoice_details` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_invoice_details`(
    IN p_invoice_id CHAR(36)
)
BEGIN
    
    SELECT 
        i.invoice_id,
        i.org_id,
        o.name AS organization_name,
        o.street_address AS organization_street_address,
        o.city AS organization_city,
        o.state AS organization_state,
        o.zip_code AS organization_zip_code,
        o.country AS organization_country,
        i.customer_id,
        c.name AS customer_name,
        c.street_address AS customer_street_address,
        c.city AS customer_city,
        c.state AS customer_state,
        c.zip_code AS customer_zip_code,
        c.country AS customer_country,
        i.template_id,
        i.template_version,
        t.name AS template_name,
        t.currency_code,
        i.issue_date,
        i.due_date,
        i.status
    FROM invoice i
    JOIN organization o ON i.org_id = o.org_id
    JOIN customer c ON i.customer_id = c.customer_id
    LEFT JOIN template t ON i.template_id = t.template_id AND i.template_version = t.version
    WHERE i.invoice_id = p_invoice_id;
    
    
    SELECT 
        iv.value_id,
        iv.field_id,
        f.name AS field_name,
        f.display_name AS field_display_name,
        f.display_name AS field_label,
        f.data_type,
        f.calculation_formula,
        f.is_currency,
        s.name AS section_name,
        s.display_name AS section_display_name,
        s.display_name AS section_title,
        s.ordinal AS section_ordinal,
        s.section_type,
        f.ordinal AS field_ordinal,
        iv.ordinal AS value_ordinal,
        iv.val_string,
        iv.val_number,
        iv.val_date,
        iv.val_boolean
    FROM invoice_value iv
    LEFT JOIN field f ON iv.field_id = f.field_id
    LEFT JOIN section s ON f.section_id = s.section_id
    WHERE iv.invoice_id = p_invoice_id
    ORDER BY s.ordinal, s.section_type, iv.ordinal, f.ordinal;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_get_invoice_payments` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_invoice_payments`(
    IN p_invoice_id CHAR(36)
)
BEGIN
    SELECT 
        payment_id,
        amount,
        method,
        reference_number,
        payment_date
    FROM payment
    WHERE invoice_id = p_invoice_id
    ORDER BY payment_date DESC;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_get_invoice_status_distribution` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_invoice_status_distribution`(
    IN p_org_id CHAR(36)
)
BEGIN
    SELECT 
        IFNULL(status, 'draft') AS status,
        COUNT(*) AS count
    FROM invoice
    WHERE org_id = p_org_id
    GROUP BY status;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_get_organization_details` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_organization_details`(
    IN p_org_id CHAR(36)
)
BEGIN
    SELECT 
        org_id,
        name,
        domain,
        street_address,
        city,
        state,
        zip_code,
        country,
        created_at
    FROM organization
    WHERE org_id = p_org_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_get_revenue_by_status` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_revenue_by_status`(
    IN p_org_id CHAR(36)
)
BEGIN
    SELECT 
        IFNULL(status, 'draft') AS status,
        IFNULL(SUM(total_amount), 0) AS revenue
    FROM invoice
    WHERE org_id = p_org_id
      AND status IN ('paid', 'pending')
    GROUP BY status;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_get_revenue_timeseries` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_revenue_timeseries`(
    IN p_org_id CHAR(36)
)
BEGIN
    
    SELECT 
        DATE_FORMAT(IFNULL(i.issue_date, CURDATE()), '%Y-%m') AS month,
        DATE_FORMAT(IFNULL(i.issue_date, CURDATE()), '%b %Y') AS month_label,
        CAST(IFNULL(SUM(i.total_amount), 0) AS DECIMAL(10, 2)) AS revenue
    FROM invoice i
    WHERE i.org_id = p_org_id
      AND i.status IN ('paid', 'pending')
      AND IFNULL(i.total_amount, 0) > 0
    GROUP BY DATE_FORMAT(IFNULL(i.issue_date, CURDATE()), '%Y-%m'), 
             DATE_FORMAT(IFNULL(i.issue_date, CURDATE()), '%b %Y')
    ORDER BY month DESC
    LIMIT 12;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_get_template_fields` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_template_fields`(
    IN p_template_id CHAR(36)
)
BEGIN
    DECLARE v_latest_version INT;
    
    
    SELECT MAX(version) INTO v_latest_version
    FROM template
    WHERE template_id = p_template_id;
    
    IF v_latest_version IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Template does not exist';
    END IF;
    
    
    SELECT 
        s.section_id,
        s.name AS section_name,
        s.display_name AS section_display_name,
        s.display_name AS section_title,
        s.ordinal AS section_ordinal,
        s.section_type,
        f.field_id,
        f.name AS field_name,
        f.display_name AS field_display_name,
        f.data_type,
        f.is_required,
        f.is_currency,
        f.ordinal AS field_ordinal,
        f.calculation_formula
    FROM section s
    JOIN field f ON s.section_id = f.section_id
    WHERE s.template_id = p_template_id
      AND s.template_version = v_latest_version
    ORDER BY s.ordinal, f.ordinal;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_get_user_by_email` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_user_by_email`(
    IN p_email VARCHAR(255)
)
BEGIN
    SELECT user_id, email, password_hash
    FROM users
    WHERE email = p_email;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_get_user_organizations` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_user_organizations`(
    IN p_user_id CHAR(36)
)
BEGIN
    SELECT uo.org_id, o.name, o.domain, uo.role
    FROM user_organization uo
    JOIN organization o ON uo.org_id = o.org_id
    WHERE uo.user_id = p_user_id
    ORDER BY uo.created_at DESC;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_list_customers` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_list_customers`(
    IN p_org_id CHAR(36),
    IN p_include_archived BOOLEAN
)
BEGIN
    SELECT 
        c.customer_id,
        c.name,
        c.tax_id,
        c.street_address,
        c.city,
        c.state,
        c.zip_code,
        c.country,
        c.is_archived,
        c.created_at,
        COUNT(DISTINCT i.invoice_id) AS invoice_count
    FROM customer c
    LEFT JOIN invoice i ON c.customer_id = i.customer_id
    WHERE c.org_id = p_org_id
      AND (p_include_archived = TRUE OR c.is_archived = FALSE)
    GROUP BY c.customer_id, c.name, c.tax_id, c.street_address, c.city, c.state, c.zip_code, c.country, c.is_archived, c.created_at
    ORDER BY c.is_archived ASC, c.created_at DESC;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_list_invoices` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_list_invoices`(
    IN p_org_id CHAR(36),
    IN p_status_filter VARCHAR(20),
    IN p_limit INT,
    IN p_offset INT
)
BEGIN
    DECLARE v_limit INT DEFAULT 50;
    DECLARE v_offset INT DEFAULT 0;
    
    SET v_limit = IFNULL(p_limit, 50);
    SET v_offset = IFNULL(p_offset, 0);
    
    SELECT 
        i.invoice_id,
        i.customer_id,
        c.name AS customer_name,
        i.template_id,
        t.name AS template_name,
        i.issue_date,
        i.due_date,
        i.status,
        (SELECT IFNULL(SUM(amount), 0) FROM payment WHERE invoice_id = i.invoice_id) AS paid_amount,
        i.total_amount AS total_amount
    FROM invoice i
    JOIN customer c ON i.customer_id = c.customer_id
    LEFT JOIN template t ON i.template_id = t.template_id AND i.template_version = t.version
    WHERE i.org_id = p_org_id
      AND (p_status_filter IS NULL OR i.status = p_status_filter)
    ORDER BY i.issue_date DESC, i.invoice_id DESC
    LIMIT v_limit
    OFFSET v_offset;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_list_templates` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_list_templates`(
    IN p_org_id CHAR(36),
    IN p_include_archived BOOLEAN
)
BEGIN
    SELECT 
        t.template_id,
        t.version,
        t.name,
        t.currency_code,
        t.is_archived,
        t.created_at,
        (SELECT MAX(version) FROM template WHERE template_id = t.template_id) AS latest_version
    FROM template t
    WHERE t.org_id = p_org_id
      AND (p_include_archived = TRUE OR t.is_archived = FALSE)
    GROUP BY t.template_id, t.version, t.name, t.currency_code, t.is_archived, t.created_at
    ORDER BY t.is_archived ASC, t.created_at DESC;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_record_payment` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_record_payment`(
    IN p_invoice_id CHAR(36),
    IN p_amount DECIMAL(15, 4),
    IN p_method VARCHAR(50),
    IN p_reference_number VARCHAR(100),
    OUT p_payment_id CHAR(36)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    IF NOT EXISTS (SELECT 1 FROM invoice WHERE invoice_id = p_invoice_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invoice does not exist';
    END IF;
    
    IF p_amount <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Payment amount must be greater than zero';
    END IF;
    
    SET p_payment_id = UUID();
    
    INSERT INTO payment (payment_id, invoice_id, amount, method, reference_number)
    VALUES (p_payment_id, p_invoice_id, p_amount, p_method, p_reference_number);
    
    
    SELECT p_payment_id AS payment_id;
    
    
    CALL sp_update_invoice_total(p_invoice_id);
    
    
    UPDATE invoice i
    SET status = 'paid'
    WHERE i.invoice_id = p_invoice_id
      AND (SELECT IFNULL(SUM(amount), 0) FROM payment WHERE invoice_id = i.invoice_id) >= i.total_amount;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_save_invoice_value` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_save_invoice_value`(
    IN p_invoice_id CHAR(36),
    IN p_field_id CHAR(36),
    IN p_val_string TEXT,
    IN p_val_number DECIMAL(15, 4),
    IN p_val_date DATE,
    IN p_val_boolean TINYINT(1),
    IN p_ordinal INT
)
BEGIN
    DECLARE v_value_id CHAR(36);
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    
    IF NOT EXISTS (SELECT 1 FROM invoice WHERE invoice_id = p_invoice_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invoice does not exist';
    END IF;
    
    
    
    
    IF p_ordinal IS NULL THEN
        
        SELECT value_id INTO v_value_id
        FROM invoice_value
        WHERE invoice_id = p_invoice_id 
          AND field_id = p_field_id
          AND (ordinal IS NULL OR ordinal = 0);
    ELSE
        
        SELECT value_id INTO v_value_id
        FROM invoice_value
        WHERE invoice_id = p_invoice_id 
          AND field_id = p_field_id
          AND ordinal = p_ordinal;
    END IF;
    
    IF v_value_id IS NOT NULL THEN
        
        UPDATE invoice_value
        SET 
            val_string = p_val_string,
            val_number = p_val_number,
            val_date = p_val_date,
            val_boolean = p_val_boolean,
            ordinal = IFNULL(p_ordinal, 0)
        WHERE value_id = v_value_id;
    ELSE
        
        SET v_value_id = UUID();
    INSERT INTO invoice_value (value_id, invoice_id, field_id, val_string, val_number, val_date, val_boolean, ordinal)
    VALUES (v_value_id, p_invoice_id, p_field_id, p_val_string, p_val_number, p_val_date, p_val_boolean, IFNULL(p_ordinal, 0));
    END IF;
    
    
    CALL sp_update_invoice_total(p_invoice_id);
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_set_template_total_field` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_set_template_total_field`(
    IN p_template_id CHAR(36),
    IN p_template_version INT,
    IN p_total_field_id CHAR(36)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    IF NOT EXISTS (SELECT 1 FROM template WHERE template_id = p_template_id AND version = p_template_version) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Template version does not exist';
    END IF;
    
    
    IF p_total_field_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1 
            FROM field f
            JOIN section s ON f.section_id = s.section_id
            WHERE f.field_id = p_total_field_id
              AND s.template_id = p_template_id
              AND s.template_version = p_template_version
        ) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Field does not belong to this template';
        END IF;
    END IF;
    
    UPDATE template
    SET total_field_id = p_total_field_id
    WHERE template_id = p_template_id AND version = p_template_version;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_unarchive_customer` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_unarchive_customer`(
    IN p_customer_id CHAR(36),
    IN p_org_id CHAR(36)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    IF NOT EXISTS (SELECT 1 FROM customer WHERE customer_id = p_customer_id AND org_id = p_org_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Customer does not exist or does not belong to organization';
    END IF;
    
    UPDATE customer
    SET is_archived = FALSE
    WHERE customer_id = p_customer_id AND org_id = p_org_id;
    
    SELECT ROW_COUNT() AS rows_affected;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_unarchive_template` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_unarchive_template`(
    IN p_template_id CHAR(36),
    IN p_org_id CHAR(36)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    IF NOT EXISTS (SELECT 1 FROM template WHERE template_id = p_template_id AND org_id = p_org_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Template does not exist or does not belong to organization';
    END IF;
    
    UPDATE template
    SET is_archived = FALSE
    WHERE template_id = p_template_id AND org_id = p_org_id;
    
    SELECT ROW_COUNT() AS rows_affected;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_update_customer` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_update_customer`(
    IN p_customer_id CHAR(36),
    IN p_name VARCHAR(255),
    IN p_tax_id VARCHAR(50),
    IN p_street_address VARCHAR(255),
    IN p_city VARCHAR(100),
    IN p_state VARCHAR(100),
    IN p_zip_code VARCHAR(20),
    IN p_country VARCHAR(100)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    IF NOT EXISTS (SELECT 1 FROM customer WHERE customer_id = p_customer_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Customer does not exist';
    END IF;
    
    UPDATE customer
    SET 
        name = IFNULL(p_name, name),
        tax_id = p_tax_id,
        street_address = p_street_address,
        city = p_city,
        state = p_state,
        zip_code = p_zip_code,
        country = p_country
    WHERE customer_id = p_customer_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_update_field` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_update_field`(
    IN p_field_id CHAR(36),
    IN p_name VARCHAR(100),
    IN p_display_name VARCHAR(100),
    IN p_data_type VARCHAR(20),
    IN p_is_required BOOLEAN,
    IN p_is_currency BOOLEAN,
    IN p_ordinal INT,
    IN p_calculation_formula TEXT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    IF NOT EXISTS (SELECT 1 FROM field WHERE field_id = p_field_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Field does not exist';
    END IF;
    
    IF p_data_type IS NOT NULL AND p_data_type NOT IN ('string', 'number', 'date', 'boolean') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid data type. Must be: string, number, date, or boolean';
    END IF;
    
    IF p_name IS NOT NULL AND p_name LIKE '% %' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Field name cannot contain spaces';
    END IF;
    
    UPDATE field
    SET 
        name = IFNULL(p_name, name),
        display_name = p_display_name,
        data_type = IFNULL(p_data_type, data_type),
        is_required = IFNULL(p_is_required, is_required),
        is_currency = IFNULL(p_is_currency, is_currency),
        ordinal = IFNULL(p_ordinal, ordinal),
        calculation_formula = p_calculation_formula
    WHERE field_id = p_field_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_update_invoice_dates` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_update_invoice_dates`(
    IN p_invoice_id CHAR(36),
    IN p_issue_date DATE,
    IN p_due_date DATE
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    IF NOT EXISTS (SELECT 1 FROM invoice WHERE invoice_id = p_invoice_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invoice does not exist';
    END IF;
    
    UPDATE invoice
    SET 
        issue_date = IFNULL(p_issue_date, issue_date),
        due_date = IFNULL(p_due_date, due_date)
    WHERE invoice_id = p_invoice_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_update_invoice_status` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_update_invoice_status`(
    IN p_invoice_id CHAR(36),
    IN p_status VARCHAR(20)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    IF NOT EXISTS (SELECT 1 FROM invoice WHERE invoice_id = p_invoice_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invoice does not exist';
    END IF;
    
    UPDATE invoice
    SET status = p_status
    WHERE invoice_id = p_invoice_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_update_invoice_total` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_update_invoice_total`(
    IN p_invoice_id CHAR(36)
)
BEGIN
    DECLARE v_total DECIMAL(15, 4) DEFAULT 0;
    DECLARE v_total_field_id CHAR(36);
    DECLARE v_template_total_field_id CHAR(36);
    
    
    SELECT t.total_field_id INTO v_template_total_field_id
    FROM invoice i
    JOIN template t ON i.template_id = t.template_id AND i.template_version = t.version
    WHERE i.invoice_id = p_invoice_id;
    
    IF v_template_total_field_id IS NOT NULL THEN
        
        SELECT IFNULL(SUM(iv.val_number), 0) INTO v_total
        FROM invoice_value iv
        WHERE iv.invoice_id = p_invoice_id
          AND iv.field_id = v_template_total_field_id
          AND (iv.ordinal IS NULL OR iv.ordinal = 0);
    ELSE
        
        SELECT f.field_id INTO v_total_field_id
        FROM invoice i
        JOIN template t ON i.template_id = t.template_id AND i.template_version = t.version
        JOIN section s ON s.template_id = t.template_id AND s.template_version = t.version
        JOIN field f ON f.section_id = s.section_id
        WHERE i.invoice_id = p_invoice_id
          AND LOWER(f.label) IN ('total', 'grand total', 'grand_total', 'amount', 'invoice total', 'invoice_total')
          AND f.data_type = 'number'
          AND s.section_type = 'normal'
        ORDER BY 
            CASE LOWER(f.label)
                WHEN 'total' THEN 1
                WHEN 'grand total' THEN 2
                WHEN 'grand_total' THEN 2
                WHEN 'invoice total' THEN 3
                WHEN 'invoice_total' THEN 3
                WHEN 'amount' THEN 4
                ELSE 6
            END
        LIMIT 1;
        
        
        IF v_total_field_id IS NOT NULL THEN
            SELECT IFNULL(SUM(iv.val_number), 0) INTO v_total
            FROM invoice_value iv
            WHERE iv.invoice_id = p_invoice_id
              AND iv.field_id = v_total_field_id
              AND (iv.ordinal IS NULL OR iv.ordinal = 0);
        ELSE
            
            SELECT IFNULL(SUM(iv.val_number), 0) INTO v_total
            FROM invoice_value iv
            JOIN field f ON iv.field_id = f.field_id
            JOIN section s ON f.section_id = s.section_id
            WHERE iv.invoice_id = p_invoice_id
              AND f.data_type = 'number'
              AND f.calculation_formula IS NOT NULL
              AND (LOWER(f.calculation_formula) LIKE '%sum%' OR LOWER(f.label) LIKE '%total%')
              AND s.section_type = 'normal'
              AND (iv.ordinal IS NULL OR iv.ordinal = 0);
            
            
            IF v_total = 0 THEN
                SELECT IFNULL(SUM(iv.val_number), 0) INTO v_total
                FROM invoice_value iv
                JOIN field f ON iv.field_id = f.field_id
                JOIN section s ON f.section_id = s.section_id
                WHERE iv.invoice_id = p_invoice_id
                  AND f.data_type = 'number'
                  AND s.section_type = 'normal'
                  AND (iv.ordinal IS NULL OR iv.ordinal = 0);
            END IF;
        END IF;
    END IF;
    
    
    UPDATE invoice
    SET total_amount = IFNULL(v_total, 0)
    WHERE invoice_id = p_invoice_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_update_organization` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_update_organization`(
    IN p_org_id CHAR(36),
    IN p_name VARCHAR(100),
    IN p_street_address VARCHAR(255),
    IN p_city VARCHAR(100),
    IN p_state VARCHAR(100),
    IN p_zip_code VARCHAR(20),
    IN p_country VARCHAR(100)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    IF NOT EXISTS (SELECT 1 FROM organization WHERE org_id = p_org_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Organization does not exist';
    END IF;
    
    UPDATE organization
    SET 
        name = IFNULL(p_name, name),
        street_address = p_street_address,
        city = p_city,
        state = p_state,
        zip_code = p_zip_code,
        country = p_country
    WHERE org_id = p_org_id;
    
    SELECT ROW_COUNT() AS rows_affected;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_update_section` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_update_section`(
    IN p_section_id CHAR(36),
    IN p_name VARCHAR(100),
    IN p_display_name VARCHAR(100),
    IN p_ordinal INT,
    IN p_section_type VARCHAR(20)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    IF NOT EXISTS (SELECT 1 FROM section WHERE section_id = p_section_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Section does not exist';
    END IF;
    
    IF p_section_type IS NOT NULL AND p_section_type NOT IN ('normal', 'line_item') THEN
        SET p_section_type = 'normal';
    END IF;
    
    IF p_name IS NOT NULL AND p_name LIKE '% %' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Section name cannot contain spaces';
    END IF;
    
    UPDATE section
    SET 
        name = IFNULL(p_name, name),
        display_name = p_display_name,
        ordinal = IFNULL(p_ordinal, ordinal),
        section_type = IFNULL(p_section_type, section_type)
    WHERE section_id = p_section_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-12-04 11:19:09
