# Complete single-round validation

New task: FullRoundTest. It waits three seconds for foreground focus, opens/verifies the selector, selects the boss (or charges up to 30 times if disabled), verifies the entry confirmation and clicks it, then requires two consecutive Inside title matches before movement.

The current recorded Inside route runs with minimap memory. Chest and altar branches interact and loot; six valid map frames with zero target hits across the completed route skip target recovery and exit directly. Uncertain target state saves a screenshot and fails the task rather than claiming a successful round.

After loot/clear exit: confirm Outside -> updated Outside movement -> fixed selector click -> verified core fallback if needed -> selector_round_complete screenshot -> stop. No automatic repetition is enabled. FullRoundTest and existing partial tests do not loop.

Recommended first start: human opens the map selector, then runs only the full-round task. Alternatively start at the exact normal portal-return spawn to let the recorded Outside route open it. Arbitrary Outside starting positions are not supported by an open-loop recording. Keep Last Epoch foreground; use Seize for mouse and keyboard, and close old automation/recorder. Know the Stop control.

Entry uses existing legacy calibration through tools/yolo_runtime.json. Templates are cropped after resizing to 1080p. Ready detection also requires bright enabled-button glyphs; grayscale similarity alone is not treated as readiness. Entry confirmation has priority over boss/charge, so a popup is not mistaken for a charge screen. No input is sent during loading uncertainty beyond bounded observation. EnterInsideOnlyTest is available to isolate this newly added step.

This version may spend real in-game charge resources (bounded to 30 clicks). It must be human-supervised. Inventory-full, failed recognition/input, unknown zone, lost focus during interactions and Stop fail/stop tasks. It does not yet have comprehensive death/disconnect dialogs, independently verified chest/altar activation, a guaranteed recovery for arbitrary spawn shifts, or warmed persistent YOLO. Those limitations remain before unattended continuous use.

Offline tests cover enabled/disabled/confirmation reference images, charge bounds, stable Inside confirmation, input suppression on uncertain UI, existing branches and the non-looping terminal node. They do not establish live entry correctness on the current UI. Test one round before considering repetition.
