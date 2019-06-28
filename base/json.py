from uuid import UUID
from datetime import datetime
from types import MappingProxyType
from inspect import isgenerator

from rapidjson import dumps as rapidjson_dumps, loads as rapidjson_loads
from django.utils import dateparse
from xmltodict import _DictSAXHandler, expat, _unicode

from base.utils import console_log

JSON_CONTAINER_TYPES = (dict, MappingProxyType, list, tuple)
JSON_MAPPING_TYPES = (dict, MappingProxyType)
JSON_ARRAY_TYPES = (list, tuple)
JSON_LEAF_TYPES = (str, int, type(None), float, bool)


def json_dumps(d, **options):
    if "ensure_ascii" not in options:
        options["ensure_ascii"] = False
    return rapidjson_dumps(d, **options)


def json_loads(s, **options):
    return rapidjson_loads(s, **options)


def json_read_file(path, **options):
    with open(path, "r") as f:
        return json_loads(f.read(), **options)


def json_write_file(d, path, **options):
    with open(path, "w") as f:
        f.write(json_dumps(d, **options))


def json_walk(d, f, context={}):
    if isinstance(d, dict):
        for k, v in d.items():
            f(d, k, v, context)
            json_walk(v, f, context)
    elif isinstance(d, list):
        for i, v in enumerate(d):
            f(d, i, v, context)
            json_walk(v, f, context)
    return context


def json_ensure_schema(total_d, total_schema):
    def helper(d, schema):
        d_type = type(d)
        schema_type = type(schema)

        # list 처리
        if d_type == list:
            assert schema_type in JSON_ARRAY_TYPES, schema_type
            for element in d:
                helper(element, schema[0])
            return

        # 형식 확인 및 안전 장치 세팅
        assert d_type == dict, d_type
        assert schema_type in JSON_MAPPING_TYPES, schema_type
        if schema_type != MappingProxyType:
            schema = MappingProxyType(schema)

        # schema 에 없는 항목 처리
        for schema_k, schema_v in schema.items():
            if schema_k not in d:
                schema_v_type = type(schema_v)
                if schema_v_type in JSON_ARRAY_TYPES:
                    d[schema_k] = []
                elif schema_v_type in JSON_MAPPING_TYPES:
                    d[schema_k] = {}
                    helper(d[schema_k], schema_v)
                else:
                    assert schema_v_type in JSON_LEAF_TYPES, schema_v_type
                    d[schema_k] = schema_v

        # schema 에 있는 항목 처리
        for k, v in d.items():
            if k in schema:
                v_type = type(v)
                if v_type in JSON_CONTAINER_TYPES:
                    helper(v, schema[k])
                else:
                    assert v_type in JSON_LEAF_TYPES, v_type
                    schema_v = schema[k]
                    schema_v_type = type(schema_v)
                    assert schema_v_type in JSON_LEAF_TYPES, schema_v_type
                    if v is not None and schema_v is not None:
                        if not isinstance(v, type(schema_v)):
                            if v_type == int and schema_v_type in (float, str):
                                d[k] = schema_v_type(v)
                            elif v_type == float and schema_v_type in (str,):
                                d[k] = schema_v_type(v)
                            else:
                                assert False, "k:v == ({}, {})\nschema = {}".format(k, v, schema)

    # recursive call
    helper(total_d, total_schema)


def json_schema(d):
    if isinstance(d, dict):
        schema = {}
        schema.update(d)
        for k, v in d.items():
            if isinstance(v, dict):
                schema[k] = json_schema(v)
            elif isinstance(v, list):
                schema[k] = json_schema(v)
            elif isinstance(v, int):
                schema[k] = 0
            elif isinstance(v, str):
                schema[k] = ""
            else:
                schema[k] = None
    elif isinstance(d, list):
        schema = []
        if d:
            v = d[0]
            if isinstance(v, dict):
                schema.append(json_schema(v))
            elif isinstance(v, list):
                schema.append(json_schema(v))
            elif isinstance(v, int):
                schema.append(0)
            elif isinstance(v, str):
                schema.append("")
            else:
                schema.append(None)
    else:
        assert False, console_log("d 가 json type 이 아닙니다", d)
    return schema


def json_freeze(d):
    td = type(d)
    if td is dict:
        for k, v in d.items():
            t = type(v)
            if t is dict:
                d[k] = json_freeze(v)
            elif t is list:
                d[k] = tuple(v)
            elif t in (MappingProxyType, tuple):
                d[k] = v
        return MappingProxyType(d)
    elif td in (list, range) or isgenerator(d):
        return tuple(d)
    elif td in (MappingProxyType, tuple):
        return d
    else:
        raise AssertionError("json freeze 가 가능한 타입이 아닙니다.")


