from vidispine_api import VSApi, VSNotFound
import xml.etree.ElementTree as ET
import traceback


class VSGlobalMetadataGroup(VSApi):
    """
    This class allows access to the actual values and their IDs, as present in the global metadata groups.
    You get an initialised instance by using VSGlobalMetadata, then get a dictionary of uuids and values by calling
    .values() on this object.
    """
    class VSGlobalMetadataIterator(object):
        def __init__(self, xmlNodeList, xmlns):
            self._nodelist = xmlNodeList
            self.xmlns = xmlns
            self._internalcounter = -1

        def _build_dict_for_current(self):
            node = self._nodelist[self._internalcounter]

            rtn = {}
            rtn['uuid'] = node.attrib['uuid']
            for fieldnode in node.findall("{0}field".format(self.xmlns)):
                fieldname = fieldnode.find("{0}name".format(self.xmlns)).text
                values = []
                for valnode in fieldnode.findall("{0}value".format(self.xmlns)):
                    values.append(valnode.text)
                if len(values) == 1:
                    rtn[fieldname] = values[0]
                else:
                    rtn[fieldname] = values
            return rtn

        def next(self):
            self._internalcounter +=1
            if self._internalcounter>=len(self._nodelist): raise StopIteration

            return self._build_dict_for_current()

    def __init__(self,groupname="(none)",*args,**kwargs):
        super(VSGlobalMetadataGroup,self).__init__(*args,**kwargs)
        self.xmlnodes = []
        self.name = groupname

    def _addNode(self,xmlnode):
        self.xmlnodes.append(xmlnode)

    def __iter__(self):
        return self.VSGlobalMetadataIterator(self.xmlnodes,self.xmlns)

    def values(self):
        """
        DEPRECATED DO NOT USE
        Returns a dictionary of keys and values from this metadata group
        :return: dict
        """
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

    def value_for(self,name,namefield='gnm_subgroup_displayname'):
        for entry in self:
            if entry[namefield]==name: return entry
        return None

class VSGlobalMetadata(VSApi):
    """
    This class represents the global metadata groups of a Vidispine system.  You can access them by:
    md = VSGlobalMetadata(hostname,port,user,passwd)
    md.populate()
    #either iterate
    for group in md.items():
      pprint(group.values())
    #or get a group directly
    group = md.get_group("MyMetaGroup")
    pprint(group.values())

    """
    def populate(self):
        """
        Loads the global metadata definitions from the server into memmory.  Call this first, before calling anything else.
        :return: self
        """
        self.xml_doc = self.request("/metadata")
        return self

    def get_group(self,groupname):
        """
        Returns a VSGlobalMetadataGroup object for the given group name
        :param groupname: group name that you're interested in
        :return: The group, or raises VSNotFound
        """
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        #ET.dump(self.xml_doc)

        rtn = VSGlobalMetadataGroup(groupname=groupname, host=self.host,port=self.port,user=self.user,passwd=self.passwd)
        foundit = False

        for groupnode in self.xml_doc.findall("{0}timespan/{0}group".format(ns)):
            #ET.dump(groupnode)
            try:
                name = groupnode.find("{0}name".format(ns)).text
                if groupname == name:
                    rtn._addNode(groupnode)
                    foundit = True
            except AttributeError as e:
                pass

        if not foundit:
            e=VSNotFound()
            e.exceptionWhat=groupname
            e.exceptionContext="Global metadata group"
            raise e
        return rtn

    def items(self):
        """
        Generator that yields VSMetadataGroup objects for each group present
        :return: Yields VSMetadataGroup
        """
        rtn = {}
        for groupnode in self.xml_doc.findall("{0}timespan/{0}group".format(self.xmlns)):
            try:
                name = groupnode.find("{0}name".format(self.xmlns)).text
                if not name in rtn:
                    rtn[name] = VSGlobalMetadataGroup(groupname=name,host=self.host, port=self.port, user=self.user,
                                                      passwd=self.passwd)
                rtn[name]._addNode(groupnode)
            except AttributeError as e:
                pass

        for k,v in rtn.items():
            yield v
