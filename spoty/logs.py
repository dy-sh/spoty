from loguru import logger as log
import sys

log.remove() # remove default handler to prevent printing to console

log.add('logs/logs.log', level='DEBUG')
