from base.tests import BaseTestCase
from base.json import json_schema
from base.models.samples import Dummy
from datetime import datetime


class JsonSchemaTest(BaseTestCase):
    def test(self):
        instance1 = Dummy.objects.create(temp=1, monitors=[1, 2])
        schema1 = json_schema(instance1.data)
        instance2 = Dummy.objects.create(temp=2, monitors=[100])
        schema2 = json_schema(instance2.data)
        assert schema1 == schema2


class JsonSchemaTest2(BaseTestCase):
    def test(self):
        test_dict01 = {
            "list": [
                {"dict01": {"int01": 10, "str01": "str01", "list01": ["list", "list"]}},
                {"dict02": {"int02": 20, "str02": "str02", "list02": ["list2", "list2"]}},
                ["list3", "list3"],
                datetime.now(),
            ]
        }
        schema = json_schema(test_dict01)

        test_dict02 = [
            [
                {
                    "list": [
                        {"dict01": {"int01": 10, "str01": "str01", "list01": ["list", "list"]}},
                        {"dict02": {"int02": 20, "str02": "str02", "list02": ["list2", "list2"]}},
                        ["list3", "list3"],
                        datetime.now(),
                    ]
                },
                {
                    "list2": [
                        {"dict03": {"int01": 10, "str01": "str01", "list01": ["list", "list"]}},
                        {"dict04": {"int02": 20, "str02": "str02", "list02": ["list2", "list2"]}},
                        ["list3", "list3"],
                        datetime.now(),
                    ]
                },
            ]
        ]
        schema2 = json_schema(test_dict02)
        assert [[schema]] == schema2
