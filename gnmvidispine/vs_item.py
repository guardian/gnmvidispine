import xml.etree.cElementTree as ET
from vidispine_api import InvalidData, VSBadRequest
from vs_job import VSJob, VSJobFailed
from vs_shape import VSShape
from vs_acl import VSAcl
from vs_thumbnail import VSThumbnailCollection
import os.path
from pprint import pprint
from time import sleep
import logging
import re

from vidispine_api import HTTPError, VSApi, VSException, VSNotFound
from vs_storage_rule import VSStorageRule
import io


class VSTranscodeError(VSException):
    def __init__(self, failedJob):
        super(VSTranscodeError, self).__init__()
        self.transcodeJob = failedJob

    def __unicode__(self):
        return u"Transcode error: {0}".format(self.transcodeJob.errorMessage)


class InvalidSourceError(StandardError):
    """
    Raised if the xml (or other) source does not contain the data that we expect
    """


class VSItem(VSApi):
    """
    This class represents a Vidispine item, and as such is one of the main pieces of functionality.

    Often, you would use VSSearch to prepare a search which will return VSItem objects, either populated or not.
    See VSSearch for more information.

    To get information on an existing item when you know the item ID:
    i = VSItem(host,port,user,password)
    i.populate(item_id) #to load in all metadata
    i.populate(item_id,specific_fields=('field_1','field_2'))   #to load in only field_1 and field_2
    title = i.get('title') #any field name is valid here

    #set metadata on an item
    item.set_metadata({'title': 'new title', 'field_1': 'new value', 'group_1': {'field_1a': 'another value'}})

    i.reload()  #refresh the locally held information from Vidispine

    i.import_sidecar('/path/to/sidecar.xml')    #import a sidecar XML to the item.  The file path is as seen by the VS server.

    for s in i.shapes():    #iterate over shapes
      pprint(s.__dict__) #s is a populated VSShape object

    s = i.get_shape('shape_tag') #get a specific shape. s is a populated VSShape object

    projected_xml = i.project('projection_id')  #convert the metadata to another form using an XSLT projection registered in VS
    i.export()
    rule = i.storageRule('shape_tag') #convenience method to get the storage rule for a specific shape

    builder = i.get_metadata_builder() #Return a VSMetadataBuilder object to help construct complex metadata sets
    """
    def __init__(self, *args, **kwargs):
        super(VSItem, self).__init__(*args, **kwargs)
        self.dataContent = None
        self.name = "INVALIDNAME"
        self.type="item"
        self.contentDict = {}
        self._shapeListContent = None

    def path(self):
        """
        Returns the base URL path to the item in Vidispine, e.g. /item/{id}
        :return: string
        """
        return "/{0}/{1}".format(self.type,self.name)

    def reload(self):
        """
        Refreshes the currently held data from the server
        :return:
        """
        self.contentDict = {}
        self.populate(self.name)

    def createPlaceholder(self,metadata=None,group=None):
        """
        Creates a new placeholder item and associates it with this object.  Can raise InvalidData if the content is not
         acceptable.
        Use placeholderImport() to attach some media to it
        :param metadata: (optional) dictionary of metadata to populate the new placeholder with
        :param group: (optional) primary metadata group
        :return:
        """
        rqbody = None
        if isinstance(metadata,dict):
            rqbody = self._make_metadata_document(metadata, group=group)
        elif isinstance(metadata,basestring):
            rqbody = metadata
        elif metadata is not None:
            raise TypeError("Metadata should be a dictionary or XML document string, not {0}".format(metadata.__class__.__name__))

        try:
            if metadata is not None:
                response = self.request("/import/placeholder",
                                        method="POST",
                                        query={'container': 1},
                                        body=rqbody)
            else:
                response = self.request("/import/placeholder",
                                    method="POST",
                                    query={'container': 1, 'video': 1,
                                    })
        except VSBadRequest as e:
            print rqbody
            raise

        try:
            gotId = response.attrib['id']
            self.name = gotId
        except ValueError as e:
            raise InvalidData("Did not get created collection ID from Vidispine")
        return self

    def toXML(self,encoding="UTF-8"):
        """
        Returns a reconstructed XML document for the metadata of this item.
        :return: XML string
        """
        return ET.tostring(self.dataContent,encoding)

    def fromXML(self, xmldata=None, objectClass="item"):
        """
        populate this item from the given XML document rather than directly from Vidispine.
        raises InvalidSourceError if the XML does not contain what we need.
        :param xmlstring: XML to parse
        :param objectClass: is this an item or collection
        :return: self
        """
        if isinstance(xmldata,basestring):
            self.dataContent = ET.fromstring(xmldata)
        else:
            self.dataContent = xmldata

        self.type=objectClass

        namespace = "{http://xml.vidispine.com/schema/vidispine}"
        if self.type == "item":
            node = self.dataContent.find('{0}item'.format(namespace))
            if node is None:
                raise InvalidSourceError("VSItem::fromXML - declared as item but source document does not have an <item> node")
            self.name = node.attrib['id']

        if self.type == "item":
            for x in self.dataContent.findall('{0}item/{0}metadata/{0}timespan'.format(namespace)):
                self.makeContentDict(x)
        elif self.type == "collection":
            for x in self.dataContent.findall('{0}timespan'.format(namespace)):
                self.makeContentDict(x)
            self.name = self.contentDict['collectionId']
        else:
            raise TypeError("item populate() called on something not identifying an item or collection")
        return self

    def populate(self, entity_id=None, type="item", specificFields=None):
        """
        Loads metadata about the item from Vidispine.
        :param id: VS ID of the item to load. You only need to specify this if you're loading an item from a specific ID;
        if you have got the item from a VSSearch you only need to call populate() if you specified shouldPopulate=False
        in the results() call.  In that case, you can call with no id parameter and it will populate with the ID in item.name
        :param type: either "item" (default) or "collection"
        :param specificFields: list or tuple of specific field names to load. If this is None (default), then load everything.
        Only loading the fields you need can significantly speed up your program
        :return: self
        """
        if entity_id is None:
            entity_id = self.name

        if isinstance(specificFields,list) or isinstance(specificFields,tuple):
            fields=",".join(specificFields)
            content = self.request("/{t}/{i}/metadata?field={f}".format(t=type,i=entity_id,f=fields, method="GET"))
        else:
            content = self.request("/%s/%s/metadata" % (type, entity_id), method="GET")

        return self.fromXML(content,objectClass=type)

    def importSidecar(self, filepath):
        """
        Import a sidecar XML onto the item
        :param filepath: file path (relative to the VS Server) of the sidecar file to import
        :return: None
        """
        fileurl = 'file://' + filepath

        self.request('/import/sidecar/{0}'.format(self.name),
                     method="POST",
                     query={'sidecar': fileurl})

    @property
    def master_group(self):
        """
        Return the name of the master group associated with the item, if any
        :return: string
        """
        try:
            group_node = self.dataContent.find('{0}item/{0}metadata/{0}group'.format(self.xmlns))
            if group_node is not None:
                return group_node.text
            return None
        except AttributeError:
            return None

    def makeContentDict(self, node, ns="{http://xml.vidispine.com/schema/vidispine}", parent_key=None):
        """
        Internal private method
        :param node:
        :param ns:
        :return:
        """

        if parent_key is not None:
            logging.debug("makeContentDict: parent key {0}".format(parent_key))
        logging.debug("makeContentDict: on {0}".format(node.tag))
        for child in node:
            # print "%s" % child.tag

            if child.tag.endswith("field"):
                try:
                    key = child.find('{0}name'.format(ns)).text
                except AttributeError:
                    key = ""

                logging.debug(u"key is {0}".format(key))
                #try:
                for valNode in child.findall('{0}value'.format(ns)):
                    try:
                        val = valNode.text
                    except AttributeError:
                        val = ""
                    logging.debug(u"got {0} for {1}".format(val,key))
                    if key in self.contentDict:
                        #raise Exception("contentDict already has a value %s for %s, trying to insert new value %s\n" % (self.contentDict[key],key,val))
                        if isinstance(self.contentDict[key],list):
                            self.contentDict[key].append(val)
                        else:
                            self.contentDict[key] = [ self.contentDict[key], val ]

                        #self.contentDict[key] = "%s|%s" % (self.contentDict[key], val)
                    else:
                        self.contentDict[key] = val
                        #print "debug: item::makeContentDict: key=%s val=%s\n" % (key,val)
            elif child.tag.endswith("group"):
                key = child.find('{0}name'.format(ns)).text
                logging.debug("makeContentDict: recursing into {0}".format(key))
                #print "group: %s" % key
                self.makeContentDict(child, parent_key=key)
        return

    def dump_text(self, *fields):
        """
        Debugging method to output text information about the item to stdout
        :param fields:
        :return:
        """
        # pprint(self.contentDict)
        level=0
        if isinstance(fields[0],int):
            level=fields[0]

        print "Item:"
        for n in range(0,level):
            print "\t",

        print "ID: %s" % (self.name.encode('utf-8'))
        for f in fields:
            if isinstance(f,int): continue
            try:
                for n in range(0,level):
                    print "\t",
                print "%s: %s" % (f, self.contentDict[f])
            except:
                pass

    def dump_xml(self):
        """
        Returns an XML of the item's MetadataDocument as a string
        :return: string of xml
        """
        print ET.tostring(self.dataContent)

    def delete(self, keepShapeTagMedia=None, keepShapeTagStorage=None):
        """
        Delete the item.  The item does NOT have to be populated for this to work. Raises a VSException if the operation
        fails.
        :param keepShapeTagMedia: If specified, a list or tuple of shape tags whose media should not be deleted.
        :param keepShapeTagStorage: If specified, a list or tuple of either storage IDs as strings or VSStorage objects
        :return: None
        """
        from vs_storage import VSStorage
        qp = {}

        if keepShapeTagStorage is not None:
            storage_ids = []
            if not isinstance(keepShapeTagStorage,list):
                raise TypeError
            for x in keepShapeTagStorage:
                if isinstance(x, VSStorage):
                    storage_ids.append(x.name)
                else:
                    storage_ids.append(x)
            qp['keepShapeTagStorage'] = ",".join(storage_ids)

        if keepShapeTagMedia is not None:
            storage_ids = []
            if not isinstance(keepShapeTagMedia,list):
                raise TypeError
            for x in keepShapeTagMedia:
                storage_ids.append(x)
            qp['keepShapeTagMedia'] = ",".join(storage_ids)

        if self.type!='collection' and self.type!='item':
            raise ValueError("A VSItem must either be of type collection or of type item. Not deleting.")

        response = self.request("/%s/%s" % (self.type,self.name), method="DELETE", query=qp)

    def get(self, fieldname, allowArray=False):
        """
        Get the value of a metadata field
        :param fieldname: field name to look up
        :param allowArray: if there are multiple values, then set allowArray=True to return a list. Otherwise, a string
        will be returned with the values delimited by a |
        :return: list or string
        """
        if fieldname in self.contentDict:
            if isinstance(self.contentDict[fieldname],list):
                if allowArray==True:
                    return self.contentDict[fieldname]
                elif self.contentDict[fieldname] is not None:
                    try:
                        return '|'.join(self.contentDict[fieldname]) #default, old behaviour
                    except TypeError:
                        #if join fails cos of bad data, then do it the crap way but catching excaptions as we go
                        str=""
                        for x in self.contentDict[fieldname]:
                            try:
                                str += unicode(x) + '|'
                            except StandardError:
                                pass
                        return str[0:-2]
            return self.contentDict[fieldname]

        return None

    def copyToPlaceholder(self,host='localhost',port=8080,user='admin',passwd=None):
        """
        Copies the metadata associated with this item to a placeholder, on another VS server. This does NOT copy any
        shapes, media, storage rules, ACLs, etc.
        :param host: host of the VS server to copy to (default: localhost)
        :param port: port of the VS server to copy to (default: 8080)
        :param user: username for the VS server to copy to (default: admin)
        :param passwd: password for the VS server to copy to (default: None)
        :return: a new VSItem representing the duplicated item
        """
        md = self.metadata_document()
        logging.debug(md)
        newItem = VSItem(host,port,user,passwd)
        newItem.createPlaceholder(metadata=md)
        return newItem

    def metadata_document(self):
        """
        Returns an XML string MetadataDocument for the item
        :return: string
        """
        #logging.debug("in metadata_document")

        root = ET.Element('MetadataDocument',{'xmlns': 'http://xml.vidispine.com/schema/vidispine'})
        #logging.debug(str(root))

        tsNode = ET.SubElement(root,"timespan",{'start': '-INF', 'end': '+INF'})

        ignored_field = re.compile(r'^_')
        for fieldname,value in self.contentDict.items():
            if ignored_field.match(fieldname): continue
            if fieldname == "itemId" or fieldname == "collectionId": continue
            #logging.debug('took field {0}'.format(fieldname))

            fieldEl = ET.SubElement(tsNode,'field')
            nameEl = ET.SubElement(fieldEl,'name')
            nameEl.text=fieldname
            if not isinstance(value,list):
                value = [value]
            for v in value:
                if v is not None:
                    valueEl = ET.SubElement(fieldEl,'value')
                    valueEl.text = str(v)

        return ET.tostring(root,encoding="UTF-8")

    def metadata_changesets(self):
        """
        Generator that yields VSMDChangeSet objects for each changeset on the item
        :return: yields MDChangeSet objects
        """
        from vs_mdchangeset import VSMDChangeSet

        doctree = self.request("/{c}/{i}/metadata/changes".format(c=self.type,i=self.name))
        for node in doctree.findall('{0}changeSet'.format(self.xmlns)):
            changeset = VSMDChangeSet(host=self.host,port=self.port,user=self.user,passwd=self.passwd)
            changeset.from_xml(node)
            yield changeset

    def metadata_changeset_list(self):
        """
        Convenience function that returns a list of all metadata changes to the item as VSMDChangeSet objects.
        This might allocate a large amount of memory for complex objects! Better to use the generator version metadata_changesets
        :return: list of VSMDChangeSet objects
        """

        return map(lambda x:x,self.metadata_changesets())

    def metadata_changesets_for_field(self,fieldname):
        """
        Generator that will only yield VSMDChangeSet objects for changests containing the given field
        :param fieldname: field name to filter for
        :return: yields MDChangeSet objects
        """
        for c in self.metadata_changesets():
            if c.fields is None:
                continue
            if fieldname in c.fields:
                yield c

    def project(self, projection_name):
        """
        Converts the metadata to another format, given by an XSLT "projection" registered in Vidispine. Consult the
        Vidispine documentation for more information on this
        :param projection_name: Identifier of the outgoing projection to use
        :return: string of the projected deta
        """
        return self.raw_request("/item/%s/metadata" % self.name, matrix={'projection': projection_name})

    def import_external_xml(self, xmlstring, projection_name="default"):
        """
        Import metadata from a "foreign" format to this item using an XSLT "projection" registered in Vidispine.
        :param xmlstring: XML metadata to import
        :param projection_name: projection name to use
        :return: updated vidispine metadata document
        """
        return self.raw_request("/item/%s/metadata" % self.name, method="PUT", matrix={'projection': projection_name}, body=xmlstring)

    def _make_metadata_document(self, md, group=None, mode="default"):
        b = self.get_metadata_builder(master_group=group)
        b.addMeta(md)
        return b.as_xml("UTF-8")

    def set_metadata(self, md, group=None, entitytype="default", mode="default"):
        """
        Sets metadata values on the item (see also get_metadata_builder).  Raises VSExceptions if the operation fails.
        :param md: dictionary of key/value pairs to set.  lists are allowed as values but dicts are not.
        :param group: Set a master group in the metadata to set
        :return: Server output (usually blank string)
        """
        import xml.etree.ElementTree as ET
        if entitytype == "item":
            path = "/item/%s/metadata" % (self.name)
        else:
            path = "/%s/%s/metadata" % (self.type,self.name)

        if mode == "add":
            metadoc = self._make_metadata_document(md,group,mode="add")
        else:
            metadoc = self._make_metadata_document(md,group)

        return self.request(path, method="PUT", body=metadoc)

    def add_mdgroup(self,groupname,meta,mode="add",root_group=None):
        """
        Add a metadata group to the item
        :param groupname:
        :param meta:
        :param mode:
        :param root_group:
        :return:
        """
        if not isinstance(meta,dict):
            raise TypeError
        rootelem = ET.Element('MetadataDocument',{'xmlns': "http://xml.vidispine.com/schema/vidispine"})
        timespan = ET.SubElement(rootelem,"timespan",{'end': "+INF", 'start': "-INF"})
        if root_group is not None:
            rootgroupnode = ET.SubElement(timespan,"group")
            rootgroupnode.text = root_group

        groupnode = ET.SubElement(timespan,"group",{'mode': mode})
        for key,value in meta.items():
            fieldnode = ET.SubElement(groupnode,"field")
            fieldname = ET.SubElement(fieldnode,"name")
            fieldname.text = key
            fieldvalue = ET.SubElement(fieldnode,"value")
            fieldvalue.text = value

    def get_shape(self, shapetag):
        """
        Get a specific shape from the item.  Raises VSNotFound if there is no shape with the specified tag
        :param shapetag: shape tag to get
        :return: populated VSShape object
        """
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        path = "/item/%s/shape" % self.name

        if self._shapeListContent is None:
            self._shapeListContent = self.request(path)

        #print ET.tostring(shapeListContent)

        for node in self._shapeListContent.findall('{0}uri'.format(ns)):
            if self.debug:
                logging.debug("got shape id %s" % node.text)

            shape = VSShape(host=self.host, port=self.port, user=self.user, passwd=self.passwd)
            shape.populate(self.name, node.text)
            if self.debug:
                logging.debug("shape tag %s" % shape.tag())

            if shape.tag() == shapetag:
                return shape

        raise VSNotFound("No shape matching %s could be found" % shapetag)

    def shapes(self):
        """
        Generator to iterate over all shapes attached to item.

        :return: Yields VSShape objects
        """
        path = "/item/%s/shape" % self.name

        if self._shapeListContent is None:
            self._shapeListContent = self.request(path)

        for node in self._shapeListContent.findall('{0}uri'.format(self.xmlns)):
            if self.debug:
                logging.debug("got shape id %s" % node.text)

            shape = VSShape(host=self.host, port=self.port, user=self.user, passwd=self.passwd)
            shape.populate(self.name, node.text)
            if self.debug:
                logging.debug("shape tag %s" % shape.tag())

            yield shape

    def transcode(self, shapetag, priority='MEDIUM', wait=True, allow_object=False):
        """
        Transcode the item's video to a new format
        :param shapetag: shape tag to transcode to
        :param priority: job priority
        :param wait: if True (default), do not return until the job completes.  VSTranscodeError is raised if the transcode fails.
        :param allow_object: if False (default) and wait=False, return the job ID for the transcode job. If True, return a
        VSJob object.
        :return: the job ID of the transcode job, or a populated VSJob object (if wait=False) or None (if wait=True)
        """
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        path = "/item/%s/transcode" % self.name

        jobDocument = self.request(path, method="POST",
                                   query={'priority': priority, 'tag': shapetag.replace(' ', '%20')})

        jobID = jobDocument.find("{0}jobId".format(ns)).text
        logging.debug("Transcode job ID is %s" % jobID)

        if wait == False:
            if allow_object:
                job = VSJob(host=self.host, port=self.port, user=self.user, passwd=self.passwd)
                job.populate(jobID)
                return job
            else:
                return jobID

        while True:
            job = VSJob(host=self.host, port=self.port, user=self.user, passwd=self.passwd)
            job.populate(jobID)

            if job.status() == "FINISHED":
                break

            if job.status() == "FAILED" or job.status() == "FAILED_TOTAL":
                raise VSTranscodeError(job)

            sleep(5)

        return

    def export(self, shapetag, output_path, metadata_projection=None, use_media_filename=True, media_extension=None):
        """
        Export the item to a file with metadata sidecar
        :param shapetag:
        :param output_path:
        :param metadata_projection:
        :param use_media_filename:
        :param media_extension:
        :return:
        """
        ns = "{http://xml.vidispine.com/schema/vidispine}"

        path = "/item/%s/export" % self.name

        if use_media_filename is True and 'originalFilename' in self.contentDict:
            (outputFileName, originalExtension) = os.path.splitext(self.contentDict['originalFilename'])
            output_path = os.path.join(os.path.dirname(output_path), outputFileName)

        output_path = output_path.replace(' ', '%20')
        args = {'tag': shapetag.replace(' ', '%20'), 'uri': "file:" + output_path}
        if metadata_projection is not None:
            #metadata_projection=
            args['projection'] = metadata_projection.replace(' ', "%20")
            args['metadata'] = 'true'

        if self.debug:
            print "item::export: arguments:"
            pprint(args)

        jobDocument = self.request(path, method="POST", query=args)
        jobID = jobDocument.find("{0}jobId".format(ns)).text
        print "Export job ID is %s" % jobID

        while True:
            job = VSJob(host=self.host, port=self.port, user=self.user, passwd=self.passwd)
            job.populate(jobID)

            print "Job %s has status %s" % (job.name, job.status())
            if job.status() == "FINISHED":
                break

            if job.status() == "FAILED" or job.status() == "ABORTED":
                raise VSJobFailed(job)

            sleep(5)

            #tag=h264%20Mezzanine&uri=file:/media/sanwatchers/&metadata=true&projection=inmeta_V3&useOriginalFileName=1"

    def storageRule(self,shapeTag='original'):
        """
        Convenience method to return a storage rule for a specific shape tag
        :param shapeTag: shape tag to return information on
        :return: populated VSStorageRule
        """
        return self.get_shape(shapeTag).storageRule()

    def applyStorageRule(self,rule,shapeTag='original'):
        """
        Apply a VSStorageRule to a shape on this item.  Raises TypeError if the rule is not correct, or VSException if
        the server reports an error
        :param rule: configured VSStorageRule to apply
        :param shapeTag: shape tag to apply it to
        :return: None
        """
        if not isinstance(rule,VSStorageRule):
            raise TypeError

        path = "/item/{0}/storage-rule/{1}".format(self.name,shapeTag)
        self.request(path, method="POST", body=rule.toXml())

    def applyStorageRuleXML(self,string,shapeTag='original'):
        """
        This method should be considered internal.  Directly apply an XML string as the storage rule for the given tag
        :param string: XML storage rule document
        :param shapeTag: shape tag to apply to
        :return: None
        """
        path = "/item/{0}/storage-rule/{1}".format(self.name,shapeTag)
        self.request(path, method="PUT", body=string)

    def get_acl(self):
        """
        Returns the Access Control List (ACL) for this item
        :return: populated VSAcl object
        """
        a = VSAcl(self.host,self.port,self.user,self.passwd)
        a.populate(self)
        return a

    def get_metadata_builder(self, master_group=None):
        """
        Returns a VSMetadataBuilder object relating to this item
        :return: configured VSMetadataBuilder object
        """
        return VSMetadataBuilder(self, master_group=self.master_group if master_group is None else master_group)

    def placeholder_adopt(self, file_ref, shape_tag='original', priority='MEDIUM'):
        """
        'Adopts' the given file reference as the specified shape
        :param file_ref:
        :param shape_tag:
        :param priority:
        :return:
        """
        from vs_storage import VSFile
        from xml.etree.cElementTree import tostring
        if not isinstance(file_ref,VSFile):
            raise TypeError("file_ref must be a VSFile")

        url = "/import/placeholder/{item}/container/adopt/{file}".format(item=self.name,file=file_ref.name)
        rtn = self.request(url,method="POST")

        if rtn is None:
            logging.info("placeholder adopt returned no data")
        else:
            try:
                logging.info(tostring(rtn))
            except AssertionError:
                logging.info(rtn)

    def import_base(self,shape_tag='original', priority='MEDIUM', essence=False, thumbnails=True, jobMetadata=None):
        """
        prepares arguments for an import call. This is an internal method, called by import_to_shape and streaming_import_to_shape
        :param shape_tag: shape tag to import to. Defaults to 'original'
        :param priority: priority for import job. Defaults to 'Medium'
        :param essence: is this an essence update or not
        :param thumbnails: should Vidispine re-create thumbnails or not
        :param jobMetadata: Dictionary of key/values for the job metadata - see Vidispine import documentation for details
        :return: dictionary of arguments for the import call.
        """
        if isinstance(shape_tag,basestring):
            shape_tag_string = shape_tag
        else:
            shape_tag_string = ",".join(shape_tag)

        if thumbnails:
            t = 'true'
            nt = 'false'
        else:
            t = 'false'
            nt = 'true'

        if essence:
            e = 'true'
        else:
            e = 'false'

        if jobMetadata is not None:
            extra_args = {'jobmetadata': map(lambda (k,v): "{0}={1}".format(k,v), jobMetadata.items())}
        else:
            extra_args = {}

        rtn = {
            'tag'         : shape_tag_string,
            'priority'    : priority,
            'thumbnails'  : t,
            'no-transcode': nt,
            'essence'     : e
        }
        rtn.update(extra_args)
        return rtn
        
    def streaming_import_to_shape(self, filename, transferPriority=500, throttle=True, rename=None, **kwargs):
        """
        Attempts a streaming import from an open local stream to Vidispine
        :param input_io: Open file object
        :param shape_tag: shape tag to assign to the file, Specify an array to assign multiple tags.
        :param priority: job priority
        :param essence: is this an essence version import? True or false
        :param thumbnails: should thumbnails be re-extracted? True or false
        :return: VSJob describing the import job
        """
        args = self.import_base(**kwargs)
        
        url = "/item/{0}/shape/raw"
        if rename is None: rename=os.path.basename(filename)
        
        self.chunked_upload_request(io.FileIO(filename),os.path.getsize(filename),chunk_size=1024*1024,
                                    path=url.format(self.name).format(self.name),filename=rename,
                                    transferPriority=transferPriority,throttle=throttle,query=args,method="POST")
        
    def import_to_shape(self, uri=None, file_ref=None, **kwargs):
        """
        Imports a file given by URI (as seen by the Vidispine server; does not have to be a Vidispine storage) to the item
        as the specified shape
        :param uri: URI to the file to import
        :param file_ref: VSFile object to import. Either file_ref or uri must be specified, not both
        :param shape_tag: shape tag to assign to the file, Specify an array to assign multiple tags.
        :param priority: job priority
        :return: VSJob describing the import job
        """
        from vs_storage import VSFile
        if uri is None and file_ref is None:
            raise ValueError("You must specify a uri to import_to_shape")

        if uri is not None and file_ref is not None:
            raise ValueError("You must specify either uri or file_ref, not both")

        args = self.import_base(**kwargs)
        
        if uri is not None:
            args['uri'] = uri
        if file_ref is not None:
            if not isinstance(file_ref,VSFile):
                raise ValueError("file_ref must be a VSFile object")
            args['fileId']=file_ref.name

        #if the request fails, this will raise an exception that should be caught by the caller
        url = "/item/{0}/shape"
        if 'essence' in kwargs:
            url += "/essence"
        response = self.request(url.format(self.name),
                                method="POST",
                                query=args
                                )
        j= VSJob(self.host,self.port,self.user,self.passwd)
        j.fromResponse(response)
        return j

    def thumbnails(self):
        """
        Returns a populated VSThumbnailCollection for the item
        :return: VSThumbnailCollection
        """
        th = VSThumbnailCollection(self.host,self.port,self.user,self.passwd)
        th.populate(self)
        return th

    @property
    def parent_collection_number(self):
        """
        Returns the number of colletions that this item belongs to, excluding ancestors
        :return: integer
        """
        return int(self.contentDict['__collection_size'])

    def parent_collections(self, shouldPopulate=False):
        """
        Generator that yields VSCollection objects for each collection that the item belongs to.
        The item does NOT need to be populated with metadata for this to work.
        :param: shouldPopulate - (default False) - if set to True, this will pre-load the metadata of the collection for you
        :return: yields VSCollection objects
        """
        from vs_collection import VSCollection

        response = self.request("/item/{0}/collections".format(self.name),method="GET")
        for uri_entry in response.findall('{0}uri'.format(self.xmlns)):
            cref = VSCollection(host=self.host,port=self.port,user=self.user,passwd=self.passwd)
            if shouldPopulate:
                cref.populate(uri_entry.text)
            else:
                cref.name = uri_entry.text
            yield cref


