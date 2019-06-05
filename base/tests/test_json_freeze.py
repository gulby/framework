from base.tests import BaseTestCase
from base.json import json_freeze, json_deepcopy_with_callable


class JsonFreezeTest(BaseTestCase):
    def test_json_freeze(self):
        d = {
            "data": {"d": {}, "temp": 0, "patent": {"raw": "", "plain": "", "html": ""}, "monitors": [0]},
            "computed": {"patent": {"len": 0, "summary": ""}, "sub_dummy_count": 0, "other_sub_dummy_count": 0},
        }
        df = json_freeze(d)
        assert id(d) != id(df)
        df2 = json_freeze(df)
        assert id(df) == id(df2)

        with self.assertRaises(TypeError):
            df["data"] = {}
        with self.assertRaises(TypeError):
            df["computed"] = {}
        with self.assertRaises(TypeError):
            df["data"]["patent"] = {}
        with self.assertRaises(TypeError):
            df["data"]["patent"]["raw"] = ""
        with self.assertRaises(TypeError):
            df["data"]["monitors"] = []
        with self.assertRaises(AttributeError):
            df["data"]["monitors"].append(0)
        with self.assertRaises(AttributeError):
            df["data"]["monitors"].remove(0)
        with self.assertRaises(TypeError):
            df["data"]["monitors"][0] = 1
        with self.assertRaises(TypeError):
            df["data"]["monitors"] += [0]
        with self.assertRaises(TypeError):
            df["computed"]["patent"] = {}

    def test_json_deepcopy1(self):
        d = {
            "data": {"d": {}, "temp": 0, "patent": {"raw": "", "plain": "", "html": ""}, "monitors": [0]},
            "computed": {"patent": {"len": 0, "summary": ""}, "sub_dummy_count": 0, "other_sub_dummy_count": 0},
        }
        assert json_deepcopy_with_callable(d) == d

        df = json_freeze(d)
        d2 = json_deepcopy_with_callable(df)
        assert id(d) != id(d2)
        assert id(d["data"]) != id(d2["data"])
        assert id(d["data"]["patent"]) != id(d2["data"]["patent"])
        assert id(d["data"]["monitors"]) != id(d2["data"]["monitors"])
        assert id(d["computed"]) != id(d2["computed"])
        assert id(d["computed"]["patent"]) != id(d2["computed"]["patent"])
        assert type(d2["data"]) is dict
        assert type(d2["data"]["patent"]) is dict
        assert type(d2["data"]["monitors"]) is list
        assert type(d2["computed"]) is dict
        assert type(d2["computed"]["patent"]) is dict

        assert json_deepcopy_with_callable(df)
        assert json_deepcopy_with_callable(df)
