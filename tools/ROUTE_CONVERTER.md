# Route converter v1

## Monotonic-clock playback (preferred)

The delay-only pipeline can overrun because each node adds scheduling/screenshot overhead. Use the new InsideRouteClock task instead. It reads routes/inside.json directly through the ReplayRecordedRoute custom action; no regeneration is required after recording a new route.

The project interface is configured to launch ../agent/main.py through ../.venv/Scripts/python.exe relative to assets/interface.json. MaaFW is pinned to 5.13.0 to match the current VS Code plugin.

Select only the clock playback task. It waits 3 seconds before starting so the human can return to the game. The route clock starts after this preparation delay. Keep Last Epoch foreground; focus loss, Stop or input failure triggers held-key release attempts. Input scheduling more than 150 ms late aborts instead of rushing through stale events. A crashed process or disconnected controller cannot guarantee key release; verify Stop behavior before unattended use.

Offline tests verify non-accumulating timing, cancellation cleanup, and validation. Live endpoint accuracy and cancellation still require human testing. This version has no minimap monitoring or interactions.

Requires Python 3.10 or later; standard library only. Run from the project root:

```powershell
py -3 tools/convert_route.py routes/inside.json --output assets/resource/pipeline/inside_route_generated.json
```

If the generated output already exists, inspect it first and add `--force` to regenerate. The recording cannot be overwritten by this tool.

Add a task to assets/interface.json:

```json
{"name": "Inside route playback test", "entry": "InsideRoute"}
```

Rescan the interface and run only this task. Use the previously tested Seize keyboard controller and keep the game foreground. Start at the recorded spawn position. Stop old automation and the recorder first. Know the Maa Stop control before starting.

The generated pipeline preserves overlapping WASD key-down/key-up events, enables auto_up for every key-down, and requires all recorded movement keys to be released. Idle time before the first movement is preserved; idle time after the final release is trimmed. Other events are ignored and listed in the report. No map checking, target memory, skills, mouse replay or interaction is included in v1.

Timing is relative between actions, rounded to milliseconds. Maa screenshot and scheduling overhead adds to the timing, potentially increasing travel distance while keys remain held. Compare the endpoint and duration against manual recording before using this in a farming workflow. If drift is material, use a monotonic-clock custom Maa action rather than pretending delay-only nodes are exact playback.

Tests:

```powershell
py -3 -m unittest discover -s tools -p test_convert_route.py
```

Use a distinct --prefix when generating another route into the same resource bundle; duplicate node names may collide. Generated pipeline files should not be edited manually if you intend to regenerate them.
