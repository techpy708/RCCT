from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import SetPasswordForm
from .models import CustomUser,NoticeCompliance,ClientMaster,ComplianceFormEntry,GSTComplianceEntry
import datetime

class CustomUserSimpleForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'department','user_role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class CustomPasswordChangeForm(SetPasswordForm):
    # You can customize labels, widgets, etc. here if needed.
    old_password = forms.CharField(
        label="Old Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

def generate_financial_year_choices(start_year=2023, years_ahead=25):
    current_year = datetime.date.today().year
    end_year = current_year + years_ahead
    choices = []

    for year in range(start_year, end_year):
        next_year = year + 1
        label = f"{year}-{str(next_year)[-2:]}"
        choices.append((label, label))

    return choices


class NoticeComplianceForm(forms.ModelForm):
    financial_year = forms.ChoiceField(choices=generate_financial_year_choices())
    client_selection = forms.ChoiceField(label="Client", choices=[])
    group_selection = forms.ChoiceField(label="group_code", choices=[])

    class Meta:
        model = NoticeCompliance
        exclude = ['created_by', 'client_code', 'name_of_client']
        widgets = {
            'date_of_receipt': forms.DateInput(attrs={'type': 'date'}),
            'action_date': forms.DateInput(attrs={'type': 'date'}),
            'status_date':forms.DateInput(attrs={'type': 'date'}),
            'date_of_task_completion':forms.DateInput(attrs={'type': 'date'}),
            
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        

        # Populate client dropdown
        # self.fields['client_selection'].choices = [
        #     (f"{c.client_code}|||{c.client_name}", f"{c.client_code} - {c.client_name}")
        #     for c in ClientMaster.objects.all().order_by('client_name')
        # ]


        if user and user.department in ['Admin', 'Accounts']:
            # Admin or Accounts department: show all clients
            #client_queryset = ClientMaster.objects.all()
            group_queryset = ClientMaster.objects.all().distinct('group_code')

        elif user and user.department:
            # Other departments: filter clients by user's department
            #client_queryset = ClientMaster.objects.filter(department=[user.department])
            group_queryset = ClientMaster.objects.filter(department=[user.department]).distinct('group_code')
        else:
            # No user or no department: show none
            #client_queryset = ClientMaster.objects.none()
            group_queryset = ClientMaster.objects.none()

        # self.fields['client_selection'].choices = [
        #     (f"{c.client_code}|||{c.client_name}", f"{c.client_code} - {c.client_name}")
        #     for c in client_queryset.order_by('client_name')
        # ]

        # if self.instance and self.instance.pk:
        #     combined_value = f"{self.instance.client_code}|||{self.instance.name_of_client}"
        #     self.fields['client_selection'].initial = combined_value



        self.fields['group_selection'].choices = [('', '---------')] + [
            (c.group_code, c.group_code)
            for c in group_queryset.order_by('group_code')
        ]


        #client_queryset = ClientMaster.objects.none()
        group_queryset = ClientMaster.objects.none()

        # Keep rest of your existing logic
        if user:

            
            self.fields['department'].initial = user.department

            allowed_departments = ['Admin', 'Accounts']
            user_dept = user.department.name if hasattr(user.department, 'name') else str(user.department)

            if not user.is_superuser and user_dept not in allowed_departments:
                for field in ['billing_amount', 'bill_no','billing_status']:
                    if field in self.fields:
                        del self.fields[field]

        for field_name, field in self.fields.items():
            css_class = "form-control"
            
            
            if field_name in ['description_of_work', 'action_to_be_taken', 'progress', 'remarks']:
                field.widget = forms.TextInput(attrs={'class': css_class})
            else:
                field.widget.attrs.update({'class': css_class})

    def save(self, commit=True):
        instance = super().save(commit=False)
        client_val = self.cleaned_data.get('client_selection')
        if client_val:
            client_code, client_name = client_val.split("|||")
            instance.client_code = client_code
            instance.name_of_client = client_name
        if commit:
            instance.save()
        return instance


from django import forms
from .models import ComplianceFormEntry
from multiselectfield import MultiSelectFormField



class ClientMasterForm(forms.ModelForm):
    department = MultiSelectFormField(choices=CustomUser.DEPARTMENT_CHOICES)

    class Meta:
        model = ClientMaster
        fields = ['client_code', 'client_name', 'nature_of_client', 'department','group_code','phone_number','email']

    def __init__(self, *args, **kwargs):
        self.show_department_field = True  # default
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            if user.department == 'Admin':
                self.fields['department'].choices = CustomUser.DEPARTMENT_CHOICES
            else:
                self.fields['department'].choices = [(user.department, user.department)]
                self.fields['department'].initial = [user.department]
                self.fields['department'].widget = forms.MultipleHiddenInput()
                self.show_department_field = False

        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

import datetime

def generate_financial_year_choices_itr(years_ahead=25):
    current_year = datetime.date.today().year
    start_year = current_year - 1
    end_year = current_year + years_ahead

    choices = []
    for year in range(start_year, end_year):
        next_year = year + 1
        label = f"{year}-{str(next_year)[-2:]}"  # e.g., 2024-25
        choices.append((label, label))
    return choices


def generate_financial_quarters_with_year(years_ahead=5):
    current_year = datetime.date.today().year
    start = current_year - 1
    end = current_year + years_ahead

    quarters = []
    for y in range(start, end):
        quarters.extend([
            (f"April–June {y}", f"April–June {y}"),
            (f"July–September {y}", f"July–September {y}"),
            (f"October–December {y}", f"October–December {y}"),
            (f"January–March {y+1}", f"January–March {y+1}")
        ])
    return quarters


class ComplianceFormEntryForm(forms.ModelForm):
    form_type = forms.CharField(widget=forms.HiddenInput())
    year = forms.ChoiceField(choices=generate_financial_year_choices_itr())
    quarter = forms.ChoiceField(choices=generate_financial_quarters_with_year())
    

    class Meta:
        model = ComplianceFormEntry
        fields = ['form_type', 'client', 'nature', 'year', 'asy','quarter', 'date', 'remarks']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.TextInput(attrs={'placeholder': 'Enter remarks'}),  # Textbox instead of Textarea
        }

    def __init__(self, *args, form_type=None, clients = None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if clients is not None:
            self.fields['client'].queryset = clients



        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

        if 'nature' in self.fields:
            self.fields['nature'].widget.attrs['readonly'] = True  # ← disable manual edit


        if not form_type:
            form_type = kwargs.get('data', {}).get('form_type') or getattr(self.instance, 'form_type', None)
        self.fields['year'].required = False
        self.fields['quarter'].required = False
        if form_type == 'ITR':
            self.fields['quarter'].widget = forms.HiddenInput()
            self.fields['year'].required = True
        elif form_type == 'TDS Return':
            self.fields['year'].widget = forms.HiddenInput()
            self.fields['quarter'].required = True
        else:
            self.fields['year'].widget = forms.HiddenInput()
            self.fields['quarter'].widget = forms.HiddenInput()



import datetime
from django import forms
from .models import GSTComplianceEntry

def generate_financial_year_choices():
    current_year = datetime.date.today().year
    return [(f"{y}-{y+1}", f"{y}-{y+1}") for y in range(current_year - 5, current_year + 1)]



import calendar

def get_month_choices_with_year(years_ahead=1):
    current_year = datetime.date.today().year
    current_month = datetime.date.today().month
    choices = []

    for year in range(current_year - 1, current_year + years_ahead + 1):
        for month_num in range(1, 13):
            month_name = calendar.month_name[month_num]
            label = f"{month_name} {year}"
            value = label  # You could customize this format if needed
            choices.append((value, label))

    return choices


class GSTComplianceForm(forms.ModelForm):
    FORM_CHOICES = [
        ('GSTR 1', 'GSTR 1'),
        ('GSTR 3B', 'GSTR 3B'),
        ('GSTR 9', 'GSTR 9'),
        ('GSTR 9C', 'GSTR 9C'),
    ]

    form_type = forms.ChoiceField(choices=FORM_CHOICES)
    year = forms.ChoiceField(choices=generate_financial_year_choices(), required=False)
    month = forms.ChoiceField(choices=get_month_choices_with_year(), required=False)

    class Meta:
        model = GSTComplianceEntry
        fields = ['form_type', 'client', 'nature', 'year', 'month','date', 'remarks']
        widgets = {
            'remarks': forms.TextInput(attrs={'placeholder': 'Enter remarks'}),
           
            'date': forms.DateInput(attrs={'type': 'date'}),
          
        }

    def __init__(self, *args, clients = None, **kwargs):
        form_type = kwargs.pop('form_type', None)
        super().__init__(*args, **kwargs)

        if clients is not None:
            self.fields['client'].queryset = clients


        # Add Bootstrap styling
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

        # Determine form_type from POST data or initial
        if not form_type:
            form_type = self.data.get('form_type') or self.initial.get('form_type') or getattr(self.instance, 'form_type', None)

        if 'nature' in self.fields:
            self.fields['nature'].widget.attrs['readonly'] = True  # ← disable manual edit

        
        # Hide both fields by default
        self.fields['month'].widget = forms.HiddenInput()
        self.fields['year'].widget = forms.HiddenInput()

        # Show only the appropriate one
        if form_type in ['GSTR 1', 'GSTR 3B']:
            self.fields['month'].widget = forms.Select(choices=get_month_choices_with_year(), attrs={'class': 'form-control'})
        elif form_type in ['GSTR 9', 'GSTR 9C']:
            self.fields['year'].widget = forms.Select(choices=generate_financial_year_choices(), attrs={'class': 'form-control'})
