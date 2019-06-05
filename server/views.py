import math
import random
from time import sleep, time

from django.http import HttpResponse


def timeout(request):
    start = time()
    second = int(request.GET.get("second", 0))
    sleep(second)
    end = time()
    return HttpResponse(
        "start: {}, end: {}, elapsed: {}, second: {}".format(start, end, end - start, second), content_type="text/plain"
    )


def spin(request):
    start = time()
    loop = int(request.GET.get("loop", 0))
    for i in range(loop):
        r = random.random()
        l = math.exp(r)
    end = time()
    return HttpResponse(
        "start: {}, end: {}, elapsed: {}, loop: {}".format(start, end, end - start, loop), content_type="text/plain"
    )
