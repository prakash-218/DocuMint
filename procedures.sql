-- ============================================================================
-- STORED PROCEDURES FOR MULTI-TENANT INVOICING SYSTEM
-- All database operations must go through these procedures
-- ============================================================================

DELIMITER //

-- ============================================================================
-- AUTHENTICATION & USER MANAGEMENT
-- ============================================================================

-- Create a new organization
CREATE PROCEDURE sp_create_organization(
    IN p_name VARCHAR(100),
    IN p_domain VARCHAR(100),
    OUT p_org_id CHAR(36)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    SET p_org_id = UUID();
    
    INSERT INTO organization (org_id, domain, name)
    VALUES (p_org_id, p_domain, p_name);
    
    -- Return the created org_id as a result set
    SELECT p_org_id AS org_id;
END //

-- Create a new user
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
    
    -- Return the created user_id as a result set
    SELECT p_user_id AS user_id;
END //

-- Assign user to organization
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

-- Authenticate user and return user info with organizations
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
    
    -- Return user info as first result set
    SELECT v_user_id AS user_id, p_email AS email;
    
    -- Return organizations for this user as second result set
    SELECT uo.org_id, o.name, o.domain, uo.role
    FROM user_organization uo
    JOIN organization o ON uo.org_id = o.org_id
    WHERE uo.user_id = v_user_id;
END //

-- Get user by email (for authentication)
CREATE PROCEDURE sp_get_user_by_email(
    IN p_email VARCHAR(255)
)
BEGIN
    SELECT user_id, email, password_hash
    FROM users
    WHERE email = p_email;
END //

-- Get user organizations
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

-- ============================================================================
-- TEMPLATE MANAGEMENT
-- ============================================================================

-- Create a new template (version 1)
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
    
    -- Return the created template_id and version as a result set
    SELECT p_template_id AS template_id, p_version AS version;
END //

-- Create a new version of an existing template (copies all sections and fields)
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
    
    -- Validate organization
    IF NOT EXISTS (SELECT 1 FROM organization WHERE org_id = p_org_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Organization does not exist';
    END IF;
    
    -- Get latest version
    SELECT MAX(version) INTO v_latest_version
    FROM template
    WHERE template_id = p_template_id
      AND org_id = p_org_id;
    
    IF v_latest_version IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Template does not exist or does not belong to organization';
    END IF;
    
    -- Get template details
    SELECT name, currency_code, total_field_id
    INTO v_template_name, v_currency_code, v_old_total_field_id
    FROM template
    WHERE template_id = p_template_id
      AND version = v_latest_version;
    
    -- Calculate new version
    SET p_new_version = v_latest_version + 1;
    
    -- Create new template version
    INSERT INTO template (template_id, version, org_id, name, currency_code, total_field_id)
    VALUES (p_template_id, p_new_version, p_org_id, v_template_name, v_currency_code, NULL);
    
    -- Copy all sections with new IDs
    INSERT INTO section (section_id, template_id, template_version, title, ordinal, section_type)
    SELECT UUID(), p_template_id, p_new_version, title, ordinal, section_type
    FROM section
    WHERE template_id = p_template_id
      AND template_version = v_latest_version
    ORDER BY ordinal;
    
    -- Copy all fields, mapping old section IDs to new section IDs
    INSERT INTO field (field_id, section_id, label, data_type, is_required, ordinal, calculation_formula)
    SELECT 
        UUID(),
        new_s.section_id,
        f.label,
        f.data_type,
        f.is_required,
        f.ordinal,
        f.calculation_formula
    FROM field f
    JOIN section old_s ON f.section_id = old_s.section_id
    JOIN section new_s ON new_s.template_id = p_template_id
                      AND new_s.template_version = p_new_version
                      AND new_s.ordinal = old_s.ordinal
                      AND new_s.title = old_s.title
    WHERE old_s.template_id = p_template_id
      AND old_s.template_version = v_latest_version
    ORDER BY old_s.ordinal, f.ordinal;
    
    -- Update total_field_id if it exists
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
    
    -- Return the new version as a result set
    SELECT p_new_version AS new_version;
END //

-- Create a new section in a template
CREATE PROCEDURE sp_create_section(
    IN p_template_id CHAR(36),
    IN p_template_version INT,
    IN p_title VARCHAR(100),
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
    
    SET p_section_id = UUID();
    
    INSERT INTO section (section_id, template_id, template_version, title, ordinal, section_type)
    VALUES (p_section_id, p_template_id, p_template_version, p_title, IFNULL(p_ordinal, 0), IFNULL(p_section_type, 'normal'));
    
    -- Return the created section_id as a result set
    SELECT p_section_id AS section_id;
END //

-- Add a field to a section
CREATE PROCEDURE sp_add_template_field(
    IN p_section_id CHAR(36),
    IN p_label VARCHAR(100),
    IN p_data_type VARCHAR(20),
    IN p_is_required TINYINT(1),
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
    
    SET p_field_id = UUID();
    
    INSERT INTO field (field_id, section_id, label, data_type, is_required, ordinal, calculation_formula)
    VALUES (p_field_id, p_section_id, p_label, p_data_type, IFNULL(p_is_required, 0), IFNULL(p_ordinal, 0), p_calculation_formula);
    
    -- Return the created field_id as a result set
    SELECT p_field_id AS field_id;
END //

-- Update template's total_field_id
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
    
    -- Verify the field exists and belongs to this template
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

-- Get template fields (latest version) with sections
CREATE PROCEDURE sp_get_template_fields(
    IN p_template_id CHAR(36)
)
BEGIN
    DECLARE v_latest_version INT;
    
    -- Get latest version
    SELECT MAX(version) INTO v_latest_version
    FROM template
    WHERE template_id = p_template_id;
    
    IF v_latest_version IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Template does not exist';
    END IF;
    
    -- Return fields grouped by section
    SELECT 
        s.section_id,
        s.title AS section_title,
        s.ordinal AS section_ordinal,
        s.section_type,
        f.field_id,
        f.label,
        f.data_type,
        f.is_required,
        f.ordinal AS field_ordinal,
        f.calculation_formula
    FROM section s
    JOIN field f ON s.section_id = f.section_id
    WHERE s.template_id = p_template_id
      AND s.template_version = v_latest_version
    ORDER BY s.ordinal, f.ordinal;
END //

-- Get all templates for an organization
CREATE PROCEDURE sp_list_templates(
    IN p_org_id CHAR(36)
)
BEGIN
    SELECT 
        t.template_id,
        t.version,
        t.name,
        t.currency_code,
        t.created_at,
        (SELECT MAX(version) FROM template WHERE template_id = t.template_id) AS latest_version
    FROM template t
    WHERE t.org_id = p_org_id
    GROUP BY t.template_id, t.version, t.name, t.currency_code, t.created_at
    ORDER BY t.created_at DESC;
END //

-- ============================================================================
-- CUSTOMER MANAGEMENT
-- ============================================================================

-- Create a new customer
CREATE PROCEDURE sp_create_customer(
    IN p_org_id CHAR(36),
    IN p_name VARCHAR(255),
    IN p_tax_id VARCHAR(50),
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
    
    INSERT INTO customer (customer_id, org_id, name, tax_id)
    VALUES (p_customer_id, p_org_id, p_name, p_tax_id);
    
    -- Return the created customer_id as a result set
    SELECT p_customer_id AS customer_id;
END //

-- List customers for an organization
CREATE PROCEDURE sp_list_customers(
    IN p_org_id CHAR(36)
)
BEGIN
    SELECT 
        c.customer_id,
        c.name,
        c.tax_id,
        c.created_at,
        COUNT(DISTINCT i.invoice_id) AS invoice_count
    FROM customer c
    LEFT JOIN invoice i ON c.customer_id = i.customer_id
    WHERE c.org_id = p_org_id
    GROUP BY c.customer_id, c.name, c.tax_id, c.created_at
    ORDER BY c.name;
END //

-- Get customer details with contacts
CREATE PROCEDURE sp_get_customer_details(
    IN p_customer_id CHAR(36)
)
BEGIN
    -- Customer info
    SELECT 
        c.customer_id,
        c.org_id,
        c.name,
        c.tax_id,
        c.created_at
    FROM customer c
    WHERE c.customer_id = p_customer_id;
    
    -- Customer contacts
    SELECT 
        p.person_id,
        p.email,
        p.full_name,
        cca.role
    FROM customer_contact_assignment cca
    JOIN person p ON cca.person_id = p.person_id
    WHERE cca.customer_id = p_customer_id;
END //

-- ============================================================================
-- INVOICE MANAGEMENT
-- ============================================================================

-- Create a new invoice (auto-resolves latest template version)
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
    
    -- Validate organization
    IF NOT EXISTS (SELECT 1 FROM organization WHERE org_id = p_org_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Organization does not exist';
    END IF;
    
    -- Validate customer
    IF NOT EXISTS (SELECT 1 FROM customer WHERE customer_id = p_customer_id AND org_id = p_org_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Customer does not exist or does not belong to organization';
    END IF;
    
    -- Get latest template version
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
    
    -- Return the created invoice_id and template_version as a result set
    SELECT p_invoice_id AS invoice_id, p_template_version AS template_version;
END //

-- Save invoice value (upsert)
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
    
    -- Validate invoice exists
    IF NOT EXISTS (SELECT 1 FROM invoice WHERE invoice_id = p_invoice_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invoice does not exist';
    END IF;
    
    -- Check if value already exists (for line items, check by field_id AND ordinal)
    -- For line items (ordinal is not NULL), match by field_id AND ordinal
    -- For normal fields (ordinal is NULL), match by field_id only
    IF p_ordinal IS NULL THEN
        -- Normal field - match by invoice_id and field_id only
        SELECT value_id INTO v_value_id
        FROM invoice_value
        WHERE invoice_id = p_invoice_id 
          AND field_id = p_field_id
          AND (ordinal IS NULL OR ordinal = 0);
    ELSE
        -- Line item - match by invoice_id, field_id, AND ordinal
        SELECT value_id INTO v_value_id
        FROM invoice_value
        WHERE invoice_id = p_invoice_id 
          AND field_id = p_field_id
          AND ordinal = p_ordinal;
    END IF;
    
    IF v_value_id IS NOT NULL THEN
        -- Update existing
        UPDATE invoice_value
        SET 
            val_string = p_val_string,
            val_number = p_val_number,
            val_date = p_val_date,
            val_boolean = p_val_boolean,
            ordinal = IFNULL(p_ordinal, 0)
        WHERE value_id = v_value_id;
    ELSE
        -- Insert new
        SET v_value_id = UUID();
    INSERT INTO invoice_value (value_id, invoice_id, field_id, val_string, val_number, val_date, val_boolean, ordinal)
    VALUES (v_value_id, p_invoice_id, p_field_id, p_val_string, p_val_number, p_val_date, p_val_boolean, IFNULL(p_ordinal, 0));
    END IF;
    
    -- Update invoice total amount after saving value
    CALL sp_update_invoice_total(p_invoice_id);
END //

-- Update invoice total amount (called automatically after value changes)
CREATE PROCEDURE sp_update_invoice_total(
    IN p_invoice_id CHAR(36)
)
BEGIN
    DECLARE v_total DECIMAL(15, 4) DEFAULT 0;
    DECLARE v_total_field_id CHAR(36);
    DECLARE v_template_total_field_id CHAR(36);
    
    -- Strategy 1: Use the field specified in the template (if set)
    SELECT t.total_field_id INTO v_template_total_field_id
    FROM invoice i
    JOIN template t ON i.template_id = t.template_id AND i.template_version = t.version
    WHERE i.invoice_id = p_invoice_id;
    
    IF v_template_total_field_id IS NOT NULL THEN
        -- Use the template's specified total field
        SELECT IFNULL(SUM(iv.val_number), 0) INTO v_total
        FROM invoice_value iv
        WHERE iv.invoice_id = p_invoice_id
          AND iv.field_id = v_template_total_field_id
          AND (iv.ordinal IS NULL OR iv.ordinal = 0);
    ELSE
        -- Strategy 2: Try to find a field labeled "total", "grand total", "amount", etc.
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
        
        -- If found, use that field's value (from normal section, ordinal 0)
        IF v_total_field_id IS NOT NULL THEN
            SELECT IFNULL(SUM(iv.val_number), 0) INTO v_total
            FROM invoice_value iv
            WHERE iv.invoice_id = p_invoice_id
              AND iv.field_id = v_total_field_id
              AND (iv.ordinal IS NULL OR iv.ordinal = 0);
        ELSE
            -- Strategy 3: Look for calculated fields with sum() formulas
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
            
            -- Strategy 4: Fallback - sum all number fields from normal sections
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
    
    -- Update invoice total
    UPDATE invoice
    SET total_amount = IFNULL(v_total, 0)
    WHERE invoice_id = p_invoice_id;
END //

-- Get invoice details (multiple result sets)
CREATE PROCEDURE sp_get_invoice_details(
    IN p_invoice_id CHAR(36)
)
BEGIN
    -- Result set 1: Invoice header
    SELECT 
        i.invoice_id,
        i.org_id,
        i.customer_id,
        c.name AS customer_name,
        i.template_id,
        i.template_version,
        t.name AS template_name,
        t.currency_code,
        i.issue_date,
        i.due_date,
        i.status
    FROM invoice i
    JOIN customer c ON i.customer_id = c.customer_id
    LEFT JOIN template t ON i.template_id = t.template_id AND i.template_version = t.version
    WHERE i.invoice_id = p_invoice_id;
    
    -- Result set 2: Invoice values with field metadata
    SELECT 
        iv.value_id,
        iv.field_id,
        f.label AS field_label,
        f.data_type,
        f.calculation_formula,
        s.title AS section_title,
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

-- List invoices with pagination
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

-- Update invoice status
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

-- Update invoice dates
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

-- ============================================================================
-- PAYMENT MANAGEMENT
-- ============================================================================

-- Record a payment
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
    
    -- Return the created payment_id as a result set
    SELECT p_payment_id AS payment_id;
    
    -- Update invoice total amount
    CALL sp_update_invoice_total(p_invoice_id);
    
    -- Auto-update invoice status if fully paid
    UPDATE invoice i
    SET status = 'paid'
    WHERE i.invoice_id = p_invoice_id
      AND (SELECT IFNULL(SUM(amount), 0) FROM payment WHERE invoice_id = i.invoice_id) >= i.total_amount;
END //

-- Get invoice payments
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

-- ============================================================================
-- DASHBOARD STATISTICS
-- ============================================================================

-- Get dashboard statistics for an organization
CREATE PROCEDURE sp_get_dashboard_stats(
    IN p_org_id CHAR(36)
)
BEGIN
    SELECT 
        -- Total revenue (sum of all invoice totals for paid/pending invoices)
        (SELECT IFNULL(SUM(i.total_amount), 0)
         FROM invoice i
         WHERE i.org_id = p_org_id 
           AND i.status IN ('paid', 'pending')) AS total_revenue,
        
        -- Pending invoices count
        (SELECT COUNT(*)
         FROM invoice
         WHERE org_id = p_org_id AND status = 'pending') AS pending_count,
        
        -- Paid invoices count
        (SELECT COUNT(*)
         FROM invoice
         WHERE org_id = p_org_id AND status = 'paid') AS paid_count,
        
        -- Overdue invoices count
        (SELECT COUNT(*)
         FROM invoice
         WHERE org_id = p_org_id 
           AND status IN ('pending', 'draft')
           AND due_date < CURDATE()) AS overdue_count,
        
        -- Total invoices
        (SELECT COUNT(*)
         FROM invoice
         WHERE org_id = p_org_id) AS total_invoices,
        
        -- Revenue this month (from invoices issued this month)
        (SELECT IFNULL(SUM(i.total_amount), 0)
         FROM invoice i
         WHERE i.org_id = p_org_id
           AND i.status IN ('paid', 'pending')
           AND YEAR(i.issue_date) = YEAR(CURDATE())
           AND MONTH(i.issue_date) = MONTH(CURDATE())) AS revenue_this_month,
        
        -- Revenue last month (from invoices issued last month)
        (SELECT IFNULL(SUM(i.total_amount), 0)
         FROM invoice i
         WHERE i.org_id = p_org_id
           AND i.status IN ('paid', 'pending')
           AND YEAR(i.issue_date) = YEAR(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
           AND MONTH(i.issue_date) = MONTH(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))) AS revenue_last_month;
END //

-- Get revenue data for the last 6 months (for charts)
CREATE PROCEDURE sp_get_revenue_timeseries(
    IN p_org_id CHAR(36)
)
BEGIN
    -- Get revenue grouped by month, using issue_date or falling back to current date
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

-- Get invoice status distribution (for pie chart)
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

-- Get revenue by status (for charts)
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

-- ============================================================================
-- CUSTOMER PORTAL PROCEDURES
-- ============================================================================

-- Create customer user account
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
    
    -- Return the created customer_user_id as a result set
    SELECT p_customer_user_id AS customer_user_id;
END //

-- Get customer user by email (for password verification)
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

-- Get all portal accounts for a customer
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

-- Authenticate customer
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
    
    -- Return customer user info
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

-- Get invoices for customer
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

DELIMITER ;

