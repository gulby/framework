import os
import sys
import platform
import inspect
import re
import pickle
import pdfkit
import gzip
import io

from uuid import UUID
from timeit import timeit as builtin_timeit
from multiprocessing import Lock
from datetime import datetime, timedelta
from html import unescape
from argparse import ArgumentParser as PythonArgumentParser
from pathlib import Path
from io import TextIOWrapper
from glob2 import glob as glob2_glob
from math import log, e as 밑
from pysnooper import snoop as pysnooper_snoop

from django.conf import settings
from django.db import transaction, connection
from django.db.utils import ProgrammingError
from django.core.cache import caches
from django.core.mail import EmailMessage
from django.utils.timezone import now
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string as django_render_to_string
from django.contrib import messages
from django.shortcuts import render
from django.http import JsonResponse

from xxhash import xxh32_intdigest, xxh64_intdigest, xxh64_hexdigest

try:
    from cityhash import CityHash128 as hash128
except ImportError:
    assert platform.system() == "Darwin"
    hash128 = xxh64_intdigest

# TODO : 몸에 더 좋은 모듈로 교체하기
from cryptography.fernet import Fernet

from base.constant import CHUNK_SIZE, MIN_BIGINT


FILE_LOG_LOCK = Lock()


def is_mac():
    return platform.system() == "Darwin"


def capture_caller_info():
    stack = inspect.stack()
    base_frame = stack[1].frame
    my_dir = settings.BASE_DIR
    for frame in (s.frame for s in stack[2:]):
        filename = frame.f_code.co_filename
        if filename != base_frame.f_code.co_filename and filename.find(my_dir) == 0:
            return filename[len(my_dir) + 1 :], frame.f_code.co_name, frame.f_lineno
    return None


def reversed_bit_array_with_padding(n, bit_array_length):
    bit_array = [int(x) for x in bin(n)[2:]]
    bit_array_reversed = [0] * (bit_array_length - len(bit_array)) + bit_array
    bit_array_reversed.reverse()
    return bit_array_reversed


def compute_hash_uuid(value):
    if value is None:
        return None
    return UUID(int=hash128(value))


def compute_hash_int32(value):
    n = xxh32_intdigest(value)
    return (n ^ 0x80000000) - 0x80000000


def compute_hash_int64(value):
    n = xxh64_intdigest(value)
    return (n ^ 0x8000000000000000) - 0x8000000000000000


def compute_file_hash(file):
    return xxh64_hexdigest(file.read())


def timeit(func, number=300000):
    return builtin_timeit(func, number=number)


def console_log(*args, extra=None, log_to="stderr"):
    if log_to == "stderr":
        for arg in args or []:
            sys.stderr.write(str(arg))
            sys.stderr.write("\t")
        sys.stderr.write("\n")
    if extra:
        sys.stderr.write("\t")
        sys.stderr.write(str(extra))
        sys.stderr.write("\n")
    return args[0]


def file_log(*args, extra=None):
    if not settings.IS_UNIT_TEST:
        console_log(*args, extra=extra)
    try:
        with FILE_LOG_LOCK:
            with open("file_log.txt", "a") as file:
                file.write("[{}] ".format(now()))
                for v in args or []:
                    file.write(str(v))
                    file.write("\t")
                file.write("\n")
                if extra:
                    file.write("\t")
                    file.write(str(extra))
                    file.write("\n")
                file.write("\n")
    except Exception as e:
        console_log("\tfile_log() failed", e)


def shallow_copy(v):
    result = v
    t = type(v)
    if t is dict:
        result = {}
        result.update(v)
    elif t is list:
        result = v[:]
    return result


def run_sql(sql, params=()):
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            try:
                fields = [col[0] for col in cursor.description]
                return [dict(zip(fields, row)) for row in cursor.fetchall()]
            except ProgrammingError:
                result = None
            except TypeError:
                result = None
    return result


def send_email(subject, body, mail_to):
    if type(mail_to) is str:
        mail_to = [mail_to]
    EmailMessage(subject, body, to=mail_to).send()


def cache_get(key):
    cache = caches["email_onetime_password"]
    return cache.get(key)


def cache_set(key, value):
    cache = caches["email_onetime_password"]
    return cache.set(key, value)


def cache_delete(key):
    cache = caches["email_onetime_password"]
    return cache.delete(key)


