from base.tests import BaseTestCase
from base.utils import get_referenced_members_of_self_from_source


class GetSubfieldNamesFromSourceTest(BaseTestCase):
    def test(self):
        s1 = "    uname = UnameSubfield(default=lambda self: get_mapping_uname(self.S, self.T), expire=Expire.ONCHNAGE)\n"
        assert get_referenced_members_of_self_from_source(s1) == ["S", "T"]
        s2 = "    def compute_uri(self, caller=None):\n        unique_subfield = self.unique_subfield\n        assert unique_subfield\n        unique_value = unique_subfield.__get__(self, self.__class__)\n        return self.convert_uri(unique_value)\n"
        assert get_referenced_members_of_self_from_source(s2) == ["unique_subfield"]
