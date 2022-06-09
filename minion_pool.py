import logging
import random
import sys

#import utils.minion_handler
import minion_handler 

logging.basicConfig(format='%(asctime)s\t%(filename)s:%(lineno)d\t%(message)s', datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Mapping of available minions to corresponding video conferences.
minions = {
    "raspi-e4:5f:01:28:d9:c2": "https://ucsb.zoom.us/j/8065842740" #vino
    # "raspi-e4:5f:01:28:d9:c2": "https://ucsb.zoom.us/j/2432166736" #PJ
}

class MinionPool:
    def __init__(self):
        self.minions = {minion_handler.MinionHandler(m_id): url for m_id, url in minions.items()}
        if not self.minions:
            raise Exception("No minions are available.")

        for minion in self.minions:
            logger.info(f"{minion.minion_id} is available.")

    def get(self, count=0):
        """
        Returns a tuple of a MinionHandler and its corresponding video
        conference URL. Each minion is connected to a single video conference.
        """
        if not isinstance(count, int):
            raise Exception("count should be an integer")
        return list(self.minions.items())[0:count]
