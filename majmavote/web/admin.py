from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import *
# Register your models here.


class VoterAdmin(ModelAdmin):
    list_display = ('user_id', 'name', 'user', 'phone_number', 'activate_code', 'uuid')
    list_editable = ('name', 'phone_number')


class ElectionAdmin(ModelAdmin):
    list_display = ('id', 'name', 'title', 'voters_count', 'voters_list')
    list_editable = ('name', 'title')


admin.site.register(Voter, VoterAdmin)
admin.site.register(Election, ElectionAdmin)
admin.site.register(Vote)
admin.site.register(Candidate)

