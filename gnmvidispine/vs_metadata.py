__author__ = 'Andy Gallagher <andy.gallagher@theguardian.com>'

import xml.etree.ElementTree as ET


class VSMetadata:
    def __init__(self, initial_data={}):
        self.contentDict=initial_data
        self.primaryGroup = None

    def addValue(self,key,value):
        if key in self.contentDict:
            self.contentDict[key].append(value)
        else:
            self.contentDict[key]=[]
            self.contentDict[key].append(value)

    def setPrimaryGroup(self,g):
        self.primaryGroup = g

    def toXML(self,mdGroup=None):
        from datetime import datetime
        xmldoc=ET.ElementTree()

        ns = "{http://xml.vidispine.com/schema/vidispine}"
        rootEl=ET.Element('{0}MetadataDocument'.format(ns))
        xmldoc._setroot(rootEl)

        timespanEl=ET.Element('{0}timespan'.format(ns),
                              attrib={'start': '-INF',
                                      'end': '+INF'})
        rootEl.append(timespanEl)

        if mdGroup is None and self.primaryGroup is not None:
            mdGroup = self.primaryGroup

        if(mdGroup):
            groupEl=ET.Element('{0}group'.format(ns))
            groupEl.text=mdGroup
            rootEl.append(groupEl)

        for key,value in self.contentDict.items():
            fieldEl=ET.Element('{0}field'.format(ns))

            nameEl=ET.Element('{0}name'.format(ns))
            nameEl.text = key
            fieldEl.append(nameEl)

            if not isinstance(value,list):
                value = [value]

            for line in value:
                valueEl=ET.Element('{0}value'.format(ns))
                if isinstance(line,datetime):
                    line = line.strftime("%Y-%m-%dT%H:%M:%S%Z")

                valueEl.text = unicode(line)
                fieldEl.append(valueEl)

            timespanEl.append(fieldEl)

        return ET.tostring(rootEl,encoding="UTF-8")