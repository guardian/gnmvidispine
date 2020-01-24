__author__ = 'Andy Gallagher <andy.gallagher@theguardian.com>'

from .vidispine_api import VSApi,VSException,VSNotFound
import xml.etree.ElementTree as ET
import logging

class VSGlobalMetadata(VSApi):
    def __init__(self, *args,**kwargs):
        super(VSGlobalMetadata, self).__init__(*args,**kwargs)
        self.contentDict = {}
        self.byUUID = {}

    def populate(self):
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        self.dataContent = self.request("/metadata")

        for groupNode in self.dataContent.findall("{0}timespan/{0}group".format(ns)):
            try:
                groupName = groupNode.find('{0}name'.format(ns)).text
                uuid = groupNode.attrib['uuid']
            except Exception as e:
                logging.warning(str(e))
                continue

            groupValues=[]
            for fieldNode in groupNode.findall("{0}field".format(ns)):
                nameNode=fieldNode.find("{0}name".format(ns))
                valueNode=fieldNode.find("{0}value".format(ns))
                if nameNode is not None and valueNode is not None:
                    elementValue= VSElementValue(self.host,self.port,self.user,self.passwd)
                    elementValue.name=nameNode.text
                    elementValue.value=valueNode.text
                    groupValues.append(elementValue)

            self.contentDict[groupName]=groupValues
            self.byUUID[uuid]=groupValues

    def getall(self,name):
        if not name in self.contentDict:
            raise AssertionError("%s is not a recognised global metadata group name" % name)

        for v in self.contentDict[name]:
            yield v


class VSElementValue(VSApi):
    def __init__(self, *args,**kwargs):
        super(VSElementValue, self).__init__(*args,**kwargs)
        self.dataContent = None
        self.name = "INVALIDNAME"
        self.value = "(no value)"
        self.contentDict = {}
        self.values = []
        self.empty = True

    def populate(self,id):
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        self.name = id
        self.dataContent = self.request("/metadata/%s" % id)

        #print ET.dump(self.dataContent)

        nameNode = self.dataContent.find('{0}group/{0}name'.format(ns))
        if nameNode is not None:
            self.name=nameNode.text

        fieldNodes = self.dataContent.findall('{0}group/{0}field'.format(ns))
        for fieldNode in fieldNodes:
            try:
                key = fieldNode.find('{0}name'.format(ns)).text
                val = fieldNode.find('{0}value'.format(ns)).text
                self.contentDict[key] = val
                self.values.append(val)

            except KeyError:
                pass
            except AttributeError:
                pass
        if len(self.values)>0:
            self.empty = False
            self.value = self.values[0]