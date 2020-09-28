import uuid

from django.utils import timezone

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField
from .vote_exception import MaxVoteException, ExpireElectionException


# Create your models here.


class Voter(models.Model):
    uuid = models.CharField(default=uuid.uuid4().hex[:12], editable=False, max_length=64)
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

    def __str__(self):
        return str(self.name) + ' ' + str(self.title)


class Candidate(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    avatar = models.ImageField()


class Vote(models.Model):
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if Vote.objects.filter(voter=self.voter, candidate=self.candidate).count() >= self.candidate.election.max_select:
            raise MaxVoteException("Voter vote before that :)")
        if self.candidate.election.expire_time < timezone.now():
            raise ExpireElectionException("Election Expire before")
        else:
            super(Vote, self).save(*args, **kwargs)
