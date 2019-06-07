from base.tests import BaseTestCase
from base.nlp import refine


class NormalizeTest(BaseTestCase):
    def test(self):
        # ‘ ’ => ' '
        assert (
            refine("1959년 ‘풀브라이트 장학계획’의 일원으로 선발되어 풀브라이트 장학생으로 미국으로 건너가, 노스웨스턴 대학교에서 신문학 연수를 받았다.")
            == "1959년 '풀브라이트 장학계획'의 일원으로 선발되어 풀브라이트 장학생으로 미국으로 건너가, 노스웨스턴 대학교에서 신문학 연수를 받았다."
        )
        # “ ” => " "
        assert (
            refine("“최적의 칼만 이득”이라 불리는, 이 이득은 MMSE 추정을 사용했을 때 산출되는 값이다.")
            == '"최적의 칼만 이득"이라 불리는, 이 이득은 MMSE 추정을 사용했을 때 산출되는 값이다.'
        )
        # 연속된 공백을 ' '하나의 공백으로, 앞뒤 공백 제거
        assert refine("또한  범퍼에 날개를 연상시키는 디자인을 넣은 것도 특징이다. ") == "또한 범퍼에 날개를 연상시키는 디자인을 넣은 것도 특징이다."
        # 문장 끝의 '?' 는 앞에 공백이 있다면 제거
        assert refine("5천만 원 대에서 위에서 말한 모든 것이 가능한 차가 있다면 믿겠는가  ?") == "5천만 원 대에서 위에서 말한 모든 것이 가능한 차가 있다면 믿겠는가?"

    def test_2(self):
        with self.assertRaises(AssertionError):
            assert refine("test\ntest\rtest") == "test test test"
