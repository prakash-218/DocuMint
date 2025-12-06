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
-- Table structure for table `audit_log`
--

DROP TABLE IF EXISTS `audit_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_log` (
  `audit_id` char(36) NOT NULL,
  `table_name` varchar(100) NOT NULL,
  `record_id` varchar(100) NOT NULL,
  `action_type` enum('INSERT','UPDATE','DELETE') NOT NULL,
  `field_name` varchar(100) DEFAULT NULL,
  `old_value` text,
  `new_value` text,
  `changed_by` varchar(255) DEFAULT NULL,
  `changed_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `additional_info` text,
  PRIMARY KEY (`audit_id`),
  KEY `idx_audit_table_record` (`table_name`,`record_id`),
  KEY `idx_audit_changed_at` (`changed_at`),
  KEY `idx_audit_action` (`action_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_log`
--

LOCK TABLES `audit_log` WRITE;
/*!40000 ALTER TABLE `audit_log` DISABLE KEYS */;
INSERT INTO `audit_log` VALUES ('093a1b73-d22b-11f0-a496-e40d36ebc7e6','payment','093a1411-d22b-11f0-a496-e40d36ebc7e6','INSERT','amount',NULL,'13945.8000',NULL,'2025-12-05 22:37:52','Invoice: 9846665a-d22a-11f0-a496-e40d36ebc7e6 | Method: Credit card | Reference: TXN-18123234'),('168b613f-d22b-11f0-a496-e40d36ebc7e6','payment','168b5ab7-d22b-11f0-a496-e40d36ebc7e6','INSERT','amount',NULL,'43905.4000',NULL,'2025-12-05 22:38:15','Invoice: 95fad294-d22a-11f0-a496-e40d36ebc7e6 | Method:  | Reference: '),('95f9d287-d22a-11f0-a496-e40d36ebc7e6','invoice','95d9649f-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:39','Customer: Sydney Financial Group | Amount: 17984.0000'),('960fdb00-d22a-11f0-a496-e40d36ebc7e6','invoice','95fad294-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','paid',NULL,'2025-12-05 22:34:39','Customer: Brisbane Logistics Solutions | Amount: 39914.0000'),('962d4ace-d22a-11f0-a496-e40d36ebc7e6','invoice','961119c9-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:39','Customer: Brisbane Logistics Solutions | Amount: 30688.0000'),('96486c41-d22a-11f0-a496-e40d36ebc7e6','invoice','962e660f-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:40','Customer: Brisbane Logistics Solutions | Amount: 18342.0000'),('965f45f7-d22a-11f0-a496-e40d36ebc7e6','invoice','96498229-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:40','Customer: Melbourne Tech Ventures | Amount: 26381.0000'),('96872bc8-d22a-11f0-a496-e40d36ebc7e6','invoice','96603ee6-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:40','Customer: Melbourne Tech Ventures | Amount: 36629.0000'),('96a9fb30-d22a-11f0-a496-e40d36ebc7e6','invoice','96887555-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:40','Customer: Perth Mining Services | Amount: 61190.0000'),('96fbeaa6-d22a-11f0-a496-e40d36ebc7e6','invoice','96dba254-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','paid',NULL,'2025-12-05 22:34:41','Customer: Melbourne Tech Ventures | Amount: 26572.0000'),('97198476-d22a-11f0-a496-e40d36ebc7e6','invoice','96fd072e-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','paid',NULL,'2025-12-05 22:34:41','Customer: Perth Mining Services | Amount: 36094.0000'),('97908e25-d22a-11f0-a496-e40d36ebc7e6','invoice','976a7917-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:42','Customer: Brisbane Logistics Solutions | Amount: 24873.0000'),('97c0e416-d22a-11f0-a496-e40d36ebc7e6','invoice','97a541f9-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','paid',NULL,'2025-12-05 22:34:42','Customer: Melbourne Tech Ventures | Amount: 20829.0000'),('97f4f38c-d22a-11f0-a496-e40d36ebc7e6','invoice','97e0ea32-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','paid',NULL,'2025-12-05 22:34:42','Customer: Melbourne Tech Ventures | Amount: 9532.0000'),('981ab882-d22a-11f0-a496-e40d36ebc7e6','invoice','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:43','Customer: Delhi Digital Services | Amount: 37853.0000'),('984561a6-d22a-11f0-a496-e40d36ebc7e6','invoice','981bc736-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:43','Customer: Chennai Manufacturing Ltd | Amount: 45202.0000'),('985940fd-d22a-11f0-a496-e40d36ebc7e6','invoice','9846665a-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','paid',NULL,'2025-12-05 22:34:43','Customer: Delhi Digital Services | Amount: 12678.0000'),('98a3ff54-d22a-11f0-a496-e40d36ebc7e6','invoice','98924ddc-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','paid',NULL,'2025-12-05 22:34:43','Customer: Delhi Digital Services | Amount: 14840.0000'),('98dd95d3-d22a-11f0-a496-e40d36ebc7e6','invoice','98c40289-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:44','Customer: Pune Engineering Services | Amount: 40218.0000'),('9908b32d-d22a-11f0-a496-e40d36ebc7e6','invoice','98dec825-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','paid',NULL,'2025-12-05 22:34:44','Customer: Chennai Manufacturing Ltd | Amount: 10192.0000'),('992f4b19-d22a-11f0-a496-e40d36ebc7e6','invoice','990a94b2-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','paid',NULL,'2025-12-05 22:34:44','Customer: Mumbai Tech Solutions | Amount: 29200.0000'),('9943ab00-d22a-11f0-a496-e40d36ebc7e6','invoice','9930517d-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:45','Customer: Pune Engineering Services | Amount: 41026.0000'),('997e161f-d22a-11f0-a496-e40d36ebc7e6','invoice','9969e36f-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:45','Customer: Delhi Digital Services | Amount: 14779.0000'),('99aefbce-d22a-11f0-a496-e40d36ebc7e6','invoice','998cf97b-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:45','Customer: Hyderabad Software Group | Amount: 51231.0000'),('99cae213-d22a-11f0-a496-e40d36ebc7e6','invoice','99b00fa1-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','paid',NULL,'2025-12-05 22:34:45','Customer: Mumbai Tech Solutions | Amount: 19164.0000'),('99ed24b8-d22a-11f0-a496-e40d36ebc7e6','invoice','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:46','Customer: Delhi Digital Services | Amount: 53784.0000'),('9a0c3a18-d22a-11f0-a496-e40d36ebc7e6','invoice','99ee1ace-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','paid',NULL,'2025-12-05 22:34:46','Customer: Chennai Manufacturing Ltd | Amount: 23503.0000'),('9a275957-d22a-11f0-a496-e40d36ebc7e6','invoice','9a0d34ad-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:46','Customer: Pune Engineering Services | Amount: 20300.0000'),('9a3d3b8c-d22a-11f0-a496-e40d36ebc7e6','invoice','9a28841e-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','paid',NULL,'2025-12-05 22:34:46','Customer: Birmingham Manufacturing Co | Amount: 11299.0000'),('9a56ce59-d22a-11f0-a496-e40d36ebc7e6','invoice','9a3e3499-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:46','Customer: Edinburgh Financial Services | Amount: 7409.0000'),('9a7e882f-d22a-11f0-a496-e40d36ebc7e6','invoice','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:47','Customer: Birmingham Manufacturing Co | Amount: 39302.0000'),('9ad96827-d22a-11f0-a496-e40d36ebc7e6','invoice','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','paid',NULL,'2025-12-05 22:34:47','Customer: Manchester Industrial Group | Amount: 30333.0000'),('9b162111-d22a-11f0-a496-e40d36ebc7e6','invoice','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','paid',NULL,'2025-12-05 22:34:48','Customer: Cambridge Analytics Ltd | Amount: 40248.0000'),('9b33a781-d22a-11f0-a496-e40d36ebc7e6','invoice','9b17559c-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:48','Customer: Cambridge Analytics Ltd | Amount: 32075.0000'),('9b539eb4-d22a-11f0-a496-e40d36ebc7e6','invoice','9b34a914-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:48','Customer: Cambridge Analytics Ltd | Amount: 33945.0000'),('9b8e102f-d22a-11f0-a496-e40d36ebc7e6','invoice','9b728e96-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','paid',NULL,'2025-12-05 22:34:48','Customer: Manchester Industrial Group | Amount: 24591.0000'),('9ba975a5-d22a-11f0-a496-e40d36ebc7e6','invoice','9b8f6e3d-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:49','Customer: Cambridge Analytics Ltd | Amount: 17892.0000'),('9bce3e1f-d22a-11f0-a496-e40d36ebc7e6','invoice','9baade12-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','paid',NULL,'2025-12-05 22:34:49','Customer: Manchester Industrial Group | Amount: 54333.0000'),('9be3df86-d22a-11f0-a496-e40d36ebc7e6','invoice','9bcf2e9b-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','paid',NULL,'2025-12-05 22:34:49','Customer: Edinburgh Financial Services | Amount: 29488.0000'),('9bf32912-d22a-11f0-a496-e40d36ebc7e6','invoice','9be4cd76-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:49','Customer: Birmingham Manufacturing Co | Amount: 16048.0000'),('9c044d75-d22a-11f0-a496-e40d36ebc7e6','invoice','9bf4215e-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','paid',NULL,'2025-12-05 22:34:49','Customer: Manchester Industrial Group | Amount: 14064.0000'),('9c1fb45c-d22a-11f0-a496-e40d36ebc7e6','invoice','9c056456-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:49','Customer: Cambridge Analytics Ltd | Amount: 12280.0000'),('9c49237b-d22a-11f0-a496-e40d36ebc7e6','invoice','9c397c0b-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','paid',NULL,'2025-12-05 22:34:50','Customer: Aurora Digital Systems | Amount: 1059.3000'),('9c5cc534-d22a-11f0-a496-e40d36ebc7e6','invoice','9c4a0ae5-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:50','Customer: Aurora Digital Systems | Amount: 34637.9000'),('9c6f25ca-d22a-11f0-a496-e40d36ebc7e6','invoice','9c5db651-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','paid',NULL,'2025-12-05 22:34:50','Customer: Meridian Technologies | Amount: 11385.0000'),('9c85f272-d22a-11f0-a496-e40d36ebc7e6','invoice','9c700523-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:50','Customer: Meridian Technologies | Amount: 41160.9000'),('9c94deff-d22a-11f0-a496-e40d36ebc7e6','invoice','9c86dee1-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:50','Customer: Catalyst Enterprises | Amount: 28600.0000'),('9cd019c9-d22a-11f0-a496-e40d36ebc7e6','invoice','9cb9c755-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:50','Customer: Vertex Manufacturing Group | Amount: 40899.1000'),('9ced77a9-d22a-11f0-a496-e40d36ebc7e6','invoice','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:51','Customer: Catalyst Enterprises | Amount: 33223.3000'),('9d10efd1-d22a-11f0-a496-e40d36ebc7e6','invoice','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','paid',NULL,'2025-12-05 22:34:51','Customer: Meridian Technologies | Amount: 26340.6000'),('9d2129e4-d22a-11f0-a496-e40d36ebc7e6','invoice','9d11fd67-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:51','Customer: Aurora Digital Systems | Amount: 5721.1000'),('9d3e4123-d22a-11f0-a496-e40d36ebc7e6','invoice','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:51','Customer: Vertex Manufacturing Group | Amount: 16069.9000'),('9d5256a6-d22a-11f0-a496-e40d36ebc7e6','invoice','9d3f19ca-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:51','Customer: Vertex Manufacturing Group | Amount: 38710.1000'),('9d625e66-d22a-11f0-a496-e40d36ebc7e6','invoice','9d5331e1-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:51','Customer: Meridian Technologies | Amount: 4466.0000'),('9d76a414-d22a-11f0-a496-e40d36ebc7e6','invoice','9d634062-d22a-11f0-a496-e40d36ebc7e6','UPDATE','status','draft','pending',NULL,'2025-12-05 22:34:52','Customer: Vertex Manufacturing Group | Amount: 8022.3000'),('adfe37c4-d22f-11f0-a496-e40d36ebc7e6','user_organization','48874172-d22a-11f0-a496-e40d36ebc7e6:496afc2a-d22a-11f0-a496-e40d36ebc7e6','UPDATE','role','member','owner',NULL,'2025-12-05 23:11:07','User: sarah.martinez@techflow.com | Org: TechFlow USA'),('af2bbff0-d22f-11f0-a496-e40d36ebc7e6','user_organization','48874172-d22a-11f0-a496-e40d36ebc7e6:496afc2a-d22a-11f0-a496-e40d36ebc7e6','UPDATE','role','owner','member',NULL,'2025-12-05 23:11:09','User: sarah.martinez@techflow.com | Org: TechFlow USA'),('f820c85d-d22a-11f0-a496-e40d36ebc7e6','payment','f820bed5-d22a-11f0-a496-e40d36ebc7e6','INSERT','amount',NULL,'32120.0000',NULL,'2025-12-05 22:37:24','Invoice: 990a94b2-d22a-11f0-a496-e40d36ebc7e6 | Method: Bank Transfer | Reference: TXN-18294729281');
/*!40000 ALTER TABLE `audit_log` ENABLE KEYS */;
UNLOCK TABLES;

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
INSERT INTO `customer` VALUES ('497ca535-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','Aurora Digital Systems','TAX-45-7891234','2847 Commerce Plaza','Seattle','WA','98101','USA','2025-12-05 22:32:31',0),('497e02eb-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','Meridian Technologies','TAX-32-4567890','1562 Tech Park Avenue','Austin','TX','78701','USA','2025-12-05 22:32:31',0),('497f49ee-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','Vertex Manufacturing Group','TAX-67-2345678','3891 Industrial Way','Chicago','IL','60601','USA','2025-12-05 22:32:31',0),('49807a06-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','Catalyst Enterprises','TAX-89-3456789','5123 Business Center Drive','Boston','MA','02101','USA','2025-12-05 22:32:31',0),('4981f85c-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','Quantum Solutions Inc','TAX-23-5678901','789 Innovation Boulevard','Denver','CO','80202','USA','2025-12-05 22:32:31',0),('498332a6-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','Cambridge Analytics Ltd','GB-987654321','15 King\'s Parade','Cambridge',NULL,'CB2 1SP','United Kingdom','2025-12-05 22:32:31',0),('49847c4e-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','Manchester Industrial Group','GB-123456789','42 Deansgate','Manchester',NULL,'M3 2BW','United Kingdom','2025-12-05 22:32:31',0),('49861309-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','Edinburgh Financial Services','GB-456789123','88 Princes Street','Edinburgh',NULL,'EH2 2ER','United Kingdom','2025-12-05 22:32:31',0),('49875afa-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','Birmingham Manufacturing Co','GB-789123456','100 Broad Street','Birmingham',NULL,'B15 1AE','United Kingdom','2025-12-05 22:32:31',0),('4988a4fa-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','Mumbai Tech Solutions','GST-27AABCU1234D1Z5','Bandra Kurla Complex, Tower A','Mumbai','Maharashtra','400051','India','2025-12-05 22:32:31',0),('4989eeb2-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','Delhi Digital Services','GST-07AABCT2345E2Z6','Connaught Place, Block C','New Delhi','Delhi','110001','India','2025-12-05 22:32:31',0),('498b796b-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','Hyderabad Software Group','GST-36AABCD3456F3Z7','HITEC City, Phase 2','Hyderabad','Telangana','500081','India','2025-12-05 22:32:31',0),('498ca492-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','Pune Engineering Services','GST-27AABCE4567G4Z8','Hinjewadi IT Park','Pune','Maharashtra','411057','India','2025-12-05 22:32:31',0),('498ddaae-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','Chennai Manufacturing Ltd','GST-33AABCF5678H5Z9','OMR IT Corridor','Chennai','Tamil Nadu','600113','India','2025-12-05 22:32:31',0),('498f1164-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','Sydney Financial Group','ABN-12345678901','Level 25, 1 Martin Place','Sydney','NSW','2000','Australia','2025-12-05 22:32:31',0),('499045e9-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','Melbourne Tech Ventures','ABN-23456789012','500 Collins Street','Melbourne','VIC','3000','Australia','2025-12-05 22:32:31',0),('4991ca0c-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','Brisbane Logistics Solutions','ABN-34567890123','123 Eagle Street','Brisbane','QLD','4000','Australia','2025-12-05 22:32:31',0),('49932c8b-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','Perth Mining Services','ABN-45678901234','200 St Georges Terrace','Perth','WA','6000','Australia','2025-12-05 22:32:31',0);
/*!40000 ALTER TABLE `customer` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_customer_archive_update` AFTER UPDATE ON `customer` FOR EACH ROW BEGIN
    IF OLD.is_archived != NEW.is_archived THEN
        INSERT INTO audit_log (
        audit_id,
            table_name,
            record_id,
            action_type,
            field_name,
            old_value,
            new_value,
            additional_info
        ) VALUES (
        UUID(),
            'customer',
            NEW.customer_id,
            'UPDATE',
            'is_archived',
            OLD.is_archived,
            NEW.is_archived,
            CONCAT('Customer: ', NEW.name, ' | Org: ', (SELECT name FROM organization WHERE org_id = NEW.org_id))
        );
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

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
INSERT INTO `customer_user` VALUES ('778dffb2-d242-11f0-a496-e40d36ebc7e6','498332a6-d22a-11f0-a496-e40d36ebc7e6','cust@cambridge.com','$2b$12$uMoUTcdKfY/6TkoTDJSaLOz.RxVBaRnoBxQic9ntXMQ1daH.ku.bi','2025-12-06 01:25:36'),('9ee6296f-d242-11f0-a496-e40d36ebc7e6','497ca535-d22a-11f0-a496-e40d36ebc7e6','cust@aurora.com','$2b$12$5gagM2t.ogwgmMsi8w2/qOBEMmBtrfVmjFBqEWiXpnml449U/hPGW','2025-12-06 01:26:42'),('b93a8778-d242-11f0-a496-e40d36ebc7e6','498ddaae-d22a-11f0-a496-e40d36ebc7e6','cust@chennai.com','$2b$12$dkn7.qNWEt2gnelBljBtreIjwrvGy1qVCgfo/bqJ.oHQvXiQ5Rg/.','2025-12-06 01:27:26');
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
INSERT INTO `field` VALUES ('8cb1e086-d22a-11f0-a496-e40d36ebc7e6','8cb0c21b-d22a-11f0-a496-e40d36ebc7e6','name','name',NULL,'string',1,0,1,NULL),('8cb2d50d-d22a-11f0-a496-e40d36ebc7e6','8cb0c21b-d22a-11f0-a496-e40d36ebc7e6','qty','qty',NULL,'number',1,0,2,NULL),('8cb413d4-d22a-11f0-a496-e40d36ebc7e6','8cb0c21b-d22a-11f0-a496-e40d36ebc7e6','price','price',NULL,'number',1,1,3,NULL),('8cb513be-d22a-11f0-a496-e40d36ebc7e6','8cb0c21b-d22a-11f0-a496-e40d36ebc7e6','total','total',NULL,'number',0,1,4,'this.price * this.qty'),('8cb71e68-d22a-11f0-a496-e40d36ebc7e6','8cb61851-d22a-11f0-a496-e40d36ebc7e6','total','Total',NULL,'number',0,1,1,'SUM(items.total)'),('8cb83313-d22a-11f0-a496-e40d36ebc7e6','8cb61851-d22a-11f0-a496-e40d36ebc7e6','tax','Tax',NULL,'number',0,1,2,'total * 0.1'),('8cb9d88c-d22a-11f0-a496-e40d36ebc7e6','8cb61851-d22a-11f0-a496-e40d36ebc7e6','grand_total','Grand Total',NULL,'number',0,1,3,'total + tax'),('9232db67-d22a-11f0-a496-e40d36ebc7e6','9231b8c6-d22a-11f0-a496-e40d36ebc7e6','name','name',NULL,'string',1,0,1,NULL),('92340fd4-d22a-11f0-a496-e40d36ebc7e6','9231b8c6-d22a-11f0-a496-e40d36ebc7e6','qty','qty',NULL,'number',1,0,2,NULL),('9235621e-d22a-11f0-a496-e40d36ebc7e6','9231b8c6-d22a-11f0-a496-e40d36ebc7e6','price','price',NULL,'number',1,1,3,NULL),('9236a14a-d22a-11f0-a496-e40d36ebc7e6','9231b8c6-d22a-11f0-a496-e40d36ebc7e6','total','total',NULL,'number',0,1,4,'this.price * this.qty'),('92391898-d22a-11f0-a496-e40d36ebc7e6','9237e737-d22a-11f0-a496-e40d36ebc7e6','total','Total',NULL,'number',0,1,1,'SUM(items.total)'),('923a493d-d22a-11f0-a496-e40d36ebc7e6','9237e737-d22a-11f0-a496-e40d36ebc7e6','tax','Tax',NULL,'number',0,1,2,'total * 0.1'),('923b5888-d22a-11f0-a496-e40d36ebc7e6','9237e737-d22a-11f0-a496-e40d36ebc7e6','grand_total','Grand Total',NULL,'number',0,1,3,'total + tax'),('923efe22-d22a-11f0-a496-e40d36ebc7e6','923de288-d22a-11f0-a496-e40d36ebc7e6','name','name',NULL,'string',1,0,1,NULL),('924049f0-d22a-11f0-a496-e40d36ebc7e6','923de288-d22a-11f0-a496-e40d36ebc7e6','qty','qty',NULL,'number',1,0,2,NULL),('9241a6e8-d22a-11f0-a496-e40d36ebc7e6','923de288-d22a-11f0-a496-e40d36ebc7e6','price','price',NULL,'number',1,1,3,NULL),('9242fef8-d22a-11f0-a496-e40d36ebc7e6','923de288-d22a-11f0-a496-e40d36ebc7e6','total','total',NULL,'number',0,1,4,'this.price * this.qty'),('9245fdc0-d22a-11f0-a496-e40d36ebc7e6','924455a4-d22a-11f0-a496-e40d36ebc7e6','total','Total',NULL,'number',0,1,1,'SUM(items.total)'),('9247c61e-d22a-11f0-a496-e40d36ebc7e6','924455a4-d22a-11f0-a496-e40d36ebc7e6','tax','Tax',NULL,'number',0,1,2,'total * 0.1'),('924924a2-d22a-11f0-a496-e40d36ebc7e6','924455a4-d22a-11f0-a496-e40d36ebc7e6','grand_total','Grand Total',NULL,'number',0,1,3,'total + tax'),('924cb7c9-d22a-11f0-a496-e40d36ebc7e6','924b99bc-d22a-11f0-a496-e40d36ebc7e6','name','name',NULL,'string',1,0,1,NULL),('924df576-d22a-11f0-a496-e40d36ebc7e6','924b99bc-d22a-11f0-a496-e40d36ebc7e6','qty','qty',NULL,'number',1,0,2,NULL),('924f4946-d22a-11f0-a496-e40d36ebc7e6','924b99bc-d22a-11f0-a496-e40d36ebc7e6','price','price',NULL,'number',1,1,3,NULL),('925087f2-d22a-11f0-a496-e40d36ebc7e6','924b99bc-d22a-11f0-a496-e40d36ebc7e6','total','total',NULL,'number',0,1,4,'this.price * this.qty'),('9252da43-d22a-11f0-a496-e40d36ebc7e6','9251ba98-d22a-11f0-a496-e40d36ebc7e6','total','Total',NULL,'number',0,1,1,'SUM(items.total)'),('92540789-d22a-11f0-a496-e40d36ebc7e6','9251ba98-d22a-11f0-a496-e40d36ebc7e6','tax','Tax',NULL,'number',0,1,2,'total * 0.1'),('925521d9-d22a-11f0-a496-e40d36ebc7e6','9251ba98-d22a-11f0-a496-e40d36ebc7e6','grand_total','Grand Total',NULL,'number',0,1,3,'total + tax');
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
INSERT INTO `invoice` VALUES ('95bc2d9c-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','4991ca0c-d22a-11f0-a496-e40d36ebc7e6','924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'2025-10-03','2025-10-20','draft',35282.0000),('95d9649f-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','498f1164-d22a-11f0-a496-e40d36ebc7e6','924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'2025-07-02','2025-07-18','pending',17984.0000),('95fad294-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','4991ca0c-d22a-11f0-a496-e40d36ebc7e6','924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'2025-12-06','2026-01-18','paid',39914.0000),('961119c9-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','4991ca0c-d22a-11f0-a496-e40d36ebc7e6','924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'2025-10-21','2025-11-05','pending',30688.0000),('962e660f-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','4991ca0c-d22a-11f0-a496-e40d36ebc7e6','924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'2025-11-25','2025-12-16','pending',18342.0000),('96498229-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','499045e9-d22a-11f0-a496-e40d36ebc7e6','924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'2025-11-18','2025-12-05','pending',26381.0000),('96603ee6-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','499045e9-d22a-11f0-a496-e40d36ebc7e6','924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'2025-10-26','2025-12-09','pending',36629.0000),('96887555-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','49932c8b-d22a-11f0-a496-e40d36ebc7e6','924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'2025-08-19','2025-09-30','pending',61190.0000),('96ab0b5c-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','498f1164-d22a-11f0-a496-e40d36ebc7e6','924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'2025-07-12','2025-07-31','draft',24251.0000),('96c875e0-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','4991ca0c-d22a-11f0-a496-e40d36ebc7e6','924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'2025-12-11','2026-01-12','draft',8105.0000),('96dba254-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','499045e9-d22a-11f0-a496-e40d36ebc7e6','924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'2025-11-22','2025-12-29','paid',26572.0000),('96fd072e-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','49932c8b-d22a-11f0-a496-e40d36ebc7e6','924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'2025-09-14','2025-10-27','paid',36094.0000),('971aa403-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','49932c8b-d22a-11f0-a496-e40d36ebc7e6','924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'2025-07-05','2025-08-03','draft',7851.0000),('97351c42-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','498f1164-d22a-11f0-a496-e40d36ebc7e6','924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'2025-11-09','2025-11-30','draft',23784.0000),('974ec12f-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','4991ca0c-d22a-11f0-a496-e40d36ebc7e6','924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'2025-07-16','2025-08-16','draft',32865.0000),('976a7917-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','4991ca0c-d22a-11f0-a496-e40d36ebc7e6','924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'2025-09-09','2025-10-13','pending',24873.0000),('9791a50d-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','4991ca0c-d22a-11f0-a496-e40d36ebc7e6','924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'2025-12-05','2025-12-21','draft',34011.0000),('97a541f9-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','499045e9-d22a-11f0-a496-e40d36ebc7e6','924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'2025-11-03','2025-11-27','paid',20829.0000),('97c1b94d-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','498f1164-d22a-11f0-a496-e40d36ebc7e6','924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'2025-10-30','2025-12-08','draft',23569.0000),('97e0ea32-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','499045e9-d22a-11f0-a496-e40d36ebc7e6','924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'2025-09-20','2025-10-30','paid',9532.0000),('97f5efaa-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','4989eeb2-d22a-11f0-a496-e40d36ebc7e6','923cbfa3-d22a-11f0-a496-e40d36ebc7e6',1,'2025-08-21','2025-09-26','pending',37853.0000),('981bc736-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','498ddaae-d22a-11f0-a496-e40d36ebc7e6','923cbfa3-d22a-11f0-a496-e40d36ebc7e6',1,'2025-08-29','2025-09-25','pending',45202.0000),('9846665a-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','4989eeb2-d22a-11f0-a496-e40d36ebc7e6','923cbfa3-d22a-11f0-a496-e40d36ebc7e6',1,'2025-10-27','2025-11-24','paid',12678.0000),('985a4098-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','498ca492-d22a-11f0-a496-e40d36ebc7e6','923cbfa3-d22a-11f0-a496-e40d36ebc7e6',1,'2025-08-16','2025-09-02','draft',17008.0000),('986ef85d-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','4989eeb2-d22a-11f0-a496-e40d36ebc7e6','923cbfa3-d22a-11f0-a496-e40d36ebc7e6',1,'2025-09-28','2025-11-11','draft',25186.0000),('98924ddc-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','4989eeb2-d22a-11f0-a496-e40d36ebc7e6','923cbfa3-d22a-11f0-a496-e40d36ebc7e6',1,'2025-07-17','2025-08-20','paid',14840.0000),('98a52e5f-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','498b796b-d22a-11f0-a496-e40d36ebc7e6','923cbfa3-d22a-11f0-a496-e40d36ebc7e6',1,'2025-07-10','2025-08-24','draft',21352.0000),('98c40289-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','498ca492-d22a-11f0-a496-e40d36ebc7e6','923cbfa3-d22a-11f0-a496-e40d36ebc7e6',1,'2025-09-08','2025-09-25','pending',40218.0000),('98dec825-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','498ddaae-d22a-11f0-a496-e40d36ebc7e6','923cbfa3-d22a-11f0-a496-e40d36ebc7e6',1,'2025-09-29','2025-10-17','paid',10192.0000),('990a94b2-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','4988a4fa-d22a-11f0-a496-e40d36ebc7e6','923cbfa3-d22a-11f0-a496-e40d36ebc7e6',1,'2025-12-22','2026-01-26','paid',29200.0000),('9930517d-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','498ca492-d22a-11f0-a496-e40d36ebc7e6','923cbfa3-d22a-11f0-a496-e40d36ebc7e6',1,'2025-11-05','2025-12-13','pending',41026.0000),('9944a5fe-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','498ca492-d22a-11f0-a496-e40d36ebc7e6','923cbfa3-d22a-11f0-a496-e40d36ebc7e6',1,'2025-11-16','2025-12-14','draft',29935.0000),('9969e36f-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','4989eeb2-d22a-11f0-a496-e40d36ebc7e6','923cbfa3-d22a-11f0-a496-e40d36ebc7e6',1,'2025-10-29','2025-12-05','pending',14779.0000),('997edf61-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','498ddaae-d22a-11f0-a496-e40d36ebc7e6','923cbfa3-d22a-11f0-a496-e40d36ebc7e6',1,'2025-07-18','2025-08-08','draft',20977.0000),('998cf97b-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','498b796b-d22a-11f0-a496-e40d36ebc7e6','923cbfa3-d22a-11f0-a496-e40d36ebc7e6',1,'2025-07-27','2025-08-30','pending',51231.0000),('99b00fa1-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','4988a4fa-d22a-11f0-a496-e40d36ebc7e6','923cbfa3-d22a-11f0-a496-e40d36ebc7e6',1,'2025-09-16','2025-10-26','paid',19164.0000),('99cbc6be-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','4989eeb2-d22a-11f0-a496-e40d36ebc7e6','923cbfa3-d22a-11f0-a496-e40d36ebc7e6',1,'2025-07-24','2025-08-12','pending',53784.0000),('99ee1ace-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','498ddaae-d22a-11f0-a496-e40d36ebc7e6','923cbfa3-d22a-11f0-a496-e40d36ebc7e6',1,'2025-09-10','2025-10-24','paid',23503.0000),('9a0d34ad-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','498ca492-d22a-11f0-a496-e40d36ebc7e6','923cbfa3-d22a-11f0-a496-e40d36ebc7e6',1,'2025-10-08','2025-10-24','pending',20300.0000),('9a28841e-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','49875afa-d22a-11f0-a496-e40d36ebc7e6','9230756d-d22a-11f0-a496-e40d36ebc7e6',1,'2025-09-08','2025-10-20','paid',11299.0000),('9a3e3499-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','49861309-d22a-11f0-a496-e40d36ebc7e6','9230756d-d22a-11f0-a496-e40d36ebc7e6',1,'2025-07-02','2025-07-31','pending',7409.0000),('9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','49875afa-d22a-11f0-a496-e40d36ebc7e6','9230756d-d22a-11f0-a496-e40d36ebc7e6',1,'2025-10-13','2025-11-15','pending',39302.0000),('9a7fb48f-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','498332a6-d22a-11f0-a496-e40d36ebc7e6','9230756d-d22a-11f0-a496-e40d36ebc7e6',1,'2025-09-29','2025-10-31','draft',19293.0000),('9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','49875afa-d22a-11f0-a496-e40d36ebc7e6','9230756d-d22a-11f0-a496-e40d36ebc7e6',1,'2025-09-08','2025-10-02','draft',19372.0000),('9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','49847c4e-d22a-11f0-a496-e40d36ebc7e6','9230756d-d22a-11f0-a496-e40d36ebc7e6',1,'2025-11-05','2025-12-03','paid',30333.0000),('9ada5692-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','498332a6-d22a-11f0-a496-e40d36ebc7e6','9230756d-d22a-11f0-a496-e40d36ebc7e6',1,'2025-08-05','2025-09-13','draft',8720.0000),('9af42ee3-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','498332a6-d22a-11f0-a496-e40d36ebc7e6','9230756d-d22a-11f0-a496-e40d36ebc7e6',1,'2025-10-11','2025-11-17','paid',40248.0000),('9b17559c-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','498332a6-d22a-11f0-a496-e40d36ebc7e6','9230756d-d22a-11f0-a496-e40d36ebc7e6',1,'2025-12-15','2026-01-06','pending',32075.0000),('9b34a914-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','498332a6-d22a-11f0-a496-e40d36ebc7e6','9230756d-d22a-11f0-a496-e40d36ebc7e6',1,'2025-07-04','2025-08-07','pending',33945.0000),('9b54ad4a-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','49847c4e-d22a-11f0-a496-e40d36ebc7e6','9230756d-d22a-11f0-a496-e40d36ebc7e6',1,'2025-09-20','2025-10-21','draft',13423.0000),('9b728e96-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','49847c4e-d22a-11f0-a496-e40d36ebc7e6','9230756d-d22a-11f0-a496-e40d36ebc7e6',1,'2025-10-01','2025-11-12','paid',24591.0000),('9b8f6e3d-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','498332a6-d22a-11f0-a496-e40d36ebc7e6','9230756d-d22a-11f0-a496-e40d36ebc7e6',1,'2025-09-30','2025-10-31','pending',17892.0000),('9baade12-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','49847c4e-d22a-11f0-a496-e40d36ebc7e6','9230756d-d22a-11f0-a496-e40d36ebc7e6',1,'2025-07-18','2025-08-10','paid',54333.0000),('9bcf2e9b-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','49861309-d22a-11f0-a496-e40d36ebc7e6','9230756d-d22a-11f0-a496-e40d36ebc7e6',1,'2025-12-24','2026-01-27','paid',29488.0000),('9be4cd76-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','49875afa-d22a-11f0-a496-e40d36ebc7e6','9230756d-d22a-11f0-a496-e40d36ebc7e6',1,'2025-07-16','2025-08-23','pending',16048.0000),('9bf4215e-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','49847c4e-d22a-11f0-a496-e40d36ebc7e6','9230756d-d22a-11f0-a496-e40d36ebc7e6',1,'2025-09-20','2025-10-14','paid',14064.0000),('9c056456-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','498332a6-d22a-11f0-a496-e40d36ebc7e6','9230756d-d22a-11f0-a496-e40d36ebc7e6',1,'2025-11-26','2026-01-08','pending',12280.0000),('9c20a22b-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','49861309-d22a-11f0-a496-e40d36ebc7e6','9230756d-d22a-11f0-a496-e40d36ebc7e6',1,'2025-12-25','2026-01-23','draft',20339.0000),('9c397c0b-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','497ca535-d22a-11f0-a496-e40d36ebc7e6','8caf7295-d22a-11f0-a496-e40d36ebc7e6',1,'2025-11-19','2025-12-31','paid',1059.3000),('9c4a0ae5-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','497ca535-d22a-11f0-a496-e40d36ebc7e6','8caf7295-d22a-11f0-a496-e40d36ebc7e6',1,'2025-07-26','2025-09-02','pending',34637.9000),('9c5db651-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','497e02eb-d22a-11f0-a496-e40d36ebc7e6','8caf7295-d22a-11f0-a496-e40d36ebc7e6',1,'2025-09-05','2025-10-03','paid',11385.0000),('9c700523-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','497e02eb-d22a-11f0-a496-e40d36ebc7e6','8caf7295-d22a-11f0-a496-e40d36ebc7e6',1,'2025-10-15','2025-11-16','pending',41160.9000),('9c86dee1-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','49807a06-d22a-11f0-a496-e40d36ebc7e6','8caf7295-d22a-11f0-a496-e40d36ebc7e6',1,'2025-12-27','2026-01-27','pending',28600.0000),('9c95ac06-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','497e02eb-d22a-11f0-a496-e40d36ebc7e6','8caf7295-d22a-11f0-a496-e40d36ebc7e6',1,'2025-12-02','2026-01-06','draft',31742.7000),('9cb9c755-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','497f49ee-d22a-11f0-a496-e40d36ebc7e6','8caf7295-d22a-11f0-a496-e40d36ebc7e6',1,'2025-10-15','2025-11-26','pending',40899.1000),('9cd1176a-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','49807a06-d22a-11f0-a496-e40d36ebc7e6','8caf7295-d22a-11f0-a496-e40d36ebc7e6',1,'2025-10-05','2025-11-17','pending',33223.3000),('9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','497e02eb-d22a-11f0-a496-e40d36ebc7e6','8caf7295-d22a-11f0-a496-e40d36ebc7e6',1,'2025-11-11','2025-12-26','paid',26340.6000),('9d11fd67-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','497ca535-d22a-11f0-a496-e40d36ebc7e6','8caf7295-d22a-11f0-a496-e40d36ebc7e6',1,'2025-10-31','2025-12-06','pending',5721.1000),('9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','497f49ee-d22a-11f0-a496-e40d36ebc7e6','8caf7295-d22a-11f0-a496-e40d36ebc7e6',1,'2025-07-24','2025-08-26','pending',16069.9000),('9d3f19ca-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','497f49ee-d22a-11f0-a496-e40d36ebc7e6','8caf7295-d22a-11f0-a496-e40d36ebc7e6',1,'2025-08-31','2025-10-13','pending',38710.1000),('9d5331e1-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','497e02eb-d22a-11f0-a496-e40d36ebc7e6','8caf7295-d22a-11f0-a496-e40d36ebc7e6',1,'2025-12-16','2026-01-17','pending',4466.0000),('9d634062-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','497f49ee-d22a-11f0-a496-e40d36ebc7e6','8caf7295-d22a-11f0-a496-e40d36ebc7e6',1,'2025-11-09','2025-12-11','pending',8022.3000),('9d77771b-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','497ca535-d22a-11f0-a496-e40d36ebc7e6','8caf7295-d22a-11f0-a496-e40d36ebc7e6',1,'2025-09-25','2025-10-29','draft',13912.8000);
/*!40000 ALTER TABLE `invoice` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_invoice_status_update` AFTER UPDATE ON `invoice` FOR EACH ROW BEGIN
    IF OLD.status != NEW.status THEN
        INSERT INTO audit_log (
        audit_id,
            table_name,
            record_id,
            action_type,
            field_name,
            old_value,
            new_value,
            additional_info
        ) VALUES (
        UUID(),
            'invoice',
            NEW.invoice_id,
            'UPDATE',
            'status',
            IFNULL(OLD.status, 'NULL'),
            IFNULL(NEW.status, 'NULL'),
            CONCAT('Customer: ', (SELECT name FROM customer WHERE customer_id = NEW.customer_id),
                   ' | Amount: ', NEW.total_amount)
        );
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

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
INSERT INTO `invoice_value` VALUES ('95bdb06b-d22a-11f0-a496-e40d36ebc7e6','95bc2d9c-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,1),('95beedc4-d22a-11f0-a496-e40d36ebc7e6','95bc2d9c-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,11.0000,NULL,NULL,1),('95c010f6-d22a-11f0-a496-e40d36ebc7e6','95bc2d9c-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,477.0000,NULL,NULL,1),('95c1261c-d22a-11f0-a496-e40d36ebc7e6','95bc2d9c-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,2),('95c234a2-d22a-11f0-a496-e40d36ebc7e6','95bc2d9c-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,38.0000,NULL,NULL,2),('95c36012-d22a-11f0-a496-e40d36ebc7e6','95bc2d9c-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,462.0000,NULL,NULL,2),('95c50358-d22a-11f0-a496-e40d36ebc7e6','95bc2d9c-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,3),('95c63755-d22a-11f0-a496-e40d36ebc7e6','95bc2d9c-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,25.0000,NULL,NULL,3),('95c76754-d22a-11f0-a496-e40d36ebc7e6','95bc2d9c-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,407.0000,NULL,NULL,3),('95c8e59a-d22a-11f0-a496-e40d36ebc7e6','95bc2d9c-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,4),('95ca1d51-d22a-11f0-a496-e40d36ebc7e6','95bc2d9c-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,6.0000,NULL,NULL,4),('95cb05bf-d22a-11f0-a496-e40d36ebc7e6','95bc2d9c-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,384.0000,NULL,NULL,4),('95ceb2f2-d22a-11f0-a496-e40d36ebc7e6','95bc2d9c-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,5247.0000,NULL,NULL,1),('95cfc092-d22a-11f0-a496-e40d36ebc7e6','95bc2d9c-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,17556.0000,NULL,NULL,2),('95d0d613-d22a-11f0-a496-e40d36ebc7e6','95bc2d9c-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,10175.0000,NULL,NULL,3),('95d1dd48-d22a-11f0-a496-e40d36ebc7e6','95bc2d9c-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,2304.0000,NULL,NULL,4),('95d31b99-d22a-11f0-a496-e40d36ebc7e6','95bc2d9c-d22a-11f0-a496-e40d36ebc7e6','9252da43-d22a-11f0-a496-e40d36ebc7e6',NULL,35282.0000,NULL,NULL,0),('95d52d74-d22a-11f0-a496-e40d36ebc7e6','95bc2d9c-d22a-11f0-a496-e40d36ebc7e6','92540789-d22a-11f0-a496-e40d36ebc7e6',NULL,3528.2000,NULL,NULL,0),('95d68848-d22a-11f0-a496-e40d36ebc7e6','95bc2d9c-d22a-11f0-a496-e40d36ebc7e6','925521d9-d22a-11f0-a496-e40d36ebc7e6',NULL,38810.2000,NULL,NULL,0),('95daf524-d22a-11f0-a496-e40d36ebc7e6','95d9649f-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,1),('95dc1814-d22a-11f0-a496-e40d36ebc7e6','95d9649f-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,12.0000,NULL,NULL,1),('95df8159-d22a-11f0-a496-e40d36ebc7e6','95d9649f-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,368.0000,NULL,NULL,1),('95e0a49f-d22a-11f0-a496-e40d36ebc7e6','95d9649f-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,2),('95e1e34c-d22a-11f0-a496-e40d36ebc7e6','95d9649f-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,8.0000,NULL,NULL,2),('95e30a29-d22a-11f0-a496-e40d36ebc7e6','95d9649f-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,139.0000,NULL,NULL,2),('95e46bf8-d22a-11f0-a496-e40d36ebc7e6','95d9649f-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,3),('95e5b1c9-d22a-11f0-a496-e40d36ebc7e6','95d9649f-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,24.0000,NULL,NULL,3),('95e6d434-d22a-11f0-a496-e40d36ebc7e6','95d9649f-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,259.0000,NULL,NULL,3),('95e80166-d22a-11f0-a496-e40d36ebc7e6','95d9649f-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Cloud Infrastructure Setup',NULL,NULL,NULL,4),('95e95bc2-d22a-11f0-a496-e40d36ebc7e6','95d9649f-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,40.0000,NULL,NULL,4),('95ea8351-d22a-11f0-a496-e40d36ebc7e6','95d9649f-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,156.0000,NULL,NULL,4),('95efbd92-d22a-11f0-a496-e40d36ebc7e6','95d9649f-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,4416.0000,NULL,NULL,1),('95f11a1d-d22a-11f0-a496-e40d36ebc7e6','95d9649f-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,1112.0000,NULL,NULL,2),('95f2a9e3-d22a-11f0-a496-e40d36ebc7e6','95d9649f-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,6216.0000,NULL,NULL,3),('95f451a9-d22a-11f0-a496-e40d36ebc7e6','95d9649f-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,6240.0000,NULL,NULL,4),('95f59c56-d22a-11f0-a496-e40d36ebc7e6','95d9649f-d22a-11f0-a496-e40d36ebc7e6','9252da43-d22a-11f0-a496-e40d36ebc7e6',NULL,17984.0000,NULL,NULL,0),('95f6e4d8-d22a-11f0-a496-e40d36ebc7e6','95d9649f-d22a-11f0-a496-e40d36ebc7e6','92540789-d22a-11f0-a496-e40d36ebc7e6',NULL,1798.4000,NULL,NULL,0),('95f86fd5-d22a-11f0-a496-e40d36ebc7e6','95d9649f-d22a-11f0-a496-e40d36ebc7e6','925521d9-d22a-11f0-a496-e40d36ebc7e6',NULL,19782.4000,NULL,NULL,0),('95fc583e-d22a-11f0-a496-e40d36ebc7e6','95fad294-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,1),('95fdaa31-d22a-11f0-a496-e40d36ebc7e6','95fad294-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,46.0000,NULL,NULL,1),('95fef64e-d22a-11f0-a496-e40d36ebc7e6','95fad294-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,437.0000,NULL,NULL,1),('960047e2-d22a-11f0-a496-e40d36ebc7e6','95fad294-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,2),('9601b8b4-d22a-11f0-a496-e40d36ebc7e6','95fad294-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,44.0000,NULL,NULL,2),('9602e056-d22a-11f0-a496-e40d36ebc7e6','95fad294-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,371.0000,NULL,NULL,2),('9603ea4f-d22a-11f0-a496-e40d36ebc7e6','95fad294-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,3),('9604eb88-d22a-11f0-a496-e40d36ebc7e6','95fad294-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,32.0000,NULL,NULL,3),('9605da19-d22a-11f0-a496-e40d36ebc7e6','95fad294-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,109.0000,NULL,NULL,3),('9607e91e-d22a-11f0-a496-e40d36ebc7e6','95fad294-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,20102.0000,NULL,NULL,1),('9608d79f-d22a-11f0-a496-e40d36ebc7e6','95fad294-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,16324.0000,NULL,NULL,2),('960a259d-d22a-11f0-a496-e40d36ebc7e6','95fad294-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,3488.0000,NULL,NULL,3),('960b8645-d22a-11f0-a496-e40d36ebc7e6','95fad294-d22a-11f0-a496-e40d36ebc7e6','9252da43-d22a-11f0-a496-e40d36ebc7e6',NULL,39914.0000,NULL,NULL,0),('960d08fd-d22a-11f0-a496-e40d36ebc7e6','95fad294-d22a-11f0-a496-e40d36ebc7e6','92540789-d22a-11f0-a496-e40d36ebc7e6',NULL,3991.4000,NULL,NULL,0),('960e7b50-d22a-11f0-a496-e40d36ebc7e6','95fad294-d22a-11f0-a496-e40d36ebc7e6','925521d9-d22a-11f0-a496-e40d36ebc7e6',NULL,43905.4000,NULL,NULL,0),('961265ea-d22a-11f0-a496-e40d36ebc7e6','961119c9-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,1),('96138267-d22a-11f0-a496-e40d36ebc7e6','961119c9-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,28.0000,NULL,NULL,1),('96149266-d22a-11f0-a496-e40d36ebc7e6','961119c9-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,257.0000,NULL,NULL,1),('961992ad-d22a-11f0-a496-e40d36ebc7e6','961119c9-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,2),('961abb24-d22a-11f0-a496-e40d36ebc7e6','961119c9-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,27.0000,NULL,NULL,2),('961c1437-d22a-11f0-a496-e40d36ebc7e6','961119c9-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,404.0000,NULL,NULL,2),('961d405b-d22a-11f0-a496-e40d36ebc7e6','961119c9-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,3),('961e5fc9-d22a-11f0-a496-e40d36ebc7e6','961119c9-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,44.0000,NULL,NULL,3),('961fd92a-d22a-11f0-a496-e40d36ebc7e6','961119c9-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,286.0000,NULL,NULL,3),('9624023c-d22a-11f0-a496-e40d36ebc7e6','961119c9-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,7196.0000,NULL,NULL,1),('9625ac38-d22a-11f0-a496-e40d36ebc7e6','961119c9-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,10908.0000,NULL,NULL,2),('9627317f-d22a-11f0-a496-e40d36ebc7e6','961119c9-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,12584.0000,NULL,NULL,3),('96294ca8-d22a-11f0-a496-e40d36ebc7e6','961119c9-d22a-11f0-a496-e40d36ebc7e6','9252da43-d22a-11f0-a496-e40d36ebc7e6',NULL,30688.0000,NULL,NULL,0),('962a9abc-d22a-11f0-a496-e40d36ebc7e6','961119c9-d22a-11f0-a496-e40d36ebc7e6','92540789-d22a-11f0-a496-e40d36ebc7e6',NULL,3068.8000,NULL,NULL,0),('962bdc07-d22a-11f0-a496-e40d36ebc7e6','961119c9-d22a-11f0-a496-e40d36ebc7e6','925521d9-d22a-11f0-a496-e40d36ebc7e6',NULL,33756.8000,NULL,NULL,0),('962fcd41-d22a-11f0-a496-e40d36ebc7e6','962e660f-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Cloud Infrastructure Setup',NULL,NULL,NULL,1),('9630f637-d22a-11f0-a496-e40d36ebc7e6','962e660f-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,18.0000,NULL,NULL,1),('963249d8-d22a-11f0-a496-e40d36ebc7e6','962e660f-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,285.0000,NULL,NULL,1),('96338217-d22a-11f0-a496-e40d36ebc7e6','962e660f-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','System Integration',NULL,NULL,NULL,2),('9634a098-d22a-11f0-a496-e40d36ebc7e6','962e660f-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,12.0000,NULL,NULL,2),('96359df5-d22a-11f0-a496-e40d36ebc7e6','962e660f-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,480.0000,NULL,NULL,2),('96369fbe-d22a-11f0-a496-e40d36ebc7e6','962e660f-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','System Integration',NULL,NULL,NULL,3),('963785a8-d22a-11f0-a496-e40d36ebc7e6','962e660f-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,12.0000,NULL,NULL,3),('96388548-d22a-11f0-a496-e40d36ebc7e6','962e660f-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,420.0000,NULL,NULL,3),('9639b05b-d22a-11f0-a496-e40d36ebc7e6','962e660f-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,4),('963ac852-d22a-11f0-a496-e40d36ebc7e6','962e660f-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,12.0000,NULL,NULL,4),('963bc2fb-d22a-11f0-a496-e40d36ebc7e6','962e660f-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,201.0000,NULL,NULL,4),('9640101d-d22a-11f0-a496-e40d36ebc7e6','962e660f-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,5130.0000,NULL,NULL,1),('9641734d-d22a-11f0-a496-e40d36ebc7e6','962e660f-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,5760.0000,NULL,NULL,2),('96428dde-d22a-11f0-a496-e40d36ebc7e6','962e660f-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,5040.0000,NULL,NULL,3),('964413a4-d22a-11f0-a496-e40d36ebc7e6','962e660f-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,2412.0000,NULL,NULL,4),('96454f4f-d22a-11f0-a496-e40d36ebc7e6','962e660f-d22a-11f0-a496-e40d36ebc7e6','9252da43-d22a-11f0-a496-e40d36ebc7e6',NULL,18342.0000,NULL,NULL,0),('9646656b-d22a-11f0-a496-e40d36ebc7e6','962e660f-d22a-11f0-a496-e40d36ebc7e6','92540789-d22a-11f0-a496-e40d36ebc7e6',NULL,1834.2000,NULL,NULL,0),('96474444-d22a-11f0-a496-e40d36ebc7e6','962e660f-d22a-11f0-a496-e40d36ebc7e6','925521d9-d22a-11f0-a496-e40d36ebc7e6',NULL,20176.2000,NULL,NULL,0),('964ad3b7-d22a-11f0-a496-e40d36ebc7e6','96498229-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Cloud Infrastructure Setup',NULL,NULL,NULL,1),('964c4c01-d22a-11f0-a496-e40d36ebc7e6','96498229-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,42.0000,NULL,NULL,1),('964e003e-d22a-11f0-a496-e40d36ebc7e6','96498229-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,352.0000,NULL,NULL,1),('964fa676-d22a-11f0-a496-e40d36ebc7e6','96498229-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','System Integration',NULL,NULL,NULL,2),('9650e847-d22a-11f0-a496-e40d36ebc7e6','96498229-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,49.0000,NULL,NULL,2),('96521e2f-d22a-11f0-a496-e40d36ebc7e6','96498229-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,158.0000,NULL,NULL,2),('96531f38-d22a-11f0-a496-e40d36ebc7e6','96498229-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,3),('96540777-d22a-11f0-a496-e40d36ebc7e6','96498229-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,15.0000,NULL,NULL,3),('9654ee3b-d22a-11f0-a496-e40d36ebc7e6','96498229-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,257.0000,NULL,NULL,3),('9657437a-d22a-11f0-a496-e40d36ebc7e6','96498229-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,14784.0000,NULL,NULL,1),('96582f36-d22a-11f0-a496-e40d36ebc7e6','96498229-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,7742.0000,NULL,NULL,2),('9659b571-d22a-11f0-a496-e40d36ebc7e6','96498229-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,3855.0000,NULL,NULL,3),('965b6588-d22a-11f0-a496-e40d36ebc7e6','96498229-d22a-11f0-a496-e40d36ebc7e6','9252da43-d22a-11f0-a496-e40d36ebc7e6',NULL,26381.0000,NULL,NULL,0),('965ce24f-d22a-11f0-a496-e40d36ebc7e6','96498229-d22a-11f0-a496-e40d36ebc7e6','92540789-d22a-11f0-a496-e40d36ebc7e6',NULL,2638.1000,NULL,NULL,0),('965df108-d22a-11f0-a496-e40d36ebc7e6','96498229-d22a-11f0-a496-e40d36ebc7e6','925521d9-d22a-11f0-a496-e40d36ebc7e6',NULL,29019.1000,NULL,NULL,0),('96618eb1-d22a-11f0-a496-e40d36ebc7e6','96603ee6-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,1),('96627934-d22a-11f0-a496-e40d36ebc7e6','96603ee6-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,33.0000,NULL,NULL,1),('9663862f-d22a-11f0-a496-e40d36ebc7e6','96603ee6-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,55.0000,NULL,NULL,1),('9664bfd3-d22a-11f0-a496-e40d36ebc7e6','96603ee6-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,2),('9666186d-d22a-11f0-a496-e40d36ebc7e6','96603ee6-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,37.0000,NULL,NULL,2),('96674327-d22a-11f0-a496-e40d36ebc7e6','96603ee6-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,470.0000,NULL,NULL,2),('96686397-d22a-11f0-a496-e40d36ebc7e6','96603ee6-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,3),('96698da8-d22a-11f0-a496-e40d36ebc7e6','96603ee6-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,36.0000,NULL,NULL,3),('966b0e34-d22a-11f0-a496-e40d36ebc7e6','96603ee6-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,198.0000,NULL,NULL,3),('966c6c95-d22a-11f0-a496-e40d36ebc7e6','96603ee6-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Cloud Infrastructure Setup',NULL,NULL,NULL,4),('966da314-d22a-11f0-a496-e40d36ebc7e6','96603ee6-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,22.0000,NULL,NULL,4),('966ee8ca-d22a-11f0-a496-e40d36ebc7e6','96603ee6-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,468.0000,NULL,NULL,4),('96781634-d22a-11f0-a496-e40d36ebc7e6','96603ee6-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,1815.0000,NULL,NULL,1),('967a5e9c-d22a-11f0-a496-e40d36ebc7e6','96603ee6-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,17390.0000,NULL,NULL,2),('967cd402-d22a-11f0-a496-e40d36ebc7e6','96603ee6-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,7128.0000,NULL,NULL,3),('967f0a1f-d22a-11f0-a496-e40d36ebc7e6','96603ee6-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,10296.0000,NULL,NULL,4),('968161c0-d22a-11f0-a496-e40d36ebc7e6','96603ee6-d22a-11f0-a496-e40d36ebc7e6','9252da43-d22a-11f0-a496-e40d36ebc7e6',NULL,36629.0000,NULL,NULL,0),('96839248-d22a-11f0-a496-e40d36ebc7e6','96603ee6-d22a-11f0-a496-e40d36ebc7e6','92540789-d22a-11f0-a496-e40d36ebc7e6',NULL,3662.9000,NULL,NULL,0),('96854219-d22a-11f0-a496-e40d36ebc7e6','96603ee6-d22a-11f0-a496-e40d36ebc7e6','925521d9-d22a-11f0-a496-e40d36ebc7e6',NULL,40291.9000,NULL,NULL,0),('968a793b-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,1),('968c01ee-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,42.0000,NULL,NULL,1),('968d5d2f-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,220.0000,NULL,NULL,1),('968e9b8d-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','System Integration',NULL,NULL,NULL,2),('968fb1e5-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,42.0000,NULL,NULL,2),('9690f1bc-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,334.0000,NULL,NULL,2),('969200cf-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Cloud Infrastructure Setup',NULL,NULL,NULL,3),('969341cb-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,39.0000,NULL,NULL,3),('969461d7-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,394.0000,NULL,NULL,3),('9695d580-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,4),('96975379-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,50.0000,NULL,NULL,4),('9698dbac-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,441.0000,NULL,NULL,4),('9699ba45-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,5),('969aa3e6-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,2.0000,NULL,NULL,5),('969c2d7e-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,253.0000,NULL,NULL,5),('969f8a3b-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,9240.0000,NULL,NULL,1),('96a0decc-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,14028.0000,NULL,NULL,2),('96a24433-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,15366.0000,NULL,NULL,3),('96a38ddd-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,22050.0000,NULL,NULL,4),('96a48ee8-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,506.0000,NULL,NULL,5),('96a57896-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','9252da43-d22a-11f0-a496-e40d36ebc7e6',NULL,61190.0000,NULL,NULL,0),('96a675dc-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','92540789-d22a-11f0-a496-e40d36ebc7e6',NULL,6119.0000,NULL,NULL,0),('96a8116e-d22a-11f0-a496-e40d36ebc7e6','96887555-d22a-11f0-a496-e40d36ebc7e6','925521d9-d22a-11f0-a496-e40d36ebc7e6',NULL,67309.0000,NULL,NULL,0),('96ac4044-d22a-11f0-a496-e40d36ebc7e6','96ab0b5c-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,1),('96ad48c2-d22a-11f0-a496-e40d36ebc7e6','96ab0b5c-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,45.0000,NULL,NULL,1),('96ae5258-d22a-11f0-a496-e40d36ebc7e6','96ab0b5c-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,406.0000,NULL,NULL,1),('96af32f8-d22a-11f0-a496-e40d36ebc7e6','96ab0b5c-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,2),('96b01342-d22a-11f0-a496-e40d36ebc7e6','96ab0b5c-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,21.0000,NULL,NULL,2),('96b12b53-d22a-11f0-a496-e40d36ebc7e6','96ab0b5c-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,214.0000,NULL,NULL,2),('96b232a8-d22a-11f0-a496-e40d36ebc7e6','96ab0b5c-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,3),('96b38dcd-d22a-11f0-a496-e40d36ebc7e6','96ab0b5c-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,6.0000,NULL,NULL,3),('96b4eacf-d22a-11f0-a496-e40d36ebc7e6','96ab0b5c-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,225.0000,NULL,NULL,3),('96b62186-d22a-11f0-a496-e40d36ebc7e6','96ab0b5c-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,4),('96b7591d-d22a-11f0-a496-e40d36ebc7e6','96ab0b5c-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,1.0000,NULL,NULL,4),('96b89fb2-d22a-11f0-a496-e40d36ebc7e6','96ab0b5c-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,137.0000,NULL,NULL,4),('96bd0ba3-d22a-11f0-a496-e40d36ebc7e6','96ab0b5c-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,18270.0000,NULL,NULL,1),('96be67ea-d22a-11f0-a496-e40d36ebc7e6','96ab0b5c-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,4494.0000,NULL,NULL,2),('96bfcd30-d22a-11f0-a496-e40d36ebc7e6','96ab0b5c-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,1350.0000,NULL,NULL,3),('96c1b324-d22a-11f0-a496-e40d36ebc7e6','96ab0b5c-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,137.0000,NULL,NULL,4),('96c3550a-d22a-11f0-a496-e40d36ebc7e6','96ab0b5c-d22a-11f0-a496-e40d36ebc7e6','9252da43-d22a-11f0-a496-e40d36ebc7e6',NULL,24251.0000,NULL,NULL,0),('96c4a050-d22a-11f0-a496-e40d36ebc7e6','96ab0b5c-d22a-11f0-a496-e40d36ebc7e6','92540789-d22a-11f0-a496-e40d36ebc7e6',NULL,2425.1000,NULL,NULL,0),('96c5e8d3-d22a-11f0-a496-e40d36ebc7e6','96ab0b5c-d22a-11f0-a496-e40d36ebc7e6','925521d9-d22a-11f0-a496-e40d36ebc7e6',NULL,26676.1000,NULL,NULL,0),('96c9e392-d22a-11f0-a496-e40d36ebc7e6','96c875e0-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Cloud Infrastructure Setup',NULL,NULL,NULL,1),('96cb1087-d22a-11f0-a496-e40d36ebc7e6','96c875e0-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,10.0000,NULL,NULL,1),('96cc1895-d22a-11f0-a496-e40d36ebc7e6','96c875e0-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,302.0000,NULL,NULL,1),('96cd0c5f-d22a-11f0-a496-e40d36ebc7e6','96c875e0-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,2),('96ce71a1-d22a-11f0-a496-e40d36ebc7e6','96c875e0-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,15.0000,NULL,NULL,2),('96cfb9e5-d22a-11f0-a496-e40d36ebc7e6','96c875e0-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,339.0000,NULL,NULL,2),('96d2fb41-d22a-11f0-a496-e40d36ebc7e6','96c875e0-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,3020.0000,NULL,NULL,1),('96d471bc-d22a-11f0-a496-e40d36ebc7e6','96c875e0-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,5085.0000,NULL,NULL,2),('96d5b460-d22a-11f0-a496-e40d36ebc7e6','96c875e0-d22a-11f0-a496-e40d36ebc7e6','9252da43-d22a-11f0-a496-e40d36ebc7e6',NULL,8105.0000,NULL,NULL,0),('96d75b34-d22a-11f0-a496-e40d36ebc7e6','96c875e0-d22a-11f0-a496-e40d36ebc7e6','92540789-d22a-11f0-a496-e40d36ebc7e6',NULL,810.5000,NULL,NULL,0),('96d875f1-d22a-11f0-a496-e40d36ebc7e6','96c875e0-d22a-11f0-a496-e40d36ebc7e6','925521d9-d22a-11f0-a496-e40d36ebc7e6',NULL,8915.5000,NULL,NULL,0),('96dd6ece-d22a-11f0-a496-e40d36ebc7e6','96dba254-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,1),('96df0dca-d22a-11f0-a496-e40d36ebc7e6','96dba254-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,50.0000,NULL,NULL,1),('96e0c850-d22a-11f0-a496-e40d36ebc7e6','96dba254-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,318.0000,NULL,NULL,1),('96e28963-d22a-11f0-a496-e40d36ebc7e6','96dba254-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,2),('96e3f1e4-d22a-11f0-a496-e40d36ebc7e6','96dba254-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,5.0000,NULL,NULL,2),('96e56f55-d22a-11f0-a496-e40d36ebc7e6','96dba254-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,326.0000,NULL,NULL,2),('96e6fe28-d22a-11f0-a496-e40d36ebc7e6','96dba254-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,3),('96e840d9-d22a-11f0-a496-e40d36ebc7e6','96dba254-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,3.0000,NULL,NULL,3),('96e98828-d22a-11f0-a496-e40d36ebc7e6','96dba254-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,310.0000,NULL,NULL,3),('96eac868-d22a-11f0-a496-e40d36ebc7e6','96dba254-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,4),('96ebfe29-d22a-11f0-a496-e40d36ebc7e6','96dba254-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,48.0000,NULL,NULL,4),('96ed3ede-d22a-11f0-a496-e40d36ebc7e6','96dba254-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,169.0000,NULL,NULL,4),('96f2563b-d22a-11f0-a496-e40d36ebc7e6','96dba254-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,15900.0000,NULL,NULL,1),('96f3c8cd-d22a-11f0-a496-e40d36ebc7e6','96dba254-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,1630.0000,NULL,NULL,2),('96f4ddc5-d22a-11f0-a496-e40d36ebc7e6','96dba254-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,930.0000,NULL,NULL,3),('96f641ac-d22a-11f0-a496-e40d36ebc7e6','96dba254-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,8112.0000,NULL,NULL,4),('96f7cf53-d22a-11f0-a496-e40d36ebc7e6','96dba254-d22a-11f0-a496-e40d36ebc7e6','9252da43-d22a-11f0-a496-e40d36ebc7e6',NULL,26572.0000,NULL,NULL,0),('96f9106c-d22a-11f0-a496-e40d36ebc7e6','96dba254-d22a-11f0-a496-e40d36ebc7e6','92540789-d22a-11f0-a496-e40d36ebc7e6',NULL,2657.2000,NULL,NULL,0),('96fa4c5e-d22a-11f0-a496-e40d36ebc7e6','96dba254-d22a-11f0-a496-e40d36ebc7e6','925521d9-d22a-11f0-a496-e40d36ebc7e6',NULL,29229.2000,NULL,NULL,0),('96fec0fb-d22a-11f0-a496-e40d36ebc7e6','96fd072e-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,1),('9700003a-d22a-11f0-a496-e40d36ebc7e6','96fd072e-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,42.0000,NULL,NULL,1),('970175af-d22a-11f0-a496-e40d36ebc7e6','96fd072e-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,364.0000,NULL,NULL,1),('97031270-d22a-11f0-a496-e40d36ebc7e6','96fd072e-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,2),('9704410f-d22a-11f0-a496-e40d36ebc7e6','96fd072e-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,47.0000,NULL,NULL,2),('97054946-d22a-11f0-a496-e40d36ebc7e6','96fd072e-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,244.0000,NULL,NULL,2),('97065b1f-d22a-11f0-a496-e40d36ebc7e6','96fd072e-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,3),('97077a29-d22a-11f0-a496-e40d36ebc7e6','96fd072e-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,35.0000,NULL,NULL,3),('97089c09-d22a-11f0-a496-e40d36ebc7e6','96fd072e-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,170.0000,NULL,NULL,3),('9709fec7-d22a-11f0-a496-e40d36ebc7e6','96fd072e-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','System Integration',NULL,NULL,NULL,4),('970b09ff-d22a-11f0-a496-e40d36ebc7e6','96fd072e-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,44.0000,NULL,NULL,4),('970c3f7e-d22a-11f0-a496-e40d36ebc7e6','96fd072e-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,77.0000,NULL,NULL,4),('970fb549-d22a-11f0-a496-e40d36ebc7e6','96fd072e-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,15288.0000,NULL,NULL,1),('9711110d-d22a-11f0-a496-e40d36ebc7e6','96fd072e-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,11468.0000,NULL,NULL,2),('97124bdd-d22a-11f0-a496-e40d36ebc7e6','96fd072e-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,5950.0000,NULL,NULL,3),('97138b77-d22a-11f0-a496-e40d36ebc7e6','96fd072e-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,3388.0000,NULL,NULL,4),('9714f5ea-d22a-11f0-a496-e40d36ebc7e6','96fd072e-d22a-11f0-a496-e40d36ebc7e6','9252da43-d22a-11f0-a496-e40d36ebc7e6',NULL,36094.0000,NULL,NULL,0),('9716b30b-d22a-11f0-a496-e40d36ebc7e6','96fd072e-d22a-11f0-a496-e40d36ebc7e6','92540789-d22a-11f0-a496-e40d36ebc7e6',NULL,3609.4000,NULL,NULL,0),('9717f58b-d22a-11f0-a496-e40d36ebc7e6','96fd072e-d22a-11f0-a496-e40d36ebc7e6','925521d9-d22a-11f0-a496-e40d36ebc7e6',NULL,39703.4000,NULL,NULL,0),('971c28b2-d22a-11f0-a496-e40d36ebc7e6','971aa403-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,1),('971d5eb8-d22a-11f0-a496-e40d36ebc7e6','971aa403-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,9.0000,NULL,NULL,1),('971e91c6-d22a-11f0-a496-e40d36ebc7e6','971aa403-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,401.0000,NULL,NULL,1),('971fbc3f-d22a-11f0-a496-e40d36ebc7e6','971aa403-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,2),('9721146f-d22a-11f0-a496-e40d36ebc7e6','971aa403-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,8.0000,NULL,NULL,2),('972260b6-d22a-11f0-a496-e40d36ebc7e6','971aa403-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,488.0000,NULL,NULL,2),('9723e0ff-d22a-11f0-a496-e40d36ebc7e6','971aa403-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,3),('9725120b-d22a-11f0-a496-e40d36ebc7e6','971aa403-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,2.0000,NULL,NULL,3),('97265779-d22a-11f0-a496-e40d36ebc7e6','971aa403-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,169.0000,NULL,NULL,3),('972a8bda-d22a-11f0-a496-e40d36ebc7e6','971aa403-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,3609.0000,NULL,NULL,1),('972c5dcd-d22a-11f0-a496-e40d36ebc7e6','971aa403-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,3904.0000,NULL,NULL,2),('972e32f6-d22a-11f0-a496-e40d36ebc7e6','971aa403-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,338.0000,NULL,NULL,3),('972fcbd1-d22a-11f0-a496-e40d36ebc7e6','971aa403-d22a-11f0-a496-e40d36ebc7e6','9252da43-d22a-11f0-a496-e40d36ebc7e6',NULL,7851.0000,NULL,NULL,0),('97314eb4-d22a-11f0-a496-e40d36ebc7e6','971aa403-d22a-11f0-a496-e40d36ebc7e6','92540789-d22a-11f0-a496-e40d36ebc7e6',NULL,785.1000,NULL,NULL,0),('973295d2-d22a-11f0-a496-e40d36ebc7e6','971aa403-d22a-11f0-a496-e40d36ebc7e6','925521d9-d22a-11f0-a496-e40d36ebc7e6',NULL,8636.1000,NULL,NULL,0),('97369b20-d22a-11f0-a496-e40d36ebc7e6','97351c42-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,1),('9737c4ce-d22a-11f0-a496-e40d36ebc7e6','97351c42-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,33.0000,NULL,NULL,1),('9738dfee-d22a-11f0-a496-e40d36ebc7e6','97351c42-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,332.0000,NULL,NULL,1),('9739fb45-d22a-11f0-a496-e40d36ebc7e6','97351c42-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','System Integration',NULL,NULL,NULL,2),('973b0f90-d22a-11f0-a496-e40d36ebc7e6','97351c42-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,14.0000,NULL,NULL,2),('973c2838-d22a-11f0-a496-e40d36ebc7e6','97351c42-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,260.0000,NULL,NULL,2),('973d3c0c-d22a-11f0-a496-e40d36ebc7e6','97351c42-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,3),('973e471f-d22a-11f0-a496-e40d36ebc7e6','97351c42-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,45.0000,NULL,NULL,3),('973f7256-d22a-11f0-a496-e40d36ebc7e6','97351c42-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,180.0000,NULL,NULL,3),('97405494-d22a-11f0-a496-e40d36ebc7e6','97351c42-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,4),('9741334e-d22a-11f0-a496-e40d36ebc7e6','97351c42-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,8.0000,NULL,NULL,4),('9742196a-d22a-11f0-a496-e40d36ebc7e6','97351c42-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,136.0000,NULL,NULL,4),('974490a4-d22a-11f0-a496-e40d36ebc7e6','97351c42-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,10956.0000,NULL,NULL,1),('97457ea1-d22a-11f0-a496-e40d36ebc7e6','97351c42-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,3640.0000,NULL,NULL,2),('9746ad3d-d22a-11f0-a496-e40d36ebc7e6','97351c42-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,8100.0000,NULL,NULL,3),('97481007-d22a-11f0-a496-e40d36ebc7e6','97351c42-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,1088.0000,NULL,NULL,4),('974935ec-d22a-11f0-a496-e40d36ebc7e6','97351c42-d22a-11f0-a496-e40d36ebc7e6','9252da43-d22a-11f0-a496-e40d36ebc7e6',NULL,23784.0000,NULL,NULL,0),('974ab7af-d22a-11f0-a496-e40d36ebc7e6','97351c42-d22a-11f0-a496-e40d36ebc7e6','92540789-d22a-11f0-a496-e40d36ebc7e6',NULL,2378.4000,NULL,NULL,0),('974be1f1-d22a-11f0-a496-e40d36ebc7e6','97351c42-d22a-11f0-a496-e40d36ebc7e6','925521d9-d22a-11f0-a496-e40d36ebc7e6',NULL,26162.4000,NULL,NULL,0),('974fd1c6-d22a-11f0-a496-e40d36ebc7e6','974ec12f-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,1),('9750edcf-d22a-11f0-a496-e40d36ebc7e6','974ec12f-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,23.0000,NULL,NULL,1),('9752197f-d22a-11f0-a496-e40d36ebc7e6','974ec12f-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,310.0000,NULL,NULL,1),('97535d64-d22a-11f0-a496-e40d36ebc7e6','974ec12f-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,2),('9754ef85-d22a-11f0-a496-e40d36ebc7e6','974ec12f-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,17.0000,NULL,NULL,2),('97562674-d22a-11f0-a496-e40d36ebc7e6','974ec12f-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,234.0000,NULL,NULL,2),('9757992c-d22a-11f0-a496-e40d36ebc7e6','974ec12f-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,3),('9758f212-d22a-11f0-a496-e40d36ebc7e6','974ec12f-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,23.0000,NULL,NULL,3),('975a4470-d22a-11f0-a496-e40d36ebc7e6','974ec12f-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,461.0000,NULL,NULL,3),('975b7ed7-d22a-11f0-a496-e40d36ebc7e6','974ec12f-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Cloud Infrastructure Setup',NULL,NULL,NULL,4),('975ca883-d22a-11f0-a496-e40d36ebc7e6','974ec12f-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,39.0000,NULL,NULL,4),('975dc776-d22a-11f0-a496-e40d36ebc7e6','974ec12f-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,286.0000,NULL,NULL,4),('9761d3ba-d22a-11f0-a496-e40d36ebc7e6','974ec12f-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,7130.0000,NULL,NULL,1),('97632971-d22a-11f0-a496-e40d36ebc7e6','974ec12f-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,3978.0000,NULL,NULL,2),('97646332-d22a-11f0-a496-e40d36ebc7e6','974ec12f-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,10603.0000,NULL,NULL,3),('9765ceda-d22a-11f0-a496-e40d36ebc7e6','974ec12f-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,11154.0000,NULL,NULL,4),('9766bf0f-d22a-11f0-a496-e40d36ebc7e6','974ec12f-d22a-11f0-a496-e40d36ebc7e6','9252da43-d22a-11f0-a496-e40d36ebc7e6',NULL,32865.0000,NULL,NULL,0),('9767a55e-d22a-11f0-a496-e40d36ebc7e6','974ec12f-d22a-11f0-a496-e40d36ebc7e6','92540789-d22a-11f0-a496-e40d36ebc7e6',NULL,3286.5000,NULL,NULL,0),('97687fa6-d22a-11f0-a496-e40d36ebc7e6','974ec12f-d22a-11f0-a496-e40d36ebc7e6','925521d9-d22a-11f0-a496-e40d36ebc7e6',NULL,36151.5000,NULL,NULL,0),('976bd5e2-d22a-11f0-a496-e40d36ebc7e6','976a7917-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Cloud Infrastructure Setup',NULL,NULL,NULL,1),('976d4c05-d22a-11f0-a496-e40d36ebc7e6','976a7917-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,25.0000,NULL,NULL,1),('976ef8cf-d22a-11f0-a496-e40d36ebc7e6','976a7917-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,264.0000,NULL,NULL,1),('9770931e-d22a-11f0-a496-e40d36ebc7e6','976a7917-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,2),('9771d5ec-d22a-11f0-a496-e40d36ebc7e6','976a7917-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,37.0000,NULL,NULL,2),('97732ac4-d22a-11f0-a496-e40d36ebc7e6','976a7917-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,145.0000,NULL,NULL,2),('97745406-d22a-11f0-a496-e40d36ebc7e6','976a7917-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,3),('977587f6-d22a-11f0-a496-e40d36ebc7e6','976a7917-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,14.0000,NULL,NULL,3),('9776afa0-d22a-11f0-a496-e40d36ebc7e6','976a7917-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,241.0000,NULL,NULL,3),('9777cc83-d22a-11f0-a496-e40d36ebc7e6','976a7917-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,4),('9778fe10-d22a-11f0-a496-e40d36ebc7e6','976a7917-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,21.0000,NULL,NULL,4),('977a305a-d22a-11f0-a496-e40d36ebc7e6','976a7917-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,454.0000,NULL,NULL,4),('978048a2-d22a-11f0-a496-e40d36ebc7e6','976a7917-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,6600.0000,NULL,NULL,1),('9782e661-d22a-11f0-a496-e40d36ebc7e6','976a7917-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,5365.0000,NULL,NULL,2),('97857595-d22a-11f0-a496-e40d36ebc7e6','976a7917-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,3374.0000,NULL,NULL,3),('9787d471-d22a-11f0-a496-e40d36ebc7e6','976a7917-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,9534.0000,NULL,NULL,4),('978a30ea-d22a-11f0-a496-e40d36ebc7e6','976a7917-d22a-11f0-a496-e40d36ebc7e6','9252da43-d22a-11f0-a496-e40d36ebc7e6',NULL,24873.0000,NULL,NULL,0),('978c5f17-d22a-11f0-a496-e40d36ebc7e6','976a7917-d22a-11f0-a496-e40d36ebc7e6','92540789-d22a-11f0-a496-e40d36ebc7e6',NULL,2487.3000,NULL,NULL,0),('978e684a-d22a-11f0-a496-e40d36ebc7e6','976a7917-d22a-11f0-a496-e40d36ebc7e6','925521d9-d22a-11f0-a496-e40d36ebc7e6',NULL,27360.3000,NULL,NULL,0),('97931106-d22a-11f0-a496-e40d36ebc7e6','9791a50d-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,1),('97940649-d22a-11f0-a496-e40d36ebc7e6','9791a50d-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,47.0000,NULL,NULL,1),('9794e52f-d22a-11f0-a496-e40d36ebc7e6','9791a50d-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,297.0000,NULL,NULL,1),('9795cddb-d22a-11f0-a496-e40d36ebc7e6','9791a50d-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,2),('9796ca14-d22a-11f0-a496-e40d36ebc7e6','9791a50d-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,39.0000,NULL,NULL,2),('9797b051-d22a-11f0-a496-e40d36ebc7e6','9791a50d-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,432.0000,NULL,NULL,2),('9798babf-d22a-11f0-a496-e40d36ebc7e6','9791a50d-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Project Management',NULL,NULL,NULL,3),('9799a62a-d22a-11f0-a496-e40d36ebc7e6','9791a50d-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,12.0000,NULL,NULL,3),('979a9668-d22a-11f0-a496-e40d36ebc7e6','9791a50d-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,267.0000,NULL,NULL,3),('979d4f15-d22a-11f0-a496-e40d36ebc7e6','9791a50d-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,13959.0000,NULL,NULL,1),('979e8856-d22a-11f0-a496-e40d36ebc7e6','9791a50d-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,16848.0000,NULL,NULL,2),('979fa318-d22a-11f0-a496-e40d36ebc7e6','9791a50d-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,3204.0000,NULL,NULL,3),('97a0fbc9-d22a-11f0-a496-e40d36ebc7e6','9791a50d-d22a-11f0-a496-e40d36ebc7e6','9252da43-d22a-11f0-a496-e40d36ebc7e6',NULL,34011.0000,NULL,NULL,0),('97a232e2-d22a-11f0-a496-e40d36ebc7e6','9791a50d-d22a-11f0-a496-e40d36ebc7e6','92540789-d22a-11f0-a496-e40d36ebc7e6',NULL,3401.1000,NULL,NULL,0),('97a35efb-d22a-11f0-a496-e40d36ebc7e6','9791a50d-d22a-11f0-a496-e40d36ebc7e6','925521d9-d22a-11f0-a496-e40d36ebc7e6',NULL,37412.1000,NULL,NULL,0),('97a6482d-d22a-11f0-a496-e40d36ebc7e6','97a541f9-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,1),('97a723f0-d22a-11f0-a496-e40d36ebc7e6','97a541f9-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,4.0000,NULL,NULL,1),('97a7fd66-d22a-11f0-a496-e40d36ebc7e6','97a541f9-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,488.0000,NULL,NULL,1),('97a8e1f5-d22a-11f0-a496-e40d36ebc7e6','97a541f9-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,2),('97a9c1ed-d22a-11f0-a496-e40d36ebc7e6','97a541f9-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,7.0000,NULL,NULL,2),('97aac1c5-d22a-11f0-a496-e40d36ebc7e6','97a541f9-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,115.0000,NULL,NULL,2),('97aba8eb-d22a-11f0-a496-e40d36ebc7e6','97a541f9-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,3),('97acb32a-d22a-11f0-a496-e40d36ebc7e6','97a541f9-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,3.0000,NULL,NULL,3),('97adac67-d22a-11f0-a496-e40d36ebc7e6','97a541f9-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,109.0000,NULL,NULL,3),('97ae8e38-d22a-11f0-a496-e40d36ebc7e6','97a541f9-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','System Integration',NULL,NULL,NULL,4),('97af76ed-d22a-11f0-a496-e40d36ebc7e6','97a541f9-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,39.0000,NULL,NULL,4),('97b07c23-d22a-11f0-a496-e40d36ebc7e6','97a541f9-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,455.0000,NULL,NULL,4),('97b67003-d22a-11f0-a496-e40d36ebc7e6','97a541f9-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,1952.0000,NULL,NULL,1),('97b85a4e-d22a-11f0-a496-e40d36ebc7e6','97a541f9-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,805.0000,NULL,NULL,2),('97b9efda-d22a-11f0-a496-e40d36ebc7e6','97a541f9-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,327.0000,NULL,NULL,3),('97bbb1cd-d22a-11f0-a496-e40d36ebc7e6','97a541f9-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,17745.0000,NULL,NULL,4),('97bcfbed-d22a-11f0-a496-e40d36ebc7e6','97a541f9-d22a-11f0-a496-e40d36ebc7e6','9252da43-d22a-11f0-a496-e40d36ebc7e6',NULL,20829.0000,NULL,NULL,0),('97be3988-d22a-11f0-a496-e40d36ebc7e6','97a541f9-d22a-11f0-a496-e40d36ebc7e6','92540789-d22a-11f0-a496-e40d36ebc7e6',NULL,2082.9000,NULL,NULL,0),('97bf44b8-d22a-11f0-a496-e40d36ebc7e6','97a541f9-d22a-11f0-a496-e40d36ebc7e6','925521d9-d22a-11f0-a496-e40d36ebc7e6',NULL,22911.9000,NULL,NULL,0),('97c31f0a-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,1),('97c4618b-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,23.0000,NULL,NULL,1),('97c5a815-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,167.0000,NULL,NULL,1),('97c6f4b6-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Project Management',NULL,NULL,NULL,2),('97c842e6-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,6.0000,NULL,NULL,2),('97c99b25-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,220.0000,NULL,NULL,2),('97cae4d3-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,3),('97cc4124-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,9.0000,NULL,NULL,3),('97cd73bd-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,182.0000,NULL,NULL,3),('97cea77c-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,4),('97cfc6c5-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,25.0000,NULL,NULL,4),('97d0da3f-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,473.0000,NULL,NULL,4),('97d1c344-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,5),('97d2f65f-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,23.0000,NULL,NULL,5),('97d430dc-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,215.0000,NULL,NULL,5),('97d6ff88-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,3841.0000,NULL,NULL,1),('97d81b69-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,1320.0000,NULL,NULL,2),('97d964c4-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,1638.0000,NULL,NULL,3),('97da9ded-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,11825.0000,NULL,NULL,4),('97db8bad-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,4945.0000,NULL,NULL,5),('97dc82b4-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','9252da43-d22a-11f0-a496-e40d36ebc7e6',NULL,23569.0000,NULL,NULL,0),('97dd60d3-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','92540789-d22a-11f0-a496-e40d36ebc7e6',NULL,2356.9000,NULL,NULL,0),('97de6a6b-d22a-11f0-a496-e40d36ebc7e6','97c1b94d-d22a-11f0-a496-e40d36ebc7e6','925521d9-d22a-11f0-a496-e40d36ebc7e6',NULL,25925.9000,NULL,NULL,0),('97e26e21-d22a-11f0-a496-e40d36ebc7e6','97e0ea32-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,1),('97e3930b-d22a-11f0-a496-e40d36ebc7e6','97e0ea32-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,32.0000,NULL,NULL,1),('97e4f2de-d22a-11f0-a496-e40d36ebc7e6','97e0ea32-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,71.0000,NULL,NULL,1),('97e64913-d22a-11f0-a496-e40d36ebc7e6','97e0ea32-d22a-11f0-a496-e40d36ebc7e6','924cb7c9-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,2),('97e75f07-d22a-11f0-a496-e40d36ebc7e6','97e0ea32-d22a-11f0-a496-e40d36ebc7e6','924df576-d22a-11f0-a496-e40d36ebc7e6',NULL,15.0000,NULL,NULL,2),('97e8990a-d22a-11f0-a496-e40d36ebc7e6','97e0ea32-d22a-11f0-a496-e40d36ebc7e6','924f4946-d22a-11f0-a496-e40d36ebc7e6',NULL,484.0000,NULL,NULL,2),('97ec1b28-d22a-11f0-a496-e40d36ebc7e6','97e0ea32-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,2272.0000,NULL,NULL,1),('97edc9b0-d22a-11f0-a496-e40d36ebc7e6','97e0ea32-d22a-11f0-a496-e40d36ebc7e6','925087f2-d22a-11f0-a496-e40d36ebc7e6',NULL,7260.0000,NULL,NULL,2),('97f06cae-d22a-11f0-a496-e40d36ebc7e6','97e0ea32-d22a-11f0-a496-e40d36ebc7e6','9252da43-d22a-11f0-a496-e40d36ebc7e6',NULL,9532.0000,NULL,NULL,0),('97f1e686-d22a-11f0-a496-e40d36ebc7e6','97e0ea32-d22a-11f0-a496-e40d36ebc7e6','92540789-d22a-11f0-a496-e40d36ebc7e6',NULL,953.2000,NULL,NULL,0),('97f370fa-d22a-11f0-a496-e40d36ebc7e6','97e0ea32-d22a-11f0-a496-e40d36ebc7e6','925521d9-d22a-11f0-a496-e40d36ebc7e6',NULL,10485.2000,NULL,NULL,0),('97f76658-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,1),('97f90e6f-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,29.0000,NULL,NULL,1),('97fadb66-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,342.0000,NULL,NULL,1),('97fc5b1a-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,2),('97fdb9e6-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,28.0000,NULL,NULL,2),('97feedff-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,202.0000,NULL,NULL,2),('98001769-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,3),('980130aa-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,49.0000,NULL,NULL,3),('980277c1-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,81.0000,NULL,NULL,3),('98039a5a-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,4),('9804b511-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,26.0000,NULL,NULL,4),('98064692-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,485.0000,NULL,NULL,4),('98087f24-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Project Management',NULL,NULL,NULL,5),('980a5e21-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,15.0000,NULL,NULL,5),('980bac22-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,380.0000,NULL,NULL,5),('98109000-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,9918.0000,NULL,NULL,1),('9811e68c-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,5656.0000,NULL,NULL,2),('98138cfc-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,3969.0000,NULL,NULL,3),('98149b04-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,12610.0000,NULL,NULL,4),('98158a53-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,5700.0000,NULL,NULL,5),('98167120-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','9245fdc0-d22a-11f0-a496-e40d36ebc7e6',NULL,37853.0000,NULL,NULL,0),('98179327-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','9247c61e-d22a-11f0-a496-e40d36ebc7e6',NULL,3785.3000,NULL,NULL,0),('981912c5-d22a-11f0-a496-e40d36ebc7e6','97f5efaa-d22a-11f0-a496-e40d36ebc7e6','924924a2-d22a-11f0-a496-e40d36ebc7e6',NULL,41638.3000,NULL,NULL,0),('981d3e03-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','System Integration',NULL,NULL,NULL,1),('981e79a3-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,43.0000,NULL,NULL,1),('981f8cfd-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,304.0000,NULL,NULL,1),('9820ba5b-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,2),('982236de-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,13.0000,NULL,NULL,2),('98237e50-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,89.0000,NULL,NULL,2),('9824d085-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Project Management',NULL,NULL,NULL,3),('98260c52-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,25.0000,NULL,NULL,3),('9827315f-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,203.0000,NULL,NULL,3),('98285d1d-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Cloud Infrastructure Setup',NULL,NULL,NULL,4),('9829916f-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,46.0000,NULL,NULL,4),('982ac12a-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,476.0000,NULL,NULL,4),('982c2c53-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,5),('982d6ae9-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,29.0000,NULL,NULL,5),('982ee305-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,138.0000,NULL,NULL,5),('98387ec8-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,13072.0000,NULL,NULL,1),('983a5fbb-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,1157.0000,NULL,NULL,2),('983c0103-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,5075.0000,NULL,NULL,3),('983daaaf-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,21896.0000,NULL,NULL,4),('983f2817-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,4002.0000,NULL,NULL,5),('9840d92c-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','9245fdc0-d22a-11f0-a496-e40d36ebc7e6',NULL,45202.0000,NULL,NULL,0),('98423d96-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','9247c61e-d22a-11f0-a496-e40d36ebc7e6',NULL,4520.2000,NULL,NULL,0),('98438bda-d22a-11f0-a496-e40d36ebc7e6','981bc736-d22a-11f0-a496-e40d36ebc7e6','924924a2-d22a-11f0-a496-e40d36ebc7e6',NULL,49722.2000,NULL,NULL,0),('9848148f-d22a-11f0-a496-e40d36ebc7e6','9846665a-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Project Management',NULL,NULL,NULL,1),('98496c5a-d22a-11f0-a496-e40d36ebc7e6','9846665a-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,23.0000,NULL,NULL,1),('984adb00-d22a-11f0-a496-e40d36ebc7e6','9846665a-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,424.0000,NULL,NULL,1),('984c1f0a-d22a-11f0-a496-e40d36ebc7e6','9846665a-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,2),('984d5af1-d22a-11f0-a496-e40d36ebc7e6','9846665a-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,19.0000,NULL,NULL,2),('984eabf9-d22a-11f0-a496-e40d36ebc7e6','9846665a-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,154.0000,NULL,NULL,2),('9851fb2d-d22a-11f0-a496-e40d36ebc7e6','9846665a-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,9752.0000,NULL,NULL,1),('98534148-d22a-11f0-a496-e40d36ebc7e6','9846665a-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,2926.0000,NULL,NULL,2),('9854bc95-d22a-11f0-a496-e40d36ebc7e6','9846665a-d22a-11f0-a496-e40d36ebc7e6','9245fdc0-d22a-11f0-a496-e40d36ebc7e6',NULL,12678.0000,NULL,NULL,0),('98565740-d22a-11f0-a496-e40d36ebc7e6','9846665a-d22a-11f0-a496-e40d36ebc7e6','9247c61e-d22a-11f0-a496-e40d36ebc7e6',NULL,1267.8000,NULL,NULL,0),('9857f931-d22a-11f0-a496-e40d36ebc7e6','9846665a-d22a-11f0-a496-e40d36ebc7e6','924924a2-d22a-11f0-a496-e40d36ebc7e6',NULL,13945.8000,NULL,NULL,0),('985bc240-d22a-11f0-a496-e40d36ebc7e6','985a4098-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,1),('985ceeec-d22a-11f0-a496-e40d36ebc7e6','985a4098-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,32.0000,NULL,NULL,1),('985e74b0-d22a-11f0-a496-e40d36ebc7e6','985a4098-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,64.0000,NULL,NULL,1),('985f923f-d22a-11f0-a496-e40d36ebc7e6','985a4098-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,2),('9860ecc0-d22a-11f0-a496-e40d36ebc7e6','985a4098-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,40.0000,NULL,NULL,2),('98623600-d22a-11f0-a496-e40d36ebc7e6','985a4098-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,374.0000,NULL,NULL,2),('98657d76-d22a-11f0-a496-e40d36ebc7e6','985a4098-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,2048.0000,NULL,NULL,1),('98670d71-d22a-11f0-a496-e40d36ebc7e6','985a4098-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,14960.0000,NULL,NULL,2),('9868c8c2-d22a-11f0-a496-e40d36ebc7e6','985a4098-d22a-11f0-a496-e40d36ebc7e6','9245fdc0-d22a-11f0-a496-e40d36ebc7e6',NULL,17008.0000,NULL,NULL,0),('986a8004-d22a-11f0-a496-e40d36ebc7e6','985a4098-d22a-11f0-a496-e40d36ebc7e6','9247c61e-d22a-11f0-a496-e40d36ebc7e6',NULL,1700.8000,NULL,NULL,0),('986beddb-d22a-11f0-a496-e40d36ebc7e6','985a4098-d22a-11f0-a496-e40d36ebc7e6','924924a2-d22a-11f0-a496-e40d36ebc7e6',NULL,18708.8000,NULL,NULL,0),('987050bb-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,1),('98716d7e-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,33.0000,NULL,NULL,1),('9872a535-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,52.0000,NULL,NULL,1),('9873ea97-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,2),('98753cfd-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,12.0000,NULL,NULL,2),('98767a2b-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,476.0000,NULL,NULL,2),('9877ac41-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,3),('9878dd82-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,46.0000,NULL,NULL,3),('987a1972-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,327.0000,NULL,NULL,3),('987b34eb-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,4),('987c9139-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,19.0000,NULL,NULL,4),('987dcac2-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,66.0000,NULL,NULL,4),('987f2908-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,5),('98808325-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,17.0000,NULL,NULL,5),('9881c28e-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,86.0000,NULL,NULL,5),('9887d445-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,1716.0000,NULL,NULL,1),('98894d45-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,5712.0000,NULL,NULL,2),('988a8b12-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,15042.0000,NULL,NULL,3),('988be014-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,1254.0000,NULL,NULL,4),('988d33e1-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,1462.0000,NULL,NULL,5),('988e4afa-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','9245fdc0-d22a-11f0-a496-e40d36ebc7e6',NULL,25186.0000,NULL,NULL,0),('988f68dd-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','9247c61e-d22a-11f0-a496-e40d36ebc7e6',NULL,2518.6000,NULL,NULL,0),('989076f3-d22a-11f0-a496-e40d36ebc7e6','986ef85d-d22a-11f0-a496-e40d36ebc7e6','924924a2-d22a-11f0-a496-e40d36ebc7e6',NULL,27704.6000,NULL,NULL,0),('989342bd-d22a-11f0-a496-e40d36ebc7e6','98924ddc-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,1),('98941cc5-d22a-11f0-a496-e40d36ebc7e6','98924ddc-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,49.0000,NULL,NULL,1),('9894f8f6-d22a-11f0-a496-e40d36ebc7e6','98924ddc-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,251.0000,NULL,NULL,1),('9895f965-d22a-11f0-a496-e40d36ebc7e6','98924ddc-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,2),('98972ed5-d22a-11f0-a496-e40d36ebc7e6','98924ddc-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,11.0000,NULL,NULL,2),('98986876-d22a-11f0-a496-e40d36ebc7e6','98924ddc-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,231.0000,NULL,NULL,2),('989c660b-d22a-11f0-a496-e40d36ebc7e6','98924ddc-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,12299.0000,NULL,NULL,1),('989ddaa8-d22a-11f0-a496-e40d36ebc7e6','98924ddc-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,2541.0000,NULL,NULL,2),('989f5efb-d22a-11f0-a496-e40d36ebc7e6','98924ddc-d22a-11f0-a496-e40d36ebc7e6','9245fdc0-d22a-11f0-a496-e40d36ebc7e6',NULL,14840.0000,NULL,NULL,0),('98a0d751-d22a-11f0-a496-e40d36ebc7e6','98924ddc-d22a-11f0-a496-e40d36ebc7e6','9247c61e-d22a-11f0-a496-e40d36ebc7e6',NULL,1484.0000,NULL,NULL,0),('98a26a92-d22a-11f0-a496-e40d36ebc7e6','98924ddc-d22a-11f0-a496-e40d36ebc7e6','924924a2-d22a-11f0-a496-e40d36ebc7e6',NULL,16324.0000,NULL,NULL,0),('98a6dfda-d22a-11f0-a496-e40d36ebc7e6','98a52e5f-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,1),('98a8148c-d22a-11f0-a496-e40d36ebc7e6','98a52e5f-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,16.0000,NULL,NULL,1),('98a94935-d22a-11f0-a496-e40d36ebc7e6','98a52e5f-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,165.0000,NULL,NULL,1),('98aa739a-d22a-11f0-a496-e40d36ebc7e6','98a52e5f-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Project Management',NULL,NULL,NULL,2),('98abaa53-d22a-11f0-a496-e40d36ebc7e6','98a52e5f-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,39.0000,NULL,NULL,2),('98acfb58-d22a-11f0-a496-e40d36ebc7e6','98a52e5f-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,192.0000,NULL,NULL,2),('98ae4ef9-d22a-11f0-a496-e40d36ebc7e6','98a52e5f-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,3),('98af8d7b-d22a-11f0-a496-e40d36ebc7e6','98a52e5f-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,21.0000,NULL,NULL,3),('98b0c87f-d22a-11f0-a496-e40d36ebc7e6','98a52e5f-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,368.0000,NULL,NULL,3),('98b1fabf-d22a-11f0-a496-e40d36ebc7e6','98a52e5f-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,4),('98b3588c-d22a-11f0-a496-e40d36ebc7e6','98a52e5f-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,46.0000,NULL,NULL,4),('98b48d92-d22a-11f0-a496-e40d36ebc7e6','98a52e5f-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,76.0000,NULL,NULL,4),('98b92f5b-d22a-11f0-a496-e40d36ebc7e6','98a52e5f-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,2640.0000,NULL,NULL,1),('98bad5d9-d22a-11f0-a496-e40d36ebc7e6','98a52e5f-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,7488.0000,NULL,NULL,2),('98bc3fe9-d22a-11f0-a496-e40d36ebc7e6','98a52e5f-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,7728.0000,NULL,NULL,3),('98bdd4ef-d22a-11f0-a496-e40d36ebc7e6','98a52e5f-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,3496.0000,NULL,NULL,4),('98bef710-d22a-11f0-a496-e40d36ebc7e6','98a52e5f-d22a-11f0-a496-e40d36ebc7e6','9245fdc0-d22a-11f0-a496-e40d36ebc7e6',NULL,21352.0000,NULL,NULL,0),('98c055fb-d22a-11f0-a496-e40d36ebc7e6','98a52e5f-d22a-11f0-a496-e40d36ebc7e6','9247c61e-d22a-11f0-a496-e40d36ebc7e6',NULL,2135.2000,NULL,NULL,0),('98c1a252-d22a-11f0-a496-e40d36ebc7e6','98a52e5f-d22a-11f0-a496-e40d36ebc7e6','924924a2-d22a-11f0-a496-e40d36ebc7e6',NULL,23487.2000,NULL,NULL,0),('98c555ac-d22a-11f0-a496-e40d36ebc7e6','98c40289-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,1),('98c6783c-d22a-11f0-a496-e40d36ebc7e6','98c40289-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,41.0000,NULL,NULL,1),('98c7d224-d22a-11f0-a496-e40d36ebc7e6','98c40289-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,447.0000,NULL,NULL,1),('98c9010b-d22a-11f0-a496-e40d36ebc7e6','98c40289-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Project Management',NULL,NULL,NULL,2),('98ca303a-d22a-11f0-a496-e40d36ebc7e6','98c40289-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,17.0000,NULL,NULL,2),('98cb62fb-d22a-11f0-a496-e40d36ebc7e6','98c40289-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,255.0000,NULL,NULL,2),('98ccac7d-d22a-11f0-a496-e40d36ebc7e6','98c40289-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,3),('98ce271e-d22a-11f0-a496-e40d36ebc7e6','98c40289-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,20.0000,NULL,NULL,3),('98cf31d9-d22a-11f0-a496-e40d36ebc7e6','98c40289-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,133.0000,NULL,NULL,3),('98d02a61-d22a-11f0-a496-e40d36ebc7e6','98c40289-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,4),('98d15bd0-d22a-11f0-a496-e40d36ebc7e6','98c40289-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,49.0000,NULL,NULL,4),('98d28579-d22a-11f0-a496-e40d36ebc7e6','98c40289-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,304.0000,NULL,NULL,4),('98d53fec-d22a-11f0-a496-e40d36ebc7e6','98c40289-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,18327.0000,NULL,NULL,1),('98d67c5a-d22a-11f0-a496-e40d36ebc7e6','98c40289-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,4335.0000,NULL,NULL,2),('98d7bded-d22a-11f0-a496-e40d36ebc7e6','98c40289-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,2660.0000,NULL,NULL,3),('98d90529-d22a-11f0-a496-e40d36ebc7e6','98c40289-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,14896.0000,NULL,NULL,4),('98da1f12-d22a-11f0-a496-e40d36ebc7e6','98c40289-d22a-11f0-a496-e40d36ebc7e6','9245fdc0-d22a-11f0-a496-e40d36ebc7e6',NULL,40218.0000,NULL,NULL,0),('98db1b4e-d22a-11f0-a496-e40d36ebc7e6','98c40289-d22a-11f0-a496-e40d36ebc7e6','9247c61e-d22a-11f0-a496-e40d36ebc7e6',NULL,4021.8000,NULL,NULL,0),('98dc2174-d22a-11f0-a496-e40d36ebc7e6','98c40289-d22a-11f0-a496-e40d36ebc7e6','924924a2-d22a-11f0-a496-e40d36ebc7e6',NULL,44239.8000,NULL,NULL,0),('98e02d40-d22a-11f0-a496-e40d36ebc7e6','98dec825-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,1),('98e44aad-d22a-11f0-a496-e40d36ebc7e6','98dec825-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,46.0000,NULL,NULL,1),('98e98b42-d22a-11f0-a496-e40d36ebc7e6','98dec825-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,90.0000,NULL,NULL,1),('98ec089d-d22a-11f0-a496-e40d36ebc7e6','98dec825-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,2),('98ee6241-d22a-11f0-a496-e40d36ebc7e6','98dec825-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,14.0000,NULL,NULL,2),('98f0b4df-d22a-11f0-a496-e40d36ebc7e6','98dec825-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,222.0000,NULL,NULL,2),('98f32c6a-d22a-11f0-a496-e40d36ebc7e6','98dec825-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','System Integration',NULL,NULL,NULL,3),('98f48766-d22a-11f0-a496-e40d36ebc7e6','98dec825-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,32.0000,NULL,NULL,3),('98f62e53-d22a-11f0-a496-e40d36ebc7e6','98dec825-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,92.0000,NULL,NULL,3),('98fd3651-d22a-11f0-a496-e40d36ebc7e6','98dec825-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,4140.0000,NULL,NULL,1),('98ff4b7a-d22a-11f0-a496-e40d36ebc7e6','98dec825-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,3108.0000,NULL,NULL,2),('99016283-d22a-11f0-a496-e40d36ebc7e6','98dec825-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,2944.0000,NULL,NULL,3),('99037f30-d22a-11f0-a496-e40d36ebc7e6','98dec825-d22a-11f0-a496-e40d36ebc7e6','9245fdc0-d22a-11f0-a496-e40d36ebc7e6',NULL,10192.0000,NULL,NULL,0),('990535dc-d22a-11f0-a496-e40d36ebc7e6','98dec825-d22a-11f0-a496-e40d36ebc7e6','9247c61e-d22a-11f0-a496-e40d36ebc7e6',NULL,1019.2000,NULL,NULL,0),('9906bdd4-d22a-11f0-a496-e40d36ebc7e6','98dec825-d22a-11f0-a496-e40d36ebc7e6','924924a2-d22a-11f0-a496-e40d36ebc7e6',NULL,11211.2000,NULL,NULL,0),('990c57c0-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,1),('990dc1af-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,50.0000,NULL,NULL,1),('990f4eb1-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,279.0000,NULL,NULL,1),('99108c40-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,2),('99147a3d-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,21.0000,NULL,NULL,2),('9915c4fe-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,376.0000,NULL,NULL,2),('991707ef-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,3),('991855f8-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,9.0000,NULL,NULL,3),('9919ae3f-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,161.0000,NULL,NULL,3),('991ae426-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,4),('991c5e3c-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,31.0000,NULL,NULL,4),('991d9b30-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,157.0000,NULL,NULL,4),('991eca3f-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,5),('991fdf7f-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,3.0000,NULL,NULL,5),('992116a8-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,346.0000,NULL,NULL,5),('99240bcd-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,13950.0000,NULL,NULL,1),('9925439c-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,7896.0000,NULL,NULL,2),('9926b766-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,1449.0000,NULL,NULL,3),('992897df-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,4867.0000,NULL,NULL,4),('992a1df7-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,1038.0000,NULL,NULL,5),('992b7a5a-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','9245fdc0-d22a-11f0-a496-e40d36ebc7e6',NULL,29200.0000,NULL,NULL,0),('992ccdbc-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','9247c61e-d22a-11f0-a496-e40d36ebc7e6',NULL,2920.0000,NULL,NULL,0),('992dc1cf-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6','924924a2-d22a-11f0-a496-e40d36ebc7e6',NULL,32120.0000,NULL,NULL,0),('9931aca1-d22a-11f0-a496-e40d36ebc7e6','9930517d-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,1),('9932e40d-d22a-11f0-a496-e40d36ebc7e6','9930517d-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,27.0000,NULL,NULL,1),('99340b74-d22a-11f0-a496-e40d36ebc7e6','9930517d-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,485.0000,NULL,NULL,1),('99356f08-d22a-11f0-a496-e40d36ebc7e6','9930517d-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','System Integration',NULL,NULL,NULL,2),('9936aa2b-d22a-11f0-a496-e40d36ebc7e6','9930517d-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,49.0000,NULL,NULL,2),('99379ed9-d22a-11f0-a496-e40d36ebc7e6','9930517d-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,491.0000,NULL,NULL,2),('9938815b-d22a-11f0-a496-e40d36ebc7e6','9930517d-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,3),('993961d7-d22a-11f0-a496-e40d36ebc7e6','9930517d-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,8.0000,NULL,NULL,3),('993a4710-d22a-11f0-a496-e40d36ebc7e6','9930517d-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,484.0000,NULL,NULL,3),('993c6775-d22a-11f0-a496-e40d36ebc7e6','9930517d-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,13095.0000,NULL,NULL,1),('993d57f2-d22a-11f0-a496-e40d36ebc7e6','9930517d-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,24059.0000,NULL,NULL,2),('993e7b88-d22a-11f0-a496-e40d36ebc7e6','9930517d-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,3872.0000,NULL,NULL,3),('993ff8e6-d22a-11f0-a496-e40d36ebc7e6','9930517d-d22a-11f0-a496-e40d36ebc7e6','9245fdc0-d22a-11f0-a496-e40d36ebc7e6',NULL,41026.0000,NULL,NULL,0),('99412ad6-d22a-11f0-a496-e40d36ebc7e6','9930517d-d22a-11f0-a496-e40d36ebc7e6','9247c61e-d22a-11f0-a496-e40d36ebc7e6',NULL,4102.6000,NULL,NULL,0),('994244e9-d22a-11f0-a496-e40d36ebc7e6','9930517d-d22a-11f0-a496-e40d36ebc7e6','924924a2-d22a-11f0-a496-e40d36ebc7e6',NULL,45128.6000,NULL,NULL,0),('9945f0f5-d22a-11f0-a496-e40d36ebc7e6','9944a5fe-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,1),('994737f1-d22a-11f0-a496-e40d36ebc7e6','9944a5fe-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,28.0000,NULL,NULL,1),('99484c99-d22a-11f0-a496-e40d36ebc7e6','9944a5fe-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,323.0000,NULL,NULL,1),('994975c1-d22a-11f0-a496-e40d36ebc7e6','9944a5fe-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,2),('994a8bda-d22a-11f0-a496-e40d36ebc7e6','9944a5fe-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,14.0000,NULL,NULL,2),('994bb16a-d22a-11f0-a496-e40d36ebc7e6','9944a5fe-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,277.0000,NULL,NULL,2),('994cf0db-d22a-11f0-a496-e40d36ebc7e6','9944a5fe-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,3),('994eb4ff-d22a-11f0-a496-e40d36ebc7e6','9944a5fe-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,30.0000,NULL,NULL,3),('9950044d-d22a-11f0-a496-e40d36ebc7e6','9944a5fe-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,322.0000,NULL,NULL,3),('99510a03-d22a-11f0-a496-e40d36ebc7e6','9944a5fe-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,4),('99526339-d22a-11f0-a496-e40d36ebc7e6','9944a5fe-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,19.0000,NULL,NULL,4),('995444f7-d22a-11f0-a496-e40d36ebc7e6','9944a5fe-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,387.0000,NULL,NULL,4),('995ce99b-d22a-11f0-a496-e40d36ebc7e6','9944a5fe-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,9044.0000,NULL,NULL,1),('995ec829-d22a-11f0-a496-e40d36ebc7e6','9944a5fe-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,3878.0000,NULL,NULL,2),('9960713e-d22a-11f0-a496-e40d36ebc7e6','9944a5fe-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,9660.0000,NULL,NULL,3),('9962471a-d22a-11f0-a496-e40d36ebc7e6','9944a5fe-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,7353.0000,NULL,NULL,4),('9963a301-d22a-11f0-a496-e40d36ebc7e6','9944a5fe-d22a-11f0-a496-e40d36ebc7e6','9245fdc0-d22a-11f0-a496-e40d36ebc7e6',NULL,29935.0000,NULL,NULL,0),('99656322-d22a-11f0-a496-e40d36ebc7e6','9944a5fe-d22a-11f0-a496-e40d36ebc7e6','9247c61e-d22a-11f0-a496-e40d36ebc7e6',NULL,2993.5000,NULL,NULL,0),('99671f5d-d22a-11f0-a496-e40d36ebc7e6','9944a5fe-d22a-11f0-a496-e40d36ebc7e6','924924a2-d22a-11f0-a496-e40d36ebc7e6',NULL,32928.5000,NULL,NULL,0),('996b397d-d22a-11f0-a496-e40d36ebc7e6','9969e36f-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','System Integration',NULL,NULL,NULL,1),('996c74a9-d22a-11f0-a496-e40d36ebc7e6','9969e36f-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,27.0000,NULL,NULL,1),('996d9b97-d22a-11f0-a496-e40d36ebc7e6','9969e36f-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,155.0000,NULL,NULL,1),('996eaafa-d22a-11f0-a496-e40d36ebc7e6','9969e36f-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Cloud Infrastructure Setup',NULL,NULL,NULL,2),('996f88e6-d22a-11f0-a496-e40d36ebc7e6','9969e36f-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,28.0000,NULL,NULL,2),('99707694-d22a-11f0-a496-e40d36ebc7e6','9969e36f-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,168.0000,NULL,NULL,2),('99716900-d22a-11f0-a496-e40d36ebc7e6','9969e36f-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,3),('997281c1-d22a-11f0-a496-e40d36ebc7e6','9969e36f-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,31.0000,NULL,NULL,3),('9973a421-d22a-11f0-a496-e40d36ebc7e6','9969e36f-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,190.0000,NULL,NULL,3),('9976ccda-d22a-11f0-a496-e40d36ebc7e6','9969e36f-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,4185.0000,NULL,NULL,1),('997871cd-d22a-11f0-a496-e40d36ebc7e6','9969e36f-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,4704.0000,NULL,NULL,2),('9979cde6-d22a-11f0-a496-e40d36ebc7e6','9969e36f-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,5890.0000,NULL,NULL,3),('997b0eea-d22a-11f0-a496-e40d36ebc7e6','9969e36f-d22a-11f0-a496-e40d36ebc7e6','9245fdc0-d22a-11f0-a496-e40d36ebc7e6',NULL,14779.0000,NULL,NULL,0),('997c2bd7-d22a-11f0-a496-e40d36ebc7e6','9969e36f-d22a-11f0-a496-e40d36ebc7e6','9247c61e-d22a-11f0-a496-e40d36ebc7e6',NULL,1477.9000,NULL,NULL,0),('997d1354-d22a-11f0-a496-e40d36ebc7e6','9969e36f-d22a-11f0-a496-e40d36ebc7e6','924924a2-d22a-11f0-a496-e40d36ebc7e6',NULL,16256.9000,NULL,NULL,0),('997fcf54-d22a-11f0-a496-e40d36ebc7e6','997edf61-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,1),('9980a624-d22a-11f0-a496-e40d36ebc7e6','997edf61-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,28.0000,NULL,NULL,1),('9981831d-d22a-11f0-a496-e40d36ebc7e6','997edf61-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,394.0000,NULL,NULL,1),('998261b3-d22a-11f0-a496-e40d36ebc7e6','997edf61-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,2),('99834407-d22a-11f0-a496-e40d36ebc7e6','997edf61-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,39.0000,NULL,NULL,2),('998423ab-d22a-11f0-a496-e40d36ebc7e6','997edf61-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,255.0000,NULL,NULL,2),('99864add-d22a-11f0-a496-e40d36ebc7e6','997edf61-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,11032.0000,NULL,NULL,1),('998737d1-d22a-11f0-a496-e40d36ebc7e6','997edf61-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,9945.0000,NULL,NULL,2),('99886005-d22a-11f0-a496-e40d36ebc7e6','997edf61-d22a-11f0-a496-e40d36ebc7e6','9245fdc0-d22a-11f0-a496-e40d36ebc7e6',NULL,20977.0000,NULL,NULL,0),('9989956c-d22a-11f0-a496-e40d36ebc7e6','997edf61-d22a-11f0-a496-e40d36ebc7e6','9247c61e-d22a-11f0-a496-e40d36ebc7e6',NULL,2097.7000,NULL,NULL,0),('998b0066-d22a-11f0-a496-e40d36ebc7e6','997edf61-d22a-11f0-a496-e40d36ebc7e6','924924a2-d22a-11f0-a496-e40d36ebc7e6',NULL,23074.7000,NULL,NULL,0),('998df8e6-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,1),('998ee0d3-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,30.0000,NULL,NULL,1),('998fd7cd-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,235.0000,NULL,NULL,1),('9990b4bb-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,2),('9991a780-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,44.0000,NULL,NULL,2),('9992afe6-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,276.0000,NULL,NULL,2),('9993d2eb-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,3),('999503c0-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,50.0000,NULL,NULL,3),('99968137-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,260.0000,NULL,NULL,3),('9997b970-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,4),('9998f5b2-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,35.0000,NULL,NULL,4),('999a14b1-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,67.0000,NULL,NULL,4),('999b5c90-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,5),('999c9113-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,39.0000,NULL,NULL,5),('999db174-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,428.0000,NULL,NULL,5),('99a39cff-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,7050.0000,NULL,NULL,1),('99a4e432-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,12144.0000,NULL,NULL,2),('99a6b8ea-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,13000.0000,NULL,NULL,3),('99a8045f-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,2345.0000,NULL,NULL,4),('99a95c84-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,16692.0000,NULL,NULL,5),('99ab3f30-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','9245fdc0-d22a-11f0-a496-e40d36ebc7e6',NULL,51231.0000,NULL,NULL,0),('99ac6793-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','9247c61e-d22a-11f0-a496-e40d36ebc7e6',NULL,5123.1000,NULL,NULL,0),('99ad7c73-d22a-11f0-a496-e40d36ebc7e6','998cf97b-d22a-11f0-a496-e40d36ebc7e6','924924a2-d22a-11f0-a496-e40d36ebc7e6',NULL,56354.1000,NULL,NULL,0),('99b18eee-d22a-11f0-a496-e40d36ebc7e6','99b00fa1-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,1),('99b2c77b-d22a-11f0-a496-e40d36ebc7e6','99b00fa1-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,38.0000,NULL,NULL,1),('99b42bb8-d22a-11f0-a496-e40d36ebc7e6','99b00fa1-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,316.0000,NULL,NULL,1),('99b59696-d22a-11f0-a496-e40d36ebc7e6','99b00fa1-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Project Management',NULL,NULL,NULL,2),('99b74d63-d22a-11f0-a496-e40d36ebc7e6','99b00fa1-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,29.0000,NULL,NULL,2),('99b8b271-d22a-11f0-a496-e40d36ebc7e6','99b00fa1-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,104.0000,NULL,NULL,2),('99b9fd6d-d22a-11f0-a496-e40d36ebc7e6','99b00fa1-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,3),('99bb5594-d22a-11f0-a496-e40d36ebc7e6','99b00fa1-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,36.0000,NULL,NULL,3),('99bcd0da-d22a-11f0-a496-e40d36ebc7e6','99b00fa1-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,115.0000,NULL,NULL,3),('99c121ff-d22a-11f0-a496-e40d36ebc7e6','99b00fa1-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,12008.0000,NULL,NULL,1),('99c2d794-d22a-11f0-a496-e40d36ebc7e6','99b00fa1-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,3016.0000,NULL,NULL,2),('99c47f75-d22a-11f0-a496-e40d36ebc7e6','99b00fa1-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,4140.0000,NULL,NULL,3),('99c66618-d22a-11f0-a496-e40d36ebc7e6','99b00fa1-d22a-11f0-a496-e40d36ebc7e6','9245fdc0-d22a-11f0-a496-e40d36ebc7e6',NULL,19164.0000,NULL,NULL,0),('99c81adc-d22a-11f0-a496-e40d36ebc7e6','99b00fa1-d22a-11f0-a496-e40d36ebc7e6','9247c61e-d22a-11f0-a496-e40d36ebc7e6',NULL,1916.4000,NULL,NULL,0),('99c9a0a9-d22a-11f0-a496-e40d36ebc7e6','99b00fa1-d22a-11f0-a496-e40d36ebc7e6','924924a2-d22a-11f0-a496-e40d36ebc7e6',NULL,21080.4000,NULL,NULL,0),('99ccfc64-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Cloud Infrastructure Setup',NULL,NULL,NULL,1),('99ce13ad-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,14.0000,NULL,NULL,1),('99cf4f55-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,412.0000,NULL,NULL,1),('99d09115-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','System Integration',NULL,NULL,NULL,2),('99d1c8b0-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,23.0000,NULL,NULL,2),('99d302c9-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,298.0000,NULL,NULL,2),('99d4193e-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,3),('99d53675-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,38.0000,NULL,NULL,3),('99d67304-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,417.0000,NULL,NULL,3),('99d7a029-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,4),('99d8c661-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,32.0000,NULL,NULL,4),('99d9e9d9-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,347.0000,NULL,NULL,4),('99db0832-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,5),('99dc164f-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,34.0000,NULL,NULL,5),('99dd319b-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,418.0000,NULL,NULL,5),('99e305fd-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,5768.0000,NULL,NULL,1),('99e49471-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,6854.0000,NULL,NULL,2),('99e5e8c5-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,15846.0000,NULL,NULL,3),('99e71796-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,11104.0000,NULL,NULL,4),('99e869d0-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,14212.0000,NULL,NULL,5),('99e99f6a-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','9245fdc0-d22a-11f0-a496-e40d36ebc7e6',NULL,53784.0000,NULL,NULL,0),('99eaded2-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','9247c61e-d22a-11f0-a496-e40d36ebc7e6',NULL,5378.4000,NULL,NULL,0),('99ebdab2-d22a-11f0-a496-e40d36ebc7e6','99cbc6be-d22a-11f0-a496-e40d36ebc7e6','924924a2-d22a-11f0-a496-e40d36ebc7e6',NULL,59162.4000,NULL,NULL,0),('99ef6ccc-d22a-11f0-a496-e40d36ebc7e6','99ee1ace-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,1),('99f09040-d22a-11f0-a496-e40d36ebc7e6','99ee1ace-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,37.0000,NULL,NULL,1),('99f1a81d-d22a-11f0-a496-e40d36ebc7e6','99ee1ace-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,195.0000,NULL,NULL,1),('99f2cf4f-d22a-11f0-a496-e40d36ebc7e6','99ee1ace-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,2),('99f427c0-d22a-11f0-a496-e40d36ebc7e6','99ee1ace-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,17.0000,NULL,NULL,2),('99f53ec4-d22a-11f0-a496-e40d36ebc7e6','99ee1ace-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,432.0000,NULL,NULL,2),('99f67646-d22a-11f0-a496-e40d36ebc7e6','99ee1ace-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,3),('99f7b9a4-d22a-11f0-a496-e40d36ebc7e6','99ee1ace-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,22.0000,NULL,NULL,3),('99f900f6-d22a-11f0-a496-e40d36ebc7e6','99ee1ace-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,264.0000,NULL,NULL,3),('99fa28ba-d22a-11f0-a496-e40d36ebc7e6','99ee1ace-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,4),('99fb49e6-d22a-11f0-a496-e40d36ebc7e6','99ee1ace-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,8.0000,NULL,NULL,4),('99fc8242-d22a-11f0-a496-e40d36ebc7e6','99ee1ace-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,392.0000,NULL,NULL,4),('9a01aa45-d22a-11f0-a496-e40d36ebc7e6','99ee1ace-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,7215.0000,NULL,NULL,1),('9a0373fd-d22a-11f0-a496-e40d36ebc7e6','99ee1ace-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,7344.0000,NULL,NULL,2),('9a04ff22-d22a-11f0-a496-e40d36ebc7e6','99ee1ace-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,5808.0000,NULL,NULL,3),('9a06d91e-d22a-11f0-a496-e40d36ebc7e6','99ee1ace-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,3136.0000,NULL,NULL,4),('9a08c364-d22a-11f0-a496-e40d36ebc7e6','99ee1ace-d22a-11f0-a496-e40d36ebc7e6','9245fdc0-d22a-11f0-a496-e40d36ebc7e6',NULL,23503.0000,NULL,NULL,0),('9a09ebd3-d22a-11f0-a496-e40d36ebc7e6','99ee1ace-d22a-11f0-a496-e40d36ebc7e6','9247c61e-d22a-11f0-a496-e40d36ebc7e6',NULL,2350.3000,NULL,NULL,0),('9a0afeb0-d22a-11f0-a496-e40d36ebc7e6','99ee1ace-d22a-11f0-a496-e40d36ebc7e6','924924a2-d22a-11f0-a496-e40d36ebc7e6',NULL,25853.3000,NULL,NULL,0),('9a0ebbad-d22a-11f0-a496-e40d36ebc7e6','9a0d34ad-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,1),('9a1006b3-d22a-11f0-a496-e40d36ebc7e6','9a0d34ad-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,33.0000,NULL,NULL,1),('9a115cda-d22a-11f0-a496-e40d36ebc7e6','9a0d34ad-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,341.0000,NULL,NULL,1),('9a12c111-d22a-11f0-a496-e40d36ebc7e6','9a0d34ad-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,2),('9a142c82-d22a-11f0-a496-e40d36ebc7e6','9a0d34ad-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,9.0000,NULL,NULL,2),('9a15883e-d22a-11f0-a496-e40d36ebc7e6','9a0d34ad-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,249.0000,NULL,NULL,2),('9a16b604-d22a-11f0-a496-e40d36ebc7e6','9a0d34ad-d22a-11f0-a496-e40d36ebc7e6','923efe22-d22a-11f0-a496-e40d36ebc7e6','System Integration',NULL,NULL,NULL,3),('9a17e049-d22a-11f0-a496-e40d36ebc7e6','9a0d34ad-d22a-11f0-a496-e40d36ebc7e6','924049f0-d22a-11f0-a496-e40d36ebc7e6',NULL,41.0000,NULL,NULL,3),('9a190d6e-d22a-11f0-a496-e40d36ebc7e6','9a0d34ad-d22a-11f0-a496-e40d36ebc7e6','9241a6e8-d22a-11f0-a496-e40d36ebc7e6',NULL,166.0000,NULL,NULL,3),('9a1d293f-d22a-11f0-a496-e40d36ebc7e6','9a0d34ad-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,11253.0000,NULL,NULL,1),('9a1f079f-d22a-11f0-a496-e40d36ebc7e6','9a0d34ad-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,2241.0000,NULL,NULL,2),('9a2091cb-d22a-11f0-a496-e40d36ebc7e6','9a0d34ad-d22a-11f0-a496-e40d36ebc7e6','9242fef8-d22a-11f0-a496-e40d36ebc7e6',NULL,6806.0000,NULL,NULL,3),('9a2216b1-d22a-11f0-a496-e40d36ebc7e6','9a0d34ad-d22a-11f0-a496-e40d36ebc7e6','9245fdc0-d22a-11f0-a496-e40d36ebc7e6',NULL,20300.0000,NULL,NULL,0),('9a242114-d22a-11f0-a496-e40d36ebc7e6','9a0d34ad-d22a-11f0-a496-e40d36ebc7e6','9247c61e-d22a-11f0-a496-e40d36ebc7e6',NULL,2030.0000,NULL,NULL,0),('9a256795-d22a-11f0-a496-e40d36ebc7e6','9a0d34ad-d22a-11f0-a496-e40d36ebc7e6','924924a2-d22a-11f0-a496-e40d36ebc7e6',NULL,22330.0000,NULL,NULL,0),('9a2a32e0-d22a-11f0-a496-e40d36ebc7e6','9a28841e-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,1),('9a2b5500-d22a-11f0-a496-e40d36ebc7e6','9a28841e-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,8.0000,NULL,NULL,1),('9a2c5b87-d22a-11f0-a496-e40d36ebc7e6','9a28841e-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,92.0000,NULL,NULL,1),('9a2d3d52-d22a-11f0-a496-e40d36ebc7e6','9a28841e-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,2),('9a2e4112-d22a-11f0-a496-e40d36ebc7e6','9a28841e-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,39.0000,NULL,NULL,2),('9a2f4e48-d22a-11f0-a496-e40d36ebc7e6','9a28841e-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,197.0000,NULL,NULL,2),('9a305df1-d22a-11f0-a496-e40d36ebc7e6','9a28841e-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Project Management',NULL,NULL,NULL,3),('9a316f71-d22a-11f0-a496-e40d36ebc7e6','9a28841e-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,32.0000,NULL,NULL,3),('9a32860b-d22a-11f0-a496-e40d36ebc7e6','9a28841e-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,90.0000,NULL,NULL,3),('9a3524f6-d22a-11f0-a496-e40d36ebc7e6','9a28841e-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,736.0000,NULL,NULL,1),('9a364d0b-d22a-11f0-a496-e40d36ebc7e6','9a28841e-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,7683.0000,NULL,NULL,2),('9a37b94c-d22a-11f0-a496-e40d36ebc7e6','9a28841e-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,2880.0000,NULL,NULL,3),('9a39228f-d22a-11f0-a496-e40d36ebc7e6','9a28841e-d22a-11f0-a496-e40d36ebc7e6','92391898-d22a-11f0-a496-e40d36ebc7e6',NULL,11299.0000,NULL,NULL,0),('9a3a9bd9-d22a-11f0-a496-e40d36ebc7e6','9a28841e-d22a-11f0-a496-e40d36ebc7e6','923a493d-d22a-11f0-a496-e40d36ebc7e6',NULL,1129.9000,NULL,NULL,0),('9a3bc6bb-d22a-11f0-a496-e40d36ebc7e6','9a28841e-d22a-11f0-a496-e40d36ebc7e6','923b5888-d22a-11f0-a496-e40d36ebc7e6',NULL,12428.9000,NULL,NULL,0),('9a3f6dcb-d22a-11f0-a496-e40d36ebc7e6','9a3e3499-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Cloud Infrastructure Setup',NULL,NULL,NULL,1),('9a407ee7-d22a-11f0-a496-e40d36ebc7e6','9a3e3499-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,1.0000,NULL,NULL,1),('9a41964a-d22a-11f0-a496-e40d36ebc7e6','9a3e3499-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,223.0000,NULL,NULL,1),('9a42d96c-d22a-11f0-a496-e40d36ebc7e6','9a3e3499-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,2),('9a442590-d22a-11f0-a496-e40d36ebc7e6','9a3e3499-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,17.0000,NULL,NULL,2),('9a457b30-d22a-11f0-a496-e40d36ebc7e6','9a3e3499-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,328.0000,NULL,NULL,2),('9a47357c-d22a-11f0-a496-e40d36ebc7e6','9a3e3499-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Project Management',NULL,NULL,NULL,3),('9a485056-d22a-11f0-a496-e40d36ebc7e6','9a3e3499-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,23.0000,NULL,NULL,3),('9a49639b-d22a-11f0-a496-e40d36ebc7e6','9a3e3499-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,70.0000,NULL,NULL,3),('9a4e248d-d22a-11f0-a496-e40d36ebc7e6','9a3e3499-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,223.0000,NULL,NULL,1),('9a50c869-d22a-11f0-a496-e40d36ebc7e6','9a3e3499-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,5576.0000,NULL,NULL,2),('9a525e9d-d22a-11f0-a496-e40d36ebc7e6','9a3e3499-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,1610.0000,NULL,NULL,3),('9a53d9de-d22a-11f0-a496-e40d36ebc7e6','9a3e3499-d22a-11f0-a496-e40d36ebc7e6','92391898-d22a-11f0-a496-e40d36ebc7e6',NULL,7409.0000,NULL,NULL,0),('9a54ecb2-d22a-11f0-a496-e40d36ebc7e6','9a3e3499-d22a-11f0-a496-e40d36ebc7e6','923a493d-d22a-11f0-a496-e40d36ebc7e6',NULL,740.9000,NULL,NULL,0),('9a55cb93-d22a-11f0-a496-e40d36ebc7e6','9a3e3499-d22a-11f0-a496-e40d36ebc7e6','923b5888-d22a-11f0-a496-e40d36ebc7e6',NULL,8149.9000,NULL,NULL,0),('9a589f29-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,1),('9a5985ef-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,44.0000,NULL,NULL,1),('9a5a699c-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,197.0000,NULL,NULL,1),('9a5b4e99-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,2),('9a5c3802-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,35.0000,NULL,NULL,2),('9a5d472c-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,207.0000,NULL,NULL,2),('9a5e4329-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,3),('9a5f26b3-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,17.0000,NULL,NULL,3),('9a600f86-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,328.0000,NULL,NULL,3),('9a611f38-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,4),('9a626487-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,46.0000,NULL,NULL,4),('9a63a2d5-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,299.0000,NULL,NULL,4),('9a651444-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Project Management',NULL,NULL,NULL,5),('9a668083-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,11.0000,NULL,NULL,5),('9a67c1f0-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,369.0000,NULL,NULL,5),('9a702a8e-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,8668.0000,NULL,NULL,1),('9a7230e0-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,7245.0000,NULL,NULL,2),('9a744a48-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,5576.0000,NULL,NULL,3),('9a7638c5-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,13754.0000,NULL,NULL,4),('9a782928-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,4059.0000,NULL,NULL,5),('9a79dc4a-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','92391898-d22a-11f0-a496-e40d36ebc7e6',NULL,39302.0000,NULL,NULL,0),('9a7b7fdf-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','923a493d-d22a-11f0-a496-e40d36ebc7e6',NULL,3930.2000,NULL,NULL,0),('9a7ce5cf-d22a-11f0-a496-e40d36ebc7e6','9a57a8a1-d22a-11f0-a496-e40d36ebc7e6','923b5888-d22a-11f0-a496-e40d36ebc7e6',NULL,43232.2000,NULL,NULL,0),('9a81155b-d22a-11f0-a496-e40d36ebc7e6','9a7fb48f-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,1),('9a822306-d22a-11f0-a496-e40d36ebc7e6','9a7fb48f-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,41.0000,NULL,NULL,1),('9a8320a5-d22a-11f0-a496-e40d36ebc7e6','9a7fb48f-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,53.0000,NULL,NULL,1),('9a841962-d22a-11f0-a496-e40d36ebc7e6','9a7fb48f-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,2),('9a851417-d22a-11f0-a496-e40d36ebc7e6','9a7fb48f-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,40.0000,NULL,NULL,2),('9a860007-d22a-11f0-a496-e40d36ebc7e6','9a7fb48f-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,428.0000,NULL,NULL,2),('9a87f06e-d22a-11f0-a496-e40d36ebc7e6','9a7fb48f-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,2173.0000,NULL,NULL,1),('9a88d663-d22a-11f0-a496-e40d36ebc7e6','9a7fb48f-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,17120.0000,NULL,NULL,2),('9a8a0bce-d22a-11f0-a496-e40d36ebc7e6','9a7fb48f-d22a-11f0-a496-e40d36ebc7e6','92391898-d22a-11f0-a496-e40d36ebc7e6',NULL,19293.0000,NULL,NULL,0),('9a8b7f68-d22a-11f0-a496-e40d36ebc7e6','9a7fb48f-d22a-11f0-a496-e40d36ebc7e6','923a493d-d22a-11f0-a496-e40d36ebc7e6',NULL,1929.3000,NULL,NULL,0),('9a8cdef7-d22a-11f0-a496-e40d36ebc7e6','9a7fb48f-d22a-11f0-a496-e40d36ebc7e6','923b5888-d22a-11f0-a496-e40d36ebc7e6',NULL,21222.3000,NULL,NULL,0),('9a91537b-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,1),('9a928bde-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,18.0000,NULL,NULL,1),('9a93b750-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,218.0000,NULL,NULL,1),('9a94ebe0-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,2),('9a960d87-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,8.0000,NULL,NULL,2),('9a973c04-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,423.0000,NULL,NULL,2),('9a985819-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,3),('9a99665b-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,4.0000,NULL,NULL,3),('9a9a9cec-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,292.0000,NULL,NULL,3),('9a9bb22c-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,4),('9a9d0929-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,11.0000,NULL,NULL,4),('9a9e3d07-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,102.0000,NULL,NULL,4),('9a9f7bc6-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,5),('9aa09ecf-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,27.0000,NULL,NULL,5),('9aa2424b-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,362.0000,NULL,NULL,5),('9aa8bcfb-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,3924.0000,NULL,NULL,1),('9aaa86c0-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,3384.0000,NULL,NULL,2),('9aac344e-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,1168.0000,NULL,NULL,3),('9aade3a9-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,1122.0000,NULL,NULL,4),('9aaf9669-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,9774.0000,NULL,NULL,5),('9ab137da-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','92391898-d22a-11f0-a496-e40d36ebc7e6',NULL,19372.0000,NULL,NULL,0),('9ab2b9ca-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','923a493d-d22a-11f0-a496-e40d36ebc7e6',NULL,1937.2000,NULL,NULL,0),('9ab42bc2-d22a-11f0-a496-e40d36ebc7e6','9a8fb1f4-d22a-11f0-a496-e40d36ebc7e6','923b5888-d22a-11f0-a496-e40d36ebc7e6',NULL,21309.2000,NULL,NULL,0),('9ab7d066-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Project Management',NULL,NULL,NULL,1),('9ab8fe2c-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,5.0000,NULL,NULL,1),('9aba2a2b-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,443.0000,NULL,NULL,1),('9abb5601-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Cloud Infrastructure Setup',NULL,NULL,NULL,2),('9abc6a2d-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,37.0000,NULL,NULL,2),('9abd83c8-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,231.0000,NULL,NULL,2),('9abea334-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,3),('9abfd819-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,33.0000,NULL,NULL,3),('9ac0f57a-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,199.0000,NULL,NULL,3),('9ac251d2-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,4),('9ac3b199-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,13.0000,NULL,NULL,4),('9ac4e0d9-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,128.0000,NULL,NULL,4),('9ac613ce-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,5),('9ac72e89-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,35.0000,NULL,NULL,5),('9ac8580c-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,324.0000,NULL,NULL,5),('9acdaa77-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,2215.0000,NULL,NULL,1),('9acf30ff-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,8547.0000,NULL,NULL,2),('9ad0ff7d-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,6567.0000,NULL,NULL,3),('9ad2dbb6-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,1664.0000,NULL,NULL,4),('9ad441e9-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,11340.0000,NULL,NULL,5),('9ad587c9-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','92391898-d22a-11f0-a496-e40d36ebc7e6',NULL,30333.0000,NULL,NULL,0),('9ad6c481-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','923a493d-d22a-11f0-a496-e40d36ebc7e6',NULL,3033.3000,NULL,NULL,0),('9ad7f5b6-d22a-11f0-a496-e40d36ebc7e6','9ab6a0a3-d22a-11f0-a496-e40d36ebc7e6','923b5888-d22a-11f0-a496-e40d36ebc7e6',NULL,33366.3000,NULL,NULL,0),('9adbacd3-d22a-11f0-a496-e40d36ebc7e6','9ada5692-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,1),('9adcec07-d22a-11f0-a496-e40d36ebc7e6','9ada5692-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,3.0000,NULL,NULL,1),('9ade4a99-d22a-11f0-a496-e40d36ebc7e6','9ada5692-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,128.0000,NULL,NULL,1),('9ae00850-d22a-11f0-a496-e40d36ebc7e6','9ada5692-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','System Integration',NULL,NULL,NULL,2),('9ae19034-d22a-11f0-a496-e40d36ebc7e6','9ada5692-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,30.0000,NULL,NULL,2),('9ae2eeaf-d22a-11f0-a496-e40d36ebc7e6','9ada5692-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,215.0000,NULL,NULL,2),('9ae43b55-d22a-11f0-a496-e40d36ebc7e6','9ada5692-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,3),('9ae5775e-d22a-11f0-a496-e40d36ebc7e6','9ada5692-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,23.0000,NULL,NULL,3),('9ae68d0c-d22a-11f0-a496-e40d36ebc7e6','9ada5692-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,82.0000,NULL,NULL,3),('9aeaf2cc-d22a-11f0-a496-e40d36ebc7e6','9ada5692-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,384.0000,NULL,NULL,1),('9aec6a62-d22a-11f0-a496-e40d36ebc7e6','9ada5692-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,6450.0000,NULL,NULL,2),('9aedad68-d22a-11f0-a496-e40d36ebc7e6','9ada5692-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,1886.0000,NULL,NULL,3),('9aeee497-d22a-11f0-a496-e40d36ebc7e6','9ada5692-d22a-11f0-a496-e40d36ebc7e6','92391898-d22a-11f0-a496-e40d36ebc7e6',NULL,8720.0000,NULL,NULL,0),('9af02158-d22a-11f0-a496-e40d36ebc7e6','9ada5692-d22a-11f0-a496-e40d36ebc7e6','923a493d-d22a-11f0-a496-e40d36ebc7e6',NULL,872.0000,NULL,NULL,0),('9af185dd-d22a-11f0-a496-e40d36ebc7e6','9ada5692-d22a-11f0-a496-e40d36ebc7e6','923b5888-d22a-11f0-a496-e40d36ebc7e6',NULL,9592.0000,NULL,NULL,0),('9af5958d-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,1),('9af6d186-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,24.0000,NULL,NULL,1),('9af7e97f-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,74.0000,NULL,NULL,1),('9af9013e-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,2),('9afa4bd8-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,15.0000,NULL,NULL,2),('9afb73f1-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,352.0000,NULL,NULL,2),('9afc9a0f-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,3),('9afdb198-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,46.0000,NULL,NULL,3),('9afee4a2-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,465.0000,NULL,NULL,3),('9b0014ba-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,4),('9b015231-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,27.0000,NULL,NULL,4),('9b028a21-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,336.0000,NULL,NULL,4),('9b03e7f5-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,5),('9b052fa4-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,35.0000,NULL,NULL,5),('9b067a60-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,78.0000,NULL,NULL,5),('9b0a6039-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,1776.0000,NULL,NULL,1),('9b0bbba7-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,5280.0000,NULL,NULL,2),('9b0d942a-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,21390.0000,NULL,NULL,3),('9b0f3a7d-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,9072.0000,NULL,NULL,4),('9b1076be-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,2730.0000,NULL,NULL,5),('9b11a26c-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','92391898-d22a-11f0-a496-e40d36ebc7e6',NULL,40248.0000,NULL,NULL,0),('9b130282-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','923a493d-d22a-11f0-a496-e40d36ebc7e6',NULL,4024.8000,NULL,NULL,0),('9b149644-d22a-11f0-a496-e40d36ebc7e6','9af42ee3-d22a-11f0-a496-e40d36ebc7e6','923b5888-d22a-11f0-a496-e40d36ebc7e6',NULL,44272.8000,NULL,NULL,0),('9b18a771-d22a-11f0-a496-e40d36ebc7e6','9b17559c-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,1),('9b19baa1-d22a-11f0-a496-e40d36ebc7e6','9b17559c-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,41.0000,NULL,NULL,1),('9b1abefe-d22a-11f0-a496-e40d36ebc7e6','9b17559c-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,193.0000,NULL,NULL,1),('9b1c2324-d22a-11f0-a496-e40d36ebc7e6','9b17559c-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Project Management',NULL,NULL,NULL,2),('9b1d440b-d22a-11f0-a496-e40d36ebc7e6','9b17559c-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,43.0000,NULL,NULL,2),('9b1e912e-d22a-11f0-a496-e40d36ebc7e6','9b17559c-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,154.0000,NULL,NULL,2),('9b1fd122-d22a-11f0-a496-e40d36ebc7e6','9b17559c-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,3),('9b20ee41-d22a-11f0-a496-e40d36ebc7e6','9b17559c-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,5.0000,NULL,NULL,3),('9b2262e4-d22a-11f0-a496-e40d36ebc7e6','9b17559c-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,283.0000,NULL,NULL,3),('9b237475-d22a-11f0-a496-e40d36ebc7e6','9b17559c-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,4),('9b2498c0-d22a-11f0-a496-e40d36ebc7e6','9b17559c-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,43.0000,NULL,NULL,4),('9b25fdb4-d22a-11f0-a496-e40d36ebc7e6','9b17559c-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,375.0000,NULL,NULL,4),('9b298a84-d22a-11f0-a496-e40d36ebc7e6','9b17559c-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,7913.0000,NULL,NULL,1),('9b2b0fb0-d22a-11f0-a496-e40d36ebc7e6','9b17559c-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,6622.0000,NULL,NULL,2),('9b2cb012-d22a-11f0-a496-e40d36ebc7e6','9b17559c-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,1415.0000,NULL,NULL,3),('9b2e675d-d22a-11f0-a496-e40d36ebc7e6','9b17559c-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,16125.0000,NULL,NULL,4),('9b2fb9c1-d22a-11f0-a496-e40d36ebc7e6','9b17559c-d22a-11f0-a496-e40d36ebc7e6','92391898-d22a-11f0-a496-e40d36ebc7e6',NULL,32075.0000,NULL,NULL,0),('9b30f570-d22a-11f0-a496-e40d36ebc7e6','9b17559c-d22a-11f0-a496-e40d36ebc7e6','923a493d-d22a-11f0-a496-e40d36ebc7e6',NULL,3207.5000,NULL,NULL,0),('9b322dcf-d22a-11f0-a496-e40d36ebc7e6','9b17559c-d22a-11f0-a496-e40d36ebc7e6','923b5888-d22a-11f0-a496-e40d36ebc7e6',NULL,35282.5000,NULL,NULL,0),('9b363cc1-d22a-11f0-a496-e40d36ebc7e6','9b34a914-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,1),('9b3757e3-d22a-11f0-a496-e40d36ebc7e6','9b34a914-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,10.0000,NULL,NULL,1),('9b38739f-d22a-11f0-a496-e40d36ebc7e6','9b34a914-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,352.0000,NULL,NULL,1),('9b39a7e6-d22a-11f0-a496-e40d36ebc7e6','9b34a914-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,2),('9b3b08dd-d22a-11f0-a496-e40d36ebc7e6','9b34a914-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,16.0000,NULL,NULL,2),('9b3c9a2e-d22a-11f0-a496-e40d36ebc7e6','9b34a914-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,330.0000,NULL,NULL,2),('9b3de2bc-d22a-11f0-a496-e40d36ebc7e6','9b34a914-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,3),('9b3f5368-d22a-11f0-a496-e40d36ebc7e6','9b34a914-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,47.0000,NULL,NULL,3),('9b40f114-d22a-11f0-a496-e40d36ebc7e6','9b34a914-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,193.0000,NULL,NULL,3),('9b42109f-d22a-11f0-a496-e40d36ebc7e6','9b34a914-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,4),('9b439337-d22a-11f0-a496-e40d36ebc7e6','9b34a914-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,47.0000,NULL,NULL,4),('9b44dcf1-d22a-11f0-a496-e40d36ebc7e6','9b34a914-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,342.0000,NULL,NULL,4),('9b489687-d22a-11f0-a496-e40d36ebc7e6','9b34a914-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,3520.0000,NULL,NULL,1),('9b4a784d-d22a-11f0-a496-e40d36ebc7e6','9b34a914-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,5280.0000,NULL,NULL,2),('9b4c4a08-d22a-11f0-a496-e40d36ebc7e6','9b34a914-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,9071.0000,NULL,NULL,3),('9b4d8e86-d22a-11f0-a496-e40d36ebc7e6','9b34a914-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,16074.0000,NULL,NULL,4),('9b4f3db5-d22a-11f0-a496-e40d36ebc7e6','9b34a914-d22a-11f0-a496-e40d36ebc7e6','92391898-d22a-11f0-a496-e40d36ebc7e6',NULL,33945.0000,NULL,NULL,0),('9b5087cd-d22a-11f0-a496-e40d36ebc7e6','9b34a914-d22a-11f0-a496-e40d36ebc7e6','923a493d-d22a-11f0-a496-e40d36ebc7e6',NULL,3394.5000,NULL,NULL,0),('9b51e159-d22a-11f0-a496-e40d36ebc7e6','9b34a914-d22a-11f0-a496-e40d36ebc7e6','923b5888-d22a-11f0-a496-e40d36ebc7e6',NULL,37339.5000,NULL,NULL,0),('9b561c3a-d22a-11f0-a496-e40d36ebc7e6','9b54ad4a-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,1),('9b5771e7-d22a-11f0-a496-e40d36ebc7e6','9b54ad4a-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,8.0000,NULL,NULL,1),('9b58dffd-d22a-11f0-a496-e40d36ebc7e6','9b54ad4a-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,84.0000,NULL,NULL,1),('9b5a2fe6-d22a-11f0-a496-e40d36ebc7e6','9b54ad4a-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,2),('9b5b575a-d22a-11f0-a496-e40d36ebc7e6','9b54ad4a-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,27.0000,NULL,NULL,2),('9b5ca520-d22a-11f0-a496-e40d36ebc7e6','9b54ad4a-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,180.0000,NULL,NULL,2),('9b5df900-d22a-11f0-a496-e40d36ebc7e6','9b54ad4a-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,3),('9b5f54af-d22a-11f0-a496-e40d36ebc7e6','9b54ad4a-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,25.0000,NULL,NULL,3),('9b6089ed-d22a-11f0-a496-e40d36ebc7e6','9b54ad4a-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,267.0000,NULL,NULL,3),('9b625198-d22a-11f0-a496-e40d36ebc7e6','9b54ad4a-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,4),('9b637d4b-d22a-11f0-a496-e40d36ebc7e6','9b54ad4a-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,19.0000,NULL,NULL,4),('9b64c3db-d22a-11f0-a496-e40d36ebc7e6','9b54ad4a-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,64.0000,NULL,NULL,4),('9b683c0a-d22a-11f0-a496-e40d36ebc7e6','9b54ad4a-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,672.0000,NULL,NULL,1),('9b69a3c8-d22a-11f0-a496-e40d36ebc7e6','9b54ad4a-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,4860.0000,NULL,NULL,2),('9b6b17ac-d22a-11f0-a496-e40d36ebc7e6','9b54ad4a-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,6675.0000,NULL,NULL,3),('9b6cb118-d22a-11f0-a496-e40d36ebc7e6','9b54ad4a-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,1216.0000,NULL,NULL,4),('9b6e1d2d-d22a-11f0-a496-e40d36ebc7e6','9b54ad4a-d22a-11f0-a496-e40d36ebc7e6','92391898-d22a-11f0-a496-e40d36ebc7e6',NULL,13423.0000,NULL,NULL,0),('9b6f7ca4-d22a-11f0-a496-e40d36ebc7e6','9b54ad4a-d22a-11f0-a496-e40d36ebc7e6','923a493d-d22a-11f0-a496-e40d36ebc7e6',NULL,1342.3000,NULL,NULL,0),('9b70a6cd-d22a-11f0-a496-e40d36ebc7e6','9b54ad4a-d22a-11f0-a496-e40d36ebc7e6','923b5888-d22a-11f0-a496-e40d36ebc7e6',NULL,14765.3000,NULL,NULL,0),('9b739931-d22a-11f0-a496-e40d36ebc7e6','9b728e96-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,1),('9b748c7c-d22a-11f0-a496-e40d36ebc7e6','9b728e96-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,21.0000,NULL,NULL,1),('9b75f599-d22a-11f0-a496-e40d36ebc7e6','9b728e96-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,293.0000,NULL,NULL,1),('9b776128-d22a-11f0-a496-e40d36ebc7e6','9b728e96-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,2),('9b78d5cb-d22a-11f0-a496-e40d36ebc7e6','9b728e96-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,21.0000,NULL,NULL,2),('9b7a22ee-d22a-11f0-a496-e40d36ebc7e6','9b728e96-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,408.0000,NULL,NULL,2),('9b7b1c17-d22a-11f0-a496-e40d36ebc7e6','9b728e96-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,3),('9b7cc120-d22a-11f0-a496-e40d36ebc7e6','9b728e96-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,42.0000,NULL,NULL,3),('9b7dbe8b-d22a-11f0-a496-e40d36ebc7e6','9b728e96-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,235.0000,NULL,NULL,3),('9b80dc2c-d22a-11f0-a496-e40d36ebc7e6','9b728e96-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,6153.0000,NULL,NULL,1),('9b8345f3-d22a-11f0-a496-e40d36ebc7e6','9b728e96-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,8568.0000,NULL,NULL,2),('9b852f5c-d22a-11f0-a496-e40d36ebc7e6','9b728e96-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,9870.0000,NULL,NULL,3),('9b878b46-d22a-11f0-a496-e40d36ebc7e6','9b728e96-d22a-11f0-a496-e40d36ebc7e6','92391898-d22a-11f0-a496-e40d36ebc7e6',NULL,24591.0000,NULL,NULL,0),('9b89d4df-d22a-11f0-a496-e40d36ebc7e6','9b728e96-d22a-11f0-a496-e40d36ebc7e6','923a493d-d22a-11f0-a496-e40d36ebc7e6',NULL,2459.1000,NULL,NULL,0),('9b8ba7b0-d22a-11f0-a496-e40d36ebc7e6','9b728e96-d22a-11f0-a496-e40d36ebc7e6','923b5888-d22a-11f0-a496-e40d36ebc7e6',NULL,27050.1000,NULL,NULL,0),('9b919085-d22a-11f0-a496-e40d36ebc7e6','9b8f6e3d-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,1),('9b935ed8-d22a-11f0-a496-e40d36ebc7e6','9b8f6e3d-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,39.0000,NULL,NULL,1),('9b94f36b-d22a-11f0-a496-e40d36ebc7e6','9b8f6e3d-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,94.0000,NULL,NULL,1),('9b9614e7-d22a-11f0-a496-e40d36ebc7e6','9b8f6e3d-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,2),('9b970908-d22a-11f0-a496-e40d36ebc7e6','9b8f6e3d-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,40.0000,NULL,NULL,2),('9b981387-d22a-11f0-a496-e40d36ebc7e6','9b8f6e3d-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,212.0000,NULL,NULL,2),('9b991057-d22a-11f0-a496-e40d36ebc7e6','9b8f6e3d-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Cloud Infrastructure Setup',NULL,NULL,NULL,3),('9b9a8e28-d22a-11f0-a496-e40d36ebc7e6','9b8f6e3d-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,34.0000,NULL,NULL,3),('9b9b7eb0-d22a-11f0-a496-e40d36ebc7e6','9b8f6e3d-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,169.0000,NULL,NULL,3),('9b9e02d3-d22a-11f0-a496-e40d36ebc7e6','9b8f6e3d-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,3666.0000,NULL,NULL,1),('9b9f26b8-d22a-11f0-a496-e40d36ebc7e6','9b8f6e3d-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,8480.0000,NULL,NULL,2),('9ba05e70-d22a-11f0-a496-e40d36ebc7e6','9b8f6e3d-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,5746.0000,NULL,NULL,3),('9ba24fa0-d22a-11f0-a496-e40d36ebc7e6','9b8f6e3d-d22a-11f0-a496-e40d36ebc7e6','92391898-d22a-11f0-a496-e40d36ebc7e6',NULL,17892.0000,NULL,NULL,0),('9ba45db8-d22a-11f0-a496-e40d36ebc7e6','9b8f6e3d-d22a-11f0-a496-e40d36ebc7e6','923a493d-d22a-11f0-a496-e40d36ebc7e6',NULL,1789.2000,NULL,NULL,0),('9ba6b6a2-d22a-11f0-a496-e40d36ebc7e6','9b8f6e3d-d22a-11f0-a496-e40d36ebc7e6','923b5888-d22a-11f0-a496-e40d36ebc7e6',NULL,19681.2000,NULL,NULL,0),('9bad1ec1-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,1),('9bae8153-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,31.0000,NULL,NULL,1),('9baf7aef-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,250.0000,NULL,NULL,1),('9bb0a90f-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,2),('9bb2098e-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,48.0000,NULL,NULL,2),('9bb359da-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,397.0000,NULL,NULL,2),('9bb4fb66-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,3),('9bb68689-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,4.0000,NULL,NULL,3),('9bb86322-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,424.0000,NULL,NULL,3),('9bb9b1a8-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,4),('9bbb1457-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,34.0000,NULL,NULL,4),('9bbc07d7-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,487.0000,NULL,NULL,4),('9bbd0a0f-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,5),('9bbe0c19-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,33.0000,NULL,NULL,5),('9bbf1c8e-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,281.0000,NULL,NULL,5),('9bc3b6aa-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,7750.0000,NULL,NULL,1),('9bc53901-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,19056.0000,NULL,NULL,2),('9bc6b095-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,1696.0000,NULL,NULL,3),('9bc81498-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,16558.0000,NULL,NULL,4),('9bc933c3-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,9273.0000,NULL,NULL,5),('9bcab235-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','92391898-d22a-11f0-a496-e40d36ebc7e6',NULL,54333.0000,NULL,NULL,0),('9bcbd7b5-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','923a493d-d22a-11f0-a496-e40d36ebc7e6',NULL,5433.3000,NULL,NULL,0),('9bccfdb3-d22a-11f0-a496-e40d36ebc7e6','9baade12-d22a-11f0-a496-e40d36ebc7e6','923b5888-d22a-11f0-a496-e40d36ebc7e6',NULL,59766.3000,NULL,NULL,0),('9bd05c1d-d22a-11f0-a496-e40d36ebc7e6','9bcf2e9b-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','System Integration',NULL,NULL,NULL,1),('9bd15cb3-d22a-11f0-a496-e40d36ebc7e6','9bcf2e9b-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,42.0000,NULL,NULL,1),('9bd2449e-d22a-11f0-a496-e40d36ebc7e6','9bcf2e9b-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,500.0000,NULL,NULL,1),('9bd3309d-d22a-11f0-a496-e40d36ebc7e6','9bcf2e9b-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,2),('9bd43150-d22a-11f0-a496-e40d36ebc7e6','9bcf2e9b-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,34.0000,NULL,NULL,2),('9bd5206e-d22a-11f0-a496-e40d36ebc7e6','9bcf2e9b-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,246.0000,NULL,NULL,2),('9bd61cb9-d22a-11f0-a496-e40d36ebc7e6','9bcf2e9b-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,3),('9bd70a73-d22a-11f0-a496-e40d36ebc7e6','9bcf2e9b-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,2.0000,NULL,NULL,3),('9bd7fe4a-d22a-11f0-a496-e40d36ebc7e6','9bcf2e9b-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,62.0000,NULL,NULL,3),('9bdabba9-d22a-11f0-a496-e40d36ebc7e6','9bcf2e9b-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,21000.0000,NULL,NULL,1),('9bdd2047-d22a-11f0-a496-e40d36ebc7e6','9bcf2e9b-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,8364.0000,NULL,NULL,2),('9bdebdfe-d22a-11f0-a496-e40d36ebc7e6','9bcf2e9b-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,124.0000,NULL,NULL,3),('9be03827-d22a-11f0-a496-e40d36ebc7e6','9bcf2e9b-d22a-11f0-a496-e40d36ebc7e6','92391898-d22a-11f0-a496-e40d36ebc7e6',NULL,29488.0000,NULL,NULL,0),('9be17e0d-d22a-11f0-a496-e40d36ebc7e6','9bcf2e9b-d22a-11f0-a496-e40d36ebc7e6','923a493d-d22a-11f0-a496-e40d36ebc7e6',NULL,2948.8000,NULL,NULL,0),('9be2b434-d22a-11f0-a496-e40d36ebc7e6','9bcf2e9b-d22a-11f0-a496-e40d36ebc7e6','923b5888-d22a-11f0-a496-e40d36ebc7e6',NULL,32436.8000,NULL,NULL,0),('9be5f27f-d22a-11f0-a496-e40d36ebc7e6','9be4cd76-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,1),('9be6d54a-d22a-11f0-a496-e40d36ebc7e6','9be4cd76-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,34.0000,NULL,NULL,1),('9be7c351-d22a-11f0-a496-e40d36ebc7e6','9be4cd76-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,454.0000,NULL,NULL,1),('9be8a826-d22a-11f0-a496-e40d36ebc7e6','9be4cd76-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','System Integration',NULL,NULL,NULL,2),('9be9a03d-d22a-11f0-a496-e40d36ebc7e6','9be4cd76-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,2.0000,NULL,NULL,2),('9bea9059-d22a-11f0-a496-e40d36ebc7e6','9be4cd76-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,306.0000,NULL,NULL,2),('9becdb05-d22a-11f0-a496-e40d36ebc7e6','9be4cd76-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,15436.0000,NULL,NULL,1),('9bedf9a2-d22a-11f0-a496-e40d36ebc7e6','9be4cd76-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,612.0000,NULL,NULL,2),('9bef4cd8-d22a-11f0-a496-e40d36ebc7e6','9be4cd76-d22a-11f0-a496-e40d36ebc7e6','92391898-d22a-11f0-a496-e40d36ebc7e6',NULL,16048.0000,NULL,NULL,0),('9bf0b301-d22a-11f0-a496-e40d36ebc7e6','9be4cd76-d22a-11f0-a496-e40d36ebc7e6','923a493d-d22a-11f0-a496-e40d36ebc7e6',NULL,1604.8000,NULL,NULL,0),('9bf1a672-d22a-11f0-a496-e40d36ebc7e6','9be4cd76-d22a-11f0-a496-e40d36ebc7e6','923b5888-d22a-11f0-a496-e40d36ebc7e6',NULL,17652.8000,NULL,NULL,0),('9bf56291-d22a-11f0-a496-e40d36ebc7e6','9bf4215e-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Project Management',NULL,NULL,NULL,1),('9bf63e81-d22a-11f0-a496-e40d36ebc7e6','9bf4215e-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,10.0000,NULL,NULL,1),('9bf768e4-d22a-11f0-a496-e40d36ebc7e6','9bf4215e-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,201.0000,NULL,NULL,1),('9bf89aca-d22a-11f0-a496-e40d36ebc7e6','9bf4215e-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Project Management',NULL,NULL,NULL,2),('9bf9af30-d22a-11f0-a496-e40d36ebc7e6','9bf4215e-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,41.0000,NULL,NULL,2),('9bfb0d80-d22a-11f0-a496-e40d36ebc7e6','9bf4215e-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,294.0000,NULL,NULL,2),('9bfe140f-d22a-11f0-a496-e40d36ebc7e6','9bf4215e-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,2010.0000,NULL,NULL,1),('9bfeff77-d22a-11f0-a496-e40d36ebc7e6','9bf4215e-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,12054.0000,NULL,NULL,2),('9c004883-d22a-11f0-a496-e40d36ebc7e6','9bf4215e-d22a-11f0-a496-e40d36ebc7e6','92391898-d22a-11f0-a496-e40d36ebc7e6',NULL,14064.0000,NULL,NULL,0),('9c01ccaf-d22a-11f0-a496-e40d36ebc7e6','9bf4215e-d22a-11f0-a496-e40d36ebc7e6','923a493d-d22a-11f0-a496-e40d36ebc7e6',NULL,1406.4000,NULL,NULL,0),('9c0309b4-d22a-11f0-a496-e40d36ebc7e6','9bf4215e-d22a-11f0-a496-e40d36ebc7e6','923b5888-d22a-11f0-a496-e40d36ebc7e6',NULL,15470.4000,NULL,NULL,0),('9c068a3f-d22a-11f0-a496-e40d36ebc7e6','9c056456-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,1),('9c0780d5-d22a-11f0-a496-e40d36ebc7e6','9c056456-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,10.0000,NULL,NULL,1),('9c086ecd-d22a-11f0-a496-e40d36ebc7e6','9c056456-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,179.0000,NULL,NULL,1),('9c095a6d-d22a-11f0-a496-e40d36ebc7e6','9c056456-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,2),('9c0a4025-d22a-11f0-a496-e40d36ebc7e6','9c056456-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,36.0000,NULL,NULL,2),('9c0b5367-d22a-11f0-a496-e40d36ebc7e6','9c056456-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,171.0000,NULL,NULL,2),('9c0c9f3c-d22a-11f0-a496-e40d36ebc7e6','9c056456-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,3),('9c0dc749-d22a-11f0-a496-e40d36ebc7e6','9c056456-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,5.0000,NULL,NULL,3),('9c0ef544-d22a-11f0-a496-e40d36ebc7e6','9c056456-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,122.0000,NULL,NULL,3),('9c0ff85a-d22a-11f0-a496-e40d36ebc7e6','9c056456-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,4),('9c110b66-d22a-11f0-a496-e40d36ebc7e6','9c056456-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,19.0000,NULL,NULL,4),('9c11f985-d22a-11f0-a496-e40d36ebc7e6','9c056456-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,196.0000,NULL,NULL,4),('9c15c777-d22a-11f0-a496-e40d36ebc7e6','9c056456-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,1790.0000,NULL,NULL,1),('9c171e32-d22a-11f0-a496-e40d36ebc7e6','9c056456-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,6156.0000,NULL,NULL,2),('9c187cc4-d22a-11f0-a496-e40d36ebc7e6','9c056456-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,610.0000,NULL,NULL,3),('9c19d814-d22a-11f0-a496-e40d36ebc7e6','9c056456-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,3724.0000,NULL,NULL,4),('9c1b4dca-d22a-11f0-a496-e40d36ebc7e6','9c056456-d22a-11f0-a496-e40d36ebc7e6','92391898-d22a-11f0-a496-e40d36ebc7e6',NULL,12280.0000,NULL,NULL,0),('9c1cb325-d22a-11f0-a496-e40d36ebc7e6','9c056456-d22a-11f0-a496-e40d36ebc7e6','923a493d-d22a-11f0-a496-e40d36ebc7e6',NULL,1228.0000,NULL,NULL,0),('9c1e19bb-d22a-11f0-a496-e40d36ebc7e6','9c056456-d22a-11f0-a496-e40d36ebc7e6','923b5888-d22a-11f0-a496-e40d36ebc7e6',NULL,13508.0000,NULL,NULL,0),('9c224819-d22a-11f0-a496-e40d36ebc7e6','9c20a22b-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,1),('9c234cfd-d22a-11f0-a496-e40d36ebc7e6','9c20a22b-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,34.0000,NULL,NULL,1),('9c247cf6-d22a-11f0-a496-e40d36ebc7e6','9c20a22b-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,245.0000,NULL,NULL,1),('9c2593be-d22a-11f0-a496-e40d36ebc7e6','9c20a22b-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,2),('9c26aa28-d22a-11f0-a496-e40d36ebc7e6','9c20a22b-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,16.0000,NULL,NULL,2),('9c27e4e1-d22a-11f0-a496-e40d36ebc7e6','9c20a22b-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,424.0000,NULL,NULL,2),('9c291147-d22a-11f0-a496-e40d36ebc7e6','9c20a22b-d22a-11f0-a496-e40d36ebc7e6','9232db67-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,3),('9c2a2328-d22a-11f0-a496-e40d36ebc7e6','9c20a22b-d22a-11f0-a496-e40d36ebc7e6','92340fd4-d22a-11f0-a496-e40d36ebc7e6',NULL,19.0000,NULL,NULL,3),('9c2b82cd-d22a-11f0-a496-e40d36ebc7e6','9c20a22b-d22a-11f0-a496-e40d36ebc7e6','9235621e-d22a-11f0-a496-e40d36ebc7e6',NULL,275.0000,NULL,NULL,3),('9c2f8444-d22a-11f0-a496-e40d36ebc7e6','9c20a22b-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,8330.0000,NULL,NULL,1),('9c30eaab-d22a-11f0-a496-e40d36ebc7e6','9c20a22b-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,6784.0000,NULL,NULL,2),('9c323129-d22a-11f0-a496-e40d36ebc7e6','9c20a22b-d22a-11f0-a496-e40d36ebc7e6','9236a14a-d22a-11f0-a496-e40d36ebc7e6',NULL,5225.0000,NULL,NULL,3),('9c335018-d22a-11f0-a496-e40d36ebc7e6','9c20a22b-d22a-11f0-a496-e40d36ebc7e6','92391898-d22a-11f0-a496-e40d36ebc7e6',NULL,20339.0000,NULL,NULL,0),('9c34b37e-d22a-11f0-a496-e40d36ebc7e6','9c20a22b-d22a-11f0-a496-e40d36ebc7e6','923a493d-d22a-11f0-a496-e40d36ebc7e6',NULL,2033.9000,NULL,NULL,0),('9c35d052-d22a-11f0-a496-e40d36ebc7e6','9c20a22b-d22a-11f0-a496-e40d36ebc7e6','923b5888-d22a-11f0-a496-e40d36ebc7e6',NULL,22372.9000,NULL,NULL,0),('9c3b3e00-d22a-11f0-a496-e40d36ebc7e6','9c397c0b-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,1),('9c3c5025-d22a-11f0-a496-e40d36ebc7e6','9c397c0b-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,1.0000,NULL,NULL,1),('9c3d753a-d22a-11f0-a496-e40d36ebc7e6','9c397c0b-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,170.0000,NULL,NULL,1),('9c3e682c-d22a-11f0-a496-e40d36ebc7e6','9c397c0b-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,2),('9c3f6094-d22a-11f0-a496-e40d36ebc7e6','9c397c0b-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,13.0000,NULL,NULL,2),('9c4062de-d22a-11f0-a496-e40d36ebc7e6','9c397c0b-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,61.0000,NULL,NULL,2),('9c42f325-d22a-11f0-a496-e40d36ebc7e6','9c397c0b-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,170.0000,NULL,NULL,1),('9c441fc7-d22a-11f0-a496-e40d36ebc7e6','9c397c0b-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,793.0000,NULL,NULL,2),('9c4578f7-d22a-11f0-a496-e40d36ebc7e6','9c397c0b-d22a-11f0-a496-e40d36ebc7e6','8cb71e68-d22a-11f0-a496-e40d36ebc7e6',NULL,963.0000,NULL,NULL,0),('9c46dac4-d22a-11f0-a496-e40d36ebc7e6','9c397c0b-d22a-11f0-a496-e40d36ebc7e6','8cb83313-d22a-11f0-a496-e40d36ebc7e6',NULL,96.3000,NULL,NULL,0),('9c47ffb4-d22a-11f0-a496-e40d36ebc7e6','9c397c0b-d22a-11f0-a496-e40d36ebc7e6','8cb9d88c-d22a-11f0-a496-e40d36ebc7e6',NULL,1059.3000,NULL,NULL,0),('9c4b4640-d22a-11f0-a496-e40d36ebc7e6','9c4a0ae5-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,1),('9c4c4696-d22a-11f0-a496-e40d36ebc7e6','9c4a0ae5-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,20.0000,NULL,NULL,1),('9c4d39ed-d22a-11f0-a496-e40d36ebc7e6','9c4a0ae5-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,441.0000,NULL,NULL,1),('9c4e2f3c-d22a-11f0-a496-e40d36ebc7e6','9c4a0ae5-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','System Integration',NULL,NULL,NULL,2),('9c4f4516-d22a-11f0-a496-e40d36ebc7e6','9c4a0ae5-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,49.0000,NULL,NULL,2),('9c503232-d22a-11f0-a496-e40d36ebc7e6','9c4a0ae5-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,271.0000,NULL,NULL,2),('9c51154a-d22a-11f0-a496-e40d36ebc7e6','9c4a0ae5-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,3),('9c5200d1-d22a-11f0-a496-e40d36ebc7e6','9c4a0ae5-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,30.0000,NULL,NULL,3),('9c52fc1b-d22a-11f0-a496-e40d36ebc7e6','9c4a0ae5-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,313.0000,NULL,NULL,3),('9c55cda3-d22a-11f0-a496-e40d36ebc7e6','9c4a0ae5-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,8820.0000,NULL,NULL,1),('9c56c501-d22a-11f0-a496-e40d36ebc7e6','9c4a0ae5-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,13279.0000,NULL,NULL,2),('9c57e4e3-d22a-11f0-a496-e40d36ebc7e6','9c4a0ae5-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,9390.0000,NULL,NULL,3),('9c58ebe1-d22a-11f0-a496-e40d36ebc7e6','9c4a0ae5-d22a-11f0-a496-e40d36ebc7e6','8cb71e68-d22a-11f0-a496-e40d36ebc7e6',NULL,31489.0000,NULL,NULL,0),('9c5a3cb3-d22a-11f0-a496-e40d36ebc7e6','9c4a0ae5-d22a-11f0-a496-e40d36ebc7e6','8cb83313-d22a-11f0-a496-e40d36ebc7e6',NULL,3148.9000,NULL,NULL,0),('9c5b73fa-d22a-11f0-a496-e40d36ebc7e6','9c4a0ae5-d22a-11f0-a496-e40d36ebc7e6','8cb9d88c-d22a-11f0-a496-e40d36ebc7e6',NULL,34637.9000,NULL,NULL,0),('9c5f266f-d22a-11f0-a496-e40d36ebc7e6','9c5db651-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,1),('9c6011a1-d22a-11f0-a496-e40d36ebc7e6','9c5db651-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,18.0000,NULL,NULL,1),('9c61352f-d22a-11f0-a496-e40d36ebc7e6','9c5db651-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,342.0000,NULL,NULL,1),('9c6224b1-d22a-11f0-a496-e40d36ebc7e6','9c5db651-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,2),('9c631833-d22a-11f0-a496-e40d36ebc7e6','9c5db651-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,9.0000,NULL,NULL,2),('9c645886-d22a-11f0-a496-e40d36ebc7e6','9c5db651-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,466.0000,NULL,NULL,2),('9c667cfe-d22a-11f0-a496-e40d36ebc7e6','9c5db651-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,6156.0000,NULL,NULL,1),('9c676c28-d22a-11f0-a496-e40d36ebc7e6','9c5db651-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,4194.0000,NULL,NULL,2),('9c6c3936-d22a-11f0-a496-e40d36ebc7e6','9c5db651-d22a-11f0-a496-e40d36ebc7e6','8cb71e68-d22a-11f0-a496-e40d36ebc7e6',NULL,10350.0000,NULL,NULL,0),('9c6d2dbf-d22a-11f0-a496-e40d36ebc7e6','9c5db651-d22a-11f0-a496-e40d36ebc7e6','8cb83313-d22a-11f0-a496-e40d36ebc7e6',NULL,1035.0000,NULL,NULL,0),('9c6e1dac-d22a-11f0-a496-e40d36ebc7e6','9c5db651-d22a-11f0-a496-e40d36ebc7e6','8cb9d88c-d22a-11f0-a496-e40d36ebc7e6',NULL,11385.0000,NULL,NULL,0),('9c7121d4-d22a-11f0-a496-e40d36ebc7e6','9c700523-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,1),('9c721cf8-d22a-11f0-a496-e40d36ebc7e6','9c700523-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,33.0000,NULL,NULL,1),('9c73166a-d22a-11f0-a496-e40d36ebc7e6','9c700523-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,213.0000,NULL,NULL,1),('9c743859-d22a-11f0-a496-e40d36ebc7e6','9c700523-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,2),('9c754f84-d22a-11f0-a496-e40d36ebc7e6','9c700523-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,47.0000,NULL,NULL,2),('9c7630cc-d22a-11f0-a496-e40d36ebc7e6','9c700523-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,345.0000,NULL,NULL,2),('9c7712fb-d22a-11f0-a496-e40d36ebc7e6','9c700523-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,3),('9c77fb48-d22a-11f0-a496-e40d36ebc7e6','9c700523-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,17.0000,NULL,NULL,3),('9c78f65a-d22a-11f0-a496-e40d36ebc7e6','9c700523-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,175.0000,NULL,NULL,3),('9c79df2f-d22a-11f0-a496-e40d36ebc7e6','9c700523-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,4),('9c7aca1e-d22a-11f0-a496-e40d36ebc7e6','9c700523-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,40.0000,NULL,NULL,4),('9c7bb5ee-d22a-11f0-a496-e40d36ebc7e6','9c700523-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,280.0000,NULL,NULL,4),('9c7e9548-d22a-11f0-a496-e40d36ebc7e6','9c700523-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,7029.0000,NULL,NULL,1),('9c7fb1be-d22a-11f0-a496-e40d36ebc7e6','9c700523-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,16215.0000,NULL,NULL,2),('9c80adf5-d22a-11f0-a496-e40d36ebc7e6','9c700523-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,2975.0000,NULL,NULL,3),('9c81c194-d22a-11f0-a496-e40d36ebc7e6','9c700523-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,11200.0000,NULL,NULL,4),('9c82ed05-d22a-11f0-a496-e40d36ebc7e6','9c700523-d22a-11f0-a496-e40d36ebc7e6','8cb71e68-d22a-11f0-a496-e40d36ebc7e6',NULL,37419.0000,NULL,NULL,0),('9c840ad0-d22a-11f0-a496-e40d36ebc7e6','9c700523-d22a-11f0-a496-e40d36ebc7e6','8cb83313-d22a-11f0-a496-e40d36ebc7e6',NULL,3741.9000,NULL,NULL,0),('9c84eb9d-d22a-11f0-a496-e40d36ebc7e6','9c700523-d22a-11f0-a496-e40d36ebc7e6','8cb9d88c-d22a-11f0-a496-e40d36ebc7e6',NULL,41160.9000,NULL,NULL,0),('9c87e3cf-d22a-11f0-a496-e40d36ebc7e6','9c86dee1-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,1),('9c88c15f-d22a-11f0-a496-e40d36ebc7e6','9c86dee1-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,40.0000,NULL,NULL,1),('9c899ac1-d22a-11f0-a496-e40d36ebc7e6','9c86dee1-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,470.0000,NULL,NULL,1),('9c8a7b89-d22a-11f0-a496-e40d36ebc7e6','9c86dee1-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,2),('9c8b5b34-d22a-11f0-a496-e40d36ebc7e6','9c86dee1-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,45.0000,NULL,NULL,2),('9c8c3597-d22a-11f0-a496-e40d36ebc7e6','9c86dee1-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,160.0000,NULL,NULL,2),('9c8e82af-d22a-11f0-a496-e40d36ebc7e6','9c86dee1-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,18800.0000,NULL,NULL,1),('9c8fa7ea-d22a-11f0-a496-e40d36ebc7e6','9c86dee1-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,7200.0000,NULL,NULL,2),('9c913c10-d22a-11f0-a496-e40d36ebc7e6','9c86dee1-d22a-11f0-a496-e40d36ebc7e6','8cb71e68-d22a-11f0-a496-e40d36ebc7e6',NULL,26000.0000,NULL,NULL,0),('9c9294cb-d22a-11f0-a496-e40d36ebc7e6','9c86dee1-d22a-11f0-a496-e40d36ebc7e6','8cb83313-d22a-11f0-a496-e40d36ebc7e6',NULL,2600.0000,NULL,NULL,0),('9c93cf22-d22a-11f0-a496-e40d36ebc7e6','9c86dee1-d22a-11f0-a496-e40d36ebc7e6','8cb9d88c-d22a-11f0-a496-e40d36ebc7e6',NULL,28600.0000,NULL,NULL,0),('9c96c25b-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Cloud Infrastructure Setup',NULL,NULL,NULL,1),('9c97b2a9-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,7.0000,NULL,NULL,1),('9c98c61b-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,301.0000,NULL,NULL,1),('9c99b8f7-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,2),('9c9ac835-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,48.0000,NULL,NULL,2),('9c9bc865-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,251.0000,NULL,NULL,2),('9ca26608-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,3),('9ca3472b-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,21.0000,NULL,NULL,3),('9ca4332c-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,320.0000,NULL,NULL,3),('9ca57155-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Security Audit',NULL,NULL,NULL,4),('9ca6ba6f-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,14.0000,NULL,NULL,4),('9ca7bebd-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,333.0000,NULL,NULL,4),('9ca8c102-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,5),('9ca9b344-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,8.0000,NULL,NULL,5),('9caac144-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,415.0000,NULL,NULL,5),('9caedddb-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,2107.0000,NULL,NULL,1),('9cb0586c-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,12048.0000,NULL,NULL,2),('9cb1c6d8-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,6720.0000,NULL,NULL,3),('9cb328a7-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,4662.0000,NULL,NULL,4),('9cb47c1f-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,3320.0000,NULL,NULL,5),('9cb5bd3e-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb71e68-d22a-11f0-a496-e40d36ebc7e6',NULL,28857.0000,NULL,NULL,0),('9cb6c357-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb83313-d22a-11f0-a496-e40d36ebc7e6',NULL,2885.7000,NULL,NULL,0),('9cb7a020-d22a-11f0-a496-e40d36ebc7e6','9c95ac06-d22a-11f0-a496-e40d36ebc7e6','8cb9d88c-d22a-11f0-a496-e40d36ebc7e6',NULL,31742.7000,NULL,NULL,0),('9cbb0387-d22a-11f0-a496-e40d36ebc7e6','9cb9c755-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,1),('9cbbf67b-d22a-11f0-a496-e40d36ebc7e6','9cb9c755-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,30.0000,NULL,NULL,1),('9cbce490-d22a-11f0-a496-e40d36ebc7e6','9cb9c755-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,496.0000,NULL,NULL,1),('9cbdeabe-d22a-11f0-a496-e40d36ebc7e6','9cb9c755-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,2),('9cbee09e-d22a-11f0-a496-e40d36ebc7e6','9cb9c755-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,8.0000,NULL,NULL,2),('9cbfc49e-d22a-11f0-a496-e40d36ebc7e6','9cb9c755-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,239.0000,NULL,NULL,2),('9cc0bbc0-d22a-11f0-a496-e40d36ebc7e6','9cb9c755-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','System Integration',NULL,NULL,NULL,3),('9cc1a82d-d22a-11f0-a496-e40d36ebc7e6','9cb9c755-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,41.0000,NULL,NULL,3),('9cc2a618-d22a-11f0-a496-e40d36ebc7e6','9cb9c755-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,221.0000,NULL,NULL,3),('9cc38558-d22a-11f0-a496-e40d36ebc7e6','9cb9c755-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,4),('9cc4963d-d22a-11f0-a496-e40d36ebc7e6','9cb9c755-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,48.0000,NULL,NULL,4),('9cc57613-d22a-11f0-a496-e40d36ebc7e6','9cb9c755-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,236.0000,NULL,NULL,4),('9cc7f61d-d22a-11f0-a496-e40d36ebc7e6','9cb9c755-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,14880.0000,NULL,NULL,1),('9cc93cf7-d22a-11f0-a496-e40d36ebc7e6','9cb9c755-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,1912.0000,NULL,NULL,2),('9cca8236-d22a-11f0-a496-e40d36ebc7e6','9cb9c755-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,9061.0000,NULL,NULL,3),('9ccba211-d22a-11f0-a496-e40d36ebc7e6','9cb9c755-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,11328.0000,NULL,NULL,4),('9ccccfde-d22a-11f0-a496-e40d36ebc7e6','9cb9c755-d22a-11f0-a496-e40d36ebc7e6','8cb71e68-d22a-11f0-a496-e40d36ebc7e6',NULL,37181.0000,NULL,NULL,0),('9ccdb9c7-d22a-11f0-a496-e40d36ebc7e6','9cb9c755-d22a-11f0-a496-e40d36ebc7e6','8cb83313-d22a-11f0-a496-e40d36ebc7e6',NULL,3718.1000,NULL,NULL,0),('9ccead53-d22a-11f0-a496-e40d36ebc7e6','9cb9c755-d22a-11f0-a496-e40d36ebc7e6','8cb9d88c-d22a-11f0-a496-e40d36ebc7e6',NULL,40899.1000,NULL,NULL,0),('9cd245a8-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Project Management',NULL,NULL,NULL,1),('9cd36d51-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,22.0000,NULL,NULL,1),('9cd47db8-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,72.0000,NULL,NULL,1),('9cd56d02-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,2),('9cd68782-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,20.0000,NULL,NULL,2),('9cd78241-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,58.0000,NULL,NULL,2),('9cd88a66-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','System Integration',NULL,NULL,NULL,3),('9cd9cf42-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,16.0000,NULL,NULL,3),('9cdace49-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,157.0000,NULL,NULL,3),('9cdbbd2a-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,4),('9cdca2c2-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,32.0000,NULL,NULL,4),('9cdd8b8c-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,144.0000,NULL,NULL,4),('9cde7e93-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,5),('9cdf6fa8-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,43.0000,NULL,NULL,5),('9ce06177-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,473.0000,NULL,NULL,5),('9ce3c317-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,1584.0000,NULL,NULL,1),('9ce567d3-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,1160.0000,NULL,NULL,2),('9ce6dd09-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,2512.0000,NULL,NULL,3),('9ce81b30-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,4608.0000,NULL,NULL,4),('9ce964d6-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,20339.0000,NULL,NULL,5),('9cea7ba7-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb71e68-d22a-11f0-a496-e40d36ebc7e6',NULL,30203.0000,NULL,NULL,0),('9ceb66f7-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb83313-d22a-11f0-a496-e40d36ebc7e6',NULL,3020.3000,NULL,NULL,0),('9cec5e0b-d22a-11f0-a496-e40d36ebc7e6','9cd1176a-d22a-11f0-a496-e40d36ebc7e6','8cb9d88c-d22a-11f0-a496-e40d36ebc7e6',NULL,33223.3000,NULL,NULL,0),('9cefaeb0-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,1),('9cf0ab76-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,30.0000,NULL,NULL,1),('9cf1d1af-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,189.0000,NULL,NULL,1),('9cf2c82c-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','System Integration',NULL,NULL,NULL,2),('9cf3b09d-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,29.0000,NULL,NULL,2),('9cf4a3f6-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,385.0000,NULL,NULL,2),('9cf5ee3d-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,3),('9cf6e18c-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,8.0000,NULL,NULL,3),('9cf7d70a-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,154.0000,NULL,NULL,3),('9cf8f432-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,4),('9cfa381b-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,30.0000,NULL,NULL,4),('9cfb708b-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,90.0000,NULL,NULL,4),('9cfced6f-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,5),('9cfe38e0-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,17.0000,NULL,NULL,5),('9cff7688-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,187.0000,NULL,NULL,5),('9d05a560-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,5670.0000,NULL,NULL,1),('9d07496f-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,11165.0000,NULL,NULL,2),('9d08bc18-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,1232.0000,NULL,NULL,3),('9d0a00d9-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,2700.0000,NULL,NULL,4),('9d0b7da7-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,3179.0000,NULL,NULL,5),('9d0ce447-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb71e68-d22a-11f0-a496-e40d36ebc7e6',NULL,23946.0000,NULL,NULL,0),('9d0e92a9-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb83313-d22a-11f0-a496-e40d36ebc7e6',NULL,2394.6000,NULL,NULL,0),('9d0fb52e-d22a-11f0-a496-e40d36ebc7e6','9cee9cbb-d22a-11f0-a496-e40d36ebc7e6','8cb9d88c-d22a-11f0-a496-e40d36ebc7e6',NULL,26340.6000,NULL,NULL,0),('9d1358b9-d22a-11f0-a496-e40d36ebc7e6','9d11fd67-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Project Management',NULL,NULL,NULL,1),('9d144cf7-d22a-11f0-a496-e40d36ebc7e6','9d11fd67-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,13.0000,NULL,NULL,1),('9d155027-d22a-11f0-a496-e40d36ebc7e6','9d11fd67-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,307.0000,NULL,NULL,1),('9d1637c5-d22a-11f0-a496-e40d36ebc7e6','9d11fd67-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,2),('9d1723a1-d22a-11f0-a496-e40d36ebc7e6','9d11fd67-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,5.0000,NULL,NULL,2),('9d184dac-d22a-11f0-a496-e40d36ebc7e6','9d11fd67-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,242.0000,NULL,NULL,2),('9d1a9ca4-d22a-11f0-a496-e40d36ebc7e6','9d11fd67-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,3991.0000,NULL,NULL,1),('9d1bda22-d22a-11f0-a496-e40d36ebc7e6','9d11fd67-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,1210.0000,NULL,NULL,2),('9d1d3ac1-d22a-11f0-a496-e40d36ebc7e6','9d11fd67-d22a-11f0-a496-e40d36ebc7e6','8cb71e68-d22a-11f0-a496-e40d36ebc7e6',NULL,5201.0000,NULL,NULL,0),('9d1eb002-d22a-11f0-a496-e40d36ebc7e6','9d11fd67-d22a-11f0-a496-e40d36ebc7e6','8cb83313-d22a-11f0-a496-e40d36ebc7e6',NULL,520.1000,NULL,NULL,0),('9d1fc3ce-d22a-11f0-a496-e40d36ebc7e6','9d11fd67-d22a-11f0-a496-e40d36ebc7e6','8cb9d88c-d22a-11f0-a496-e40d36ebc7e6',NULL,5721.1000,NULL,NULL,0),('9d230ccb-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Consulting Hours',NULL,NULL,NULL,1),('9d23ebf6-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,23.0000,NULL,NULL,1),('9d24e847-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,62.0000,NULL,NULL,1),('9d25cd7f-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Cloud Infrastructure Setup',NULL,NULL,NULL,2),('9d26bb2f-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,32.0000,NULL,NULL,2),('9d27a53b-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,166.0000,NULL,NULL,2),('9d28898e-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,3),('9d2973ec-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,3.0000,NULL,NULL,3),('9d2a5ea9-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,109.0000,NULL,NULL,3),('9d2b3d1b-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,4),('9d2c1c45-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,12.0000,NULL,NULL,4),('9d2d3a91-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,50.0000,NULL,NULL,4),('9d2e1e3e-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,5),('9d2efa79-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,32.0000,NULL,NULL,5),('9d2fd40b-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,217.0000,NULL,NULL,5),('9d340b9e-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,1426.0000,NULL,NULL,1),('9d355ba6-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,5312.0000,NULL,NULL,2),('9d36d021-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,327.0000,NULL,NULL,3),('9d3862fc-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,600.0000,NULL,NULL,4),('9d3a0347-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,6944.0000,NULL,NULL,5),('9d3b31aa-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb71e68-d22a-11f0-a496-e40d36ebc7e6',NULL,14609.0000,NULL,NULL,0),('9d3c3881-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb83313-d22a-11f0-a496-e40d36ebc7e6',NULL,1460.9000,NULL,NULL,0),('9d3d25ee-d22a-11f0-a496-e40d36ebc7e6','9d21fe5d-d22a-11f0-a496-e40d36ebc7e6','8cb9d88c-d22a-11f0-a496-e40d36ebc7e6',NULL,16069.9000,NULL,NULL,0),('9d402c4d-d22a-11f0-a496-e40d36ebc7e6','9d3f19ca-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,1),('9d411a80-d22a-11f0-a496-e40d36ebc7e6','9d3f19ca-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,45.0000,NULL,NULL,1),('9d421317-d22a-11f0-a496-e40d36ebc7e6','9d3f19ca-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,231.0000,NULL,NULL,1),('9d4313b7-d22a-11f0-a496-e40d36ebc7e6','9d3f19ca-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Training Sessions',NULL,NULL,NULL,2),('9d441b79-d22a-11f0-a496-e40d36ebc7e6','9d3f19ca-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,50.0000,NULL,NULL,2),('9d453ab5-d22a-11f0-a496-e40d36ebc7e6','9d3f19ca-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,352.0000,NULL,NULL,2),('9d46997b-d22a-11f0-a496-e40d36ebc7e6','9d3f19ca-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Technical Support',NULL,NULL,NULL,3),('9d47dc07-d22a-11f0-a496-e40d36ebc7e6','9d3f19ca-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,28.0000,NULL,NULL,3),('9d48cd43-d22a-11f0-a496-e40d36ebc7e6','9d3f19ca-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,257.0000,NULL,NULL,3),('9d4b6e69-d22a-11f0-a496-e40d36ebc7e6','9d3f19ca-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,10395.0000,NULL,NULL,1),('9d4ca00e-d22a-11f0-a496-e40d36ebc7e6','9d3f19ca-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,17600.0000,NULL,NULL,2),('9d4dd6c3-d22a-11f0-a496-e40d36ebc7e6','9d3f19ca-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,7196.0000,NULL,NULL,3),('9d4f102a-d22a-11f0-a496-e40d36ebc7e6','9d3f19ca-d22a-11f0-a496-e40d36ebc7e6','8cb71e68-d22a-11f0-a496-e40d36ebc7e6',NULL,35191.0000,NULL,NULL,0),('9d50236d-d22a-11f0-a496-e40d36ebc7e6','9d3f19ca-d22a-11f0-a496-e40d36ebc7e6','8cb83313-d22a-11f0-a496-e40d36ebc7e6',NULL,3519.1000,NULL,NULL,0),('9d513939-d22a-11f0-a496-e40d36ebc7e6','9d3f19ca-d22a-11f0-a496-e40d36ebc7e6','8cb9d88c-d22a-11f0-a496-e40d36ebc7e6',NULL,38710.1000,NULL,NULL,0),('9d546394-d22a-11f0-a496-e40d36ebc7e6','9d5331e1-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,1),('9d557567-d22a-11f0-a496-e40d36ebc7e6','9d5331e1-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,1.0000,NULL,NULL,1),('9d56964b-d22a-11f0-a496-e40d36ebc7e6','9d5331e1-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,67.0000,NULL,NULL,1),('9d57c350-d22a-11f0-a496-e40d36ebc7e6','9d5331e1-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Cloud Infrastructure Setup',NULL,NULL,NULL,2),('9d58e1cc-d22a-11f0-a496-e40d36ebc7e6','9d5331e1-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,11.0000,NULL,NULL,2),('9d59d0cc-d22a-11f0-a496-e40d36ebc7e6','9d5331e1-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,363.0000,NULL,NULL,2),('9d5c7575-d22a-11f0-a496-e40d36ebc7e6','9d5331e1-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,67.0000,NULL,NULL,1),('9d5d6f71-d22a-11f0-a496-e40d36ebc7e6','9d5331e1-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,3993.0000,NULL,NULL,2),('9d5e9c8f-d22a-11f0-a496-e40d36ebc7e6','9d5331e1-d22a-11f0-a496-e40d36ebc7e6','8cb71e68-d22a-11f0-a496-e40d36ebc7e6',NULL,4060.0000,NULL,NULL,0),('9d5fd50d-d22a-11f0-a496-e40d36ebc7e6','9d5331e1-d22a-11f0-a496-e40d36ebc7e6','8cb83313-d22a-11f0-a496-e40d36ebc7e6',NULL,406.0000,NULL,NULL,0),('9d60fae1-d22a-11f0-a496-e40d36ebc7e6','9d5331e1-d22a-11f0-a496-e40d36ebc7e6','8cb9d88c-d22a-11f0-a496-e40d36ebc7e6',NULL,4466.0000,NULL,NULL,0),('9d64aed5-d22a-11f0-a496-e40d36ebc7e6','9d634062-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Data Analysis',NULL,NULL,NULL,1),('9d65f24f-d22a-11f0-a496-e40d36ebc7e6','9d634062-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,17.0000,NULL,NULL,1),('9d66fcfd-d22a-11f0-a496-e40d36ebc7e6','9d634062-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,75.0000,NULL,NULL,1),('9d6852cb-d22a-11f0-a496-e40d36ebc7e6','9d634062-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,2),('9d697410-d22a-11f0-a496-e40d36ebc7e6','9d634062-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,27.0000,NULL,NULL,2),('9d6a5ef3-d22a-11f0-a496-e40d36ebc7e6','9d634062-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,82.0000,NULL,NULL,2),('9d6b54b1-d22a-11f0-a496-e40d36ebc7e6','9d634062-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Maintenance & Support',NULL,NULL,NULL,3),('9d6c5741-d22a-11f0-a496-e40d36ebc7e6','9d634062-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,12.0000,NULL,NULL,3),('9d6d47a7-d22a-11f0-a496-e40d36ebc7e6','9d634062-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,317.0000,NULL,NULL,3),('9d7027d5-d22a-11f0-a496-e40d36ebc7e6','9d634062-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,1275.0000,NULL,NULL,1),('9d714a9a-d22a-11f0-a496-e40d36ebc7e6','9d634062-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,2214.0000,NULL,NULL,2),('9d723408-d22a-11f0-a496-e40d36ebc7e6','9d634062-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,3804.0000,NULL,NULL,3),('9d7345d5-d22a-11f0-a496-e40d36ebc7e6','9d634062-d22a-11f0-a496-e40d36ebc7e6','8cb71e68-d22a-11f0-a496-e40d36ebc7e6',NULL,7293.0000,NULL,NULL,0),('9d74797e-d22a-11f0-a496-e40d36ebc7e6','9d634062-d22a-11f0-a496-e40d36ebc7e6','8cb83313-d22a-11f0-a496-e40d36ebc7e6',NULL,729.3000,NULL,NULL,0),('9d757af3-d22a-11f0-a496-e40d36ebc7e6','9d634062-d22a-11f0-a496-e40d36ebc7e6','8cb9d88c-d22a-11f0-a496-e40d36ebc7e6',NULL,8022.3000,NULL,NULL,0),('9d7882c8-d22a-11f0-a496-e40d36ebc7e6','9d77771b-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','Software Development Services',NULL,NULL,NULL,1),('9d797349-d22a-11f0-a496-e40d36ebc7e6','9d77771b-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,16.0000,NULL,NULL,1),('9d7a5ca0-d22a-11f0-a496-e40d36ebc7e6','9d77771b-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,282.0000,NULL,NULL,1),('9d7b4c7c-d22a-11f0-a496-e40d36ebc7e6','9d77771b-d22a-11f0-a496-e40d36ebc7e6','8cb1e086-d22a-11f0-a496-e40d36ebc7e6','System Integration',NULL,NULL,NULL,2),('9d7c4033-d22a-11f0-a496-e40d36ebc7e6','9d77771b-d22a-11f0-a496-e40d36ebc7e6','8cb2d50d-d22a-11f0-a496-e40d36ebc7e6',NULL,18.0000,NULL,NULL,2),('9d7d4b47-d22a-11f0-a496-e40d36ebc7e6','9d77771b-d22a-11f0-a496-e40d36ebc7e6','8cb413d4-d22a-11f0-a496-e40d36ebc7e6',NULL,452.0000,NULL,NULL,2),('9d80c4a5-d22a-11f0-a496-e40d36ebc7e6','9d77771b-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,4512.0000,NULL,NULL,1),('9d82b043-d22a-11f0-a496-e40d36ebc7e6','9d77771b-d22a-11f0-a496-e40d36ebc7e6','8cb513be-d22a-11f0-a496-e40d36ebc7e6',NULL,8136.0000,NULL,NULL,2),('9d845654-d22a-11f0-a496-e40d36ebc7e6','9d77771b-d22a-11f0-a496-e40d36ebc7e6','8cb71e68-d22a-11f0-a496-e40d36ebc7e6',NULL,12648.0000,NULL,NULL,0),('9d860e43-d22a-11f0-a496-e40d36ebc7e6','9d77771b-d22a-11f0-a496-e40d36ebc7e6','8cb83313-d22a-11f0-a496-e40d36ebc7e6',NULL,1264.8000,NULL,NULL,0),('9d87aafc-d22a-11f0-a496-e40d36ebc7e6','9d77771b-d22a-11f0-a496-e40d36ebc7e6','8cb9d88c-d22a-11f0-a496-e40d36ebc7e6',NULL,13912.8000,NULL,NULL,0);
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
INSERT INTO `organization` VALUES ('496afc2a-d22a-11f0-a496-e40d36ebc7e6','techflow.com','TechFlow USA','1247 Innovation Drive','San Francisco','CA','94105','USA','2025-12-05 22:32:31'),('496bd83e-d22a-11f0-a496-e40d36ebc7e6','techflow.com','TechFlow UK','42 Canary Wharf','London',NULL,'E14 5AB','United Kingdom','2025-12-05 22:32:31'),('496cc74f-d22a-11f0-a496-e40d36ebc7e6','nexus.com','Nexus India','Block A, Cyber Towers','Bangalore','Karnataka','560001','India','2025-12-05 22:32:31'),('496dc4fc-d22a-11f0-a496-e40d36ebc7e6','nexus.com','Nexus Australia','Level 15, 100 Collins Street','Melbourne','VIC','3000','Australia','2025-12-05 22:32:31');
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
INSERT INTO `payment` VALUES ('093a1411-d22b-11f0-a496-e40d36ebc7e6','9846665a-d22a-11f0-a496-e40d36ebc7e6',13945.8000,'Credit card','TXN-18123234','2025-12-05 22:37:52'),('168b5ab7-d22b-11f0-a496-e40d36ebc7e6','95fad294-d22a-11f0-a496-e40d36ebc7e6',43905.4000,'','','2025-12-05 22:38:15'),('f820bed5-d22a-11f0-a496-e40d36ebc7e6','990a94b2-d22a-11f0-a496-e40d36ebc7e6',32120.0000,'Bank Transfer','TXN-18294729281','2025-12-05 22:37:24');
/*!40000 ALTER TABLE `payment` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_payment_insert` AFTER INSERT ON `payment` FOR EACH ROW BEGIN
    INSERT INTO audit_log (
    audit_id,
        table_name,
        record_id,
        action_type,
        field_name,
        new_value,
        additional_info
    ) VALUES (
    UUID(),
        'payment',
        NEW.payment_id,
        'INSERT',
        'amount',
        NEW.amount,
        CONCAT('Invoice: ', NEW.invoice_id,
               ' | Method: ', IFNULL(NEW.method, 'N/A'),
               ' | Reference: ', IFNULL(NEW.reference_number, 'N/A'))
    );
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

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
INSERT INTO `section` VALUES ('8cb0c21b-d22a-11f0-a496-e40d36ebc7e6','8caf7295-d22a-11f0-a496-e40d36ebc7e6',1,'items','Items',NULL,1,'line_item'),('8cb61851-d22a-11f0-a496-e40d36ebc7e6','8caf7295-d22a-11f0-a496-e40d36ebc7e6',1,'total','Total',NULL,2,'normal'),('9231b8c6-d22a-11f0-a496-e40d36ebc7e6','9230756d-d22a-11f0-a496-e40d36ebc7e6',1,'items','Items',NULL,1,'line_item'),('9237e737-d22a-11f0-a496-e40d36ebc7e6','9230756d-d22a-11f0-a496-e40d36ebc7e6',1,'total','Total',NULL,2,'normal'),('923de288-d22a-11f0-a496-e40d36ebc7e6','923cbfa3-d22a-11f0-a496-e40d36ebc7e6',1,'items','Items',NULL,1,'line_item'),('924455a4-d22a-11f0-a496-e40d36ebc7e6','923cbfa3-d22a-11f0-a496-e40d36ebc7e6',1,'total','Total',NULL,2,'normal'),('924b99bc-d22a-11f0-a496-e40d36ebc7e6','924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'items','Items',NULL,1,'line_item'),('9251ba98-d22a-11f0-a496-e40d36ebc7e6','924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'total','Total',NULL,2,'normal');
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
INSERT INTO `template` VALUES ('8caf7295-d22a-11f0-a496-e40d36ebc7e6',1,'496afc2a-d22a-11f0-a496-e40d36ebc7e6','Standard Invoice','USD','8cb9d88c-d22a-11f0-a496-e40d36ebc7e6','2025-12-05 22:34:23',0),('9230756d-d22a-11f0-a496-e40d36ebc7e6',1,'496bd83e-d22a-11f0-a496-e40d36ebc7e6','Standard Invoice','USD',NULL,'2025-12-05 22:34:33',0),('923cbfa3-d22a-11f0-a496-e40d36ebc7e6',1,'496cc74f-d22a-11f0-a496-e40d36ebc7e6','Standard Invoice','USD',NULL,'2025-12-05 22:34:33',0),('924aa1f0-d22a-11f0-a496-e40d36ebc7e6',1,'496dc4fc-d22a-11f0-a496-e40d36ebc7e6','Standard Invoice','USD',NULL,'2025-12-05 22:34:33',0);
/*!40000 ALTER TABLE `template` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_template_archive_update` AFTER UPDATE ON `template` FOR EACH ROW BEGIN
    IF OLD.is_archived != NEW.is_archived THEN
        INSERT INTO audit_log (
        audit_id,
            table_name,
            record_id,
            action_type,
            field_name,
            old_value,
            new_value,
            additional_info
        ) VALUES (
        UUID(),
            'template',
            CONCAT(NEW.template_id, ':', NEW.version),
            'UPDATE',
            'is_archived',
            OLD.is_archived,
            NEW.is_archived,
            CONCAT('Template: ', NEW.name, ' v', NEW.version, ' | Org: ', (SELECT name FROM organization WHERE org_id = NEW.org_id))
        );
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `user_organization`
--

DROP TABLE IF EXISTS `user_organization`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_organization` (
  `user_id` char(36) NOT NULL,
  `org_id` char(36) NOT NULL,
  `role` enum('owner','member','viewer') NOT NULL DEFAULT 'viewer',
  `status` enum('active','pending','rejected','deactivated') NOT NULL DEFAULT 'pending',
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
INSERT INTO `user_organization` VALUES ('485281a8-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','owner','active','2025-12-05 22:32:31'),('485281a8-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','owner','active','2025-12-05 22:32:31'),('48874172-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','member','active','2025-12-05 22:32:31'),('48874172-d22a-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','member','active','2025-12-05 22:32:31'),('48beb660-d22a-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','viewer','active','2025-12-05 22:32:31'),('48faf595-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','owner','active','2025-12-05 22:32:31'),('48faf595-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','owner','active','2025-12-05 22:32:31'),('4933da06-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','member','active','2025-12-05 22:32:31'),('4933da06-d22a-11f0-a496-e40d36ebc7e6','496dc4fc-d22a-11f0-a496-e40d36ebc7e6','member','active','2025-12-05 22:32:31'),('4969caf6-d22a-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','viewer','active','2025-12-05 22:32:31'),('4d3769b6-d22f-11f0-a496-e40d36ebc7e6','496afc2a-d22a-11f0-a496-e40d36ebc7e6','member','pending','2025-12-05 23:08:24'),('91ce946d-d22f-11f0-a496-e40d36ebc7e6','496bd83e-d22a-11f0-a496-e40d36ebc7e6','member','pending','2025-12-05 23:10:20'),('fcbb22c5-d22e-11f0-a496-e40d36ebc7e6','496cc74f-d22a-11f0-a496-e40d36ebc7e6','member','pending','2025-12-05 23:06:09');
/*!40000 ALTER TABLE `user_organization` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_user_organization_prevent_last_owner` BEFORE UPDATE ON `user_organization` FOR EACH ROW BEGIN
    DECLARE owner_count INT;
    
    -- Check if we're changing an owner's role to something else
    IF OLD.role = 'owner' AND NEW.role != 'owner' THEN
        -- Count remaining owners in this organization (excluding the current user being updated)
        SELECT COUNT(*) INTO owner_count
        FROM user_organization
        WHERE org_id = NEW.org_id
          AND user_id != NEW.user_id
          AND role = 'owner'
          AND status = 'active';
        
        -- If this is the last owner, prevent the change
        IF owner_count = 0 THEN
            SIGNAL SQLSTATE '45000' 
            SET MESSAGE_TEXT = 'Cannot change role: Organization must have at least one active owner';
        END IF;
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_user_organization_role_update` AFTER UPDATE ON `user_organization` FOR EACH ROW BEGIN
    IF OLD.role != NEW.role THEN
        INSERT INTO audit_log (
			audit_id,
            table_name,
            record_id,
            action_type,
            field_name,
            old_value,
            new_value,
            additional_info
        ) VALUES (
			UUID(),
            'user_organization',
            CONCAT(NEW.user_id, ':', NEW.org_id),
            'UPDATE',
            'role',
            OLD.role,
            NEW.role,
            CONCAT('User: ', (SELECT email FROM users WHERE user_id = NEW.user_id), 
                   ' | Org: ', (SELECT name FROM organization WHERE org_id = NEW.org_id))
        );
    END IF;
    
    IF OLD.status != NEW.status THEN
        INSERT INTO audit_log (
        audit_id,
            table_name,
            record_id,
            action_type,
            field_name,
            old_value,
            new_value,
            additional_info
        ) VALUES (
        UUID(),
            'user_organization',
            CONCAT(NEW.user_id, ':', NEW.org_id),
            'UPDATE',
            'status',
            OLD.status,
            NEW.status,
            CONCAT('User: ', (SELECT email FROM users WHERE user_id = NEW.user_id), 
                   ' | Org: ', (SELECT name FROM organization WHERE org_id = NEW.org_id))
        );
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_user_organization_prevent_delete_last_owner` BEFORE DELETE ON `user_organization` FOR EACH ROW BEGIN
    DECLARE owner_count INT;
    
    -- Check if we're deleting an owner
    IF OLD.role = 'owner' AND OLD.status = 'active' THEN
        -- Count remaining owners in this organization
        SELECT COUNT(*) INTO owner_count
        FROM user_organization
        WHERE org_id = OLD.org_id
          AND role = 'owner'
          AND status = 'active';
        
        -- If this is the last owner, prevent deletion
        IF owner_count <= 1 THEN
            SIGNAL SQLSTATE '45000' 
            SET MESSAGE_TEXT = 'Cannot delete: Organization must have at least one active owner';
        END IF;
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

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
INSERT INTO `users` VALUES ('485281a8-d22a-11f0-a496-e40d36ebc7e6','michael.chen@techflow.com','$2b$12$nNOaNBV.gAATjLKcjigJ9u0zi.A1gkLEa0xVGr1i0887gyWThEhZe','2025-12-05 22:32:29'),('48874172-d22a-11f0-a496-e40d36ebc7e6','sarah.martinez@techflow.com','$2b$12$juHbGVfJ8eyHqUCH4ExRsOBGcY1hiFo1/AnW8EZsmZjN2qv2Z3IAC','2025-12-05 22:32:29'),('48beb660-d22a-11f0-a496-e40d36ebc7e6','david.kim@techflow.com','$2b$12$ceuROAnFSPEnbyNMawP3xuxWphfMY./F.E4XqZzngzspvU6aruVH2','2025-12-05 22:32:29'),('48faf595-d22a-11f0-a496-e40d36ebc7e6','emily.rodriguez@nexus.com','$2b$12$6nqCalyrNBlUkeFTwQ2xiu4Ln2NfqUtoIUhUA9kyLVECinbNZzZa2','2025-12-05 22:32:30'),('4933da06-d22a-11f0-a496-e40d36ebc7e6','james.anderson@nexus.com','$2b$12$2aVAQiVvCsVyFp2eTqfRw.VPzNzXSJ2RDF7jQuqXS8782UExSqSF6','2025-12-05 22:32:30'),('4969caf6-d22a-11f0-a496-e40d36ebc7e6','priya.sharma@nexus.com','$2b$12$ZVy3xxu1K6vI3aPDOmfIO.OMw22XORV3/Lgf8S1I/Q/Cr8x7pEuG2','2025-12-05 22:32:31'),('4d3769b6-d22f-11f0-a496-e40d36ebc7e6','nick.collins@techflow.com','$2b$12$OKeb/3Mvcf18NzaVReifeucHf8g8BE4DC/sdCeV59Hk5t6ZXm0m82','2025-12-05 23:08:24'),('91ce946d-d22f-11f0-a496-e40d36ebc7e6','victor.gonzalez@techflow.com','$2b$12$3gKNgl3SziyaErNtrjFGt.zx9OYv3y/79L3yVTKDZiSyaR7GPZmeu','2025-12-05 23:10:20'),('fcbb22c5-d22e-11f0-a496-e40d36ebc7e6','dheeraj.gupta@nexus.com','$2b$12$SZuwZKuC3xv3YSS3lc56Iuj1C.YJWyGraD2JMKCAqUoYZ3nBZ67vy','2025-12-05 23:06:09');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

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
    IN p_role VARCHAR(50),
    IN p_status VARCHAR(50)
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
    
    INSERT INTO user_organization (user_id, org_id, role,status)
    VALUES (p_user_id, p_org_id, IFNULL(p_role, 'member'),p_status)
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
/*!50003 DROP PROCEDURE IF EXISTS `sp_delete_invoice_values_by_fields` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_delete_invoice_values_by_fields`(
    IN p_invoice_id CHAR(36),
    IN p_field_ids TEXT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    SET @sql = CONCAT('DELETE FROM invoice_value WHERE invoice_id = ''', p_invoice_id, ''' AND field_id IN (', p_field_ids, ')');
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
    
    SELECT ROW_COUNT() AS rows_deleted;
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
/*!50003 DROP PROCEDURE IF EXISTS `sp_get_audit_log` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_audit_log`(
    IN p_org_id CHAR(36),
    IN p_table_name VARCHAR(100),
    IN p_limit INT,
    IN p_offset INT
)
BEGIN
    DECLARE v_limit INT DEFAULT 100;
    DECLARE v_offset INT DEFAULT 0;
    
    SET v_limit = IFNULL(p_limit, 100);
    SET v_offset = IFNULL(p_offset, 0);
    
    SELECT 
        al.audit_id,
        al.table_name,
        al.record_id,
        al.action_type,
        al.field_name,
        al.old_value,
        al.new_value,
        al.changed_by,
        al.changed_at,
        al.additional_info
    FROM audit_log al
    WHERE (p_table_name IS NULL OR al.table_name = p_table_name)
      AND (
          -- Filter by organization context for relevant tables
          (al.table_name = 'user_organization' AND al.record_id LIKE CONCAT('%:', p_org_id))
          OR (al.table_name = 'invoice' AND EXISTS (
              SELECT 1 FROM invoice i WHERE i.invoice_id = al.record_id AND i.org_id = p_org_id
          ))
          OR (al.table_name = 'payment' AND EXISTS (
              SELECT 1 FROM payment p 
              JOIN invoice i ON p.invoice_id = i.invoice_id 
              WHERE p.payment_id = al.record_id AND i.org_id = p_org_id
          ))
          OR (al.table_name = 'customer' AND EXISTS (
              SELECT 1 FROM customer c WHERE c.customer_id = al.record_id AND c.org_id = p_org_id
          ))
          OR (al.table_name = 'template' AND EXISTS (
              SELECT 1 FROM template t WHERE CONCAT(t.template_id, ':', t.version) = al.record_id AND t.org_id = p_org_id
          ))
      )
    ORDER BY al.changed_at DESC
    LIMIT v_limit
    OFFSET v_offset;
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
/*!50003 DROP PROCEDURE IF EXISTS `sp_get_org_members` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_org_members`(
    IN p_org_id CHAR(36)
)
BEGIN
    SELECT 
        u.user_id, 
        u.email, 
        uo.role, 
        uo.status,
        uo.created_at as joined_at
    FROM user_organization uo
    JOIN users u ON uo.user_id = u.user_id
    WHERE uo.org_id = p_org_id 
    AND uo.status IN ('active', 'deactivated')
    ORDER BY uo.role, u.email;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_get_pending_members` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_pending_members`(
    IN p_org_id CHAR(36)
)
BEGIN
    SELECT 
        u.user_id, 
        u.email, 
        uo.role, 
        uo.created_at as joined_at
    FROM user_organization uo
    JOIN users u ON uo.user_id = u.user_id
    WHERE uo.org_id = p_org_id 
    AND uo.status = 'pending'
    ORDER BY uo.created_at DESC;
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
/*!50003 DROP PROCEDURE IF EXISTS `sp_get_template_fields_by_version` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_template_fields_by_version`(
    IN p_template_id CHAR(36),
    IN p_version INT
)
BEGIN
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
        f.display_name AS label,
        f.data_type,
        f.is_required,
        f.is_currency,
        f.ordinal AS field_ordinal,
        f.calculation_formula
    FROM section s
    JOIN field f ON s.section_id = f.section_id
    WHERE s.template_id = p_template_id
      AND s.template_version = p_version
    ORDER BY s.ordinal, f.ordinal;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_get_template_max_version` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_template_max_version`(
    IN p_template_id CHAR(36)
)
BEGIN
    SELECT MAX(version) AS max_version
    FROM template
    WHERE template_id = p_template_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_get_template_total_field` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_template_total_field`(
    IN p_template_id CHAR(36),
    IN p_version INT
)
BEGIN
    SELECT total_field_id
    FROM template
    WHERE template_id = p_template_id AND version = p_version;
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
    SELECT uo.org_id, o.name, o.domain, uo.role, uo.status
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
/*!50003 DROP PROCEDURE IF EXISTS `sp_update_member_status` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_update_member_status`(
    IN p_org_id CHAR(36),
    IN p_user_id CHAR(36),
    IN p_status VARCHAR(20),
    IN p_role VARCHAR(20)
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
    
    IF p_status = 'rejected' THEN
        DELETE FROM user_organization 
        WHERE org_id = p_org_id AND user_id = p_user_id;
    ELSE
        UPDATE user_organization 
        SET status = p_status, role = IFNULL(p_role, role)
        WHERE org_id = p_org_id AND user_id = p_user_id;
    END IF;
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

-- Dump completed on 2025-12-05 20:29:41
