import logging

#logging.basicConfig(format='%(message)s', level=logging.ERROR)
#logger = logging.getLogger(__name__)

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

# 'application' code
logger.debug("DEBUG")
logger.info("INFO")
logger.warning("WARN")
logger.error("ERROR")
logger.critical("CRITICAL")
