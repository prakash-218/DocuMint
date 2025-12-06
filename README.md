# DocuMint - Invoice Management System

DocuMint is a comprehensive invoice management system built with Flask that allows organizations to create, manage, and track invoices with customizable templates. The system supports multi-organization workflows with role-based access control, customer portals, and automated invoice calculations.

## Hosted version
 If you want to skip running the project locally, you can head to https://documint.up.railway.app/ to view the app.
 for login credentials, you can check the bottom of this readme. (same credentials for local and hosted versions). The hosted app might be very slow as we have hosted in a free tier hosting.

## Technical Specifications

### Host Language
- **Python 3.11+** (Python 3.12 recommended)
  - Download: https://www.python.org/downloads/
  - Installation guide: https://www.python.org/downloads/

### Web Framework
- **Flask 3.0.0**
  - Documentation: https://flask.palletsprojects.com/
  - Installation: Included in `requirements.txt`

### Database
- **MySQL 8.0+**
  - MySQL Download: https://dev.mysql.com/downloads/mysql/
  - MySQL Installation Guide: https://dev.mysql.com/doc/refman/8.0/en/installing.html
  - Expected installation directory:
    - Windows: `C:\Program Files\MySQL\MySQL Server 8.0\` (default)
    - macOS: `/usr/local/mysql/` (via Homebrew) or `/Applications/MySQL/`
    - Linux: `/usr/bin/mysql` (via package manager)

### Python Libraries and Dependencies

All dependencies are listed in `requirements.txt`:

- **Flask 3.0.0** - Web framework
- **PyMySQL 1.1.0** - MySQL database connector
  - Documentation: https://pymysql.readthedocs.io/
- **PyJWT 2.8.0** - JSON Web Token implementation for authentication
  - Documentation: https://pyjwt.readthedocs.io/
- **bcrypt 4.1.2** - Password hashing library
  - Documentation: https://github.com/pyca/bcrypt/
- **python-dotenv 1.0.0** - Environment variable management
  - Documentation: https://pypi.org/project/python-dotenv/
- **xhtml2pdf 0.2.17** - PDF generation from HTML
  - Documentation: https://xhtml2pdf.readthedocs.io/
- **simpleeval 1.0.3** - Safe expression evaluation for invoice calculations
  - Documentation: https://github.com/danthedeckie/simpleeval
- **gunicorn 21.2.0** - Production WSGI HTTP server
  - Documentation: https://gunicorn.org/

### Additional System Dependencies (for PDF generation)

The application uses xhtml2pdf which requires Cairo libraries:

- **Windows**: Cairo libraries are typically bundled with Python packages
- **macOS**: Install via Homebrew: `brew install cairo pango`
- **Linux (Ubuntu/Debian)**: `sudo apt-get install libcairo2 libcairo2-dev libpango1.0-dev libpangocairo-1.0-0 pkg-config`

## Installation and Setup

### Prerequisites

Before you begin, ensure you have the following installed:

1. **Python 3.11 or higher**
   - Verify installation: `python --version` or `python3 --version`
   - Python download page: https://www.python.org/downloads/

2. **MySQL Server 8.0 or higher**
   - Verify installation: `mysql --version`
   - MySQL download page: https://dev.mysql.com/downloads/mysql/

3. **Git** (for cloning the repository)
   - Download: https://git-scm.com/downloads

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd DocuMint
```

### Step 2: Set Up Python Virtual Environment

It's recommended to use a virtual environment to isolate project dependencies:

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Python Dependencies

With your virtual environment activated, install all required packages:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Set Up MySQL Database

1. **Start MySQL Server**
   - Windows: MySQL should run as a service automatically, or start it from Services
   - macOS: `brew services start mysql` or use MySQL Workbench
   - Linux: `sudo systemctl start mysql` or `sudo service mysql start`

2. **Create the Database**

   Log into MySQL as root:
   ```bash
   mysql -u root -p
   ```

   Then create the database:
   ```sql
   CREATE DATABASE invoice_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   EXIT;
   ```

3. **Initialize Database Schema and Procedures**

   The project includes SQL files that need to be executed:
   - `data_dump.sql` - Creates all database tables, procedures and triggers
   
   **Import SQL files**
   ```bash
   mysql -u root -p invoice_db < data_dump.sql
   ```

