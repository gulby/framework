import re
from unicodedata import normalize

from base.utils import html_unescape

# from nlp.refiner import REFINE_REGEX

REFINE_REGEX = [
    # TODO: 아래에서 자동으로 생성되는 코드로 인해 현재 개행문자가 아래의 코드로 인해 자동으로 공백으로 변함
    *[(r"%s" % chr(i), r" ") for i in range(32)],
    (r"“", r'"'),
    (r"”", r'"'),
    (r"’", r"'"),
    (r"‘", r"'"),
    (r"∼", r"~"),
    (r" \? ", r" "),
    (r"\s+\?$", r"?"),
    (r"([가-힣]),([가-힣])", r"\1, \2"),
    (r"▁", r"_"),
    (r"\s\s+", r" "),
]


def refine(line):
    # 줄바꿈 제거
    line = line.strip().replace("\n", " ").replace("\r", " ")
    # unicode NFKC normalization
    line = normalize("NFKC", line)
    # HTML unescape : '&gt;' --> '<', ...
    line = html_unescape(line)
    for r in REFINE_REGEX:
        line = re.sub(r[0], r[1], line)
    # 최종 공백 제거
    line = line.strip()
    return line
