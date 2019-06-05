from base.tests import BaseTestCase, only_full_test
from base.utils import PDFRenderer


class PdfTest(BaseTestCase):
    @only_full_test()
    def test_string(self):
        string = "<html><h1>test test</h1></html>"
        pdf = PDFRenderer(string)
        assert pdf
        assert isinstance(pdf, PDFRenderer)
        pdf.render()

    @only_full_test()
    def test_path(self):
        pdf = PDFRenderer("base/tests/data/test_html_to_pdf.html")
        assert pdf
        assert isinstance(pdf, PDFRenderer)
        pdf.save("temp/pdf/pdfkit_result_path.pdf")

    @only_full_test()
    def test_file(self):
        file = open("base/tests/data/test_html_to_pdf.html")
        pdf = PDFRenderer(file)
        assert pdf
        assert isinstance(pdf, PDFRenderer)

    @only_full_test()
    def test_url(self):
        url = "https://www.google.com/"
        pdf = PDFRenderer(url)
        assert pdf
        assert isinstance(pdf, PDFRenderer)


class PdfTest2(BaseTestCase):
    @only_full_test()
    def test_string(self):
        string = "<HTML><h1>test test</h1></HTML>"
        pdf = PDFRenderer(string)
        assert pdf
        assert isinstance(pdf, PDFRenderer)

    @only_full_test()
    def test_file(self):
        string = "base/tests/data/test.htm"
        # 파일이 실제 존재하지 않는경우 pdfkit에서 에러발생
        with self.assertRaises(OSError):
            pdf = PDFRenderer(string)
            pdf.render()

    @only_full_test()
    def test_another(self):
        int_value = 1123234
        with self.assertRaises(AssertionError):
            pdf = PDFRenderer(int_value)
            pdf.render()
