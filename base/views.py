from django.http.response import FileResponse
import urllib


def make_file_response(file, file_name):
    res = FileResponse(file, filename=file_name)
    # 한글파일명 인코딩
    file_name = urllib.parse.quote_plus(file_name)
    res["Content-Type"] = "application/octet-stream"
    res["Content-Disposition"] = "attachment;filename={}".format(file_name)

    return res
