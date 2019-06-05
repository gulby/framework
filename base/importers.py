from django.db import IntegrityError
from django.conf import settings

from base.utils import file_log
from base.exceptions import InvalidRawDataException
from base.transaction import Transaction


class Importer(object):
    def __init__(self, path):
        self.path = path
        self.count = 0

    def do(self):
        cls_name = self.__class__.__name__
        file_log("{} start : {}".format(cls_name, self.path))
        self._do()
        file_log("{} end ({}) : {}".format(cls_name, self.count, self.path))

    def _do(self):
        raise NotImplementedError

    def do_item(self, item, raw_content=None):
        # console_log(item)
        try:
            with Transaction():
                self._do_item(item, raw_content=raw_content)
            self.count += 1
        except IntegrityError:
            pass
        except InvalidRawDataException:
            pass
        except Exception as e:
            self.on_unhandled_exception(item, e)

    def on_unhandled_exception(self, item, e):
        if settings.IS_UNIT_TEST:
            raise e
        file_log("{} : error - {}".format(item, e))

    def _do_item(self, item, raw_content=None):
        raise NotImplementedError
