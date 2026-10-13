# Altar and exit integration

InsideRouteClock now runs a single complete inside-to-outside attempt. Chest -> one detected click -> loot -> exit. Altar -> YOLO target -> one click -> wait two seconds -> loot -> exit. A remembered altar that cannot be located uses down/left/right/up movements of 0.5 seconds, re-detecting after each, stopping as soon as it is located. No repeated altar activation is attempted merely because no requested loot drops.

The monitor checks map validity from the purple player marker and gold map strokes. At route completion, at least six valid frames with zero chest/altar hits lead directly to exit without target recovery movements. One hit, conflicting confirmed classes, hidden map, or monitoring errors cannot be treated as clear. The route is not cut short based on early absence.

Exit first confirms the fixed zone title as inside. Press T, wait 0.8 seconds, prefer Time's End text; hover an identified blue ring to reveal its text if needed. Ring center or legacy calibrated point is a bounded fallback. Every click is followed by zone checks. Require two consecutive Outside matches. Three consecutive Inside matches trigger retry: same exact point once, then move right, open T and try; then down, T and try; then up, T and try. No more than five clicks. Unknown/loading states do not trigger movement; they abort after bounded observations. Title templates are scaled to 1080p and matched with small position tolerance instead of upscaling binary glyphs.

Portal exit does not rerun Outside movement or start the next cycle. Outside confirmation saves a screenshot and ends. Inventory-full, Stop, focus loss and input failure halt. Scripts never operate the game during offline verification.

Separate test entries: ExitPortalTest and AltarInteractionTest (the latter also picks loot and exits). Keep the game foreground and both input methods Seize. Restart Agent, rescan/reselect the current window, and run only one task from a valid scene. Test exit alone first, then altar, then InsideRouteClock. Diagnostics are under debug/interaction; the exit-confirmation screenshot is outside_exit_confirmed.png.

Limitations: altar click completion is not verified activation; a no-loot activation may be normal. Chest opening is still not independently confirmed. The no-target decision assumes the recorded route reaches the intended target area and the icons would be revealed. Cold YOLO subprocess startup remains; persistent warmed inference is the next performance task before continuous looping.
