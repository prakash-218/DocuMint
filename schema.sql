-- Database schema extracted from dump
-- Generated automatically from data_sump.sql

CREATE TABLE `users` (
  `user_id` char(36) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `person` ( `person_id` char(36) NOT NULL, `email` varchar(255) NOT NULL, `full_name` varchar(100) DEFAULT NULL, `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (`person_id`), UNIQUE KEY `email` (`email`) ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `organization` ( `org_id` char(36) NOT NULL, `domain` varchar(100) NOT NULL, `name` varchar(100) NOT NULL, `street_address` varchar(255) DEFAULT NULL, `city` varchar(100) DEFAULT NULL, `state` varchar(100) DEFAULT NULL, `zip_code` varchar(20) DEFAULT NULL, `country` varchar(100) DEFAULT NULL, `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (`org_id`), UNIQUE KEY `unique_name_domain` (`name`,`domain`) ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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

CREATE TABLE `customer` ( `customer_id` char(36) NOT NULL, `org_id` char(36) NOT NULL, `name` varchar(255) NOT NULL, `tax_id` varchar(50) DEFAULT NULL, `street_address` varchar(255) DEFAULT NULL, `city` varchar(100) DEFAULT NULL, `state` varchar(100) DEFAULT NULL, `zip_code` varchar(20) DEFAULT NULL, `country` varchar(100) DEFAULT NULL, `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP, `is_archived` tinyint(1) DEFAULT '0', PRIMARY KEY (`customer_id`), KEY `idx_customer_org_id` (`org_id`), KEY `idx_customer_archived` (`org_id`,`is_archived`), CONSTRAINT `customer_ibfk_1` FOREIGN KEY (`org_id`) REFERENCES `organization` (`org_id`) ON DELETE CASCADE ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `customer_user` ( `customer_user_id` char(36) NOT NULL, `customer_id` char(36) NOT NULL, `email` varchar(255) NOT NULL, `password_hash` varchar(255) NOT NULL, `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (`customer_user_id`), UNIQUE KEY `email` (`email`), KEY `idx_customer_user_customer` (`customer_id`), KEY `idx_customer_user_email` (`email`), CONSTRAINT `customer_user_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`) ON DELETE CASCADE ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `customer_contact_assignment` ( `customer_id` char(36) NOT NULL, `person_id` char(36) NOT NULL, `role` varchar(50) DEFAULT NULL, PRIMARY KEY (`customer_id`,`person_id`), KEY `person_id` (`person_id`), CONSTRAINT `customer_contact_assignment_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`) ON DELETE CASCADE, CONSTRAINT `customer_contact_assignment_ibfk_2` FOREIGN KEY (`person_id`) REFERENCES `person` (`person_id`) ON DELETE RESTRICT ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `template` ( `template_id` char(36) NOT NULL, `version` int NOT NULL, `org_id` char(36) NOT NULL, `name` varchar(100) DEFAULT NULL, `currency_code` char(3) NOT NULL, `total_field_id` char(36) DEFAULT NULL, `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP, `is_archived` tinyint(1) DEFAULT '0', PRIMARY KEY (`template_id`,`version`), KEY `idx_template_total_field` (`total_field_id`), KEY `idx_template_org_id` (`org_id`), KEY `idx_template_latest` (`template_id`,`version` DESC), KEY `idx_template_archived` (`org_id`,`is_archived`), CONSTRAINT `template_ibfk_1` FOREIGN KEY (`org_id`) REFERENCES `organization` (`org_id`) ON DELETE CASCADE ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `section` ( `section_id` char(36) NOT NULL, `template_id` char(36) NOT NULL, `template_version` int NOT NULL, `name` varchar(100) NOT NULL, `display_name` varchar(100) DEFAULT NULL, `title` varchar(100) DEFAULT NULL, `ordinal` int DEFAULT NULL, `section_type` enum('normal','line_item') DEFAULT 'normal', PRIMARY KEY (`section_id`), KEY `idx_section_template` (`template_id`,`template_version`), CONSTRAINT `section_ibfk_1` FOREIGN KEY (`template_id`, `template_version`) REFERENCES `template` (`template_id`, `version`) ON DELETE CASCADE ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `field` ( `field_id` char(36) NOT NULL, `section_id` char(36) NOT NULL, `name` varchar(100) NOT NULL, `display_name` varchar(100) DEFAULT NULL, `label` varchar(100) DEFAULT NULL, `data_type` varchar(20) NOT NULL, `is_required` tinyint(1) DEFAULT '0', `is_currency` tinyint(1) DEFAULT '0', `ordinal` int DEFAULT NULL, `calculation_formula` text, PRIMARY KEY (`field_id`), KEY `idx_field_section` (`section_id`), CONSTRAINT `field_ibfk_1` FOREIGN KEY (`section_id`) REFERENCES `section` (`section_id`) ON DELETE CASCADE ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `invoice` ( `invoice_id` char(36) NOT NULL, `org_id` char(36) NOT NULL, `customer_id` char(36) NOT NULL, `template_id` char(36) DEFAULT NULL, `template_version` int DEFAULT NULL, `issue_date` date DEFAULT NULL, `due_date` date DEFAULT NULL, `status` varchar(20) DEFAULT NULL, `total_amount` decimal(15,4) DEFAULT '0.0000', PRIMARY KEY (`invoice_id`), KEY `idx_invoice_org_id` (`org_id`), KEY `idx_invoice_customer_id` (`customer_id`), KEY `idx_invoice_status` (`status`), KEY `idx_invoice_template` (`template_id`,`template_version`), CONSTRAINT `invoice_ibfk_1` FOREIGN KEY (`org_id`) REFERENCES `organization` (`org_id`) ON DELETE CASCADE, CONSTRAINT `invoice_ibfk_2` FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`) ON DELETE RESTRICT, CONSTRAINT `invoice_ibfk_3` FOREIGN KEY (`template_id`, `template_version`) REFERENCES `template` (`template_id`, `version`) ON DELETE RESTRICT ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `invoice_value` ( `value_id` char(36) NOT NULL, `invoice_id` char(36) NOT NULL, `field_id` char(36) DEFAULT NULL, `val_string` text, `val_number` decimal(15,4) DEFAULT NULL, `val_date` date DEFAULT NULL, `val_boolean` tinyint(1) DEFAULT NULL, `ordinal` int DEFAULT '0', PRIMARY KEY (`value_id`), KEY `idx_invoice_value_invoice` (`invoice_id`), KEY `idx_invoice_value_field` (`field_id`), CONSTRAINT `invoice_value_ibfk_1` FOREIGN KEY (`invoice_id`) REFERENCES `invoice` (`invoice_id`) ON DELETE CASCADE, CONSTRAINT `invoice_value_ibfk_2` FOREIGN KEY (`field_id`) REFERENCES `field` (`field_id`) ON DELETE SET NULL ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `payment` ( `payment_id` char(36) NOT NULL, `invoice_id` char(36) NOT NULL, `amount` decimal(15,4) NOT NULL, `method` varchar(50) DEFAULT NULL, `reference_number` varchar(100) DEFAULT NULL, `payment_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (`payment_id`), KEY `idx_payment_invoice` (`invoice_id`), CONSTRAINT `payment_ibfk_1` FOREIGN KEY (`invoice_id`) REFERENCES `invoice` (`invoice_id`) ON DELETE RESTRICT ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
  PRIMARY KEY (`audit_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE INDEX `idx_audit_table_record` ON `audit_log` (`table_name`, `record_id`);
CREATE INDEX `idx_audit_changed_at` ON `audit_log` (`changed_at`);
CREATE INDEX `idx_audit_action` ON `audit_log` (`action_type`);