### Step 5: Configure Environment Variables

Create a `.env` file in the project root directory with the following variables:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=invoice_db

# Application Security
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET=your-jwt-secret-key-change-in-production

# Flask Environment
FLASK_ENV=development
FLASK_DEBUG=True
```

**Important Security Notes:**
- Replace `your_mysql_password` with your actual MySQL root password
- Generate strong random strings for `SECRET_KEY` and `JWT_SECRET` (you can use Python: `python -c "import secrets; print(secrets.token_hex(32))"`)


## Running the Application

### Development Mode

To run the application in development mode with auto-reload:

```bash
python app.py
```

The application will be available at: `http://localhost:5000`

### Using Docker (Alternative)

If you prefer Docker, the project includes a `Dockerfile`:

```bash
docker build -t documint .
docker run -p 5000:5000 --env-file .env documint
```

## Project Structure

```
DocuMint/
├── app.py                 # Main Flask application entry point
├── auth.py                # Authentication and authorization logic
├── config.py              # Configuration management
├── db.py                  # Database connection and stored procedure wrapper
├── calculations.py        # Invoice calculation engine
├── wsgi.py                # WSGI entry point for production
├── requirements.txt       # Python dependencies
├── schema.sql             # Database schema definitions
├── procedures.sql         # MySQL stored procedures
├── blueprints/            # Flask blueprints (modular routes)
│   ├── auth_bp.py         # Authentication routes
│   ├── dashboard_bp.py    # Dashboard routes
│   ├── invoices_bp.py     # Invoice management routes
│   ├── customers_bp.py    # Customer management routes
│   ├── templates_bp.py    # Template management routes
│   ├── settings_bp.py     # Settings and organization management
│   └── customer_portal_bp.py  # Customer-facing portal
├── templates/             # Jinja2 HTML templates
│   ├── auth/              # Login, registration templates
│   ├── invoices/          # Invoice views and forms
│   ├── customers/         # Customer management templates
│   ├── templates/         # Template management templates
│   └── settings/          # Settings and organization templates
├── static/                # Static assets
│   ├── css/               # Stylesheets
│   └── js/                # JavaScript files
├── scripts/               # Utility scripts
│   ├── setup_database.py  # Database initialization
│   ├── generate_demo_data.py      # Demo data generator
│   └── generate_realistic_data.py  # Realistic data generator
└── Dockerfile             # Docker configuration for deployment
```

## Troubleshooting

### Database Connection Issues

- **Error: "Access denied for user"**
  - Verify MySQL username and password in `.env` file
  - Ensure MySQL user has proper permissions: `GRANT ALL PRIVILEGES ON invoice_db.* TO 'your_user'@'localhost';`

- **Error: "Unknown database 'invoice_db'"**
  - Create the database: `CREATE DATABASE invoice_db;`
  - Or update `DB_NAME` in `.env` to match your database name

### PDF Generation Issues

- **Error: "Cairo library not found"**
  - Install system dependencies (see "Additional System Dependencies" above)
  - On Windows, ensure you're using a compatible Python distribution

### Port Already in Use

- **Error: "Address already in use"**
  - Change the port in `app.py`: `app.run(debug=True, host='0.0.0.0', port=5001)`
  - Or stop the process using port 5000

## Test User Accounts

**TechFlow Organization:**
- `michael.chen@techflow.com` - Owner, password: `demo12345`
- `sarah.martinez@techflow.com` - Member, password: `demo12345`
- `david.kim@techflow.com` - Viewer, password: `demo12345`

**Nexus Organization:**
- `emily.rodriguez@nexus.com` - Owner, password: `demo12345`
- `james.anderson@nexus.com` - Member, password: `demo12345`
- `priya.sharma@nexus.com` - Viewer, password: `demo12345`

### User Roles and Permissions

The system supports three role levels:

1. **Owner**
   - Full access to all features
   - Can create, edit, and delete invoices
   - Can manage invoice templates
   - Can manage organization settings
   - Can add/remove users from organization
   - Can view audit logs

2. **Member**
   - Can create and edit invoices
   - Can view templates
   - Cannot delete invoices
   - Cannot manage templates or organization settings
   - Cannot manage users

