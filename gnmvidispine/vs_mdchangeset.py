from .vidispine_api import VSApi
import xml.etree.cElementTree as ET
import dateutil.parser


class VSMDChange(object):
    """
    This class represents an individual field change within a changeset.
    It contains the following attributes which should be considered read-only:

    name - Vidispine ID of the change
    timestamp - datetime object of the change timestamp
    fieldname - field that was changed
    value - value that it was changed to. This will be either a string or a list of strings.
    uuid - uuid of the change
    username = user that made the change
    """
    def __init__(self, node, xmlns):
        self.name=None
        self.timestamp=None
        self.fieldname=None
        self.value=None
        self.uuid=None
        self.username=None

        if node is not None:
            self.timestamp = dateutil.parser.parse(node.attrib['timestamp'])
            self.username = node.attrib['user']
            self.name = node.attrib['change']
            namenode = node.find('{0}name'.format(xmlns))
            if namenode is not None:
                self.fieldname = namenode.text

            self.value = []
            for valnode in node.findall('{0}value'.format(xmlns)):
                self.value.append(valnode.text)

            if len(self.value)==1:
                self.value=self.value[0]

    def __unicode__(self):
        return '{id}: {f} changed by {u} to {v} at {t}'.format(id=self.name,u=self.username,
                                                                f=self.fieldname,v=self.value,t=self.timestamp)

    def __str__(self):
        return self.__unicode__().decode('ascii')


class VSMDChangeSet(VSApi):
    """
    This class represents an individual Vidispine metadata change set. Normally you wouldn't initialise it directly,
    but get it from an object that supports complex metadata, e.g. item.metadata_changeset()
    """
    def __init__(self,*args,**kwargs):
        super(VSMDChangeSet,self).__init__(*args,**kwargs)
        self.dataContent=None
        self._fieldlist = None

    def from_xml(self,xmlnode):
        """
        Initialise the changeset from an XML fragment
        :param xmlnode: Elementtree XML node of the <changeSet> xml node
        :return: self
        """
        self.dataContent = xmlnode
        self.mdContent = self.dataContent.find('{0}metadata'.format(self.xmlns))
        return self

    @property
    def name(self):
        """
        Return the Vidispine id of the changeset
        :return:
        """
        if self.dataContent is None: raise ValueError("Not populated!")
        content = self.dataContent.find('{0}id'.format(self.xmlns)).text
        return content

    def _timespans(self):
        if self.dataContent is None: raise ValueError("Not populated!")
        for node in self.mdContent.findall('{0}timespan'.format(self.xmlns)):
            yield node

    @property
    def fields(self):
        """
        Returns a list of the fields that have been modified in this change set
        :return:
        """
        if self._fieldlist is None:
            self._fieldlist = []
            for tsnode in self._timespans():
                #logging.debug("got timespan node {0}".format(tsnode))
                for fieldNode in tsnode.findall('{0}field'.format(self.xmlns)):
                #    logging.debug("got field node {0}".format(fieldNode))
                    fieldNameNode = fieldNode.find('{0}name'.format(self.xmlns))
                    if fieldNameNode is not None:
                        self._fieldlist.append(fieldNameNode.text)
            if len(self._fieldlist) == 0:
                self._fieldlist = None

        return self._fieldlist

    def changes(self, fieldname=None):
        """
        Generator that yields VSChange objects for each individual change in the changeset
        :param fieldname: optional, if this is specified then only changes to this exact fieldname will be yielded
        :return: None, it's a generator
        """
        for tsnode in self._timespans():
            # logging.debug("got timespan node {0}".format(tsnode))
            for fieldNode in tsnode.findall('{0}field'.format(self.xmlns)):
                c=VSMDChange(fieldNode,self.xmlns)
                if fieldname is not None:
                    if c.fieldname!=fieldname:
                        continue
                yield c

    def __unicode__(self):
        return 'Changeset ID {0} comprising fields {1}'.format(self.name,self.fields)

if __name__ == "__main__":
    import logging
    import sys
    logging.basicConfig(level=logging.DEBUG)
    logging.info("Performing tests on vs_mdchangeset")

    doctree = ET.parse(sys.argv[1])
    for node in doctree.findall('{0}changeSet'.format('{http://xml.vidispine.com/schema/vidispine}')):
        cs=VSMDChangeSet()
        cs.from_xml(node)
        #logging.info(unicode(cs))
        f=None
        if len(sys.argv)>2:
            f=sys.argv[2]
        for c in cs.changes(fieldname=f):
            logging.info(str(c))