class VSMetadataBuilder(VSApi):
    """
    Helper class to allow the construction of more complex metadata object.  This is accessed by calling get_metadata_builder()
    on a populated VSItem.

    builder = i.get_metadata_builder()

    i.addMeta({'field_name': 'value','field_2': ['value 2a', 'value 2b']}) #add fields/values to the root level

    #add a subgroup with a specific mode.  Subgroups of the group can be added by including them as subdictionaries,
    #optionally you can specify a specific mode to add them with.  consult the vidsipine documentation for possible
    #modes.
    i.addGroup('group name', mode="replace", {'field_name': 'value',
                                              'field_2': ['value 2a', 'value 2b'],
                                              'subgroup': {
                                                 'sub_field_3': ['value 3a', 'value 3b']
                                              },
                                              subgroupmode='add')

    i.commit() #save the metadata back to the item which this builder is referring to
    xml_string = i.as_xml() #get the XML MetadataDocument back as a string
    """
    def __init__(self,parent,master_group=None):
        if parent is not None:
            super(VSMetadataBuilder,self).__init__(parent.host,parent.port,parent.user,parent.passwd)
        else:
            super(VSMetadataBuilder,self).__init__()

        self.rootNode = ET.Element('MetadataDocument',{'xmlns': "http://xml.vidispine.com/schema/vidispine"})
        self.tsNode = ET.SubElement(self.rootNode,"timespan",{'end': "+INF", 'start': "-INF"})
        self.parent = parent
        if master_group is not None:
            rootgroupnode = ET.SubElement(self.rootNode,"group")
            rootgroupnode.text = master_group

    def addMeta(self,meta):
        """
        Adds metdata to the root level of the builder
        :param meta: dictionary of key/value pairs.  lists are allowed as values but dictionaries are not.
        :return: None
        """
        if not isinstance(meta,dict):
            raise TypeError

        for key,value in meta.items():
            fieldnode = ET.SubElement(self.tsNode,"field")
            fieldname = ET.SubElement(fieldnode,"name")
            fieldname.text = key
            if not isinstance(value,list):
                value=[value]
            for v in value:
                fieldvalue = ET.SubElement(fieldnode,"value")
                fieldvalue.text = v

    def _groupContent(self,parentNode,meta,subgroupmode="add"):
        """
        Private internal method
        :param parentNode:
        :param meta:
        :param subgroupmode:
        :return:
        """
        params = {}
        if subgroupmode is not None:
            params={'mode': subgroupmode}
        for key,value in meta.items():
            #print key
            #pprint(value)
            if isinstance(value,dict):
                subgroupnode = ET.SubElement(parentNode,"group",params)
                subgroupname = ET.SubElement(subgroupnode,"name")
                subgroupname.text = key
                self._groupContent(subgroupnode,value)
            elif isinstance(value,list):
                fieldnode = ET.SubElement(parentNode,"field")
                fieldname = ET.SubElement(fieldnode,"name")
                fieldname.text = key
                for item in value:
                    fieldvalue = ET.SubElement(fieldnode,"value")
                    fieldvalue.text = item
            else:
                fieldnode = ET.SubElement(parentNode,"field")
                fieldname = ET.SubElement(fieldnode,"name")
                fieldname.text = key
                fieldvalue = ET.SubElement(fieldnode,"value")
                fieldvalue.text = value

    def addGroup(self,groupname,meta,mode=None,subgroubmode=None):
        """
        Add a group to the root level, optionally including subgroups
        :param groupname: name of the group to add
        :param meta: dictionary of key/value pairs of metadata. lists and dictionaries are allowed as values.
        :param mode: (default: no mode [over-write]) Mode to use when incorporating metadata. Valid values are 'add', 'remove' or None.
        :param subgroubmode: (default: None) Mode to use when incorporating subdictionaries as subgroups. Default is to
        use the same as 'mode'.
        :return:  None
        """
        if not isinstance(meta,dict):
            raise TypeError

        if subgroubmode is None:
            subgroupmode = mode

        params = {}
        if mode is not None:
            params={'mode': mode}
            
        groupnode = ET.SubElement(self.tsNode,"group",params)
        groupnameNode = ET.SubElement(groupnode,"name")
        groupnameNode.text = groupname

        self._groupContent(groupnode,meta,subgroupmode)

    def as_xml(self,encoding="UTF-8"):
        """
        Returns the contents of the VSMetadataBuilder as a string
        :param encoding: (optional, default: "UTF-8") String encoding to use
        :return: string
        """
        return ET.tostring(self.rootNode,encoding)

    def commit(self):
        """
        Saves the current metadata back to the parent item.  Can raise VSBadRequest, VSNotFound, etc. if the operation
        fails.
        :return: None
        """
        path="{0}/metadata".format(self.parent.path())
        try:
            self.request(path,method="PUT",body=self.as_xml(encoding="UTF-8"))
        except VSBadRequest as e:
            logging.error(e)
            logging.error(unicode(self.as_xml(encoding="UTF-8")))
            raise