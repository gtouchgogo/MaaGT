# World chest YOLO validation

## One-click test

WorldChestClickTest is a separate opt-in task. It waits three seconds, recognizes one confident chest, then ClickWorldChestOnce clicks the exact detection-box center through Maa. It requires Last Epoch foreground, a valid 1080p box and a confirmed recognition result. It sends only one mouse click, waits five seconds for manual observation, saves world_chest_after_one_click.png, and ends. It does not verify open state, pick loot, press T or join the route workflow. Task success means the click and observation completed, not that the chest opened. Keep the character still while the cold model loads so the detection frame does not become stale.

## Persistent inference

The Agent now uses one persistent inference process. It loads and GPU-warms the weights once, reuses them for chest and altar requests, uses sequenced immutable response files, and shuts down on Agent exit. The bounded-round task warms before movement; standalone detection warms lazily on its first request. Keep the character still for that first standalone request. The frame-in/detections-out boundary remains separate from the model.

The WorldChestTest task calls the WorldChestYOLO custom recognition and then DoNothing. It does not click or send keys and is not connected to route branches.

The Agent passes the current 1920x1080 BGR Maa frame to an inference-only subprocess. The worker uses the existing YOLO11 weights, crops [500,75,925,775], maps results back to the full 1080p frame, and returns exactly one chest above confidence 0.55 as the target. Weak, absent or multiple confident chests yield no target. The model does not explicitly classify chest open/closed state.

Diagnostics: debug/world-yolo/<timestamp>.json, <timestamp>-raw.png and <timestamp>-marked.png. Temporary input arrays are removed after worker completion. Save representative occluded and opened-chest screenshots before integrating clicks.

tools/yolo_runtime.json points to the sender's old automation virtual environment containing CUDA PyTorch, OpenCV and Ultralytics. This avoids duplicating large dependencies during validation, but is machine-specific: update it on another machine. The model file is assets/resource/model/detect/world_yolo11.pt. The current Maa environment needs no additional packages.

Startup has a 60-second timeout, and each warmed request has a 15-second timeout. GPU inference timing excludes diagnostic image writes; request_ms measures the full request. An offline saved-frame test reused one worker and identical boxes across two calls (223ms and 203ms on this machine). This is not a guarantee for live gameplay. YOLO26 can later replace the inference worker without changing the task entry.

Restart Agent after Python changes, rescan interface and run only the world chest test. Confirm the recognition box and marked image rather than merely task success. No detections normally cause the recognition test to time out; inspect logs to distinguish a missing target from a worker/environment failure.
