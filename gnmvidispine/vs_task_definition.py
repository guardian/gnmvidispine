import xml.etree.ElementTree as ET
from vidispine_api import VSApi,VSException,VSNotFound
import json
import sys
import os.path
from pprint import pprint

__author__ = 'Andy Gallagher <andy.gallagher@theguardian.com>'

#FIXME: needs to be seperated out
#thanks to https://gist.github.com/zlalanne/5711847

def CDATA(text=None,tail=""):
    element = ET.Element('![CDATA[')
    element.text = text
    element.tail = tail
    return element

#class ElementTreeCDATA(ET.ElementTree):
#    def _write(self, file, node, encoding, namespaces):
#        if node.tag is '![CDATA[':
#            text = node.text.encode(encoding)
#            file.write("\n<![CDATA[%s]]>\n" % text)
#        else:
#            ET.ElementTree._write(self, file, node, encoding, namespaces)
ET._original_serialize_xml = ET._serialize_xml


def _serialize_xml(write, elem, encoding, qnames, namespaces):
    if elem.tag == '![CDATA[':
        write("<%s%s]]>%s" % (elem.tag, elem.text, elem.tail))
        return
    return ET._original_serialize_xml(
        write, elem, encoding, qnames, namespaces)

ET._serialize_xml = ET._serialize['xml'] = _serialize_xml


def serializeXML(info,parentNode,ns=""):
    #root = ET.Element("{0}{1}".format(ns,rootname))
    for k,v in info.items():
        node = ET.SubElement(parentNode,k)
        if(type(v) == type(dict)):
            serializeXML(v,node,ns)
        else:
            #value = v
            node.text = v
    return



class VSTaskDefinition(VSApi):
    def populate(self,vsid):
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        self.dataContent = self.request("/task-definition/{0}".format(vsid))

        self.id=vsid
        self.contentDict = {}

        for key in ['description','flags','bean','method','plugin','step','jobType','cleanup','critical','script']:
            nodeName = "{0}%s" % key
            node = self.dataContent.find(nodeName.format(ns))

            if node is not None:
                self.contentDict[key] = node.text

    def store(self):
        #fixme: this SHOULD raise an exception if the script exists and is not valid javascript
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        for key in ['description','flags','bean','method','plugin','step','jobType','cleanup','critical', 'dependency', 'parallelDependency']:
            if key in self.contentDict:
                nodeName = "{0}%s" % key
                node = self.dataContent.find(nodeName.format(ns))
                if node is None:
                    root = self.dataContent
                    node = ET.SubElement(root,"{0}{1}".format(ns,key))
                if type(self.contentDict[key]) == type(dict()):
                    serializeXML(self.contentDict[key],node)
                else:
                    node.text = self.contentDict[key]
        for key in ['script']:
            if key in self.contentDict:
                nodeName = "{0}%s" % key
                node = self.dataContent.find(nodeName.format(ns))
                if node is None:
                    root = self.dataContent
                    node = ET.SubElement(root,"{0}{1}".format(ns,key))
                if type(self.contentDict[key]) == type(dict()):
                    serializeXML(self.contentDict[key],node)
                else:
                    cdata = CDATA(self.contentDict[key])
                    #self.dataContent=ElementTreeCDATA(self.dataContent)
                    node.append(cdata)
                    subtext = node.find("text")
                    if subtext:
                        node.delete(subtext)

        ET.ElementTree(self.dataContent).write(sys.stdout,"utf-8")

    def create(self):
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        self.dataContent = ET.Element("{0}TaskDefinitionDocument".format(ns))
        self.contentDict['dependency'] = {"step": "0","previous": "false","allprevious": "false"}
        self.contentDict['parallelDependency'] = {"step": "0","previous": "false","allprevious": "false"}
        self.store()
        pass