def encrypt(key, value):
    # pre condition check
    assert type(key) is bytes, "key 는 bytes 형이어야 합니다"
    assert type(value) in (str, bytes), "value 는 str 혹은 bytes 형이어야 합니다."
    if type(value) is str:
        value = value.encode()
    assert type(value) is bytes
    # encrypt
    crypto = Fernet(key)
    encrypted = crypto.encrypt(value)
    assert type(encrypted) is bytes
    result = encrypted.decode()
    assert type(result) is str
    return result


def decrypt(key, value):
    # pre condition check
    assert type(key) is bytes, "key 는 bytes 형이어야 합니다"
    assert type(value) in (str, bytes), "value 는 str 혹은 bytes 형이어야 합니다."
    if type(value) is str:
        value = value.encode()
    assert type(value) is bytes
    # decrypt
    crypto = Fernet(key)
    decrypted = crypto.decrypt(value)
    assert type(decrypted) is bytes
    result = decrypted.decode()
    assert type(result) is str
    return result


def convert_datetime(value):
    split_value = value.split(" ") if value else " "
    try:
        result = datetime.strptime(split_value[0] + "+0900", "%Y-%m-%d%z")
    except ValueError:
        result = None
    return result


def is_same_file(path1, path2):
    with open(path1) as f:
        hash1 = compute_hash_uuid(f.read())
    with open(path2) as f:
        hash2 = compute_hash_uuid(f.read())
    return hash1 == hash2


def clean_xml(s):
    s = s.strip()
    # 정규식 처리
    re_mappings = (
        (r">[\s\r\n]+<", "><"),
        (r"&", "&amp;"),
        (r"<<", "<"),
        (r"<li>\(<li>", "<li>"),
        (r"<\./p></P>", "</P>"),
        (r"<p( |>)", r"<P\1"),
        (r"</p>", "</P>"),
        (r"nameend=meend=", "nameend="),
        (r"<!-- Temp tag</PATDOC>Te", ""),
        (r"</i>\), 모든 ></i>", "</i>\), 모든 >"),
        (r'<B510 VER="<B511>', '<B510 VER="4"><B511>'),
        (r"<B43p>", "<B430>"),
        (r"<B21p>", "<B210>"),
        (r"</B43p>", "</B430>"),
        (r"</Bt30>", "</B430>"),
        (r"/B210></B210>", "</B210>"),
        (r'<B510 VER ="5>', '<B510 VER ="5">'),
    )
    for m in re_mappings:
        s = re.sub(m[0], m[1], s)
    # 닫히지 않은 태그 처리
    unclosed_tags = (
        "PCTPatentDOC",
        "KIPO",
        "PatentDOC",
        "PATDOC",
        "PCTPatentCAFDOC",
        "KR_Patent_Law_18",
        "PCTDOC",
        "KR_Patent_Law_10",
        "UtilDOC",
        "UTMDOC",
        "KR_Patent_Law_19",
        "KR_Patent_Law_18_2_2",
    )
    for tag in unclosed_tags:
        if "<{}".format(tag) not in s:
            s = s.replace("</{}>".format(tag), "")
    # 끝부분 replace 처리
    tail_replace_mappings = (
        ("</KR", "</KR_RegisterPatent>"),
        ("</KR_RegisterPate</KR_RegisterPatent>", "</KR_RegisterPatent>"),
        ("</KR_RegisterPat", "</KR_RegisterPatent>"),
        ("</KR_RegisterPatent></KR_RegisterPatent>", "</KR_RegisterPatent>"),
    )
    for m in tail_replace_mappings:
        if s.endswith(m[0]):
            s = s[: len(s) - len(m[0])] + m[1]
    return s


def safe_read_file(file):
    with open(file, "rb") as f:
        b = f.read()
        try:
            s = b.decode(encoding="utf-8")
        except UnicodeDecodeError:
            # TODO : 인코딩을 자동 인식하여 처리
            broken_bytes = [b"\x00", b"\x04", b"\x05", b"\x1e", b"\x13", b"\x15", b"\x0f", b"\x16", b"\x11", b"\x0c"]
            for bb in broken_bytes:
                b = b.replace(bb, b"")
            s = b.decode(encoding="ks_c_5601-1987", errors="ignore")
    return s


def convert_bool(s):
    if s in ("True", "true", "T", "1", 1, True):
        return True
    elif s in ("False", "false", "F", "", "0", 0, False):
        return False
    return None


def html_unescape(s):
    s = unescape(s)
    additional_escapes = [("&quot;", '"'), ("&lt;", ">"), ("&gt;", "<")]
    for e in additional_escapes:
        s = s.replace(e[0], e[1])
    return s


class WriterContext(object):
    def __init__(self, path):
        self.path = path
        self.f = None

    def __enter__(self):
        if self.path:
            self.f = open(self.path, "w")
            return self.f
        else:
            return sys.stdout

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.f:
            self.f.close()


