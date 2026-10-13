"""Convert recorded WASD edges into a movement-only Maa pipeline."""
import argparse
import json
import math
from pathlib import Path

WASD = {65, 68, 83, 87}


def convert(record, prefix='InsideRoute'):
    events = record.get('events')
    if not isinstance(events, list):
        raise ValueError('events must be a list')
    duration = record.get('duration')
    if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration < 0:
        raise ValueError('invalid duration')
    held, edges, ignored = set(), [], {}
    previous = -1
    for event in events:
        t = event.get('t')
        if not isinstance(t, (int, float)) or not math.isfinite(t) or not 0 <= t <= duration or t < previous:
            raise ValueError('timestamps must be finite, ordered, and within duration')
        previous = t
        kind = event.get('kind')
        if kind != 'key' or event.get('vk') not in WASD:
            label = f"key:{event.get('vk')}" if kind == 'key' else str(kind)
            ignored[label] = ignored.get(label, 0) + 1
            continue
        key, down = event['vk'], event.get('down')
        if not isinstance(down, bool):
            raise ValueError('key down must be boolean')
        if down and key in held:
            raise ValueError(f'duplicate key down: {key}')
        if not down and key not in held:
            raise ValueError(f'key up without key down: {key}')
        (held.add if down else held.remove)(key)
        edges.append((round(t*1000), key, down))
    if held:
        raise ValueError(f'unreleased keys: {sorted(held)}')
    if not edges:
        raise ValueError('no WASD events')
    names = [f'{prefix}_{i:03d}' for i in range(len(edges))]
    finish = f'{prefix}_Finished'
    pipeline = {prefix: {
        'recognition': 'DirectHit', 'action': 'DoNothing',
        'pre_delay': 0, 'post_delay': edges[0][0],
        'rate_limit': 0, 'next': [names[0]]}}
    for i, (t, key, down) in enumerate(edges):
        next_time = edges[i+1][0] if i+1 < len(edges) else t
        node = {'recognition': 'DirectHit', 'action': 'KeyDown' if down else 'KeyUp',
                'key': key, 'pre_delay': 0, 'post_delay': next_time-t,
                'rate_limit': 0, 'next': [names[i+1] if i+1 < len(names) else finish]}
        if down:
            node['auto_up'] = True
        pipeline[names[i]] = node
    pipeline[finish] = {'recognition': 'DirectHit', 'action': 'DoNothing',
                        'pre_delay': 0, 'post_delay': 0, 'next': []}
    return pipeline, {'entry': prefix, 'events': len(edges), 'ignored': ignored,
                      'recorded_duration_ms': round(duration*1000),
                      'planned_duration_ms': edges[-1][0],
                      'note': 'Trailing idle trimmed. Maa scheduling/screenshot overhead can extend playback; this is not exact wall-clock replay.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--prefix', default='InsideRoute')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    try:
        if not args.prefix or not args.prefix.replace('_', '').isalnum():
            raise ValueError('prefix must contain letters, numbers or underscores')
        if args.output.resolve() == args.input.resolve():
            raise ValueError('output must not overwrite recording')
        if args.output.exists() and not args.force:
            raise ValueError('output exists; use --force to replace the generated file')
        pipeline, report = convert(json.loads(args.input.read_text(encoding='utf-8-sig')), args.prefix)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(pipeline, indent=2)+'\n', encoding='utf-8')
        print(json.dumps(report, indent=2))
        print(f'Written: {args.output}')
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Conversion failed: {exc}\n')


if __name__ == '__main__':
    main()
