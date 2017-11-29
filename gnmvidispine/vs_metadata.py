__author__ = 'Andy Gallagher <andy.gallagher@theguardian.com>'

import xml.etree.ElementTree as ET
import dateutil.parser


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


class VSMetadataMixin(object):
    _xmlns = "{http://xml.vidispine.com/schema/vidispine}"

    @staticmethod
    def _safe_get_attrib(xmlnode, attribute, default):
        try:
            return xmlnode.attrib[attribute]
        except AttributeError:
            return default

    @staticmethod
    def _safe_get_subvalue(xmlnode, subnode_name, default):
        try:
            node = xmlnode.find(subnode_name)
            if node is not None:
                return node.text
            else:
                return default
        except AttributeError:
            return default


class VSMetadataValue(VSMetadataMixin):
    def __init__(self, valuenode):
        self.uuid = self._safe_get_attrib(valuenode,"uuid", None)
        self.user = self._safe_get_attrib(valuenode, "user", None)
        try:
            self.timestamp = dateutil.parser.parse(self._safe_get_attrib(valuenode,"timestamp", None))
        except TypeError: #dateutil.parser got nothing
            self.timestamp = None
        self.change = self._safe_get_attrib(valuenode, "change", None)
        self.value = valuenode.text

    def __repr__(self):
        return "VSMetadataValue(\"{0}\")".format(self.value)


class VSMetadataAttribute(VSMetadataMixin):
    """
    this class represents the full metadata present in an xml <field> entry
    """
    def __init__(self, fieldnode):
        self.uuid = self._safe_get_attrib(fieldnode,"uuid", None)
        self.user = self._safe_get_attrib(fieldnode, "user", None)
        try:
            self.timestamp = dateutil.parser.parse(self._safe_get_attrib(fieldnode,"timestamp", None))
        except TypeError: #dateutil.parser got nothing
            self.timestamp = None
        self.change = self._safe_get_attrib(fieldnode,"change",None)
        self.name = self._safe_get_subvalue(fieldnode, "{0}name".format(self._xmlns), None)

        self.values = map(lambda value_node: VSMetadataValue(value_node), fieldnode.findall('{0}value'.format(self._xmlns)))

