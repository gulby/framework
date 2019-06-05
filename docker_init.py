import os


def init_db():
    from django.contrib.auth import get_user_model
    from django.conf import settings
    from base.utils import console_log

    User = get_user_model()
    admin = User.objects.filter(username="admin").order_by("-id").first()
    if admin is None:
        admin = User()
        admin.username = "admin"
        admin.set_password(settings.PASSWORD)
        admin.is_superuser = True
        admin.is_staff = True
        admin.save()
        console_log("admin created")
    else:
        console_log("admin already created. so passed")
        return False

    from base.transaction import Transaction
    from server.specs.spec_db_initialize import InitializeDBSpec
    from django.db import IntegrityError

    try:
        with Transaction():
            InitializeDBSpec().setUp()
    except IntegrityError:
        console_log("InitializeDBSpec already called. so passed")
        return False

    return True


if __name__ == "__main__":
    DEPLOYMENT_LEVEL = os.environ.setdefault("DEPLOYMENT_LEVEL", "development")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings_{dlevel}".format(dlevel=DEPLOYMENT_LEVEL))
    import django

    django.setup()
    # TODO : DB 초기화가 된 경우에는 아예 호출되지 않도록 수정
    init_db()