def LineStripReader(f):
    need_close = False
    if isinstance(f, str):
        f = open(f)
        need_close = True
    try:
        for line in f:
            line = line.strip()
            if line:
                yield line
    finally:
        if need_close:
            f.close()


def ChunkedLineStripReader(f, chunk_size=CHUNK_SIZE):
    need_close = False
    if isinstance(f, str):
        f = open(f)
        need_close = True
    chunk = []
    try:
        for line in f:
            line = line.strip()
            if line:
                chunk.append(line)
                if len(chunk) >= chunk_size:
                    yield chunk
                    chunk = []
    finally:
        if chunk:
            yield chunk
        if need_close:
            f.close()


class ReaderContext(object):
    def __init__(self, path):
        self.path = path
        self.f = None

    def __enter__(self):
        if self.path:
            if self.path.endswith(".gz"):
                self.f = gzip.open(self.path, "rt")
            else:
                self.f = open(self.path, "r")
            return self.f
        else:
            assert self.f is None
            return sys.stdin

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.f:
            self.f.close()


class ArgumentParser(PythonArgumentParser):
    def __init__(self, **kwargs):
        super().__init__()
        self.kwargs = kwargs

    def parse_args(self, args=None, namespace=None):
        args, argv = self.parse_known_args(args, namespace)
        for k, v in self.kwargs.items():
            setattr(args, k, v)
        return args


def split_with_deliminator(s, deliminator, required_after_deliminator=None):
    assert s
    splited1 = re.split(r"(%s)" % deliminator, s)
    if splited1[-1] == "":
        splited1 = splited1[:-1]
    else:
        splited1.append("")
    len1 = len(splited1)
    assert len1 % 2 == 0
    splited = ["".join(splited1[i * 2 : (i + 1) * 2]) for i in range(int(len1 / 2))]
    if not required_after_deliminator:
        return splited
    result = [splited[0]]
    for i in range(1, len(splited)):
        if splited[i].startswith(required_after_deliminator):
            result.append(splited[i])
        else:
            result[-1] = "{}{}".format(result[-1], splited[i])
    return result


def execute_shell_command(command):
    return os.popen(command).read().strip()


def get_total_line_cnt(path, min_wc=0):
    if min_wc == 0:
        return int(execute_shell_command("cat {} | wc -l".format(path)))
    with open(path, "r") as f:
        return len([None for line in f if len(line.split()) >= min_wc])


class LineNoReader(object):
    SPLITED_FILE_LINE_CNT = 100000

    def __init__(self, path, cache_file=None, line_nos=None, cache_head_cnt=10000):
        self.path = path
        self.cache = {}
        self.total_line_cnt = get_total_line_cnt(self.path)
        if not line_nos and cache_file:
            with open(cache_file, "r") as f:
                line_nos = [int(line.split()[0]) for line in LineStripReader(f)]
            assert line_nos
        if line_nos:
            line_nos = list(set(line_nos))
            line_nos.sort()
            with open(self.path, "r") as f:
                pointer = 0
                for line_no, line in enumerate(LineStripReader(f)):
                    if line_no != line_nos[pointer]:
                        continue
                    self.cache[line_no] = line
                    pointer += 1
                    if pointer >= len(line_nos):
                        break
        if cache_head_cnt:
            initial_cache_cnt = min(self.total_line_cnt, cache_head_cnt)
            with open(self.path, "r") as f:
                for line_no, line in enumerate(LineStripReader(f)):
                    self.cache[line_no] = line
                    if line_no + 1 >= initial_cache_cnt:
                        break

    # line_no 는 0 부터 시작하는 값
    def read(self, line_no):
        assert line_no < self.total_line_cnt
        try:
            return self.cache[line_no]
        except KeyError:
            if self.total_line_cnt <= self.SPLITED_FILE_LINE_CNT:
                splited_file_path = self.path
                line_no_in_splited_file = line_no
            else:
                # 성능을 위해 짤라 놓은 파일에서 읽는다
                n = int(line_no / self.SPLITED_FILE_LINE_CNT)
                line_no_in_splited_file = line_no - self.SPLITED_FILE_LINE_CNT * n
                splited_file_dir = os.path.join(os.path.dirname(self.path), "_lnreader/")
                file_name = self.path.split("/")[-1]
                splited_file_path = os.path.join(splited_file_dir, "{0}.{1:05}".format(file_name, n))
                if not os.path.exists(splited_file_path):
                    Path(splited_file_dir).mkdir(parents=True, exist_ok=True)
                    abs_path = os.path.abspath(self.path)
                    execute_shell_command(
                        "cd {0} && split -d -a 5 --lines={1} {2} {3}.".format(
                            splited_file_dir, self.SPLITED_FILE_LINE_CNT, abs_path, file_name
                        )
                    )
            # 리눅스의 line_no 는 1부터 시작
            # TODO : 그냥 python 구현으로 변경
            line = execute_shell_command(
                "cat {} | head -{} | tail -1".format(splited_file_path, line_no_in_splited_file + 1)
            )
            self.cache[line_no] = line
            return line


