#! /usr/bin/env python3
import argparse
import logging
import multiprocessing
import time
from zoom import Zoom
from run_vca import arg_parser
from minion_handler import MinionHandler
from minion_pool import MinionPool

logging.basicConfig(format='%(asctime)s\t%(filename)s:%(lineno)d\t%(message)s', datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def single_experiment(minion, url, args):
    """
    Run a single experiment. Multiple instances of this function can be run
    simultaneously using the multiprocessing module.
    """
    # Initialize the instance on the server.
    with Zoom(url, args, isMinion=False) as vca:
        # Start the conference call.

        #vca.login_headless()
        
        vca.launch_driver(duration=60)
        
        vca.end_call()


def experiment(args):
    for minion, url in MinionPool().get(count=args.n_minions):
        logger.info(f"Starting run on {minion.minion_id} at {url}.")
        # Run each individual experiment in its own process.
        multiprocessing.Process(target=single_experiment, args=(minion, url, args)).start()
        time.sleep(15)


def main():
    parser = arg_parser()
    args = parser.parse_args()
    experiment(args)
 

if __name__ == "__main__":
    main()
