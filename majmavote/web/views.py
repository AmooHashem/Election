from random import randint

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

# Create your views here.
from django.views import View

from .models import Voter
from .sms import Sms


def index(request):
    if request.user.is_authenticated:
        return render(request, 'elections.html')
    return render(request, 'index.html')


class Verification(View):

    def get(self, request):
        return render(request, 'phone_number_form.html')

    def post(self, request):
        phone = '+98'
        phone += str(request.POST['phone_number'])
        voter = Voter.objects.get(phone_number=phone)
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
        voter = Voter.objects.get(phone_number=phone)
        context = {}
        if voter and voter.activate_code == code:
            user = authenticate(request, username=voter.user.username, password=code)
            login(request, user)
            return redirect('')
        return render(request, 'verification_code.html', context)


