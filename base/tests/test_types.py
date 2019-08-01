from shutil import copyfile

from base.tests import BaseTestCase, BaseNoTransactionTestCase
from base.types import SampleType
from base.models.samples import Dummy
from base.transaction import Transaction
from base.types import Type
from base.utils import is_same_file


# TODO : base/types.py --> server/types.py 로 이동
class AutoGenerateTypesFileTest(BaseTestCase):
    def test(self):
        with open("./generated/types.py", "w") as f:
            f.write("from base._types import TypeBase, AUTO\n")
            f.write("\n\n")
            f.write("class SampleType(TypeBase):\n")
            f.write("    owner = AUTO\n")
            f.write("\n\n")
            f.write("class Type(TypeBase):\n")
            array = [t for t in Type]
            array.sort(key=lambda x: x.name)
            for t in array:
                f.write("    {} = AUTO\n".format(t.name))
        if not is_same_file("./generated/types.py", "./base/types.py"):
            copyfile("./generated/types.py", "./base/types.py")
            assert False, "types.py is changed. please test again"


class SampleTypeTest(BaseTestCase):
    def test(self):
        owns = SampleType.owns
        assert type(owns) is SampleType
        assert owns.name == "owns"
        assert owns.value == -1132732633
        assert owns == owns.value
        assert len(SampleType) == 1
        assert len([t for t in SampleType]) == 1

        owner = SampleType.owner
        assert type(owner) is SampleType
        assert owner.name == "owner"
        assert owner.value == -2037214159
        assert owner == owner.value
        assert len(SampleType) == 2
        assert len([t for t in SampleType]) == 2

        ownee = SampleType.ownee
        assert type(ownee) is SampleType
        assert ownee.name == "ownee"
        assert ownee.value == 1775019537
        assert ownee == ownee.value
        assert len(SampleType) == 3
        assert len([t for t in SampleType]) == 3

        분할출원 = SampleType.분할출원
        assert type(분할출원) is SampleType
        assert 분할출원.name == "분할출원"
        assert 분할출원.value == 1411257389
        assert 분할출원 == 분할출원.value
        assert len(SampleType) == 4
        assert len([t for t in SampleType]) == 4

        for t in SampleType:
            assert type(t) is SampleType

        owner2 = SampleType("owner")
        assert owner2 is owner
        owner3 = SampleType(owner.value)
        assert owner3 is owner


class TypeTest(BaseNoTransactionTestCase):
    def test(self):
        with Transaction():
            instance = Dummy.objects.create()
        with Transaction():
            assert Dummy.objects.get(id=instance.id) == instance


class TypeCollisionTest(BaseTestCase):
    def test(self):
        values_list = [t.value for t in Type]
        values_set = set(values_list)
        assert len(values_list) == len(values_set)
