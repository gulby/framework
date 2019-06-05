from base.utils import DurationChecker, file_log


class Logic(object):
    def do(self):
        logic_name = self.__class__.__name__
        with DurationChecker() as checker:
            result = self._do()
        file_log("{} duration : {}".format(logic_name, checker.duration))
        return result

    def _do(self):
        raise NotImplementedError
