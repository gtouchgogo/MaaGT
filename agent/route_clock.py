"""Replay validated key edges against one monotonic clock."""
import time


def replay(edges, send, stopping, clock=time.perf_counter, sleep=time.sleep,
           max_lateness=.15):
    held = set()
    start = clock()
    success = False
    try:
        for t, key, down in edges:
            deadline = start + t
            while clock() < deadline:
                if stopping():
                    return False
                sleep(min(.01, max(0, deadline-clock())))
            if stopping():
                return False
            if clock()-deadline > max_lateness:
                raise RuntimeError('Input scheduling fell more than 150 ms behind; stopping route')
            # Track before sending so a failed key-down still gets a release attempt.
            if down:
                held.add(key)
            if not send(key, down):
                raise RuntimeError(f'Maa key input failed: {key}, down={down}')
            if not down:
                held.discard(key)
        success = True
    finally:
        for key in sorted(held):
            try:
                if not send(key, False):
                    success = False
            except Exception:
                success = False
    return success
