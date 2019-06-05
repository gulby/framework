import sys
from responder import API
from starlette.testclient import TestClient

from server.wsgi import application


api = API()
api.requests = api._session = TestClient(api, base_url="http://www.deephigh.net")
api.mount("", application)

if __name__ == "__main__":
    port = int(sys.argv[1])
    api.run(address="0.0.0.0", port=port)