3. **Viewer**
   - Read-only access
   - Can view invoices and templates
   - Cannot create, edit, or delete anything

### Testing Different Roles

To test different permission levels:

1. Log in with an owner account to create templates and set up the organization
2. Log in with a member account to test invoice creation and editing
3. Log in with a viewer account to verify read-only restrictions

## Role-Based Access Control (RBAC) Matrix

The following table provides a comprehensive overview of permissions for each role in the DocuMint system:

| Feature / Action | Owner | Member | Viewer | Customer |
|-----------------|:-----:|:------:|:------:|:--------:|
| **Authentication & Access** |
| Login to System | ✅ | ✅ | ✅ | ❌ |
| Login to Customer Portal | ❌ | ❌ | ❌ | ✅ |
| View Dashboard | ✅ | ✅ | ✅ | ✅ (Customer Portal) |
| Switch Organizations | ✅ | ✅ | ✅ | ❌ |
| **Invoice Management** |
| Create Invoice | ✅ | ✅ | ❌ | ❌ |
| Edit Invoice | ✅ | ✅ | ❌ | ❌ |
| Delete Invoice | ✅ | ❌ | ❌ | ❌ |
| View Invoices | ✅ | ✅ | ✅ | ✅ (Own Only) |
| Finalize Invoice | ✅ | ✅ | ❌ | ❌ |
| View Invoice PDF | ✅ | ✅ | ✅ | ✅ (Own Only) |
| Download Invoice PDF | ✅ | ✅ | ✅ | ✅ (Own Only) |
| Update Invoice Status | ✅ | ✅ | ❌ | ❌ |
| **Template Management** |
| Create Template | ✅ | ❌ | ❌ | ❌ |
| Edit Template | ✅ | ❌ | ❌ | ❌ |
| Delete Template | ✅ | ❌ | ❌ | ❌ |
| View Templates | ✅ | ✅ | ✅ | ❌ |
| Archive Template | ✅ | ❌ | ❌ | ❌ |
| Create Template Version | ✅ | ❌ | ❌ | ❌ |
| **Customer Management** |
| Create Customer | ✅ | ❌ | ❌ | ❌ |
| Edit Customer | ✅ | ❌ | ❌ | ❌ |
| Delete Customer | ✅ | ❌ | ❌ | ❌ |
| View Customers | ✅ | ✅ | ✅ | ❌ |
| Archive Customer | ✅ | ❌ | ❌ | ❌ |
| **Organization Management** |
| View Organization Settings | ✅ | ❌ | ❌ | ❌ |
| Edit Organization Details | ✅ | ❌ | ❌ | ❌ |
| Manage Organization Members | ✅ | ❌ | ❌ | ❌ |
| Add Users to Organization | ✅ | ❌ | ❌ | ❌ |
| Remove Users from Organization | ✅ | ❌ | ❌ | ❌ |
| Change User Roles | ✅ | ❌ | ❌ | ❌ |
| View Pending Member Requests | ✅ | ❌ | ❌ | ❌ |
| Approve/Reject Member Requests | ✅ | ❌ | ❌ | ❌ |
| **Audit & Reporting** |
| View Audit Logs | ✅ | ❌ | ❌ | ❌ |
| Export Audit Logs | ✅ | ❌ | ❌ | ❌ |
| View Dashboard Statistics | ✅ | ✅ | ✅ | ❌ |
| View Revenue Reports | ✅ | ✅ | ✅ | ❌ |
| **Customer Portal Features** |
| View Own Invoices | ❌ | ❌ | ❌ | ✅ |
| Filter Own Invoices | ❌ | ❌ | ❌ | ✅ |
| View Invoice Details | ❌ | ❌ | ❌ | ✅ |
| Download Own Invoice PDF | ❌ | ❌ | ❌ | ✅ |

### Permission Legend

- ✅ **Allowed** - User has permission to perform this action
- ❌ **Denied** - User does not have permission to perform this action

### Role Summary

- **Owner**: Full administrative access with all permissions enabled
- **Member**: Can create and edit invoices, view templates and customers, but cannot delete or manage system settings
- **Viewer**: Read-only access to view invoices, templates, and customers
- **Customer**: Limited access to view and download their own invoices through the customer portal
