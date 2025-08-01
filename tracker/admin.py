from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    # Add department field to admin forms
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('department',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('department',)}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
