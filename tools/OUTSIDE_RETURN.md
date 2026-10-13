# Outside route and selector validation

The updated outside.json contains four WASD edges ending at 2.896045 seconds, with no recorded clicks. It was copied from the legacy recorder after backing up the previous MaaGT recording. Movement uses the same monotonic-clock replay as Inside. Mouse events are ignored, and trailing recorded idle is trimmed. The first click uses the fixed 1080p region [961,369,20,16], centered at (971,377), immediately after the last movement key is released.

ReturnOutsideToSelector checks the initial screenshot before movement: an already open selector needs no input; otherwise Outside title confirmation is required. After movement, there is no pre-click detection or recorded mouse pause. Click the fixed point, wait 0.35 seconds, then verify the selector. Only if still closed is the stone core used for a new click; allow up to three core retries with 0.5-second settling waits. When the selector is recognized, the vision worker skips unnecessary core matching. Click completion alone never counts as opening. No next cycle, charging or boss selection is started.

OutsideReturnTest is a separate test starting at the normal portal-return spawn, not arbitrarily beside the selector. It waits three seconds for foreground focus. Successful opening saves selector_round_complete.png. Keep both input modes Seize and stop other scripts first.

InsideRouteClock now connects loot or no-target exit to ExitAndReturnToSelector, then the Outside route and selector. The standalone portal-exit and altar-interaction tests still end after Outside confirmation and do not start this route.

The selector recognizer temporarily reuses legacy screenshots through tools/yolo_runtime.json. Samples are resized to 1080p before UI templates are cropped, preserving the resize sampling phase. Real 1080p selector screenshots on this machine should still be checked before enabling repeated rounds.

Stone recovery now prefers the user's assets/resource/image/meeting_stone.png. It matches the central upper core, excluding the player name/health bar and floor rim, at 0.9/1.0/1.1 scale within the world ROI. Confidence threshold remains 0.82; it was not lowered to accept the old failing 0.677 match. Legacy core is used only when the local image is absent. Diagnostics include stone_template and stone_score. The matching box is the core, so its center is a valid retry click above the player. Offline check: run tools/check_meeting_stone.py through the existing YOLO runtime; the regression screenshot is debug/meeting-stone-regression.png.

Performance follow-up remains a persistent warmed YOLO worker. Current template/color workers do not load YOLO, but each vision call still launches a lightweight subprocess. No automatic loop is enabled in this version.
