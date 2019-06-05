from base.tests import BaseTestCase
from base.transaction import TransactionManager
from base.models import DummyActor

from common.models import Board, Post


class BoardTest(BaseTestCase):
    def setUp(self):
        actor = DummyActor.objects.create()
        self.tran.checkin(actor)

    def test(self):
        checkin_actor = TransactionManager.get_checkin_actor()
        board = Board.objects.create(title="공지사항")

        post1 = Post()
        post1.title = "공지사항 제 1번"
        post1.content = "첫번째 공지사항입니다."
        post1.author = checkin_actor
        post1.board = board
        post1.save()

        assert board.posts.count() == 1
        assert post1.board == board
        assert post1.title == "공지사항 제 1번"
        assert post1.content == "첫번째 공지사항입니다."
        assert post1.author == checkin_actor
        assert post1.created_date.date() == post1.published_date.date()

        post2 = Post()
        post2.title = "공지사항 제 2번"
        post2.content = "두번째 공지사항입니다."
        post2.author = checkin_actor
        post2.board = board
        post2.save()

        assert board.posts.count() == 2
        assert post2.board == board
        assert post2.title == "공지사항 제 2번"
        assert post2.content == "두번째 공지사항입니다."
        assert post2.author == checkin_actor
        assert post2.created_date.date() == post2.published_date.date()
