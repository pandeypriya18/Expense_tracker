
from django.contrib import admin
from account.models import MyUser

@admin.register(MyUser)
class MyUserAdmin(admin.ModelAdmin):
    list_display = [ 'username','role','is_staff','email','is_active']
    list_filter = ['role',]
    search_fields = ['username','email','role']
