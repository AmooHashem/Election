import uuid

from django.utils import timezone

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField
from .vote_exception import MaxVoteException, ExpireElectionException, VoterPermissionException



# Create your models here.


class Voter(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4(), editable=False, max_length=64)
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    phone_number = PhoneNumberField(unique=True)
    activate_code = models.CharField(max_length=5, blank=True, default='')
    name = models.CharField(max_length=50, blank=True, default='')

    def __str__(self):
        return str(self.name)


class Election(models.Model):
    name = models.CharField(unique=True, blank=False, max_length=50)
    title = models.CharField(max_length=50, unique=True, blank=False)
    voters = models.ManyToManyField(Voter, blank=True)
    max_select = models.IntegerField(default=1)
    expire_time = models.DateTimeField(default=timezone.now())

    def voters_count(self):
        return self.voters.count()

    def voters_list(self):
        voters = ''
        for voter in self.voters.all():
            voters += str(voter) + ', '
        return voters

    def voted_count(self):
        return Vote.objects.filter(candidate__election=self).count()

    def voted_list(self):
        return list(Vote.objects.filter(candidate__election=self).values_list('voter__uuid'))

    def __str__(self):
        return str(self.name) + ' ' + str(self.title)


class Candidate(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    avatar = models.ImageField(upload_to='candidate/', default='candidate/default.png')

    def __str__(self):
        return str(self.name)

    def get_election_title(self):
        return self.election.title

    def get_vote_count(self):
        return Vote.objects.filter(candidate=self).count()

    def get_total_vote_count(self):
        return Vote.objects.filter(candidate__election=self.election).count()


class Vote(models.Model):
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    time = models.DateTimeField(default=timezone.now())

    def get_voter_uuid(self):
        return self.voter.uuid

    def __str__(self):
        return str(self.voter)

    def save(self, *args, **kwargs):
        if Vote.objects.filter(voter=self.voter, candidate__election=self.candidate.election).count() >= \
                self.candidate.election.max_select:
            raise MaxVoteException("Voter vote before that :)")
        elif self.candidate.election.expire_time < timezone.now():
            raise ExpireElectionException("Election Expire before")
        elif self.voter not in self.candidate.election.voters.all():
            raise VoterPermissionException("Voter not in election")
        else:
            super(Vote, self).save(*args, **kwargs)
