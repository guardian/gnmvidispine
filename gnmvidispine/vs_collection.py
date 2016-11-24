__author__ = 'Andy Gallagher <andy.gallagher@theguardian.com>'

from vs_item import VSItem
from vidispine_api import InvalidData
import urllib
import xml.etree.ElementTree as ET
import logging
import os
from traceback import format_exc
import re


class InvalidItemReferenceError(StandardError):
    """
    Error raised if a passed item is not of the correct type
    """
    pass


class ArgumentError(StandardError):
    """
    Error raised if an argument is not of the correct format
    """
    pass


class VSCollection(VSItem):
    """
    Object to represent a Collection in Vidispine.  This also supports all of the relevant methods from the VSItem class
    """
    def __init__(self, *args, **kwargs):
        super(VSCollection,self).__init__(*args,**kwargs)
        self.type = "collection"
        self.itemCount = -1

    def __unicode__(self):
        return u'Vidispine collection with ID {0}'.format(self.name)

    def populate(self, id, type="collection", specificFields=None):
        """
        Populates this object with data from the Vidispine system
        :param id: Vidispine ID of the collection to read
        :return:
        """
        super(VSCollection,self).populate(id,type="collection",specificFields=specificFields)
        #self.request("/collection/{id}".format(id=self.name))

    def addToCollection(self, item, type="item"):
        """
        Add an item to the Collection
        :param item: VSItem, VSCollection or similar to add to the collection
        :param type: "item" or "collection"
        :return: result of request()
        """
        if isinstance(item,VSItem):
            itemId = item.name
        elif isinstance(item,str):
            itemId = item
        else:
            raise InvalidItemReferenceError("The item passed was not a VSItem or string, class was %s" % item.__class__)

        #this will raise an exception back to the caller if it fails
        self.request("/collection/{collectionID}/{itemID}".format(collectionID=self.name,
                                                                  itemID=itemId),
                     query={'type': type},
                     method="PUT")

    def removeFromCollection(self, item, type=None):
        """
        Removes the given item from the collection
        :param item: VSItem, VSCollection or similar to remove from the collection
        :param type: if item is a string rather than an item then you need to specify whether it refers to an item or collection
        :return: None. Raises VSNotFound if item is not in collection, InvalidItemReferenceError or ValueError of the arguments are not correct.
        """
        if isinstance(item,VSItem):
            type="item"
            itemid = item.name
        elif isinstance(item,VSCollection):
            type="collection"
            itemid = item.name
        elif isinstance(item,basestring):
            itemid = item
        else:
            raise InvalidItemReferenceError("The item passed was not a VSItem, VSCollection or string, it was a %s" % item.__class__)
        if type is None:
            raise ValueError("when removing an item from a collection by string ID you must specify type")
        
        self.request("/collection/{collectionID}/{itemID}".format(collectionID=self.name,itemID=itemid),
                     query={'type': type},
                     method="DELETE")
        
    def setName(self, id):
        """
        Set the Vidispine ID internal to this object
        :param id: Vidispine ID
        :return:
        """
        self.name = id

    def createEmpty(self,metadata=None,title=None):
        """
        Create an empty collection, possibly populating with a pre-prepared MetadataDocument
        :param metadata: Dictionary of key/value metadata
        :param title: Title of the collection to create
        :return:
        """
        from vs_item import VSMetadataBuilder
        ns = "{http://xml.vidispine.com/schema/vidispine}"

        if metadata is None:
            raise StandardError("No metadata provided")
        if title is None:
            response = self.request("/collection",
                                method="POST")
        else:
            response = self.request("/collection",
                                    method="POST",
                                    query={'name': title})
        try:
            gotId = response.find("{0}id".format(ns)).text
            self.name = gotId
        except ValueError as e:
            raise InvalidData("Did not get created collection ID from Vidispine")

        if metadata is not None:
            self.debug = True
            #logging.debug("outputting metadata")
            #logging.debug(metadata)
            if isinstance(metadata,dict):
                b = VSMetadataBuilder(self)
                b.addMeta(metadata)
                mdContent = b.as_xml()
            elif isinstance(metadata,VSMetadataBuilder):
                mdContent = metadata.as_xml()
            else:
                mdContent = metadata

            response = self.request("/collection/{0}/metadata".format(self.name),
                                    method="PUT",
                                    body=mdContent)

    #Creates a new collection with the same metadata as this one and no content, possibly on a different system
    def copyToEmpty(self,host='localhost',port=8080,user='admin',passwd=None):
        """
        Creates a new collection with the same metadata as this one and no content, possibly on a different system
        :param host: Vidispine host to create the new collection on
        :param port: Port to connect to destination Vidispine
        :param user: Username for destination vidispine
        :param passwd: Password for destination vidispine
        :return: Initialised, new VSCollection object containing same metadata as this one but no content.
        """
        md = self.metadata_document()

        newItem = VSCollection(host,port,user,passwd)
        newItem.createEmpty(metadata=md,title=self.get('title'))
        return newItem

    def content(self, shouldPopulate=True):
        """
        Generator to iterate through all contents of this Collection
        :param shouldPopulate: True if the objects should be populated (looked up in database) before yielding them.
        False to return un-populated objects
        :return: None (yields results)
        """
        response = self.request("/collection/{0}".format(self.name))
        ns = "{http://xml.vidispine.com/schema/vidispine}"

        for itemNode in response.findall("{0}content".format(ns)):
            try:
                entrytype = itemNode.find("{0}type".format(ns))
                if entrytype.text == "collection":
                    rtn = VSCollection(self.host,self.port,self.user,self.passwd)
                    if shouldPopulate:
                        rtn.populate(itemNode.find("{0}id".format(ns)).text)
                    else:
                        rtn.name = itemNode.find("{0}id".format(ns)).text
                    yield rtn
                if entrytype.text == "item":
                    rtn = VSItem(self.host,self.port,self.user,self.passwd)
                    if shouldPopulate:
                        rtn.populate(itemNode.find("{0}id".format(ns)).text)
                    else:
                        rtn.name = itemNode.find("{0}id".format(ns)).text
                    yield rtn
            except StandardError as e:
                logging.error(e)
                logging.error(format_exc())

    def searchWithin(self):
        # from vs_search import VSCollectionSearch
        # s = VSCollectionSearch(self.host,self.port,self.user,self.passwd)
        from vs_search import VSSearch
        s=VSSearch(searchType="collection",host=self.host,port=self.port,user=self.user,passwd=self.passwd)
        s.container = self.name
        return s

    def items(self,item=None,itemId=None,fileName=None):
        """
        Generator to Search for specific items within the collection.
        Yields (num_hits, VSItem) tuples
        :param item: Optional - a specific VSItem to locate
        :param itemId: Optional - the ID of an item to locate
        :param fileName: Optional - filename to search for (in originalFilename item metadata)
        :return: Yields (num_hits, VSItem) tuples
        """
        if itemId is None and item is None and fileName is None:
            raise ArgumentError("You need to pass either item= or itemId= to hasItem")

        root = ET.Element("ItemSearchDocument", xmlns="http://xml.vidispine.com/schema/vidispine")

        field = ET.Element("field")
        name = ET.Element("name")
        value = ET.Element("value")
        if fileName is not None:
            name.text="originalFilename"
            value.text=os.path.basename(fileName)
        if itemId is not None:
            name.text="itemId"
            value.text=itemId
        if item is not None:
            name.text="itemId"
            value.text=item.name

        field.append(name)
        field.append(value)

        root.append(field)
        xmlquery=ET.tostring(root,encoding="UTF-8")
        logging.debug(xmlquery)

        #content=urllib.quote_plus(xmlquery)
        response=self.request("/collection/{0}/item".format(self.name),query={'q': xmlquery})

        ns = "{http://xml.vidispine.com/schema/vidispine}"
        numHits = int(response.find("{0}hits".format(ns)).text)
        logging.debug("Got %d hits for %s in %s" % (numHits,fileName,self.name))

        for itemNode in response.findall("{0}item".format(ns)):
            itemId = itemNode.attrib['id']
            itemRef = VSItem(host=self.host,port=self.port,user=self.user,passwd=self.passwd)
            itemRef.name = itemId
            yield (numHits,itemRef)
