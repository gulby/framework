from base.tests import BaseTestCase
from base.utils import ChunkedLineStripReader


class ChunkedLineStripReaderTest(BaseTestCase):
    def test1(self):
        results = []
        for lines in ChunkedLineStripReader("base/tests/data/test_html_to_pdf.html", chunk_size=7):
            for line in lines:
                results.append(line)
        assert results[0] == "<!DOCTYPE html>"
        assert results[-1] == "</html>"

    def test2(self):
        results = []
        for lines in ChunkedLineStripReader("base/tests/data/test_html_to_pdf.html", chunk_size=11):
            for line in lines:
                results.append(line)
        assert results[0] == "<!DOCTYPE html>"
        assert results[-1] == "</html>"
