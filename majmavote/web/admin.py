from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import *
# Register your models here.


class VoterAdmin(ModelAdmin):
    list_display = ('user_id', 'name', 'user', 'phone_number', 'activate_code', 'uuid')
    list_editable = ('name', 'phone_number')


class ElectionAdmin(ModelAdmin):
    list_display = ('id', 'name', 'title', 'voters_count', 'voters_list', 'voted_count', 'voted_list')
    list_editable = ('name', 'title')


class CandidateAdmin(ModelAdmin):
    list_display = ('name', 'get_election_title', 'get_vote_count', 'get_total_vote_count')


class VoteAdmin(ModelAdmin):
    list_display = ('get_voter_uuid', 'candidate')


admin.site.register(Voter, VoterAdmin)
admin.site.register(Election, ElectionAdmin)
admin.site.register(Vote, VoteAdmin)
admin.site.register(Candidate, CandidateAdmin)

