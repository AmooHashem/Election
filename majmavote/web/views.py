from itertools import chain
from random import randint

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from django.utils import timezone


# Create your views here.
from django.views import View

from .models import Voter, Election, Candidate, Vote
from .sms import Sms


def index(request):
    if request.user.is_authenticated:
        return ElectionView.as_view()(request)
    return render(request, 'index.html')


def logout_view(request):
    logout(request)
    return redirect('/')


class Verification(View):

    def get(self, request):
        return render(request, 'phone_number_form.html')

    def post(self, request):
        if not check_mobile_format(str(request.POST['phone_number'])):
            context = {'error': 'لطفا فرمت شماره تلفن همراه خود را رعاییت کنید.برای مثال به صورت 9131234567'}
            return render(request, 'phone_number_form.html', context)
        phone = '+98'
        phone += str(request.POST['phone_number'])
        try:
            voter = Voter.objects.get(phone_number=phone)
        except Voter.DoesNotExist:
            context = {'error': 'شماره شما در لیست رای‌دهندگان پیدا نشد.'}
            return render(request, 'phone_number_form.html', context)
        activate_code = ''.join(["{}".format(randint(0, 9)) for num in range(0, 5)])
        voter.activate_code = activate_code
        user = voter.user
        user.set_password(activate_code)
        user.save()
        voter.save()
        Sms.execute(phone, activate_code)
        context = {'phone': phone}
        return render(request, 'verification_code.html', context)


class Login(View):

    def post(self, request):
        phone = str(request.POST['phone_number'])
        code = str(request.POST['code'])
        try:
            voter = Voter.objects.get(phone_number=phone)
        except Voter.DoesNotExist:
            context = {'error': 'شماره شما در لیست رای‌دهندگان پیدا نشد.'}
            return render(request, 'phone_number_form.html', context)
        context = {}
        if voter and voter.activate_code == code:
            user = authenticate(request, username=voter.user.username, password=code)
            login(request, user)
            return redirect('/')
        context['phone'] = phone
        context['error'] = 'کد تایید برای شماره وارد شده اشتباه میباشد.'
        return render(request, 'verification_code.html', context)


def check_mobile_format(mobile):
    if not mobile or mobile[0] != '9' or len(mobile) != 10 or not mobile.isnumeric():
        return False
    return True


class ElectionView(View):

    def get(self, request):
        elections_obj = Election.objects.all()
        voter = Voter.objects.get(user=request.user)
        elections = []
        for election in elections_obj:
            voters_list = list(election.voters.all())
            candidates = Candidate.objects.filter(election=election)
            el_dict = {'name': election.name,
                       'id': election.id,
                       'title': election.title,
                       'expire_time': int(election.expire_time.timestamp()*1000),
                       'voters_count': len(voters_list),
                       'can_vote': True if voter in voters_list else False,
                       'is_expire': True if election.expire_time < timezone.now() else False,
                       'is_voted': Vote.objects.filter(voter=voter, candidate__election=election).count() >= election.max_select,
                       'candidates': candidates
                       }
            elections.append(el_dict)
        context = {'elections': elections}
        return render(request, 'elections.html', context)


def check_can_vote(voter, election):
    voters_list = list(election.voters.all())
    can_vote = True if voter in voters_list else False
    is_expire = True if election.expire_time < timezone.now() else False
    voted_count = Vote.objects.filter(voter=voter, candidate__election=election).count()
    if not can_vote or is_expire or voted_count >= election.max_select:
        return False
    return True


class VoteView(View):

    def get(self, request, ids):
        try:
            election = Election.objects.get(id=ids)
        except Election.DoesNotExist:
            return ElectionView.as_view()(request)
        voter = Voter.objects.get(user=request.user)
        if not check_can_vote(voter, election):
            return ElectionView.as_view()(request)
        candidates = Candidate.objects.filter(election=election)
        context = {'name': election.name,
                   'id': election.id,
                   'title': election.title,
                   'expire_time': int(election.expire_time.timestamp() * 1000),
                   'candidates': candidates
                   }
        return render(request, 'vote.html', context)
