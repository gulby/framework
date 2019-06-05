from django.http import HttpResponse
from django.shortcuts import render

from base.transaction import TransactionManager
from base.types import Type
from human.models import Email, LoginID


def email_login(request):
    return render(request, "human/email_login.html")


def email_send(request):
    email = Email.objects.get(uname=request.POST["email_address"])
    email.prepare()
    return render(request, "human/email_otp_send.html", {"email_id": email.id})


def auth_email(request):
    email = Email.objects.get(id=request.POST["email_id"])
    human_token = email.authenticate(request.POST.get("otp"))
    return HttpResponse(human_token)


def id_password_login(request):
    tran = TransactionManager.get_transaction()
    if request.method == "POST":
        login_id = LoginID.objects.get(login_id=request.POST.get("login_id", ""))
        password = request.POST.get("password", "")
        human = login_id.authenticate(password)
        human.checkin(Type.TaxAccountant)
    return render(
        request, "human/id_password_login.html", {"login_user": tran.login_user, "checkin_actor": tran.checkin_actor}
    )
