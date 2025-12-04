
CREATE TABLE users (
    user_id CHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE person (
    person_id CHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE organization (
    org_id CHAR(36) PRIMARY KEY,
    domain VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    street_address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    zip_code VARCHAR(20),
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_name_domain (name, domain)
);


CREATE TABLE user_organization (
    user_id CHAR(36) NOT NULL,
    org_id CHAR(36) NOT NULL,
    role VARCHAR(50) DEFAULT 'member',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, org_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (org_id) REFERENCES organization(org_id) ON DELETE CASCADE
);


CREATE TABLE customer (
    customer_id CHAR(36) PRIMARY KEY,
    org_id CHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    tax_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (org_id) REFERENCES organization(org_id) ON DELETE CASCADE
);

CREATE TABLE customer_contact_assignment (
    customer_id CHAR(36) NOT NULL,
    person_id CHAR(36) NOT NULL,
    role VARCHAR(50),
    PRIMARY KEY (customer_id, person_id),
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (person_id) REFERENCES person(person_id) ON DELETE RESTRICT
);


CREATE TABLE customer_user (
    customer_user_id CHAR(36) PRIMARY KEY,
    customer_id CHAR(36) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE CASCADE
);
CREATE INDEX idx_customer_user_customer ON customer_user(customer_id);
CREATE INDEX idx_customer_user_email ON customer_user(email);


CREATE TABLE template (
    template_id CHAR(36) NOT NULL,
    version INT NOT NULL,
    org_id CHAR(36) NOT NULL,
    name VARCHAR(100),
    currency_code CHAR(3) NOT NULL,
    total_field_id CHAR(36) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (template_id, version),
    FOREIGN KEY (org_id) REFERENCES organization(org_id) ON DELETE CASCADE
);

CREATE INDEX idx_template_total_field ON template(total_field_id);

CREATE TABLE section (
    section_id CHAR(36) PRIMARY KEY,
    template_id CHAR(36) NOT NULL,
    template_version INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100),
    ordinal INT,
    section_type ENUM('normal', 'line_item') DEFAULT 'normal',
    FOREIGN KEY (template_id, template_version) 
        REFERENCES template(template_id, version) ON DELETE CASCADE
);

CREATE TABLE field (
    field_id CHAR(36) PRIMARY KEY,
    section_id CHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100),
    data_type VARCHAR(20) NOT NULL, 
    is_required BOOLEAN DEFAULT FALSE, 
    is_currency BOOLEAN DEFAULT FALSE,
    ordinal INT,
    calculation_formula TEXT, 
    FOREIGN KEY (section_id) REFERENCES section(section_id) ON DELETE CASCADE
);


CREATE TABLE invoice (
    invoice_id CHAR(36) PRIMARY KEY,
    org_id CHAR(36) NOT NULL,
    customer_id CHAR(36) NOT NULL,
    template_id CHAR(36),
    template_version INT,
    issue_date DATE,
    due_date DATE,
    status VARCHAR(20),
    total_amount DECIMAL(15, 4) DEFAULT 0, 
    
    FOREIGN KEY (org_id) REFERENCES organization(org_id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE RESTRICT,
    FOREIGN KEY (template_id, template_version) 
        REFERENCES template(template_id, version) ON DELETE RESTRICT
);

CREATE TABLE invoice_value (
    value_id CHAR(36) PRIMARY KEY,
    invoice_id CHAR(36) NOT NULL,
    field_id CHAR(36),
    val_string TEXT,
    val_number DECIMAL(15, 4),
    val_date DATE,
    val_boolean TINYINT(1),
    ordinal INT DEFAULT 0,
    
    FOREIGN KEY (invoice_id) REFERENCES invoice(invoice_id) ON DELETE CASCADE,
    FOREIGN KEY (field_id) REFERENCES field(field_id) ON DELETE SET NULL
);

CREATE TABLE payment (
    payment_id CHAR(36) PRIMARY KEY,
    invoice_id CHAR(36) NOT NULL,
    amount DECIMAL(15, 4) NOT NULL,
    method VARCHAR(50),
    reference_number VARCHAR(100),
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (invoice_id) REFERENCES invoice(invoice_id) ON DELETE RESTRICT
);


CREATE INDEX idx_customer_org_id ON customer(org_id);
CREATE INDEX idx_invoice_org_id ON invoice(org_id);
CREATE INDEX idx_invoice_customer_id ON invoice(customer_id);
CREATE INDEX idx_invoice_status ON invoice(status);
CREATE INDEX idx_invoice_template ON invoice(template_id, template_version);
CREATE INDEX idx_template_org_id ON template(org_id);
CREATE INDEX idx_template_latest ON template(template_id, version DESC);
CREATE INDEX idx_section_template ON section(template_id, template_version);
CREATE INDEX idx_field_section ON field(section_id);
CREATE INDEX idx_invoice_value_invoice ON invoice_value(invoice_id);
CREATE INDEX idx_invoice_value_field ON invoice_value(field_id);
CREATE INDEX idx_payment_invoice ON payment(invoice_id);
CREATE INDEX idx_user_org_user ON user_organization(user_id);
CREATE INDEX idx_user_org_org ON user_organization(org_id);