from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import CustomUserSimpleForm,CustomPasswordChangeForm,NoticeComplianceForm
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from .models import NoticeCompliance, NoticeComplianceTrail
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import ComplianceFormEntryForm, ClientMasterForm,GSTComplianceForm
from .models import ComplianceFormEntry, ClientMaster,GSTComplianceEntry
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

# Only allow staff/superuser to access
def is_superuser(user):
    return user.is_superuser


from django.contrib.auth import logout
from django.shortcuts import redirect

@login_required
def LogoutView(request):
    logout(request)
    return redirect('login')



@login_required
def dashboard(request):
    user_department = request.user.department

    if user_department == 'Admin':
        notices_qs = NoticeCompliance.objects.all()  # Admin sees everything
    elif user_department == 'Accounts':
        notices_qs = NoticeCompliance.objects.filter(billing_status='Billing')
    else:
        notices_qs = NoticeCompliance.objects.filter(department=user_department)  # Others see their department data only

    total_notices = notices_qs.count()
    pending_count = notices_qs.filter(status='Pending').count()
    in_progress_count = notices_qs.filter(status='In Progress').count()
    completed_count = notices_qs.filter(status='Completed').count()

    latest_notices = notices_qs.order_by('-date_of_receipt')[:5]

    return render(request, 'dashboard.html', {
        'total_notices': total_notices,
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'latest_notices': latest_notices,
    })


User = get_user_model()

def add_user(request):

    if not request.user.is_superuser:
        return redirect('/tracker/login/')
    
    edit_user = None
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        if user_id:  # Editing existing user
            edit_user = get_object_or_404(User, id=user_id)
            form = CustomUserSimpleForm(request.POST, instance=edit_user)
            if form.is_valid():
                form.save()
                messages.success(request, 'User updated successfully.')
                return redirect('add_user')
        else:  # Adding new user
            form = CustomUserSimpleForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.set_password('password123')  # Default password
                user.save()
                messages.success(request, 'New user added successfully.')
                return redirect('add_user')
    else:
        user_id = request.GET.get('edit')
        if user_id:
            edit_user = get_object_or_404(User, id=user_id)
            form = CustomUserSimpleForm(instance=edit_user)
        else:
            form = CustomUserSimpleForm()

    users = User.objects.all()
    return render(request, 'add_user.html', {
        'form': form,
        'users': users,
        'edit_user': edit_user
    })



from .models import CustomUser
from .models import CustomUser

@login_required
def delete_user(request, user_id):
    if request.user.department != 'Admin':
        return redirect('dashboard')

    try:
        user = CustomUser.objects.get(id=user_id)
        user.delete()
        messages.success(request, 'User deleted successfully.')
    except CustomUser.DoesNotExist:
        messages.error(request, 'User not found.')

    return redirect('add_user')


@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in after password change
            messages.success(request, 'Your password was updated successfully.')
            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = CustomPasswordChangeForm(user=request.user)
    
    return render(request, 'change_password.html', {'form': form})

def add_notice_compliance(request):
    # if request.user.department not in ['GST', 'Income-tax']:
    #     return HttpResponseForbidden("You do not have permission to add notices.")
    
    if request.method == 'POST':
        form = NoticeComplianceForm(request.POST, user=request.user)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.created_by = request.user
            notice.save()
            return redirect('notice_list')  # Redirect to list or detail view
    else:
        form = NoticeComplianceForm(user=request.user)

    return render(request, 'notice_compliance_form.html', {'form': form,'user_role': request.user.user_role,'user': request.user,})





def notice_list(request):
    if request.user.department == 'Admin':
        notices = NoticeCompliance.objects.all()
    elif request.user.department == 'Accounts':
        notices = NoticeCompliance.objects.filter(billing_status='Billing')
    else:
        notices = NoticeCompliance.objects.filter(department=request.user.department)

    filter_range = range(20)# 18 columns to filter (excluding Actions)
    return render(request, 'notice_compliance_list.html', {
        'notices': notices,
        'filter_range': filter_range
    })


def notice_detail(request, pk):
    notice = get_object_or_404(NoticeCompliance, pk=pk)
    trails = notice.trails.all().order_by('-timestamp')
    return render(request, 'notice_compliance_detail.html', {'notice': notice, 'trails': trails})

def notice_compliance_form(request, notice_id=None):
    # Example: restrict edit to own department unless Admin
    # if request.user.department not in ['GST', 'Income-tax']:
    #     return HttpResponseForbidden("You do not have permission to edit notices.")

    if notice_id:
        notice = get_object_or_404(NoticeCompliance, id=notice_id)
        original_notice = NoticeCompliance.objects.get(id=notice_id)
    else:
        notice = None
        original_notice = None

    form = NoticeComplianceForm(request.POST or None, instance=notice, user=request.user)

    if request.method == 'POST' and form.is_valid():
        instance = form.save(commit=False)
        instance.created_by = request.user
        instance.save()
        messages.success(request, 'Notice Compliance Entry saved successfully.')

        if original_notice:
            tracked_fields = [
                'description_of_work',
                'action_to_be_taken',
                'progress',
                'status',
                'remarks',
                'date_of_task_completion'
            ]

            changes_summary = []

            for field in tracked_fields:
                old_value = getattr(original_notice, field)
                new_value = getattr(instance, field)

                if str(old_value) != str(new_value):
                    changes_summary.append(
                        f"{field.replace('_', ' ').title()}: '{old_value}' ➔ '{new_value}'"
                    )

            if changes_summary:
                NoticeComplianceTrail.objects.create(
                    notice=instance,
                    changed_by=request.user,
                    field_changed="Multiple Fields Updated",
                    previous_value="\n".join(changes_summary),
                    new_value="See Changes Above"
                )

        form.save_m2m()
        messages.success(request, "Notice Compliance saved successfully.")
        return redirect('notice_list')

    return render(request, 'notice_compliance_form.html', {
        'form': form,
        'edit_notice': notice,
    })

