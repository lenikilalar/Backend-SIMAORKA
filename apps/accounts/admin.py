from django.contrib import admin
from .models import User, StudentProfile

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_staff', 'is_active', 'created_at')
    search_fields = ('email', 'google_sub')
    list_filter = ('is_staff', 'is_active')

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'nim', 'full_name', 'major', 'entry_year')
    search_fields = ('nim', 'full_name', 'user__email')
    list_filter = ('faculty', 'major', 'entry_year')
