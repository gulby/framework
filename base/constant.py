LOOKUP_SEP = "__"

ONCHANGE_FUNC_NAME = "onchange_{}"

COMPUTE_FUNC_NAME = "compute_{}"
COMPUTED_FIELD_NAME = "computed_{}"

SPACE_REPLACER = "▁"
assert SPACE_REPLACER == "\u2581"

SPECIAL_CHAR = "▁\\{}[]()<>/?.,;:|*~`!^-_+@#$%&='\" "
assert SPACE_REPLACER in SPECIAL_CHAR
SPECIAL_CHAR_AND_NUM = "{}0123456789".format(SPECIAL_CHAR)

DOC_BEGIN_TOKEN = "<D>"
DOC_END_TOKEN = "</D>"

CHUNK_SIZE = 2000
MAX_QUERYSET_SIZE = CHUNK_SIZE * 1
MIN_BIGINT = -9223372036854775808