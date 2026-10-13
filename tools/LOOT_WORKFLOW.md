# Chest loot workflow

InsideRouteClock now performs real interaction when the route monitor remembers a chest:

InsideChestSeen -> FindChestForLoot (YOLO, one center click) -> wait 5 seconds -> PickChestLoot -> LootTestObservation -> end.

Altar and uncertain branches still only save screenshots and end. No portal or Outside route is connected. The standalone one-click test remains unchanged. Keep the game foreground and disable old automation/recording before testing from the recorded spawn point.

The pickup detector reuses the sender's validated legacy rules through tools/yolo_runtime.json. It includes pink text, orange panels, and orange text on dark backgrounds. Blue labels are ignored. Labels farther than one third of the 1080p screen width from the fixed screen-center anchor are filtered. No character repositioning is performed by this action beyond the game's own movement toward clicked loot. Recognition moves the cursor away first to remove hover styling. Future repositioning requires refreshing target coordinates and anchors.

After each pickup, wait 0.8 seconds and capture again. Two empty checks, separated by 0.35 seconds plus detection overhead, end the loop. One empty check alone does not finish. Inventory-full detection, focus loss, Stop, failed clicks, five unchanged follow-up signatures, or 60 checks stop with an error. Diagnostic frames and reports are under debug/loot. A final observation screenshot is saved, so two empty checks still produce one additional final screenshot.

This is a connected validation workflow, not a complete farming loop. Click completion does not prove the chest opened. If no requested loot appears, the task may end with zero clicks; do not infer verified opening from that. Repeated opening retries and explicit open-state verification remain to be designed.

Persistent YOLO loading remains required before adding continuous repeated detection: load and warm once in a dedicated worker, reuse across requests, bound timeouts, and close on Agent exit. Current cold-start detection is retained for correctness validation.