# Utility to allow only Admin and Income-tax department
def is_admin_or_income_tax(user):
    return user.is_authenticated and user.department in ['Admin', 'Income-tax']

# Utility to allow only Admin and Income-tax department
def is_admin_or_gst(user):
    return user.is_authenticated and user.department in ['Admin', 'GST']

@login_required
@user_passes_test(is_admin_or_income_tax)
def add_compliance_entry(request):
    form_type = request.GET.get('form_type') or request.POST.get('form_type')

    if request.user.user_role != 'Admin':
        clients = ClientMaster.objects.filter(department = request.user.department)
    else:
        clients = ClientMaster.objects.all()

    if request.method == 'POST':
        form = ComplianceFormEntryForm(request.POST, form_type=form_type, clients=clients)
        print("POST DATA:", request.POST)   # Debug form input
        print("FORM VALID?", form.is_valid())  # Should be False if it fail
        if form.is_valid():
            print("yeah")
            compliance = form.save(commit=False)
            compliance.created_by = request.user
            compliance.save()
            messages.success(request, 'ITR entry saved successfully.')
            print("done")
            
    else:
        form = ComplianceFormEntryForm(initial={'form_type': form_type}, form_type=form_type, clients = clients)

    return render(request, 'compliance_form_entry.html', {
        'form': form,
        'selected_form_type': form_type or '',
    })


# VIEW pages (for all users)
@login_required
def view_compliance_entries(request):
    entries = ComplianceFormEntry.objects.select_related('client').all().order_by('-created_at')

    filter_range = range(9)# 18 columns to filter (excluding Actions)


    return render(request, 'view_compliance_entries.html', {'entries': entries, 'filter_range': filter_range})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import ClientMaster
from .forms import ClientMasterForm

@login_required
def view_clients(request):
    client_id = request.GET.get('edit')
    edit_client = None

    if client_id:
        edit_client = get_object_or_404(ClientMaster, id=client_id)

    if request.method == 'POST':
        # Edit
        if 'client_id' in request.POST:
            client = get_object_or_404(ClientMaster, id=request.POST['client_id'])
            form = ClientMasterForm(request.POST, instance=client, user=request.user)
            if form.is_valid():
                updated_client = form.save(commit=False)
                updated_client.created_by = request.user
                updated_client.save()
                messages.success(request, "Client updated successfully.")
                return redirect('view_clients')
        else:
            # Add new
            form = ClientMasterForm(request.POST, user=request.user)
            if form.is_valid():
                new_client = form.save(commit=False)
                new_client.created_by = request.user
                new_client.save()
                messages.success(request, "New client added successfully.")
                return redirect('view_clients')
    else:
        form = ClientMasterForm(instance=edit_client if edit_client else None, user=request.user)

    clients = ClientMaster.objects.all().order_by('client_name')
    return render(request, 'client_master_form.html', {
        'form': form,
        'clients': clients,
        'edit_client': edit_client
    })


@login_required
def delete_client(request, client_id):
    client = get_object_or_404(ClientMaster, id=client_id)
    client.delete()
    messages.success(request, "Client deleted successfully.")
    return redirect('view_clients')

@login_required
@user_passes_test(is_admin_or_gst)
def add_gst_compliance_entry(request):
    form_type = request.GET.get('form_type') or request.POST.get('form_type')

    if request.user.user_role != 'Admin':
        clients = ClientMaster.objects.filter(department = request.user.department)
    else:
        clients = ClientMaster.objects.all()
    
    if request.method == 'POST':
        form = GSTComplianceForm(request.POST, form_type=form_type, clients = clients)
        print("POST DATA:", request.POST)
        print("FORM VALID?", form.is_valid())
        print("FORM ERRORS:", form.errors)

        if form.is_valid():
            entry = form.save(commit=False)
            entry.created_by = request.user
            entry.save()
            messages.success(request, 'GSTR entry saved successfully.')
            
    else:
        form = GSTComplianceForm(initial={'form_type': form_type}, form_type=form_type, clients= clients)

    return render(request, 'gst_compliance_form.html', {
        'form': form,
        'selected_form_type': form_type
    })



@login_required
@user_passes_test(is_admin_or_gst)
def view_gst_compliance_entries(request):
    entries = GSTComplianceEntry.objects.select_related('client', 'created_by').order_by('-id')

    filter_range = range(7)# 18 columns to filter (excluding Actions)




    return render(request, 'view_gst_compliance_entries.html', {
        'entries': entries,'filter_range': filter_range
    })





from django.http import JsonResponse
from .models import ClientMaster

@login_required
def get_client_nature(request):
    client_id = request.GET.get('client_id')
    try:
        client = ClientMaster.objects.get(id=client_id)
        return JsonResponse({'nature': client.nature_of_client})
    except ClientMaster.DoesNotExist:
        return JsonResponse({'error': 'Client not found'}, status=404)




# views.py
from django.http import JsonResponse
from .models import ClientMaster

def get_clients_by_group(request):
    group_code = request.GET.get('group_code')
    print("Received group code:", group_code)  # ✅ Debug
    clients = ClientMaster.objects.filter(group_code=group_code).order_by('client_name')
    client_list = [
        {"code": c.client_code, "name": c.client_name}
        for c in clients
    ]
    print("Sending clients:", client_list)  # ✅ Debug
    return JsonResponse({"clients": client_list})


