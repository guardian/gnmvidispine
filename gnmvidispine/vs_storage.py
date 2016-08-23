__author__ = 'Andy Gallagher <andy.gallagher@theguardian.com>'

import xml.etree.ElementTree as ET
from vs_job import VSJob, VSJobFailed
from vs_shape import VSShape
from vs_item import VSItem
from vs_metadata import VSMetadata

import os.path
from pprint import pprint
import re
import urllib
from time import sleep
import logging
import json

from vidispine_api import HTTPError, VSApi, VSException, VSNotFound


class FileAlreadyImportedError(StandardError):
    pass

class FileDoesNotExistError(StandardError):
    pass


class VSFile(object):
    def __init__(self, parent_storage, parsed_data, conn=None):
        self.parent = parent_storage

        self.dataContent = parsed_data
        self.contentDict = {}

        self.name = self._valueOrNone('id')
        self.path = self._valueOrNone('path')
        self.uri = self._valueOrNone('uri')
        self.state = self._valueOrNone('state')
        self.size = self._valueOrNone('size')
        self.hash = self._valueOrNone('hash')
        self.timestamp = self._valueOrNone('timestamp')
        self.refreshFlag = self._valueOrNone('refreshFlag')
        self.storageName = self._valueOrNone('storage')

        namespace = "{http://xml.vidispine.com/schema/vidispine}"

        if self.parent is None:
            self.parent = VSStorage(host=conn.host,port=conn.port,user=conn.user,passwd=conn.passwd)
            self.parent.populate(self.storageName)

        self.memberOfItem = None
        node = self.dataContent.find('{0}item'.format(namespace))
        if node is not None:
            idNode = node.find('{0}id'.format(namespace))
            if id is not None:
                host = self.parent.host
                port = self.parent.port
                user = self.parent.user
                passwd = self.parent.passwd

                self.memberOfItem = VSItem(host=host, port=port, user=user, passwd=passwd)
                self.memberOfItem.name = idNode.text

    def __unicode__(self):
        return u'Vidispine file {0}: {1} on storage {2}'.format(self.name,self.path,self.storageName)

    def _valueOrNone(self, path):
        namespace = "{http://xml.vidispine.com/schema/vidispine}"

        node = self.dataContent.find('{0}{1}'.format(namespace, path))
        if node is not None:
            return node.text
        return None

    def json_data(self):
        rtn = {
            'id': self.name,
            'path': self.path,
            'uri': self.uri,
            'state': self.state,
            'size': self.size,
            'hash': self.hash,
            'timestamp': self.timestamp,
            '@timestamp': self.timestamp,
            'refreshFlag': self.refreshFlag,
            'storageName': self.storageName,
        }
        if self.memberOfItem is not None:
            rtn['memberOfItem'] = self.memberOfItem.name
        return rtn

    def to_json(self):
        return json.dumps(self.json_data())

    def dump(self):
        pprint(self.__dict__)

    def importToItem(self, metadata, tags=['lowres','WebM'], priority="LOW"):
        if self.memberOfItem is not None:
            msg = "The file {filename} is already associated with item {itemid}".format(filename=self.path,
                                                                                        itemid=self.memberOfItem.name)
            raise FileAlreadyImportedError(msg)

        mdtext = ""
        if isinstance(metadata, basestring):
            mdtext = metadata
        elif isinstance(metadata, VSMetadata):
            mdtext = metadata.toXML()

        q = {
            'thumbnails': 'true',
            'priority': priority,
        }
        if tags:
            q['tag'] = ""
            for t in tags:
                q['tag']+=t + ','
            q['tag']=q['tag'][:-1]

        print "query is"
        pprint(q)
        self.parent.debug = True
        #raise StandardError("Testing")
        response = self.parent.request("/storage/{0}/file/{1}/import".format(self.parent.name, self.name),
                                       method="POST",
                                       query=q,
                                       body=mdtext)
        import_job = VSJob(host=self.parent.host, port=self.parent.port, user=self.parent.user,
                           passwd=self.parent.passwd)
        import_job.fromResponse(response)
        return import_job

    def refreshNewData(self,response):
        self.dataContent = response
        self.contentDict = {}

        self.name = self._valueOrNone('id')
        self.path = self._valueOrNone('path')
        self.uri = self._valueOrNone('uri')
        self.state = self._valueOrNone('state')
        self.size = self._valueOrNone('size')
        self.hash = self._valueOrNone('hash')
        self.timestamp = self._valueOrNone('timestamp')
        self.refreshFlag = self._valueOrNone('refreshFlag')
        self.storageName = self._valueOrNone('storage')

    def setNewPath(self,newPath,storage=None):
        if not os.path.exists(newPath):
            errstr = "The file %s does not exist" % (newPath)
            raise FileDoesNotExistError(errstr)

        q = {'path': self.parent.stripOwnPath(newPath)}
        if storage is not None:
            if isinstance(storage, VSStorage):
                q['storage'] = storage.name
            elif isinstance(storage,basestring):
                if not re.match(storage, r'^\w{2}-\d+'):
                    raise StandardError("When specifying a storage as a string, it must be in the form VV-nnnnn where VV is the side identifier and nnnnn is the numeric ID")
                q['storage'] = storage
            else:
                raise TypeError("storage parameter must be either a VSStorage or a string identifying the storage")

        #should raise a VSException if it fails, or return a FileDocument if it succeeds
        response = self.parent.request("/storage/{0}/file/{1}/path".format(self.parent.name,self.name),
                                       method="POST",
                                       query=q)
        self.refreshNewData(response)

    def download(self):
        """
        Initiate download of a file
        :return: HTTPResponse object. Call .read() on this to get the data
        """
        import httplib
        logging.debug("trying to download {0} from storage {1}".format(self.name,self.storageName))

        conn=httplib.HTTPConnection(self.parent.host, self.parent.port)
        response = self.parent.sendAuthorized(conn,'GET','/API/storage/file/{0}/data'.format(self.name),'',{'Accept': '*'})
        if response.status < 200 or response.status > 299:
            pprint(response.msg.__dict__)
            raise HTTPError(response.status,'GET','/API/storage/file/{0}/data'.format(self.name),response.status,response.reason,response.read()).to_VSException(method='GET',url='/storage/file/{0}/data'.format(fileId),body="")

        return response


