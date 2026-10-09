"""Reproducible bounded transport probe; refuse to overwrite reviewed evidence.

Default is a separate Python process and real loopback HTTP connections.
Handler mode is a socket-free diagnostic, never a network latency substitute.
"""
import argparse
import hashlib
import http.client
import io
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

from agent_empires.application.commands import PreviewSession
from agent_empires.application.scenarios import load_scenario
from agent_empires.application.services import DeliveryService
from agent_empires.adapters.transport.http import create_handler


def hardware():
    cpuinfo = Path('/proc/cpuinfo')
    model = next((l.split(':', 1)[1].strip() for l in cpuinfo.read_text().splitlines()
                  if l.startswith('model name')), None) if cpuinfo.exists() else None
    return dict(platform=platform.platform(), machine=platform.machine(),
                cpu_model=model, logical_cpus=os.cpu_count(), python=sys.version,
                executable=sys.executable)


def handler_sender():
    service = DeliveryService(load_scenario('scenarios/paymentco/scenario.json'),
                              run_id='benchmark', root_seed=0)
    service.start('jin', command_id='preview.work')
    handler = create_handler(PreviewSession(service))
    def send(body):
        request = (b'POST /command HTTP/1.0\r\nContent-Type: application/json\r\n'
                   + f'Content-Length: {len(body)}\r\n\r\n'.encode() + body)
        class StreamSocket:
            def __init__(self): self.output = bytearray()
            def makefile(self, *args): return io.BytesIO(request)
            def settimeout(self, timeout): pass
            def sendall(self, data): self.output.extend(data)
        sock = StreamSocket()
        handler(sock, ('127.0.0.1', 1), None)
        return json.loads(bytes(sock.output).split(b'\r\n\r\n', 1)[1])
    return send


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('loopback', 'handler'), default='loopback')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('refusing to overwrite evidence')
    result = dict(mode=args.mode, hardware=hardware(), seed=0,
        scenario_hash=hashlib.sha256(Path('scenarios/paymentco/scenario.json').read_bytes()).hexdigest(),
        warmup_count=30, sample_count=300, budget_ms=250,
        budget_classification='engineering_budget', calibration_version=None,
        protocol='30 warmups then 300 serial commands, new connection per request; nearest-rank p95',
        operations=['snapshot', 'events(cursor=0,limit=256)', 'pause(paused=true)', 'step'],
        limitations=['One tiny prepared work item; mostly polls/empty steps after the first completion.',
                    'No Godot, low-end hardware, long session, stress or usability validation.',
                    'Handler mode excludes kernel sockets, process scheduling and network lifecycle.'])
    process = None
    try:
        start = time.perf_counter_ns()
        if args.mode == 'handler':
            send = handler_sender()
        else:
            process = subprocess.Popen([sys.executable, '-m', 'agent_empires.adapters.transport.http',
                '--run-id', 'benchmark'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            # Readiness bounded independently of an unresponsive child.
            import selectors
            selector = selectors.DefaultSelector()
            selector.register(process.stdout, selectors.EVENT_READ)
            ready = selector.select(timeout=5)
            selector.close()
            if not ready:
                raise TimeoutError('no readiness within five seconds')
            line = process.stdout.readline()
            if not line:
                raise RuntimeError('server exited before readiness: ' + process.stderr.read())
            endpoint = json.loads(line)
            def send(body):
                conn = http.client.HTTPConnection(endpoint['host'], endpoint['port'], timeout=3)
                try:
                    conn.request('POST', '/command', body, {'Content-Type': 'application/json'})
                    response = conn.getresponse()
                    ack = json.loads(response.read())
                    if response.status != 200:
                        raise RuntimeError(str(ack))
                    return ack
                finally:
                    conn.close()
        result['startup_ms'] = (time.perf_counter_ns() - start) / 1e6
        samples = []
        for index in range(331):
            if index == 0:
                operation, payload = 'step', {}
            else:
                operation, payload = [('snapshot', {}), ('events', {'cursor': 0, 'limit': 256}),
                    ('pause', {'paused': True}), ('step', {})][(index - 1) % 4]
            begin = time.perf_counter_ns()
            body = json.dumps(dict(version=1, run_id='benchmark', command_id=f'probe.{index}',
                                   operation=operation, args=payload)).encode()
            ack = send(body)
            if ack['status'] != 'accepted' or ack['command_id'] != f'probe.{index}':
                raise RuntimeError('unexpected acknowledgment')
            elapsed = (time.perf_counter_ns() - begin) / 1e6
            if index == 0:
                result['real_completion_ack_ms'] = elapsed
            elif index > 30:
                samples.append(dict(operation=operation, elapsed_ms=elapsed, request_bytes=len(body)))
        times = sorted(s['elapsed_ms'] for s in samples)
        result.update(status='measured', samples=samples, p50_ms=times[math.ceil(.5*len(times))-1],
                      p95_ms=times[math.ceil(.95*len(times))-1], max_ms=max(times))
        result['meets_budget'] = result['p95_ms'] < 250 if args.mode == 'loopback' else None
    except (OSError, ValueError, RuntimeError, TimeoutError) as exc:
        result.update(status='unavailable', error=str(exc), samples=[], p95_ms=None,
                      meets_budget=None)
    finally:
        if process is not None:
            if process.poll() is None:
                process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
            result['process_result'] = dict(exit_code=process.returncode, stdout=stdout, stderr=stderr)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result.get(k) for k in ('mode', 'status', 'p95_ms', 'meets_budget')}))
    return 0 if result['status'] == 'measured' else 1


if __name__ == '__main__':
    raise SystemExit(main())
