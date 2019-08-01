import re
from unicodedata import normalize

try:
    from MeCab import Tagger
except ImportError:

    class Tagger(object):
        def parse(self, phrase):
            raise NotImplementedError


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


# KoNLPy 와 호환되도록 만들어 놓은 것임
class Mecab(object):
    tagger = Tagger()

    def morphs(self, phrase):
        return [s for s, t in self.pos(phrase)]

    def extract_ngram_corpus(self, phrase):
        tagged = self.pos(phrase)
        return [s for s, t in tagged if not t.startswith("S")]

    def nouns(self, phrase):
        tagged = self.pos(phrase)
        return [s for s, t in tagged if t[:1] in ("N",) or t[:2] in ("XR", "SL", "SH")]

    def nouns_and_verbs(self, phrase):
        tagged = self.pos(phrase)
        return [s for s, t in tagged if t[:1] in ("N", "V") or t[:2] in ("XR", "SL", "SH")]

    def without_josa(self, phrase):
        tagged = self.pos(phrase)
        return [s for s, t in tagged if not t.startswith("J")]

    def pos(self, phrase):
        return self.parse(self.tagger.parse(phrase))

    @classmethod
    def parse(cls, result):
        def split(elem):
            if not elem:
                return ("", "SY")
            s, t = elem.split("\t")
            return (s, t.split(",", 1)[0])

        return [split(elem) for elem in result.splitlines()[:-1]]
