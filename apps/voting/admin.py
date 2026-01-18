from django.contrib import admin
from .models import Vote, VoteCast


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'organization', 'type', 'status', 'start_at', 'end_at']
    list_filter = ['status', 'type']
    search_fields = ['title']


@admin.register(VoteCast)
class VoteCastAdmin(admin.ModelAdmin):
    list_display = ['vote', 'wallet_address', 'option_index', 'weight', 'cast_at']