class VSStorageMethod(object):
    def __init__(self, parent_storage, parsed_data):
        self.contentDict = {}
        self.parent = parent_storage
        self.dataContent = parsed_data

        self.name = self._valueOrNone('id')
        self.uri = self._valueOrNone('uri')
        self.read = self._valueOrNone('read')
        self.write = self._valueOrNone('write')
        self.browse = self._valueOrNone('browse')
        self.lastSuccess = self._valueOrNone('lastSuccess')
        self.lastFailure = self._valueOrNone('lastFailure')
        self.failureMessage = self._valueOrNone('failureMessage')
        self.type = self._valueOrNone('type')

    def _valueOrNone(self, path):
        namespace = "{http://xml.vidispine.com/schema/vidispine}"

        node = self.dataContent.find('{0}{1}'.format(namespace, path))
        if node is not None:
            return node.text
        return None

    def dump(self):
        pprint(self.__dict__)


class VSStorage(VSApi):
    def __init__(self, *args,**kwargs):
        super(VSStorage, self).__init__(*args,**kwargs)
        self.dataContent = None
        self.name = "INVALIDNAME"
        self.contentDict = {}

    def _valueOrNone(self, path):
        namespace = "{http://xml.vidispine.com/schema/vidispine}"

        node = self.dataContent.find('{0}{1}'.format(namespace, path))
        if node is not None:
            return node.text
        #raise StandardError("Value not found for %s" % path)
        return None

    def create_file_entity(self,filepath):
        """
        Tells Vidispine to create a new database entry pointing to an existing file.  This will raise a VSException if the file already exists.
        :param filepath: path to import
        :return: a VSFile object or
        """
        data = self.request("/storage/{0}/file".format(self.name),method="POST",query={
            'path': filepath,
            'createOnly': 'true'
        })
        
        return VSFile(parent_storage=self,parsed_data=data)
        
    def populate(self, vsid):
        if vsid is not None:
            self.dataContent = self.request("/storage/%s" % vsid, method="GET")

        #logging.debug("VSStorage::populate")
        #pprint(self.dataContent)

        self.name = self._valueOrNone('id')
        self.state = self._valueOrNone('state')
        self.type = self._valueOrNone('type')
        self.capacity = self._valueOrNone('capacity')
        self.freeCapacity = self._valueOrNone('freeCapacity')
        self.timestamp = self._valueOrNone('timestamp')

        self.methods = []
        namespace = "{http://xml.vidispine.com/schema/vidispine}"
        node = self.dataContent.find('{0}metadata'.format(namespace))
        if node is not None:
            for fieldNode in node:
                nameNode = fieldNode.find('{0}key'.format(namespace))
                valueNode = fieldNode.find('{0}value'.format(namespace))

                if nameNode is not None and valueNode is not None:
                    self.contentDict[nameNode.text] = valueNode.text

        nodeList = self.dataContent.findall('{0}method'.format(namespace))
        if nodeList is not None:
            for n in nodeList:
                storageMethod = VSStorageMethod(self, n)
                self.methods.append(storageMethod)

    def dump(self):
        # propsList=dir(self)

        #propsDict=dict(zip(propsList,map(lambda x:self.__getattribute__(x),propsList)))
        pprint(self.__dict__)
        for m in self.methods:
            m.dump()

    def urisOfType(self, uriType, pathOnly=False, decode=True):
        for m in self.methods:
            if m.uri is not None and m.uri.startswith(uriType):
                found_uri = m.uri
                if pathOnly:
                    # remove the URI descriptor from the start
                    found_uri = re.sub(u'^{0}://'.format(uriType), '', found_uri)
                if decode:
                    found_uri = urllib.url2pathname(found_uri)
                yield found_uri

    #if the given path starts with one of our own paths, remove that part
    def stripOwnPath(self,pathname):
        for u in self.urisOfType('file',pathOnly=True,decode=True):
            logging.debug("VSStorage::stripOwnPath - checking %s" % u)
            if pathname.startswith(u):
                l = len(u)
                return pathname[l:]
        return pathname

    def fileForPath(self, path):
        path = self.stripOwnPath(path)
        logging.debug("VSStorage::fileForPath - actually looking for %s" % path)
        response = self.request("/storage/{storage}/file/byURI".format(storage=self.name),
                                method="GET",
                                matrix={'includeItem': 'True',
                                        'path': path})
        return VSFile(self, response)

    def files(self, path='/', include_item=True):
        got_files = -100
        total_hits = -1
        pageSize = 100

        while(got_files<total_hits):
            q = {
                'path': path
            }
            mtx = {
                'start': got_files,
                'number': pageSize
            }
            if include_item:
                mtx['includeItem'] = True
            #
            # if self.debug:
            #     print
            response = self.request("/storage/{storage}/file".format(storage=self.name),
                                    method="GET",
                                    matrix=mtx,
                                    query=q
                                    )
            if total_hits == -1:
                total_hits = int(response.find("{0}hits".format(self.xmlns)).text)
                logging.debug("Got {0} hits".format(total_hits))

            for filenode in response.findall("{0}file".format(self.xmlns)):
                got_files += 1
                yield VSFile(self,filenode)

    def rescan(self):
        self.request("/storage/{0}/rescan".format(self.name),method="POST")

