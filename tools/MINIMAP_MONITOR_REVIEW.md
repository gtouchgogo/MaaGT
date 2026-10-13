# Inside route minimap monitor

## Windows status-file fix

Responses use immutable status-ready.json, status-1.json, status-2.json, etc. Each file is written to its own temporary name and renamed into a previously nonexistent destination. A reader holding the previous response cannot block publication of the next response. The old single-file replace protocol caused WinError 5 in live testing. Regression tests cover an open prior file and 100 sequential requests; no administrator elevation is needed for this fix.

## Runtime

InsideRouteClock opts in with monitor_minimap=true. Other routes retain movement-only behavior. After setup, the monitor starts alongside monotonic-clock playback, waits one second, then checks approximately every 400 ms. Recognition slower than the interval reduces sampling frequency; it does not create additional workers or backlogs.

AgentServer cannot create a Win32 controller, and concurrent reverse RPC calls for input and recognition caused image/response mismatches in live testing. A separate native Maa Python process now owns BOTH FramePool screenshots and TemplateMatch recognition. The monitor thread performs no Agent RPC, including stopping-status queries. The main playback thread alone uses the Agent transport.

The native worker connects to the foreground Last Epoch window before movement and never sends input. It copies just the two recognition definitions and their image files from minimap_test.json into an isolated temporary bundle, so boilerplate OCR/custom tasks are not loaded. It uses Tasker.post_recognition on 1920x1080 images; no actions or next lists are executed. RecognitionDetail.hit determines matches. Only two booleans are returned through a request-sequenced status file; stale responses are rejected. Temporary files are removed at normal shutdown.

Two accumulated matches confirm a class. Confirmed classes remain remembered when later occluded; memory resets for each action invocation. Both confirmed classes or only one match lead to InsideTargetUncertain. At least six valid map checks and zero target hits across the completed route lead to InsideNoTarget and direct exit. A visible player marker and gold map strokes validate frames; hidden/black maps do not count. This is an endpoint-based heuristic, not proof that a target outside the explored range does not exist. Do not apply it midway through the route.

After movement, the monitor is stopped and joined before selecting next using context.override_next. Chest and altar branches now interact, pick loot and attempt exit; no-target directly exits, uncertain still ends for inspection. Output prints total/valid checks, per-class hit counts, seen classes and branch. World interaction re-detects current coordinates; minimap detections are not click targets.

## Review

- Input and expensive captures must not share the original controller's action queue. Separate read-only capture addresses queue blocking, but GPU/CPU contention and Agent RPC latency still require live endpoint comparison.
- Stop causes movement's finally cleanup to release keys. Monitor shutdown waits at most five seconds per finish attempt; a stuck worker reports failure. Restart the Agent after that failure rather than immediately starting another route. Process termination or controller disconnection cannot guarantee input release.
- The user's commented-out continuous foreground check was preserved. Monitored runs require Last Epoch foreground at startup, but do not stop on later focus loss unless that check is restored. Seize input can affect other foreground applications. Keep the game foreground throughout testing.
- Confirming two matches reduces isolated false positives but does not eliminate persistent template errors. Test altar/player overlap and player-only negative frames.
- Fixed 1920x1080 capture size and existing minimap ROI are intentional. Different resolutions/layouts fail or require new calibration.

## Human verification

Restart Agent/launch session after Python changes, rescan Interface, run only InsideRouteClock from the recorded start, and return to the game during the three-second preparation delay. Check endpoint accuracy, both target branches, remembered targets after overlap, unknown branch for no visible target, Stop while holding diagonal movement, and repeated runs resetting memory. No live game input was used during implementation verification.

Tests: .venv/Scripts/python.exe -m unittest discover -s tools -p "test_*.py"

Real native offline check: .venv/Scripts/python.exe tools/check_native_minimap.py. It uses a fake controller and synthetic frames, not the game. Blank, pasted chest and pasted altar frames passed with the actual Maa 5.13 recognition engine. This exercises native resource loading and result parsing, but does not replace live concurrency/endpoint/Stop verification.
