from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='login.html'), name='logout'),


    path('dashboard/', views.dashboard, name='dashboard'),

    path('add_user/', views.add_user, name='add_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('change-password/', views.change_password, name='change_password'),

    path('notices/', views.notice_list, name='notice_list'),
    path('notices/add/', views.add_notice_compliance, name='add_notice_compliance'),
    path('notice/<int:notice_id>/edit/', views.notice_compliance_form, name='notice_edit'),
    path('notices/<int:pk>/', views.notice_detail, name='notice_detail'),

    path('add-compliance/', views.add_compliance_entry, name='add_compliance'),
    path('compliance-entries/', views.view_compliance_entries, name='view_compliance_entries'),


    path('view_clients/', views.view_clients, name='view_clients'),
    path('delete-client/<int:client_id>/', views.delete_client, name='delete_client'),

    path('gst/add/', views.add_gst_compliance_entry, name='add_gst_compliance_entry'),
    path('gst/view/', views.view_gst_compliance_entries, name='view_gst_entries'),

    path('get-client-nature/', views.get_client_nature, name='get_client_nature'),

    # urls.py
    path('ajax/get-clients/', views.get_clients_by_group, name='get_clients_by_group'),

    path('compose/', views.compose_email, name='compose_mail'),
    #path('sent/', views.sent_mails, name='sent_mails'),


]
