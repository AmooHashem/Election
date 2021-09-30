import uuid
from itertools import chain
from random import randint

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.db.models import Count


from django.utils import timezone
import xlrd



# Create your views here.
from django.views import View

from .models import Voter, Election, Candidate, Vote
from .sms import Sms
from .vote_exception import MaxVoteException, ExpireElectionException, VoterPermissionException


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
            context = {'error': 'شماره شما در لیست رای‌دهندگان پیدا نشد.در صورتی که از اعضا رسمی هستید با مدیر مجمع تماس حاصل فرمایید'}
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
                       'is_voted': Vote.objects.filter(voter=voter, candidate__election=election).exists(),
                       'candidates': candidates
                       }
            elections.append(el_dict)
        context = {'elections': elections}
        return render(request, 'elections.html', context)


def check_can_vote(voter, election):
    voters_list = list(election.voters.all())
    can_vote = True if voter in voters_list else False
    is_expire = True if election.expire_time < timezone.now() else False
    is_voted = Vote.objects.filter(voter=voter, candidate__election=election).exists()
    if not can_vote or is_expire or is_voted:
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
                   'max_vote': election.max_select,
                   'title': election.title,
                   'expire_time': int(election.expire_time.timestamp() * 1000),
                   'candidates': candidates
                   }
        return render(request, 'vote.html', context)

    def post(self, request, ids):
        voted_list = request.POST.getlist('voted_candidate')
        if len(voted_list) > Election.objects.get(id=ids).max_select:
            context = {'error': 'تعداد کاندید‌های انتخابی بیشتر از حدمجاز است'}
            return render(request, 'vote_response.html', context)
        voter = Voter.objects.get(user=request.user)
        if Vote.objects.filter(voter=voter, candidate__election__id=ids).exists():
            context = {'error': 'شما قبلا رای داده‌اید'}
            return render(request, 'vote_response.html', context)
        for candidate_id in voted_list:
            candidate = Candidate.objects.get(id=candidate_id)
            vote = Vote(voter=voter, candidate=candidate)
            try:
                vote.save()
                context = {'uuid': vote.get_voter_uuid(), 'candidate': candidate.name}
            except MaxVoteException:
                context = {'error': 'شما قبلا رای داده‌اید'}
            except ExpireElectionException:
                context = {'error': 'مهلت رای گیری تمام شده است'}
            except VoterPermissionException:
                context = {'error': 'شما اجازه رای دادن ندارید'}
        return render(request, 'vote_response.html', context)


class ResultView(View):

    def get(self, request, ids):
        try:
            election = Election.objects.get(id=ids)
        except Election.DoesNotExist:
            return ElectionView.as_view()(request)
        votes = Vote.objects.filter(candidate__election=election)
        voted_list = {}
        for vote in votes:
            if vote.get_voter_uuid() in voted_list:
                voted_list[vote.get_voter_uuid()].append(vote.candidate.name)
            else:
                voted_list[vote.get_voter_uuid()] = []
                voted_list[vote.get_voter_uuid()].append(vote.candidate.name)
        not_voted_list = []
        for voter in election.voters.all():
            if not Vote.objects.filter(candidate__election=election, voter=voter).exists():
                not_voted_list.append(voter)
        total_vote = Vote.objects.filter(candidate__election=election).values('voter')\
            .annotate(Count('voter', distinct=True))
        candidates = Candidate.objects.filter(election=election)
        candidate_result = []
        for candidate in candidates:
            candidate_result.append({'name': candidate.name, 'vote_count': candidate.get_vote_count()})
        context = {'voted_list': voted_list, 'not_voted_list': not_voted_list, 'election': election,
                   'total_vote': len(total_vote), 'candidate_result': candidate_result}
        return render(request, 'vote_result.html', context)


class RegisterView(View):

    def get(self, request):
        elections = Election.objects.all()
        context = {'elections': elections}
        return render(request, 'register.html', context)

    def post(self, request):
        file = request.FILES['file']
        book = xlrd.open_workbook(file_contents=file.read())
        sheet = book.sheet_by_index(0)
        voters = []
        election = Election.objects.get(id=request.POST['election'])
        for i in range(sheet.nrows):
            name = sheet.cell_value(i, 1)
            phone = '+98' + str(int(sheet.cell_value(i, 0)))
            print(phone)
            if not Voter.objects.filter(phone_number=phone).exists():
                user = User(username=phone)
                user.set_password(phone)
                user.save()
                voter = Voter(user=user, phone_number=phone, name=name)
                voter.uuid = uuid.uuid4()
                voter.save()
                voters.append(voter)
                election.voters.add(voter)
                election.save()
            else:
                voter = Voter.objects.get(phone_number=phone)
                election.voters.add(voter)
                election.save()
        elections = Election.objects.all()
        context = {'elections': elections, 'voters': voters}
        return render(request, 'register.html', context)
