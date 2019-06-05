from base.tests import BaseTestCase
from base.models.samples import Dummy
from base.fields import SF
from base.utils import console_log


class BasicOrderByTest(BaseTestCase):
    def setUp(self):
        Dummy.objects.create(temp=1)
        Dummy.objects.create(temp=2)
        Dummy.objects.create(temp=3)
        console_log("end of setUp()")

    def test(self):
        assert len(Dummy.objects.all()) == 3
        assert len(Dummy.objects.annotate(temp=SF("temp"))) == 3
        assert len(Dummy.objects.annotate(temp=SF("temp")).order_by("temp")) == 3

        assert Dummy.objects.annotate(temp=SF("temp")).order_by("temp").first().temp == 1
        assert Dummy.objects.annotate(temp=SF("temp")).order_by("-temp").first().temp == 3


class JsonFieldOrderByTest(BaseTestCase):
    def given(self):
        Dummy.objects.create(temp=1)
        Dummy.objects.create(temp=2)
        Dummy.objects.create(temp=3)
        console_log("end of given()")

    def test(self):
        assert len(Dummy.objects.all()) == 3
        assert len(Dummy.objects.annotate(temp=SF("temp"))) == 3
        assert len(Dummy.objects.annotate(temp=SF("temp")).order_by("temp")) == 3

        assert Dummy.objects.annotate(temp=SF("temp")).order_by("temp").first().temp == 1
        assert Dummy.objects.annotate(temp=SF("temp")).order_by("-temp").first().temp == 3


class SubfieldOrderByTest(JsonFieldOrderByTest):
    def test(self):
        assert Dummy.objects.order_by("temp").first().temp == 1
        assert Dummy.objects.order_by("-temp").first().temp == 3
