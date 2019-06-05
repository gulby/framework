from django.conf.urls import url
from human.views import email_login, email_send, auth_email, id_password_login


urlpatterns = [
    url(r"^login/$", email_login, name="login"),
    url(r"^email_send/$", email_send, name="email_send"),
    url(r"^auth_email/$", auth_email, name="auth_email"),
    url(r"^id_password_login/$", id_password_login, name="id_password_login"),
]
