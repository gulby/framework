from django.conf import settings

from base.utils import file_log, WriterContext
from base.constant import DOC_BEGIN_TOKEN, DOC_END_TOKEN


DOC_BEGIN_LINE = "{}\n".format(DOC_BEGIN_TOKEN)
DOC_END_LINE = "{}\n".format(DOC_END_TOKEN)


class Exporter(object):
    def __init__(self, path, queryset):
        self.path = path
        self.f = None
        self.count = 0
        self.queryset = queryset

    def do(self):
        cls_name = self.__class__.__name__
        file_log("{} start : {}".format(cls_name, self.path or ""))
        with WriterContext(self.path) as f:
            self.f = f
            self._do()
        file_log("{} end ({}) : {}".format(cls_name, self.count, self.path or ""))

    def _do(self):
        for instance in self.queryset.hugh_iterator():
            self.do_instance(instance)

    def do_instance(self, instance):
        # console_log(instance)
        try:
            self._do_instance(instance)
            self.count += 1
        except Exception as e:
            self.on_unhandled_exception(instance, e)

    def on_unhandled_exception(self, instance, e):
        if settings.IS_UNIT_TEST:
            raise e
        file_log("{} : error - {}".format(instance, e))

    def _do_instance(self, instance):
        raise NotImplementedError
