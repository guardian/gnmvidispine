from vidispine_api import VSApi
import xml.etree.ElementTree as ET
import traceback


class VSGlobalMetadataGroup(VSApi):
    def __init__(self,*args,**kwargs):
        super(VSGlobalMetadataGroup,self).__init__(*args,**kwargs)
        self.xmlnodes = []

    def _addNode(self,xmlnode):
        self.xmlnodes.append(xmlnode)

    def values(self):
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        rtn = []
        for node in self.xmlnodes:
            key = {}
            key['uuid'] = node.attrib['uuid']
            for fieldnode in node.findall("{0}field".format(ns)):
                try:
                    fieldname = fieldnode.find("{0}name".format(ns)).text
                    values = []
                    for valnode in fieldnode.findall("{0}value".format(ns)):
                        values.append(valnode.text)
                    if len(values) == 1:
                        key[fieldname] = values[0]
                    else:
                        key[fieldname] = values
                except Exception as e:
                    raise e
            rtn.append(key)
        return rtn


class VSGlobalMetadata(VSApi):
    def populate(self):
        self.xml_doc = self.request("/metadata")

    def get_group(self,groupname):
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        #ET.dump(self.xml_doc)

        rtn = VSGlobalMetadataGroup(self.host,self.port,self.user,self.passwd)

        for groupnode in self.xml_doc.findall("{0}timespan/{0}group".format(ns)):
            #ET.dump(groupnode)
            try:
                name = groupnode.find("{0}name".format(ns)).text
                if groupname == name:
                    rtn._addNode(groupnode)
            except AttributeError as e:
                pass

        return rtn
