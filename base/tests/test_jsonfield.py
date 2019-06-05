from base.tests import BaseNoTransactionTestCase
from base.transaction import Transaction, ReadonlyTransaction
from base.models.samples import Dummy
from base.fields import ForceChanger
from base.utils import compute_hash_uuid


class JSONFieldTest(BaseNoTransactionTestCase):
    def test(self):
        uri = "/uri/1/"
        with Transaction():
            instance = Dummy()
            with ForceChanger(instance):
                instance.uri = uri
            assert instance.uri_hash == compute_hash_uuid(uri)
            instance.save()
            assert instance.uri_hash == compute_hash_uuid(uri)
        assert instance.uri_hash == compute_hash_uuid(uri)
        mjson1 = instance.mjson

        with ReadonlyTransaction():
            instance = Dummy.objects.get(id=instance.id)
            assert instance.mjson == mjson1
            assert instance.uri == uri
            assert instance.uri_hash == compute_hash_uuid(uri)
