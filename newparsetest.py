#!/usr/bin/env python

from xml.etree.cElementTree import parse
import sys
from pprint import pprint

data = parse(sys.argv[1])

rootEl = data.getroot()

for childnode in rootEl:
    #pprint(childnode)
    if childnode.tag.endswith('hits'):
        print("Hits: {0}".format(int(childnode.text)))
    elif childnode.tag.endswith('item'):
        itemid = childnode.attrib['id']
        itemstart = childnode.attrib['start']
        itemend = childnode.attrib['end']
        print("Item: {0} ({1} -> {2})".format(itemid, itemstart,itemend))
    elif childnode.tag.endswith('collection'):
        pass
    elif childnode.tag.endswith('entry'):
        pass

