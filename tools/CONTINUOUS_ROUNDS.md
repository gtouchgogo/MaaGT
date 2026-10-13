# Bounded continuous test

Select `连续测试：3轮后停止` in the Maa task panel, reload resources and restart
the Agent after updating. Start from Outside or an already open map selector.
Keep Last Epoch foreground. Do not queue a separate full-round task alongside it.

The first launch loads and warms YOLO before movement. The same inference worker
is reused for chest and altar requests until the Agent exits. Restarting the Agent
loads it again. Diagnostics remain under debug/world-yolo.

Each round enters Inside, follows the route while monitoring the minimap,
interacts with the detected target, picks the configured loot, exits, and confirms
the map selector is open. Only then is the round counted. Later rounds enter
directly from that open selector, without repeating the Outside route.

The limit defaults to 3. To change it, edit `rounds` in
assets/resource/pipeline/bounded_rounds.json (integer 1 through 100).
Original single-round and partial tests still end normally without a loop session.
Any failed action or Stop ends progress; a new task cannot resume an old counter.

This is a supervised trial, not unattended operation. Death, disconnection,
unexpected spawn positions and independent confirmation of chest/altar activation
still need additional handling. Current loot configuration is unchanged.

Offline checks: 59 unit tests; check_yolo_session.py exercises two real inference
requests on a saved screenshot and verifies one shared worker and identical boxes.