def json_deepcopy_with_callable(value):
    value_type = type(value)
    if value_type in JSON_CONTAINER_TYPES:
        if value_type in JSON_MAPPING_TYPES:
            d = {}
            d.update(value)
        else:
            assert value_type in JSON_ARRAY_TYPES
            d = list(value)
        for k, v in d.items() if value_type in JSON_MAPPING_TYPES else enumerate(d):
            if callable(v):
                continue
            t = type(v)
            assert t in JSON_CONTAINER_TYPES or t in JSON_LEAF_TYPES
            if t in JSON_CONTAINER_TYPES:
                d[k] = json_deepcopy_with_callable(v)
        return d
    return json_encode(value)


def patch_mjson(mjson, patch):
    data_backup = mjson["data"]
    computed_backup = mjson["computed"]
    mjson.update(patch)
    mjson["data"] = data_backup
    mjson["computed"] = computed_backup
    mjson["data"].update(patch["data"])
    mjson["computed"].update(patch["computed"])
    return mjson


def json_encode(value):
    t = type(value)
    encoded = value
    if issubclass(t, str):
        encoded = str(value)
    # issubclass(bool, int) is True. 그리고 json field 에 bool 로 저장하면 오히려 로드할 때 에러가 남. int 로 저장하는 것이 좋음
    # 허나 명시적으로 확인할 수 있도록 코드 상에 남겨 놓음
    elif issubclass(t, bool):
        encoded = int(value)
    elif issubclass(t, int):
        encoded = int(value)
    elif issubclass(t, UUID) or issubclass(t, datetime):
        encoded = str(value)
    elif hasattr(value, "json_encode"):
        encoded = value.json_encode()
    return encoded


def json_decode(value, value_type):
    assert value_type
    decoded = value
    if value is not None:
        t = type(value)
        # TODO: t is not value_type -> not issubclass(t, value_type) 으로 변경
        if t not in (dict, MappingProxyType, list, tuple) and t is not value_type:
            if value_type is datetime:
                assert isinstance(value, str)
                # TODO : 제대로 구현
                value = value.replace("/", "-")
                if len(value) <= len("2018-01-01"):
                    value = "{} 00:00:00".format(value)
                decoded = dateparse.parse_datetime(value)
                assert decoded
            elif hasattr(value_type, "json_decode"):
                decoded = value_type.json_decode(value)
            else:
                decoded = value_type(value)
    return decoded


class _MyDictSAXHandler(_DictSAXHandler):
    def _build_name(self, full_name):
        name = super()._build_name(full_name)
        # TODO : 정규식 써서 튜닝 (이상하게 잘 안됨;;;)
        return name.replace("-", "_").replace(":", "_")


# xmltodict.parse() 와 거의 같음
# 허나 장고 filter 가 불가능한 key 이름이 존재하기 때문에 (-, @, #)
# key name 을 바꾸기 위한 최소한의 수정만 진행
def convert_xml(xml_input):
    encoding = None
    process_namespaces = False
    namespace_separator = ":"
    disable_entities = True
    handler = _MyDictSAXHandler(namespace_separator=namespace_separator, attr_prefix="", cdata_key="text")
    if isinstance(xml_input, _unicode):
        if not encoding:
            encoding = "utf-8"
        xml_input = xml_input.encode(encoding)
    if not process_namespaces:
        namespace_separator = None
    parser = expat.ParserCreate(encoding, namespace_separator)
    try:
        parser.ordered_attributes = True
    except AttributeError:
        # Jython's expat does not support ordered_attributes
        pass
    parser.StartNamespaceDeclHandler = handler.startNamespaceDecl
    parser.StartElementHandler = handler.startElement
    parser.EndElementHandler = handler.endElement
    parser.CharacterDataHandler = handler.characters
    parser.buffer_text = True
    if disable_entities:
        try:
            # Attempt to disable DTD in Jython's expat parser (Xerces-J).
            feature = "http://apache.org/xml/features/disallow-doctype-decl"
            parser._reader.setFeature(feature, True)
        except AttributeError:
            # For CPython / expat parser.
            # Anything not handled ends up here and entities aren't expanded.
            parser.DefaultHandler = lambda x: None
            # Expects an integer return; zero means failure -> expat.ExpatError.
            parser.ExternalEntityRefHandler = lambda *x: 1
    if hasattr(xml_input, "read"):
        parser.ParseFile(xml_input)
    else:
        parser.Parse(xml_input, True)
    return handler.item
