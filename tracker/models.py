# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    DEPARTMENT_CHOICES = [
        ('GST', 'GST'),
        ('Income-tax', 'Income-tax'),
        ('Accounts', 'Accounts'),
        ('Admin', 'Admin'),
    ]

    USER_ROLE_CHOICES = [
        ('Executive', 'Executive'),
        ('Manager', 'Manager'),
        ('Admin', 'Admin'),
    ]

    department = models.CharField(
        max_length=100,
        choices=DEPARTMENT_CHOICES,
        blank=True,
        null=True
    )

    user_role = models.CharField(
        max_length=50,
        choices=USER_ROLE_CHOICES,
        default='Executive'
    )

    def __str__(self):
        return self.username



DEPARTMENT_CHOICE = [('GST','GST'),
                     ('Income-tax', 'Income-tax')]



STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('In Progress', 'In Progress'),
    ('Completed', 'Completed'),
]
BILLING_STATUS_CHOICES = [
    ('Billing', 'Billing'),
    ('Non Billing', 'Non Billing'),
]

class NoticeCompliance(models.Model):
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICE) 
    date_of_receipt = models.DateField()
    mode_of_receipt = models.CharField(max_length=100)
    client_code = models.CharField(max_length=100)
    group_code = models.CharField(max_length=100)
    name_of_client = models.CharField(max_length=255)
    financial_year = models.CharField(max_length=10)
    description_of_work = models.TextField()
    action_to_be_taken = models.TextField()
    action_date = models.DateField(blank=True, null=True)
    progress = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    status_date = models.DateField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    date_of_task_completion = models.DateField(blank=True, null=True)
    
    billing_status = models.CharField(
        max_length=100, 
        choices=BILLING_STATUS_CHOICES, 
        blank=True, 
        null=True
    )
    
    billing_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    bill_no = models.CharField(max_length=100, blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='notice_created'
    )

    def __str__(self):
        return f"{self.client_code} - {self.name_of_client}"

class NoticeComplianceTrail(models.Model):
    notice = models.ForeignKey(NoticeCompliance, on_delete=models.CASCADE, related_name='trails')
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    field_changed = models.CharField(max_length=100)
    previous_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.notice.client_code} - {self.field_changed} changed on {self.timestamp}"

from multiselectfield import MultiSelectField

from django.db import models
from django.conf import settings
from multiselectfield import MultiSelectField

class ClientMaster(models.Model):
    DEPARTMENT_CHOICES = CustomUser.DEPARTMENT_CHOICES  # or define it locally

    client_code = models.CharField(max_length=100)
    client_name = models.CharField(max_length=255)
    group_code = models.CharField(max_length=100, blank=True, null=True)  # ✅ New
    email = models.EmailField(max_length=255, blank=True, null=True)       # ✅ New
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # ✅ New
    nature_of_client = models.CharField(max_length=255, blank=True, null=True)
    department = MultiSelectField(choices=DEPARTMENT_CHOICES)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clients_created'
    )

    def __str__(self):
        return f"{self.client_name} ({self.client_code})"

    def display_departments(self):
        return ', '.join(self.department) if self.department else ''

    
FORM_TYPE_CHOICES = [
    ('ITR', 'ITR'),
    ('TDS Return', 'TDS Return'),
]


class ComplianceFormEntry(models.Model):
    form_type = models.CharField(max_length=20, choices=FORM_TYPE_CHOICES)
    client = models.ForeignKey(ClientMaster, on_delete=models.CASCADE)
    nature = models.CharField(max_length=255)
    year = models.CharField(max_length=10, blank=True, null=True)  # for ITR
    asy = models.CharField(max_length=10, blank=True, null=True)  # for assessment_year 
    quarter = models.CharField(max_length=30, blank=True, null=True)  # for TDS (dynamic)
    date = models.DateField()
    remarks = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'itr_tds_compliance_entries'

    def __str__(self):
        return f"{self.form_type} - {self.client.client_name}"

class GSTComplianceEntry(models.Model):
    FORM_TYPE_CHOICES = [
        ('GSTR 1', 'GSTR 1'),
        ('GSTR 3B', 'GSTR 3B'),
        ('GSTR 9', 'GSTR 9'),
        ('GSTR 9C', 'GSTR 9C'),
    ]

    form_type = models.CharField(max_length=20, choices=FORM_TYPE_CHOICES)
    client = models.ForeignKey(ClientMaster, on_delete=models.CASCADE)
    nature = models.CharField(max_length=255)
    year = models.CharField(max_length=9, blank=True, null=True)
    month = models.CharField(max_length=20, blank=True, null=True)
    date = models.DateField()
    remarks = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

