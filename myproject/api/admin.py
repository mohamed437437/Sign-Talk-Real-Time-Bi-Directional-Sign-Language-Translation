from django.contrib import admin
from .models import Sign

@admin.register(Sign)
class SignAdmin(admin.ModelAdmin):
    list_display = ('id','label','hand','created_at')
    search_fields = ('label',)
    list_filter = ('hand',)
