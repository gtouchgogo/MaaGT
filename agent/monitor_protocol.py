"""Publish immutable per-request responses to avoid Windows replace/read races."""
import json
from pathlib import Path


def result_path(folder, sequence):
    if sequence != 'ready' and (type(sequence) is not int or sequence < 1):
        raise ValueError('Invalid monitor request sequence')
    return Path(folder)/f'status-{sequence}.json'


def publish_result(folder, sequence, ok, error='', hits=None):
    destination = result_path(folder, sequence)
    temporary = destination.with_suffix('.tmp')
    payload = {'sequence':sequence, 'ok':ok, 'error':error, 'hits':hits}
    with temporary.open('x', encoding='utf-8') as output:
        json.dump(payload, output)
    # The destination is new: no replacement of a file held by a reader.
    temporary.rename(destination)