def VSStoragePathMap(uriType=None,stripType=False,*args,**kwargs):
    """
    This function will return a hash in the form of uri=>VSStorage
    :param uriType: only include URIs of this type (e.g., file, omms, s3, http, etc.)
    :param stripType: remove the URI type specifier in the returned hash.  So, rather than file:///blah/blah=>{ref} you get /blah/blah=>{ref}
    :param kwargs: specify the usual host,port,user,passwd etc. arguments
    :return: Hash
    """
    api = VSApi(*args,**kwargs)

    rtn = {}

    xmldoc = api.request("/storage",method="GET")
    #pprint(xmldoc.__dict__)
    ns = "{http://xml.vidispine.com/schema/vidispine}"
    for storageNode in xmldoc.findall("{0}storage".format(ns)):
        st = VSStorage(*args,**kwargs)
        #pprint(storageNode.__dict__)
        st.dataContent = storageNode
        st.populate(None) #passing None tells the populate method not to do its own lookup, but to rely on existing dataContent
        #st.dump()
        for m in st.methods:
            try:
                if uriType:
                    if not m.uri.startswith(uriType):
                        continue
                uri = urllib.url2pathname(m.uri)
                if stripType:
                    uri = re.sub(u'^[^:]+://','',uri)

                rtn[uri] = st
            except:
                pass
    return rtn


def VSFileById(fileId,conn=None,*args,**kwargs):
    if conn is None:
        api = VSApi(*args,**kwargs)
    else:
        api = conn

    xmldoc = api.request("/storage/file/{0}".format(fileId),method="GET")
    ns = "{http://xml.vidispine.com/schema/vidispine}"
    return VSFile(None,xmldoc,conn=conn)