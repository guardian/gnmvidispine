import http.client
import base64
import string
import xml.etree.ElementTree as ET
from pprint import pprint
import logging
import traceback

from .vidispine_api import HTTPError, VSApi,VSException,InvalidData
from .vs_storage_rule import VSStorageRule

from .vs_item import VSItem

def allLibraries(vsapi):
    result = vsapi.request("/library",method="GET")

    n=0
    ns="{http://xml.vidispine.com/schema/vidispine}"
    hitsNode = result.find("{0}hits".format(ns))
    if hitsNode is not None:
        total_hits = int(hitsNode.text)
    else:
        raise InvalidData("No hits node present in returned data from library list")

    n=0
    while n<total_hits:
        for node in result.findall("{0}uri".format(ns)):
            libid = node.text
            lib = VSLibrary(vsapi.host,vsapi.port,vsapi.user,vsapi.passwd)
            lib.name = libid
            yield lib
            n+=1
        result = vsapi.request("/library",method="GET",matrix={ "first": n})


class VSLibrary(VSApi, list):
    def __init__(self,*args,**kwargs):
        super(VSLibrary, self).__init__(*args,**kwargs)
        self.dataContent = None
        self.hits = 0
        self.name = ""
        self.settings = None
        self.storage_rule = None
        # itemList=[]

    def create(self, bodydoc, maxItems=100, noyield=False):
        matrix = {'autoRefresh': 'false',
                  'updateFrequency': 60,
                  'updateMode': 'REPLACE',
                  'number': maxItems}
        query = {'result': 'library'}
        namespace = "{http://xml.vidispine.com/schema/vidispine}"
        #pprint(matrix)

        #this will throw an HTTPError if it doesn't work, which is the caller's responsibility to catch
        self.dataContent = self.request("/item", method="PUT", matrix=matrix, query=query, body=bodydoc)

        #pprint(dataContent)
        #print ET.tostring(dataContent)

        self.hits = int(self.dataContent.find("{0}hits".format(namespace)).text)
        self.name = self.dataContent.find('{0}library'.format(namespace)).text

        logging.debug("Got new library %s with %d items" % (self.name, self.hits))

        if not noyield:
            namespace = "{http://xml.vidispine.com/schema/vidispine}"
            for item in self.dataContent.findall('{0}item'.format(namespace)):
                newitem = VSItem(host=self.host, port=self.port, user=self.user, passwd=self.passwd)
                #print "\tGot item with ID %s\n" % item.attrib['id']
                newitem.populate(item.attrib['id'])
                self.append(newitem)

    def refresh(self):
        if self.name=="":
            raise InvalidData("library object not initialised")

        namespace = "{http://xml.vidispine.com/schema/vidispine}"
        self.dataContent = self.request("/library/{0}".format(self.name),method="GET")

        self.hits = int(self.dataContent.find("{0}hits".format(namespace)).text)

    #generator to get individual items out
    def items(self):
        if self.dataContent is None:
            self.refresh()

        namespace = "{http://xml.vidispine.com/schema/vidispine}"
        for item in self.dataContent.findall('{0}item'.format(namespace)):
            newitem = VSItem(host=self.host, port=self.port, user=self.user, passwd=self.passwd)
            #print "\tGot item with ID %s\n" % item.attrib['id']
            newitem.populate(item.attrib['id'])
            yield newitem

    def settingsXML(self):
        namespace = "{http://xml.vidispine.com/schema/vidispine}"
        if self.settings is None:
            response=self.request("/library/{0}/settings".format(self.name))
            self.settings=ET.dump(response)
        return self.settings

    def storageRule(self):
        if self.storage_rule is None:
            response=self.request("/library/{0}/storage-rule".format(self.name))
            self.storage_rule = VSStorageRule(self.host,self.port,self.user,self.passwd)
            self.storage_rule.populateFromXml(response)
            #self.storage_rule_xml = ET.dump(response)
        if self.storage_rule.isEmpty():
            return None

        return self.storage_rule

    def delete(self):
        response = self.request("/library/%s" % self.name, method="DELETE")
        logging.debug("VSLibrary::delete: got %s" % response)

    def set_metadata(self, md):
        return super(VSLibrary, self).set_metadata("/library/%s" % self.name, md)

    def get_metadata(self):
        return super(VSLibrary, self).get_metadata("/library/%s" % self.name)