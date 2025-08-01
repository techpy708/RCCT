import os

def normalize_department(dept):
    """
    Converts 'Income-Tax' or 'Income Tax' to 'INCOME_TAX'
    """
    return dept.strip().upper().replace('-', '_').replace(' ', '_')

def get_email_credentials(department):
    normalized = normalize_department(department)
    email = os.getenv(f"{normalized}_EMAIL")
    password = os.getenv(f"{normalized}_PASSWORD")
    if not email or not password:
        raise ValueError(f"Missing credentials for department: {department}")
    return email, password
