




DELIMITER //






CREATE PROCEDURE sp_create_organization(
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
END //


CREATE PROCEDURE sp_create_user(
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
END //


CREATE PROCEDURE sp_assign_user_to_org(
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
END //


CREATE PROCEDURE sp_authenticate_user(
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
END //


CREATE PROCEDURE sp_get_user_by_email(
    IN p_email VARCHAR(255)
)
BEGIN
    SELECT user_id, email, password_hash
    FROM users
    WHERE email = p_email;
END //


DROP PROCEDURE IF EXISTS sp_find_organizations_by_domain //
CREATE PROCEDURE sp_find_organizations_by_domain(
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
END //


DROP PROCEDURE IF EXISTS sp_find_organization_by_domain //
CREATE PROCEDURE sp_find_organization_by_domain(
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
END //


DROP PROCEDURE IF EXISTS sp_get_user_organizations //
CREATE PROCEDURE sp_get_user_organizations(
    IN p_user_id CHAR(36)
)
BEGIN
    SELECT uo.org_id, o.name, o.domain, uo.role
    FROM user_organization uo
    JOIN organization o ON uo.org_id = o.org_id
    WHERE uo.user_id = p_user_id
    ORDER BY uo.created_at DESC;
END //


DROP PROCEDURE IF EXISTS sp_get_organization_details //
CREATE PROCEDURE sp_get_organization_details(
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
END //


DROP PROCEDURE IF EXISTS sp_update_organization //
CREATE PROCEDURE sp_update_organization(
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
END //






CREATE PROCEDURE sp_create_template(
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
END //


DROP PROCEDURE IF EXISTS sp_check_template_version_has_invoices //
CREATE PROCEDURE sp_check_template_version_has_invoices(
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
END //


DROP PROCEDURE IF EXISTS sp_create_template_version //
CREATE PROCEDURE sp_create_template_version(
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
END //


CREATE PROCEDURE sp_create_section(
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
END //


CREATE PROCEDURE sp_add_template_field(
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
END //


CREATE PROCEDURE sp_set_template_total_field(
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
END //


CREATE PROCEDURE sp_get_template_fields(
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
END //


CREATE PROCEDURE sp_list_templates(
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
END //


DROP PROCEDURE IF EXISTS sp_update_section //
CREATE PROCEDURE sp_update_section(
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
END //


DROP PROCEDURE IF EXISTS sp_delete_section //
CREATE PROCEDURE sp_delete_section(
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
END //


DROP PROCEDURE IF EXISTS sp_update_field //
CREATE PROCEDURE sp_update_field(
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
END //


DROP PROCEDURE IF EXISTS sp_delete_field //
CREATE PROCEDURE sp_delete_field(
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
END //






DROP PROCEDURE IF EXISTS sp_create_customer //
CREATE PROCEDURE sp_create_customer(
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
END //


DROP PROCEDURE IF EXISTS sp_list_customers //
CREATE PROCEDURE sp_list_customers(
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
    ORDER BY c.name;
END //


DROP PROCEDURE IF EXISTS sp_get_customer_details //
CREATE PROCEDURE sp_get_customer_details(
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
END //


DROP PROCEDURE IF EXISTS sp_update_customer //
CREATE PROCEDURE sp_update_customer(
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
END //






CREATE PROCEDURE sp_create_invoice(
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
    
    IF EXISTS (SELECT 1 FROM customer WHERE customer_id = p_customer_id AND org_id = p_org_id AND is_archived = TRUE) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot create invoice for archived customer';
    END IF;
    
    
    SELECT MAX(version) INTO v_latest_version
    FROM template
    WHERE template_id = p_template_id
      AND org_id = p_org_id
      AND is_archived = FALSE;
    
    IF v_latest_version IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Template does not exist, does not belong to organization, or is archived';
    END IF;
    
    SET p_invoice_id = UUID();
    SET p_template_version = v_latest_version;
    
    INSERT INTO invoice (invoice_id, org_id, customer_id, template_id, template_version, status)
    VALUES (p_invoice_id, p_org_id, p_customer_id, p_template_id, p_template_version, 'draft');
    
    
    SELECT p_invoice_id AS invoice_id, p_template_version AS template_version;
END //


CREATE PROCEDURE sp_save_invoice_value(
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
END //


CREATE PROCEDURE sp_update_invoice_total(
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
END //


CREATE PROCEDURE sp_get_invoice_details(
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
END //


CREATE PROCEDURE sp_list_invoices(
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
END //


CREATE PROCEDURE sp_update_invoice_status(
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
END //


CREATE PROCEDURE sp_update_invoice_dates(
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
END //


DROP PROCEDURE IF EXISTS sp_delete_invoice //
CREATE PROCEDURE sp_delete_invoice(
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
END //


DROP PROCEDURE IF EXISTS sp_delete_customer //
CREATE PROCEDURE sp_delete_customer(
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
END //






CREATE PROCEDURE sp_record_payment(
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
END //


CREATE PROCEDURE sp_get_invoice_payments(
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
END //






DROP PROCEDURE IF EXISTS sp_get_dashboard_stats //
CREATE PROCEDURE sp_get_dashboard_stats(
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
END //


CREATE PROCEDURE sp_get_revenue_timeseries(
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
END //


CREATE PROCEDURE sp_get_invoice_status_distribution(
    IN p_org_id CHAR(36)
)
BEGIN
    SELECT 
        IFNULL(status, 'draft') AS status,
        COUNT(*) AS count
    FROM invoice
    WHERE org_id = p_org_id
    GROUP BY status;
END //


CREATE PROCEDURE sp_get_revenue_by_status(
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
END //






CREATE PROCEDURE sp_create_customer_user(
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
END //


CREATE PROCEDURE sp_get_customer_user_by_email(
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
END //


CREATE PROCEDURE sp_get_customer_users(
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
END //


CREATE PROCEDURE sp_authenticate_customer(
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
END //


CREATE PROCEDURE sp_get_customer_invoices(
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
END //


DROP PROCEDURE IF EXISTS sp_archive_customer //
CREATE PROCEDURE sp_archive_customer(
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
END //


DROP PROCEDURE IF EXISTS sp_unarchive_customer //
CREATE PROCEDURE sp_unarchive_customer(
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
END //


DROP PROCEDURE IF EXISTS sp_archive_template //
CREATE PROCEDURE sp_archive_template(
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
END //


DROP PROCEDURE IF EXISTS sp_unarchive_template //
CREATE PROCEDURE sp_unarchive_template(
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
END //

DELIMITER ;

