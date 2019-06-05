from base.tests import BaseTestCase
from base.models import DummyContainer


class ComputedUnameSubfieldTest(BaseTestCase):
    def test(self):
        instance = DummyContainer()
        assert instance.uname is None
        instance.uname_source = "asdf"
        assert instance.uname == "asdf"
        assert instance.uname == "asdf"
        instance.uname_source = "qwer"
        assert instance.uname == "qwer"


class ComputedUnameSubfieldTest2(BaseTestCase):
    def setUp(self):
        DummyContainer.objects.create(uname_source="asdf")

    def test(self):
        instance = DummyContainer.objects.first("id")
        assert instance.uname == "asdf"


class ComputedUnameSubfieldTest3(BaseTestCase):
    def setUp(self):
        instance = DummyContainer(uname_source="asdf")
        instance.save()

    def test(self):
        instance = DummyContainer.objects.first("-id")
        assert instance.uname == "asdf"


class ComputedUnameSubfieldTest4(BaseTestCase):
    def setUp(self):
        instance = DummyContainer.objects.create(uname_source="asdf")
        assert instance.uname == "asdf"
        instance.uname_source = "qwer"
        assert instance.uname == "qwer"
        instance.save()
        assert instance.uname == "qwer"

    def test(self):
        instance = DummyContainer.objects.get(uname="qwer")
        assert instance.uname == "qwer"


class ComputedUnameSubfieldTest5(BaseTestCase):
    def setUp(self):
        instance = DummyContainer.objects.create(uname_source="asdf")
        instance.uname_source = "qwer"
        instance.save()

    def test(self):
        instance = DummyContainer.objects.get(uname="qwer")
        assert instance.uname == "qwer"
