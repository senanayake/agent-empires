"""One bounded, sequential loopback HTTP adapter; no framework dependency."""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

from agent_empires.application.commands import PreviewSession, rejection
from agent_empires.application.scenarios import load_scenario
from agent_empires.application.services import DeliveryService

MAX_BODY = 65536


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def _constant(value):
    raise ValueError('non-finite JSON value')


def create_handler(session: PreviewSession):
    """Translate HTTP bytes; the application owns validation and projections."""
    class Handler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.0'

        def setup(self):
            super().setup()
            self.connection.settimeout(2)

        def log_message(self, format, *args):
            pass

        def do_POST(self):
            response = rejection(None, session.run_id, 'malformed_command')
            status = 400
            try:
                length = self.headers.get_all('Content-Length', [])
                if self.path != '/command':
                    response['error'] = 'unknown_path'
                    status = 404
                elif (self.headers.get('Transfer-Encoding') is not None or len(length) != 1
                      or not length[0].isascii() or not length[0].isdigit()
                      or not 0 < int(length[0]) <= MAX_BODY
                      or self.headers.get_content_type() != 'application/json'):
                    response['error'] = 'malformed_command'
                else:
                    raw = self.rfile.read(int(length[0]))
                    if len(raw) != int(length[0]):
                        raise ValueError('truncated body')
                    request = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
                                         parse_constant=_constant)
                    response = session.handle(request)
                    status = 200 if response['status'] == 'accepted' else 400
            except (UnicodeError, ValueError, RecursionError):
                pass
            except (TimeoutError, ConnectionError):
                return
            body = json.dumps(response, allow_nan=False, separators=(',', ':')).encode('utf-8')
            try:
                self.send_response(status)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Connection', 'close')
                self.end_headers()
                self.wfile.write(body)
            except (TimeoutError, ConnectionError):
                # A command may have committed: retry the identical ID/content.
                pass
            self.close_connection = True
    return Handler


def create_server(session: PreviewSession, *, port=0):
    """Only 127.0.0.1, ephemeral port supported; caller owns lifecycle/cleanup."""
    return HTTPServer(('127.0.0.1', port), create_handler(session))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', default='scenarios/paymentco/scenario.json')
    parser.add_argument('--run-id', required=True, help='unique for each new process/run')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--port', type=int, default=0)
    args = parser.parse_args()
    service = DeliveryService(load_scenario(args.scenario), run_id=args.run_id, root_seed=args.seed)
    service.start('jin', command_id='preview.work')
    server = create_server(PreviewSession(service), port=args.port)
    print(json.dumps(dict(version=1, run_id=args.run_id, host=server.server_address[0],
                          port=server.server_address[1])), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