def load_pickle(path):
    with open(path, "rb") as f:
        data = pickle.load(f)
    return data


def save_pickle(data, path):
    with open(path, "wb") as f:
        pickle.dump(data, f)


def is_url(url):
    val = URLValidator()
    try:
        val(url)
    except ValidationError:
        return False
    return True


# TODO : 버그수정
def is_file_path(path):
    regex = r"^[/가-힣0-9a-zA-Z_\.]*$"
    return bool(re.match(regex, path))


# TODO : 버그수정
def str_num_to_int_num(value):
    regex = r"[0-9]"
    result = "".join(re.findall(regex, value))
    assert result != ""
    return int(result)


def getsource(func):
    return inspect.getsource(func)


def get_referenced_members_of_self_from_source(s):
    splited = re.split(r"(\W)", s)
    result = []
    for i in range(len(splited) - 3):
        if splited[i] == "self" and splited[i + 1] == "." and splited[i + 2][0] != "_" and splited[i + 3] != "(":
            result.append(splited[i + 2])
    return result


def safe_call(func, *args, **kwargs):
    try:
        value = func(*args, **kwargs)
    except Exception as e:
        msg = "{}: {}".format(e.__class__.__name__, str(e))
        if "NoneType" in msg or "DoesNotExist" in msg or "AttributeError" in msg:
            value = None
        else:
            raise e
    return value


class PDFRenderer(object):
    def __init__(self, html):
        self._html = html
        self.data = None

    @property
    def html(self):
        return self._html

    @html.setter
    def html(self, v):
        self.data = None
        self._html = v

    def render(self):
        if self.data:
            return
        html = self.html
        # file pointer
        if isinstance(html, TextIOWrapper):
            pdf_byte = pdfkit.from_file(html, False)
        # str
        elif isinstance(html, str):
            # url
            if is_url(html):
                pdf_byte = pdfkit.from_url(html, False)
            # file
            elif is_file_path(html):
                pdf_byte = pdfkit.from_file(html, False)
            # HTML or anything(str)
            else:
                pdf_byte = pdfkit.from_string(html, False)
        # another case
        else:
            raise AssertionError
        self.data = pdf_byte

    @property
    def file(self):
        self.render()
        return io.BytesIO(self.data)

    def save(self, path):
        if settings.IS_UNIT_TEST:
            return
        self.render()
        with open(path, "wb") as f:
            f.write(self.data)


def render_to_string(template, context):
    html = django_render_to_string(template, context)
    assert "This_is_not_INVALID" not in html
    return html


def glob(path):
    files = glob2_glob(path)
    files.sort()
    return files


def isnull(v, r=MIN_BIGINT):
    return r if v is None else v


def get_last_element_name_from_path(path):
    return Path(path).resolve().stem


# TODO: 구현
def is_business_day(date_time):
    return True


def get_gte_business_day(date_time):
    business_day = date_time
    for num in range(30):
        if is_business_day(business_day + timedelta(num)):
            return business_day + timedelta(num)


def render_exception(request, e, status=400):
    request.need_rollback = True
    msg = "{}: {}".format(e.__class__.__name__, e)
    # TODO : JsonResponse 필요 판단 로직 관련 구조 개선
    if getattr(request, "need_json_response", False):
        res = JsonResponse({"status": "false", "error": msg}, status=500)
    else:
        messages.error(request, msg)
        res = render(request, "base/exception.html", status=status)
    return res


def argmax(arr):
    return max(zip(arr, range(len(arr))))[1]


def safe_multiply_by_log(*args):
    return 밑 ** sum([log(v) for v in args])


def snoop(*args, **kwargs):
    return pysnooper_snoop(*args, **kwargs)


def default_render_func(duration):
    console_log("working duration => {}".format(duration))


class DurationChecker(object):
    def __init__(self, render_func=None):
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.render_func = render_func

    def __enter__(self):
        self.start_time = datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        render_func = self.render_func or default_render_func
        render_func(self.duration)
