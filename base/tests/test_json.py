from base.tests import BaseTestCase
from base.json import json_schema, json_ensure_schema
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


class JsonEnsureSchemaTest(BaseTestCase):
    def test(self):
        d = {}
        json_ensure_schema(d, {"is_impossible": 0})
        assert d == {"is_impossible": 0}

        d = {"version": 1}
        json_ensure_schema(d, {"version": ""})
        assert d == {"version": "1"}

    def test2(self):
        d = {
            "version": "",
            "data": [
                {
                    "title": "15657",
                    "paragraphs": [
                        {
                            "context": "한국청소년단체협의회와 여성가족부는 22일부터 28일까지 서울과 충북 괴산에서 '국제청소년포럼'을 연다고 21일 밝혔다. 한국 미국 캐나다 호주 등 전 세계 32개국 75여명의 대학생, 청소년들이 모여 전 세계적 현안문제에 대한 대안과 해결책을 모색하는 자리다. 이번 포럼의 주제는 '청소년과 뉴미디어'다. 스마트폰 SNS 태블릿PC 등 새로운 커뮤니케이션 매체인 '뉴미디어'에 대한 성찰과 문제점에 대해 토론한다. 기조강연을 시작으로 국가별 주제관련 사례발표, 그룹 토론 및 전체총회, '청소년선언문' 작성 및 채택 등 다양한 프로그램을 운영한다. 개회식은 22일 서울 방화동에 있는 국제청소년센터 국제회의장에서 한다. 전 세계 32개국 대학생ㆍ청소년 참가자와 전국의 청소년기관단체장과 청소년지도자 여성가족부 주한외교사절 등 100여명이 참석할 예정이다. 23일에는 유엔미래포럼 박영숙 대표가 '뉴미디어의 균형 있는 발전을 위한 청소년의 역할'에 대해 기조강연을 한다. 뉴미디어의 올바른 활용방안과 청소년문화의 형성에 대해 설명할 계획이다. 27일 폐회식에서는 '청소년선언문'을 채택한다. 선언문에는 전 세계적으로 뉴미디어의 바람직한 발전을 촉구하며 각국 청년들이 함께 실천할 수 있는 내용 등이 담길 예정이다. 한국청소년단체협의회는 포럼이 끝난 뒤 UN 등 국제기구와 참가자 각국 정부 등 국제사회에 선언문을 전달할 예정이다.",
                            "qas": [
                                {
                                    "question": "서울과 충북 괴산에서 '국제청소년포럼'을 여는 곳은?",
                                    "answers": [{"answer_start": 0, "text": "한국청소년단체협의회와 여성가족부"}],
                                    "id": "c1_57059-1",
                                    "classtype": "work_who",
                                },
                                {
                                    "question": "'국제 청소년포럼'이 열리는 때는?",
                                    "answers": [{"answer_start": 19, "text": "22일부터 28일"}],
                                    "id": "c1_57060-1",
                                    "classtype": "work_when",
                                },
                                {
                                    "question": "이번 포럼의 주제는?",
                                    "answers": [{"answer_start": 157, "text": "'청소년과 뉴미디어'"}],
                                    "id": "c1_57061-1",
                                    "classtype": "work_what",
                                },
                                {
                                    "question": "포럼은 어떻게 진행되는가?",
                                    "answers": [
                                        {
                                            "answer_start": 232,
                                            "text": "기조강연을 시작으로 국가별 주제관련 사례발표, 그룹 토론 및 전체총회, '청소년선언문' 작성 및 채택 등 다양한 프로그램을 운영한다.",
                                        }
                                    ],
                                    "id": "c1_57062-1",
                                    "classtype": "work_how",
                                },
                            ],
                        }
                    ],
                    "source": 5,
                },
                {
                    "title": "775",
                    "paragraphs": [
                        {
                            "context": "[헤럴드POP=고승아 기자]그룹 구구단 샐리가 리듬체조에서 실수했다.15일 방송된 MBC '설특집 2018 아이돌스타 육상 볼링 양궁 리듬체조 에어로빅 선수권대회(이하 아육대)'에서는 구구단 샐리가 리듬체조 종목에 출전한 모습이 그려졌다.이날 구구단 샐리는 리듬체조 종목에 처음 출전해 훌라후프로 무대를 꾸몄다. 그러나 연기 도중 훌라후프를 받지 못하는 등 실수를 해 안타까움을 자아냈다.응원을 하던 구구단 멤버들도 열심히 연습했던 샐리를 생각해 눈물을 흘렸다.popnews@heraldcorp.com- Copyrights ⓒ 헤럴드POP & heraldpop.com, 무단 전재 및 재배포 금지 -",
                            "qas": [
                                {
                                    "question": "아육대에서 리듬체조에 출전한 구구단의 멤버는?",
                                    "answers": [{"answer_start": 22, "text": "샐리"}],
                                    "id": "m5_306705-1",
                                    "classtype": "work_who",
                                }
                            ],
                        }
                    ],
                    "source": 7,
                },
            ],
        }
        schema = {
            "version": "",
            "data": [
                {
                    "title": "",
                    "paragraphs": [
                        {
                            "qas": [
                                {
                                    "question": "",
                                    "id": "",
                                    "answers": [{"text": "", "answer_start": 0}],
                                    "is_impossible": 0,
                                }
                            ],
                            "context": "",
                        }
                    ],
                }
            ],
        }

        json_ensure_schema(d, schema)
        assert d == {
            "version": "",
            "data": [
                {
                    "title": "15657",
                    "paragraphs": [
                        {
                            "context": "한국청소년단체협의회와 여성가족부는 22일부터 28일까지 서울과 충북 괴산에서 '국제청소년포럼'을 연다고 21일 밝혔다. 한국 미국 캐나다 호주 등 전 세계 32개국 75여명의 대학생, 청소년들이 모여 전 세계적 현안문제에 대한 대안과 해결책을 모색하는 자리다. 이번 포럼의 주제는 '청소년과 뉴미디어'다. 스마트폰 SNS 태블릿PC 등 새로운 커뮤니케이션 매체인 '뉴미디어'에 대한 성찰과 문제점에 대해 토론한다. 기조강연을 시작으로 국가별 주제관련 사례발표, 그룹 토론 및 전체총회, '청소년선언문' 작성 및 채택 등 다양한 프로그램을 운영한다. 개회식은 22일 서울 방화동에 있는 국제청소년센터 국제회의장에서 한다. 전 세계 32개국 대학생ㆍ청소년 참가자와 전국의 청소년기관단체장과 청소년지도자 여성가족부 주한외교사절 등 100여명이 참석할 예정이다. 23일에는 유엔미래포럼 박영숙 대표가 '뉴미디어의 균형 있는 발전을 위한 청소년의 역할'에 대해 기조강연을 한다. 뉴미디어의 올바른 활용방안과 청소년문화의 형성에 대해 설명할 계획이다. 27일 폐회식에서는 '청소년선언문'을 채택한다. 선언문에는 전 세계적으로 뉴미디어의 바람직한 발전을 촉구하며 각국 청년들이 함께 실천할 수 있는 내용 등이 담길 예정이다. 한국청소년단체협의회는 포럼이 끝난 뒤 UN 등 국제기구와 참가자 각국 정부 등 국제사회에 선언문을 전달할 예정이다.",
                            "qas": [
                                {
                                    "question": "서울과 충북 괴산에서 '국제청소년포럼'을 여는 곳은?",
                                    "answers": [{"answer_start": 0, "text": "한국청소년단체협의회와 여성가족부"}],
                                    "id": "c1_57059-1",
                                    "classtype": "work_who",
                                    "is_impossible": 0,
                                },
                                {
                                    "question": "'국제 청소년포럼'이 열리는 때는?",
                                    "answers": [{"answer_start": 19, "text": "22일부터 28일"}],
                                    "id": "c1_57060-1",
                                    "classtype": "work_when",
                                    "is_impossible": 0,
                                },
                                {
                                    "question": "이번 포럼의 주제는?",
                                    "answers": [{"answer_start": 157, "text": "'청소년과 뉴미디어'"}],
                                    "id": "c1_57061-1",
                                    "classtype": "work_what",
                                    "is_impossible": 0,
                                },
                                {
                                    "question": "포럼은 어떻게 진행되는가?",
                                    "answers": [
                                        {
                                            "answer_start": 232,
                                            "text": "기조강연을 시작으로 국가별 주제관련 사례발표, 그룹 토론 및 전체총회, '청소년선언문' 작성 및 채택 등 다양한 프로그램을 운영한다.",
                                        }
                                    ],
                                    "id": "c1_57062-1",
                                    "classtype": "work_how",
                                    "is_impossible": 0,
                                },
                            ],
                        }
                    ],
                    "source": 5,
                },
                {
                    "title": "775",
                    "paragraphs": [
                        {
                            "context": "[헤럴드POP=고승아 기자]그룹 구구단 샐리가 리듬체조에서 실수했다.15일 방송된 MBC '설특집 2018 아이돌스타 육상 볼링 양궁 리듬체조 에어로빅 선수권대회(이하 아육대)'에서는 구구단 샐리가 리듬체조 종목에 출전한 모습이 그려졌다.이날 구구단 샐리는 리듬체조 종목에 처음 출전해 훌라후프로 무대를 꾸몄다. 그러나 연기 도중 훌라후프를 받지 못하는 등 실수를 해 안타까움을 자아냈다.응원을 하던 구구단 멤버들도 열심히 연습했던 샐리를 생각해 눈물을 흘렸다.popnews@heraldcorp.com- Copyrights ⓒ 헤럴드POP & heraldpop.com, 무단 전재 및 재배포 금지 -",
                            "qas": [
                                {
                                    "question": "아육대에서 리듬체조에 출전한 구구단의 멤버는?",
                                    "answers": [{"answer_start": 22, "text": "샐리"}],
                                    "id": "m5_306705-1",
                                    "classtype": "work_who",
                                    "is_impossible": 0,
                                }
                            ],
                        }
                    ],
                    "source": 7,
                },
            ],
        }
