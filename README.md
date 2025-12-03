# Multi-Tenant SaaS Invoicing System

A comprehensive multi-tenant invoicing system built with Flask, MySQL, and server-side rendering. All database operations are handled through stored procedures, ensuring zero SQL in Python code.

## Features

- **Multi-Tenant Architecture**: Organization-based tenant isolation
- **Template Engine**: Dynamic invoice templates with customizable fields
- **JWT Authentication**: Secure user authentication with organization management
- **Custom Theming**: Light, Dark, and Branded theme support
- **Responsive Design**: Modern UI with custom CSS (no frameworks)
- **Stored Procedures Only**: All database operations via MySQL stored procedures

## Tech Stack

- **Backend**: Python 3, Flask
- **Database**: MySQL 8.0+ (using pymysql)
- **Frontend**: Jinja2 templates with custom CSS
- **Authentication**: JWT tokens with bcrypt password hashing

## Prerequisites

- Python 3.8+
- MySQL 8.0+
- pip (Python package manager)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd invoice-gen
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=invoice_db
   SECRET_KEY=your-secret-key-here
   JWT_SECRET=your-jwt-secret-here
   FLASK_ENV=development
   FLASK_DEBUG=True
   ```

5. **Create the database**
   ```bash
   mysql -u root -p
   CREATE DATABASE invoice_db;
   ```

6. **Initialize the database schema**
   ```bash
   mysql -u root -p invoice_db < schema.sql
   ```

7. **Create stored procedures**
   ```bash
   mysql -u root -p invoice_db < procedures.sql
   ```

## Running the Application

1. **Activate the virtual environment** (if not already activated)
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Run the Flask application**
   ```bash
   python app.py
   ```

3. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

## Usage

### First Time Setup

1. **Register a new account**
   - Navigate to the registration page
   - Enter your email, password, organization name, and domain
   - This will create both your user account and organization

2. **Login**
   - Use your email and password to log in
   - You'll be automatically assigned to your organization

### Creating Templates

1. Go to **Templates** in the sidebar
2. Click **Create Template**
3. Enter template name and currency
4. Add sections and fields:
   - Click **Add Section** to create a new section
   - Within each section, click **Add Field** to add fields
   - Choose field type: String, Number, Date, or Boolean
   - Mark fields as required if needed

### Creating Customers

1. Go to **Customers** in the sidebar
2. Click **Create Customer**
3. Enter customer name and optional tax ID

### Creating Invoices

1. Go to **Invoices** in the sidebar
2. Click **Create Invoice**
3. Select a customer and template
4. Fill in the dynamic form fields based on your template
5. Set issue date and due date
6. Submit to create the invoice

### Managing Invoices

- **View**: Click on any invoice to view details
- **Add Payments**: Record payments on the invoice view page
- **Filter**: Use status filters (All, Draft, Pending, Paid) to filter invoices

### Dashboard

The dashboard displays:
- Total revenue
- Total invoices count
- Pending invoices
- Overdue invoices
- Revenue this month vs last month
- Recent invoices list

## Architecture

### Database Layer

All database operations are performed through MySQL stored procedures. The Python code never contains raw SQL statements. Key procedures include:

- `sp_create_organization` - Create new organization
- `sp_create_user` - Create new user
- `sp_authenticate_user` - Authenticate user
- `sp_create_template` - Create invoice template
- `sp_create_invoice` - Create invoice (auto-resolves latest template version)
- `sp_get_dashboard_stats` - Get dashboard statistics
- And many more...

### Application Structure

```
invoice-gen/
├── app.py                 # Main Flask application
├── config.py              # Configuration management
├── db.py                  # Database connection and procedure execution
├── auth.py                # Authentication and authorization
├── schema.sql             # Database schema
├── procedures.sql         # Stored procedures
├── blueprints/            # Flask blueprints
│   ├── auth_bp.py
│   ├── dashboard_bp.py
│   ├── invoices_bp.py
│   ├── customers_bp.py
│   ├── templates_bp.py
│   └── settings_bp.py
├── templates/             # Jinja2 templates
│   ├── base.html
│   ├── auth/
│   ├── dashboard.html
│   ├── invoices/
│   ├── customers/
│   ├── templates/
│   └── settings/
└── static/               # Static files
    ├── css/
    │   ├── variables.css
    │   └── main.css
    └── js/
        └── theme-switcher.js
```

## Theming

The application supports three themes:

- **Light**: Default light theme
- **Dark**: Dark mode for low-light environments
- **Branded**: Purple-themed branded appearance

Switch themes using the theme switcher in the header. Your preference is saved in localStorage.

## Security Features

- Password hashing with bcrypt
- JWT token-based authentication
- Organization-based data isolation
- Input validation in stored procedures
- CSRF protection (Flask default)

## Development

### Adding New Stored Procedures

1. Add the procedure to `procedures.sql`
2. Use `db.execute_proc()` in your Python code to call it
3. Never write raw SQL in Python files

### Adding New Routes

1. Create or update a blueprint in `blueprints/`
2. Use `@require_auth` or `@require_org` decorators for protected routes
3. Use stored procedures for all database operations

## Troubleshooting

### Database Connection Issues

- Verify MySQL is running
- Check `.env` file has correct database credentials
- Ensure database exists: `mysql -u root -p -e "SHOW DATABASES;"`

### Stored Procedure Errors

- Verify procedures are created: `mysql -u root -p invoice_db -e "SHOW PROCEDURE STATUS;"`
- Re-run `procedures.sql` if needed

### Authentication Issues

- Clear browser cookies/session
- Verify JWT_SECRET is set in `.env`
- Check password hashing is working

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

