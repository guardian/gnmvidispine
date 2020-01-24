from .vidispine_api import VSApi
from pprint import pprint
import xml.etree.ElementTree as ET


class VSAccess(VSApi):
    """
    Represents an individual entry in an Access Control List (ACL)
    """
    def __init__(self,*args,**kwargs):
        super(VSAccess,self).__init__(*args,**kwargs)
        self.parent = None
        self.name = "INVALIDNAME"
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        self.dataContent = ET.Element('{0}access'.format(ns))

    def populate(self, item, accessid):
        """
        Populate from a Vidispine object
        :param item: VSItem or other VS-type object to query
        :param accessid: Type of access to query
        :return: None
        """
        self.parent = item
        self.name = accessid

        url = "/{0}/{1}/access/{2}".format(item.type,item.name,accessid)
        self.dataContent = self.request(url)

    def populateFromNode(self,node):
        self.dataContent = node
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        self.name = node.attrib['id']

    def nodeContent(self,node,path):
        """
        Internal method to get the content of a node
        :param node:
        :param path:
        :return:
        """
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        try:
            return node.find('{0}{1}'.format(ns,path)).text
        except Exception:
            return None

    def setNode(self,node,path,value):
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        try:
            node.find('{0}{1}'.format(ns,path)).text = value
        except Exception:
            n = ET.Element(path)
            n.text = value
            node.append(n)

    @property
    def grantor(self):
        """
        :return: Name of the grantor
        """
        #pprint(self.dataContent)
        return self.nodeContent(self.dataContent,'grantor')

    @property
    def recursive(self):
        """
        :return: Is this recursively inherited
        """
        return self.nodeContent(self.dataContent,'recursive')

    @recursive.setter
    def recursive(self,value):
        """
        Set whether this access is recursive
        :param value:
        :return:
        """
        str="false"
        if value:
            str="true"
        self.setNode(self.dataContent,'recursive',str)

    @property
    def permission(self):
        return self.nodeContent(self.dataContent,'permission')

    @permission.setter
    def permission(self,value):
        if value != 'NONE' and value != 'READ' and value !='WRITE' and value != 'ALL':
            raise ValueError
        self.setNode(self.dataContent,'permission',value)

    @property
    def affectedUser(self):
        return self.nodeContent(self.dataContent,'user')

    @affectedUser.setter
    def affectedUser(self,value):
        self.setNode(self.dataContent,'user',value)

    @property
    def group(self):
        return self.nodeContent(self.dataContent,'group')

    @group.setter
    def group(self,value):
        self.setNode(self.dataContent,'group',value)

    def __eq__(self, other):
        if not isinstance(other,VSAccess):
            raise TypeError

        if other.group==self.group and other.user==self.user and other.permission==self.permission and other.affectedUser==self.affectedUser and other.recursive==self.recursive and other.grantor==self.grantor:
            return True
        return False

    def asXML(self):
        """
        Returns a Vidispine XML representing the contents of this entry
        :return: String of Vidispine XML
        """
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        docNode = ET.Element('{0}AccessControlDocument'.format(ns))
        for n in self.dataContent:
            docNode.append(n)
        return ET.tostring(docNode,encoding="UTF-8")


class VSAcl(VSApi):
    """
    Represents an Access Control List (ACL) for a Vidispine object
    """
    def __init__(self,*args,**kwargs):
        super(VSAcl,self).__init__(*args,**kwargs)
        self.parent = None
        self.name = "INVALIDNAME"
        self._entries = []

    def populate(self, item):
        """
        Retrieve data from a Vidispine entity and load it into this object
        :param item: VSItem or similar VS-object to retrieve access control information for
        :return: None
        """
        self.parent = item

        self._entries = []
        url = "/{0}/{1}/access".format(item.type,item.name)
        dataContent = self.request(url)

        ns = "{http://xml.vidispine.com/schema/vidispine}"
        for node in dataContent.findall('{0}access'.format(ns)):
            a = VSAccess(self.host,self.port,self.user,self.passwd)
            a.populateFromNode(node)
            self._entries.append(a)

    def populateFromString(self,xmldata):
        """
        Reads ACL data in from a string
        :param xmldata: String representing XML of ACL data
        :return: None
        """
        self.parent = None
        self._entries = []

        dataContent = ET.fromstring(xmldata)
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        for node in dataContent.findall('{0}access'.format(ns)):
            a = VSAccess(self.host,self.port,self.user,self.passwd)
            a.populateFromNode(node)
            self._entries.append(a)

    def entries(self):
        """
        Generator to yield each entry of the access control list as a VSAccess object
        :return:
        """
        for e in self._entries:
            yield e

    def add(self,entry):
        """
        Add a VSAccess entry to the list
        :param entry: VSAccess to add
        :return: None
        """
        url = "/{0}/{1}/access".format(self.parent.type,self.parent.name)
        self.request(url,method="POST",body=entry.asXML())

        self.populate(self.parent)

    def removeByRef(self, entry):
        """
        Remove the entry from the ACL
        :param entry: VSAccess entry to remove from the list
        :return:
        """
        if entry.permission =="OWNER":
            return  #can't remove owner permission

        url = "/{0}/{1}/access/{2}".format(self.parent.type,self.parent.name,entry.name)
        self.request(url,method="DELETE")

        self.populate(self.parent)

    def filter(self,grantor=None,recursive=None,permission=None,affectedUser=None,group=None):
        #rtn = []

        for e in self._entries:
            should_take = True
            if grantor is not None and e.grantor!=grantor:
                should_take=False
            if recursive is not None and e.recursive!=recursive:
                should_take=False
            if permission is not None and e.permission!=permission:
                should_take=False
            if affectedUser is not None and e.affectedUser!=affectedUser:
                should_take=False
            if group is not None and e.group!=group:
                should_take=False
            if should_take:
                yield e

