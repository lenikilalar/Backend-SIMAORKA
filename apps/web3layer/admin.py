from django.contrib import admin
from .models import Web3Contract, UserWallet, OrgPeriod, OrgRoleCatalog, OrgRoleAssignment


@admin.register(Web3Contract)
class Web3ContractAdmin(admin.ModelAdmin):
    list_display = ['contract_type', 'chain', 'address', 'is_active']
    list_filter = ['chain', 'contract_type', 'is_active']


@admin.register(UserWallet)
class UserWalletAdmin(admin.ModelAdmin):
    list_display = ['wallet_address', 'user', 'chain', 'is_verified', 'is_primary']
    list_filter = ['chain', 'is_verified', 'is_primary']


@admin.register(OrgPeriod)
class OrgPeriodAdmin(admin.ModelAdmin):
    list_display = ['organization', 'name', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active']


@admin.register(OrgRoleCatalog)
class OrgRoleCatalogAdmin(admin.ModelAdmin):
    list_display = ['organization', 'role_code', 'role_name']


@admin.register(OrgRoleAssignment)
class OrgRoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ['organization', 'period', 'role', 'wallet_address', 'is_active']
    list_filter = ['is_active', 'organization']
