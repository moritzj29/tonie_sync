#!/usr/bin/python

"""Start up script for Docker Container
"""

import sys
import getopt
import logging
import os
from time import sleep
from tonie_sync import TonieSpotifySync


if __name__ == '__main__':

    loglevel = 'WARNING'
    interval = 5
    directory = os.getcwd()
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], "hd:i:l:", ["directory=", "interval=", "loglevel="])
    except getopt.GetoptError as err:
        print('start.py --directory=<directory> --interval=<interval>'
              ' --loglevel=<level>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('start.py --directory=<directory> --interval=<interval>'
                  ' --loglevel=<level>')
            sys.exit()
        elif opt in ('-d', '--directory'):
            directory = arg
        elif opt in ('-i', '--interval'):
            interval = int(arg)
        elif opt in ('-l', '--loglevel'):
            loglevel = arg

    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    # create file handler
    fh = logging.FileHandler(os.path.join(directory, 'Logfile.log'))
    fh.setLevel(numeric_level)
    # create console handler
    ch = logging.StreamHandler()
    ch.setLevel(numeric_level)
    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    tss = TonieSpotifySync(config_from_file=True, directory=directory)
    tss.start_sync_service(sleeptime=interval, background=False)
