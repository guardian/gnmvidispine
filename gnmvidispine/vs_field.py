__author__ = 'andy.gallagher@theguardian.com'

from .vidispine_api import *
import xml.etree.ElementTree as ET
import logging


class VSField(VSApi):
    """
    This class represents a metadata field in Vidispine.

    To access an existing field:
     f = VSField(host,port,user,password)
     f.populate('field_id')
    To create a new field:
     f = VSField(host,port,user,password)
     f.create('field_id','field_type',default_value='spam')
     (default_value is optional)
    """

    def __init__(self, *args,**kwargs):
        """
        Initialises a new VSField object
        :param host:
        :param port:
        :param user:
        :param passwd:
        :return:
        """
        super(VSField, self).__init__(*args,**kwargs)
        #self.name = "INVALIDNAME"
        #self.type = "INVALIDTYPE"
        #self.defaultval = ""
        #self.origin = ""
        #self.contentDict = {}
        self.portalData = {}
        self.dataContent = ET.Element('MetadataFieldDocument', attribs={'xmlns': 'http://xml.vidispine.com/schema/vidispine'}) 
        self._logger = logging.getLogger('VSField')

    def _value_or_none(self,xp):
#        try:
            return self.dataContent.find('{0}{1}'.format(self.xmlns,xp)).text
#        except AttributeError:
#            return None

    @property
    def name(self):
        return self._value_or_none('name')

    @name.setter
    def name(self,newname):
        if self.dataContent is not None:
            node = self.dataContent.find('{0}name'.format(self.xmlns))
            node.text = newname

    @property
    def type(self):
        return self._value_or_none('type')

    @type.setter
    def type(self,value):
        node = self.dataContent.find('{0}type'.format(self.xmlns))
        node.text = value

    @property
    def default_value(self):
        return self._value_or_none('defaultValue')

    @default_value.setter
    def default_value(self,value):
        node = self.dataContent.find('{0}defaultValue'.format(self.xmlns))
        node.text = value

    @property
    def origin(self):
        return self._value_or_none('origin')

    @origin.setter
    def origin(self,value):
        node = self.dataContent.find('{0}origin'.format(self.xmlns))
        node.text = value

    def create(self, field_id, type, default_value=None,origin='VX',commit=True):
        """
        Create a new field
        :param field_id: Vidispine ID of the field to create
        :param type: Data type. Consult Vidispine documentation for details.
        :param default_value: (optional) default value. This should be specified as a string.
        :param origin: (optional) site identifier.  VX is used by default if this is not specified.
        :param commit: (optional) save the field to Vidispine immediately.  Defaults to True.
        :return: self
        """
        from xml.etree.ElementTree import Element,SubElement
        self.dataContent = Element('MetadataFieldDocument',attrib={'xmlns': 'http://xml.vidispine.com/schema/vidispine'})
        node = SubElement(self.dataContent,'name')
        node.text = field_id
        node = SubElement(self.dataContent,'type')
        node.text = type
        if default_value is not None:
            node = SubElement(self.dataContent, 'defaultValue')
            node.text = str(default_value)
        node = SubElement(self.dataContent, 'origin')
        node.text = origin
        node = SubElement(self.dataContent, 'data')
        knode = SubElement(node,"key")
        knode.text = "extradata"
        vnode = SubElement(node,"value")

        #SubElement(self.dataContent,'data')

        self.dataContent = ET.fromstring(ET.tostring(self.dataContent))
        self._logger.debug(ET.tostring(self.dataContent))
        if commit:
            self.commitXML()
        return self

    def _node_find_or_create(self,parent,xp):
        node = parent.find(xp.format(self.xmlns))
        if node is None:
            node = ET.SubElement(parent,xp.format(self.xmlns))
        return node

    def set_string_restriction(self,min,max):
        if not isinstance(min,int): raise TypeError
        if not isinstance(max,int): raise TypeError

        node = self._node_find_or_create(self.dataContent,"{0}stringRestriction")

        min_node = self._node_find_or_create(node,"{0}minLength")
        min_node.text = str(min)

        max_node = self._node_find_or_create(node,"{0}maxLength")
        max_node.text = str(max)

    def populate(self, id):
        """
        Populate the object with data about a specific Vidispine field
        :param id: Vidispine field ID.  In the Portal interface, this is shown at the bottom of the right-hand bar
        :return:
        """
        self._logger.debug("Looking up metadata field %s..." % id)
        self.dataContent = self.request("/metadata-field/%s?data=all" % id, method="GET")
        self.findPortalData(self.dataContent.find('{0}data'.format(self.xmlns)))
        return self

    def set_portal_data(self,data):
        """
        Updates the Portal-specific data object with a new one
        :param data: dictionary containing new Portal-specific data
        :return:
        """
        if not isinstance(data,dict):
            raise TypeError

        for k,v in list(data.items()):
            self.portalData[k] = v

        parent_node = self.dataContent.find('{0}data'.format(self.xmlns))
        if parent_node is None:
            parent_node = ET.SubElement(self.dataContent,"{0}data".format(self.xmlns))

        node = self.findPortalDataNode(parent_node, should_create=True)
        node.text = json.dumps(self.portalData)

        self.commitXML()
        pass

    def dump_text(self, *fields):
        """
        Debugging method to output information about the field to STDOUT
        :param fields: optionally, a list of extra fields to display
        :return: None
        """
        print("Metadata Field:")
        print("\tID: %s" % (self.name))
        print("\tData type: %s" % (self.type))
        print("\tOrigin: %s" % (self.origin))
    #    for f in fields:
    #        print "\t%s: %s" % (f, self.contentDict[f])

        print("\tPortal data:\n")
        for f, v in list(self.portalData.items()):
            print("\t%s: %s" % (f, v))

    def commitXML(self):
        """
        Saves changes made to the object back to Vidispine.  Raises a VSException if this fails.
        :return: None
        """
        response=self.request("/metadata-field/%s" % self.name, method="PUT",body=ET.tostring(self.dataContent))
        self._logger.debug("VSField::commitXML: got %s" % response)

    def delete(self):
        """
        Requests that Vidispine delete this field record.  Raises a VSException if this fails.
        :return: None
        """
        response = self.request("/metadata-field/%s" % self.name, method="DELETE")
        self._logger.debug("VSField::delete: got %s" % response)
