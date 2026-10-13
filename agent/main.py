import sys

from maa.agent.agent_server import AgentServer
from maa.toolkit import Toolkit

import my_action
import my_reco
import route_action
import world_yolo_reco
import world_chest_action
import loot_action
import interaction_actions
import outside_action
import entry_action
import round_actions
from yolo_session import close_yolo


def main():
    Toolkit.init_option("./")

    if len(sys.argv) < 2:
        print("Usage: python main.py <socket_id>")
        print("socket_id is provided by AgentIdentifier.")
        sys.exit(1)

    socket_id = sys.argv[-1]

    try:
        if not AgentServer.start_up(socket_id):
            raise RuntimeError('Cannot start Maa Agent')
        AgentServer.join()
    finally:
        close_yolo()
        AgentServer.shut_down()


if __name__ == "__main__":
    main()
