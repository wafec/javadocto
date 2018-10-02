import yaml
from munch import munchify

CONF = None

with open('config.yaml', 'r') as stream:
    d = yaml.load(stream)
    CONF = munchify(d)


