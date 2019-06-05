from django.conf import settings
from django.contrib.messages import constants

from base.utils import render_exception
from base.transaction import Transaction, ReadonlyTransaction
from base.models import User, Actor


class _Http500Exception(Exception):
    pass


class _NeedsRollbackException(Exception):
    pass


class TransactionMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 기존 로그인/체크인 정보 복원
        session, usk, ask = (request.session, settings.USER_SESSION_KEY, settings.ACTOR_SESSION_KEY)
        try:
            user = User.objects.get(id=session[usk]) if usk in session else None
            actor = Actor.objects.get(id=session[ask]) if ask in session else None
        except:
            user = None
            actor = None

        # api 호출
        tran_cls = ReadonlyTransaction if request.method == "GET" else Transaction
        try:
            with tran_cls(checkin_actor=actor, login_user=user) as tran:
                res = self.get_response(request)
                if getattr(request, "need_rollback", False):
                    raise _NeedsRollbackException
                elif res.status_code >= 500:
                    raise _Http500Exception
                for m in request._messages:
                    if m.level == constants.ERROR:
                        res.status_code = 400
        except _Http500Exception:
            pass
        except _NeedsRollbackException:
            pass
        except Exception as e:
            res = render_exception(request, e, 500)

        # 바뀐 로그인/체크인 정보 변경
        after_user, after_actor = tran.login_user, tran.checkin_actor
        if user != after_user:
            session[usk] = after_user.id if after_user else None
        if actor != after_actor:
            session[ask] = after_actor.id if after_actor else None

        return res
