# config/db_config.example.py
# Copy this file to db_config.py and fill in your credentials

DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "YOUR_PASSWORD_HERE",
    "db":       "bioagent_db",
    "charset":  "utf8mb4",
}

# Roles allowed to manage dropdown options
MANAGE_ROLES = ['admin', 'lab_manager', 'PI']

# Default options (fallback if DB is empty)
DEFAULT_DOMAINS = [
    'flu_bnab', 'noncoding_dna',
    'antibiotic_resistance', 'oncology', 'general'
]
DEFAULT_GRANTS = [
    'CIHR', 'NSERC', 'MITACS', 'Génome Québec', 'FRQS'
]
DEFAULT_ROLES = [
    'researcher', 'lab_manager', 'admin', 'PI'
]