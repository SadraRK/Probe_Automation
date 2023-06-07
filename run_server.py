# Server: 8888
# Flir Camera: 8889
# Requests: 8890

from common.asyncio_loop import asyncio_run_forever
from server.flir_server import flir_server
from server.http_server import http_server
from server.requests.request_web_socket import request_socket
import components


def main():
    http_server(8888)
    flir_server(8889)
    request_socket(8890)

    # wait on them.
    asyncio_run_forever()


# http://localhost:8888/public/index.html
if __name__ == '__main__':
    main()
