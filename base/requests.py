from base64 import b64encode, b64decode
from django.conf import settings

from requests import Response
from requests.sessions import Session as RequestsSession
from requests.exceptions import RequestException

from base.json import json_loads, json_dumps
from base.utils import compute_hash_hex64


# thread-safe
class RequestsCacheManager(object):
    _instance = None

    RESPONSE_JSONABLE_FIELDS = ("_content", "status_code", "encoding")
    REQUEST_CACHE_DIR = "_requests_cache"

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = RequestsCacheManager()
        return cls._instance

    @classmethod
    def compute_key(cls, method, url, *args, **kwargs):
        params = {"args": args, "kwargs": kwargs}
        params_str = json_dumps(str(params))
        params_hash = compute_hash_hex64(params_str)
        s = "{}__{}__{}".format(method, url, params_hash)
        s = s.replace("/", ".").replace(":", ".").replace("?", ".")
        return s

    def get(self, method, url, *args, **kwargs):
        key = self.compute_key(method, url, *args, **kwargs)
        try:
            with open("{}/{}.json".format(self.REQUEST_CACHE_DIR, key)) as f:
                d = json_loads(f.read())
        except FileNotFoundError:
            return None
        res = Response()
        for field in self.RESPONSE_JSONABLE_FIELDS:
            res.__dict__[field] = d[field]
        res._content = b64decode(res._content)
        return res

    def set(self, res, method, url, *args, **kwargs):
        key = self.compute_key(method, url, *args, **kwargs)
        d = {}
        for field in self.RESPONSE_JSONABLE_FIELDS:
            d[field] = res.__dict__[field]
        d["_content"] = b64encode(d["_content"])
        s = json_dumps(d)
        with open("{}/{}.json".format(self.REQUEST_CACHE_DIR, key), "w") as f:
            f.write(s)


class Session(RequestsSession):
    def request(self, method, url, *args, **kwargs):
        timeout = kwargs.pop("timeout", (15.01, 15.01))
        kwargs["timeout"] = timeout
        res = None
        unhandled_exception = None
        if settings.REQUESTS_USE_CACHE and settings.REQUESTS_CACHE_FIRST:
            assert settings.IS_UNIT_TEST
            res = RequestsCacheManager.get_instance().get(method, url, *args, **kwargs)
        if not res:
            try:
                res = super().request(method, url, *args, **kwargs)
            except RequestException as e:
                res = None
                unhandled_exception = e
            if res and settings.REQUESTS_IS_RECORD_RESULT:
                RequestsCacheManager.get_instance().set(res, method, url, *args, **kwargs)
        if not res and settings.REQUESTS_USE_CACHE:
            res = RequestsCacheManager.get_instance().get(method, url, *args, **kwargs)
            if res:
                unhandled_exception = None
        if unhandled_exception:
            raise unhandled_exception
        assert res
        res.raise_for_status()
        return res


def requests_get(url, params=None, **kwargs):
    with Session() as session:
        return session.request("GET", url, params=params, **kwargs)


def requests_post(url, data=None, json=None, **kwargs):
    with Session() as session:
        return session.request("POST", url, data=data, json=json, **kwargs)
