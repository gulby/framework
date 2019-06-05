from base.models.model import Model
from base.descriptors import ReverseForeignKeySubfield
from base.types import Type
from base.transaction import TransactionManager
from base.exceptions import CheckinException


# 장고 유저 (인증 단위) 에 대응됨
# Human, Machine 등이 될 수 있음
class User(Model):
    class Meta:
        proxy = True

    # relational subfields
    elements = ReverseForeignKeySubfield("computed", Type.Actor, "container", alias="actors")

    def checkin(self, actor_type):
        if not isinstance(actor_type, Type):
            assert issubclass(actor_type, Actor)
            actor_type = actor_type.my_type
        actor = self.actors.filter(type=actor_type).order_by("-id").first()
        if not actor:
            raise CheckinException("{} 권한이 없습니다.".format(actor_type.name))
        tran = TransactionManager.get_transaction()
        tran.checkin(actor)
        return actor

    def logout(self):
        tran = TransactionManager.get_transaction()
        assert tran.login_user == self
        tran.logout()


class Actor(Model):
    class Meta:
        proxy = True

    # relational subfields
    possessions = ReverseForeignKeySubfield("computed", Type.Model, "owner")
