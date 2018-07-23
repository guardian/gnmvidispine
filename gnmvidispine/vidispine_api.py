import httplib
import urllib
import base64
import string
import xml.etree.ElementTree as ET
from pprint import pprint
import json
import re
import logging
from time import sleep
import io
import os
from socket import error as socket_error
from itertools import chain, imap

logger = logging.getLogger(__name__)


class HTTPError(StandardError):
    """
    Class to represent a generic HTTP error returned from Vidispine
    """
    def __init__(self,code,method,url,status,reason,body):
        self.code = code
        self.method = method
        self.url = url
        self.status = status
        self.reason = reason
        self.body = body

    def __str__(self):
        return "Request was: %s to %s\n\nServer returned %d (%s)\n%s" % (self.method,self.url,self.status, self.reason, self.body)

    def to_VSException(self, method=None, url=None, body=None):
        #print str(self)
        try:
            if self.code == 404:
                newexcept = VSNotFound()
                newexcept.fromHTTPError(self)
                return newexcept
            elif self.code == 400:
                newexcept = VSBadRequest()
                newexcept.fromHTTPError(self,request_method=method,request_url=url,request_body=body)
                return newexcept
            elif self.code == 409:
                newexcept = VSConflict()
                newexcept.fromHTTPError(self,request_method=method,request_url=url,request_body=body)
                return newexcept

            else:
                return self
        except Exception as e:
            logging.error(e.message)
            return self


class VSException(StandardError):
    xmlns = '{http://xml.vidispine.com/schema/vidispine}'
    
    def __init__(self,*args,**kwargs):
        super(VSException,self).__init__(*args,**kwargs)
        self.request_url = None
        self.request_body = None
        self.request_method = None
        self.exceptionType="Not from Vidispine"
        self.exceptionWhat="Unknown"
        self.exceptionID="Unknown"
        self.exceptionContext = "Unknown"
        self.exceptionRawXML = ""

    def fromHTTPError(self,httperror,request_method=None,request_url=None,request_body=None):
        self.request_url=request_url
        self.request_method=request_method
        self.request_body=request_body
        if not isinstance(httperror,HTTPError):
            raise InvalidData("Provided object is not an HTTPError")
        self.fromXML(httperror.body)

    @staticmethod
    def getNodeContent(xmlnode,nodename,default=""):
        n = xmlnode.find(nodename)
        if n is not None:
            return n.text

        return default

    def fromXML(self,xmldata):
        """
        Given a parsed XML document from a Vidispine error response, populate this exception
        :param xmldata: root node of a parsed ElementTree document containing error information from Vidispine
        """
        self.exceptionType="Not from Vidispine"
        self.exceptionWhat="Unknown"
        self.exceptionID="Unknown"
        self.exceptionContext = "Unknown"
        self.exceptionRawXML = xmldata

        exceptionData = ET.fromstring(xmldata)

        for child in exceptionData:
            self.exceptionType = child.tag
            self.exceptionType = re.sub(r'{[^}]+}','',self.exceptionType)
            self.exceptionWhat = self.getNodeContent(child,'{0}explanation'.format(self.xmlns),default="no explanation provided")
            self.exceptionID = self.getNodeContent(child,'{0}id'.format(self.xmlns),default="no id provided")
            self.exceptionContext = self.getNodeContent(child,'{0}context'.format(self.xmlns),default="no context provided")

    def __str__(self):
        """
        Return a string representation of the exception
        """
        if self.exceptionType:
            rtn = "Vidispine exception %s\n" % self.__class__.__name__
            rtn += "\tType: %s\n\tContext: %s\n\tWhat: %s\n\tID: %s\n" % (self.exceptionType,self.exceptionContext,self.exceptionWhat,self.exceptionID)
            rtn += "\nReturned XML: %s\n" % (self.exceptionRawXML)
            return rtn

        return self.message


class VSBadRequest(VSException):
    """
    Exception representing a "Bad Request" error from Vidispine
    """
    pass


class VSNotFound(VSException):
    """
    Exception representing a "Not Found" error from Vidispine
    """
    pass


class InvalidData(StandardError):
    """
    Exception raised if data is passed to a VS Api function that is not valid, before sending it to Vidispine
    """
    pass


class VSConflict(VSException):
    """
    Exception raised if the operation would conflict with some other object, e.g. when creating something that already exists
    """
    pass


def flatmap(f, items):
    return chain.from_iterable(imap(f, items))


class VSApi(object):
    """
    Base class that all other api subclasses depend on. This provides fundamental send/reply functions.
    """
    dataContent=None
    user=""
    passwd=""
    host=""
    port=8080
    debug=False

    retry_attempts = 100
    retry_delay = 10

    xmlns = "{http://xml.vidispine.com/schema/vidispine}"

    def __init__(self,host="localhost",port=8080,user="",passwd="",url=None,run_as=None, conn=None, logger=None):
        """
        Initialise a new Vidispine connection.
        :param host: Hostname to connect to Vidispine on
        :param port: Port number to connect to Vidispine on
        :param user: Username to connect to Vidispine
        :param passwd: Password for the given user
        :param url: URL to the Vidispine server as {proto}://{server}; for Portal compatibility
        :param run_as: Tell Vidispine to assume the credentials of this user for the purposes of this request. This only works if you
        authenticate with administrator credentials.  Allows a program to have admin credentials but run requests on behalf of users.
        :param conn: Use this httplib connection object rather than initiating a new one. Only for testing.
        :param logger: Use this logger object rather than initiating a new one. Only for testing.
        """
        from urlparse import urlparse
        self.user=user
        self.passwd=passwd
        self.host=host
        self.run_as=run_as
        self._delay=0
        self._delayedcounter = 0
        self._undelayedcounter = 0
        self.name = None
        self.logger = logger if logger is not None else logging.getLogger(__name__)
        if port:
            self.port=port

        if url is not None:
            bits = urlparse(url)
            if ':' in bits.netloc:
                self.host, self.port = bits.netloc.split(':')
            else:
                self.host = bits.netloc

        self._conn = conn if conn is not None else httplib.HTTPConnection(self.host, self.port)
        
    class NotPopulatedError(StandardError):
        """
        Exception explaining that the Vidispine object must have been populated by a call to populate() or similar
        before the given operation can complete
        """
        pass

    def _nodeContentOrNone(self,nodeName):
        if self.dataContent is None:
            raise self.NotPopulatedError

        ns = "{http://xml.vidispine.com/schema/vidispine}"
        try:
            return self.dataContent.find(('{0}'+nodeName).format(ns)).text
        except:
            return None

    def reset_http(self):
        """
        creates a new http connection
        :return:
        """
        try:
            if self._conn is not None:
                self._conn.close()
        except:
            pass
        self._conn = httplib.HTTPConnection(self.host,self.port)

    def __eq__(self, other):
        if not isinstance(self,VSApi) or not isinstance(other,VSApi):
            return NotImplemented
        if self.name is None or other.name is None:
            raise self.NotPopulatedError #both objects must be populated, or at least have IDs, for this to work
        
        return self.name==other.name

    def __ne__(self, other):
        return not self.__eq__(other)
    
    def sendAuthorized(self,method,url,body,headers,rawData=False):
        """
        Internal method to sign requests. Callers should use request() instead
        :param method:
        :param url:
        :param body:
        :param headers:
        :return:
        """
        import time
        attempt = 0
        auth = base64.encodestring('%s:%s' % (self.user, self.passwd)).replace('\n', '')

        headers['Authorization']="Basic %s" % auth
        if self.run_as is not None:
            headers['RunAs'] = self.run_as

        response = None
        conn = self._conn

        if rawData == False and body is not None:
            body_to_send = body.decode('utf-8',"backslashreplace").encode('utf-8',"backslashreplace")
        else:
            body_to_send = body

        while True:
            self.logger.debug("sending {0} request to {1} with headers {2}".format(method,url,headers))
            try:
                conn.request(
                    method,
                    url.decode('utf-8',"backslashreplace").encode('utf-8',"backslashreplace"),
                    body_to_send if body else None,
                    headers
                )
            except httplib.CannotSendRequest:
                attempt+=1
                logger.warning("HTTP connection re-use issue detected, resetting connection")
                self.reset_http()
                time.sleep(1)
                if attempt>10:
                    raise
                continue
            except socket_error as e:
                attempt +=1
                logger.warning("Socket error: {0}, resetting conection".format(str(e)))
                self.reset_http()
                time.sleep(1)
                if attempt>10:
                    raise
                continue

            response = conn.getresponse()
            if response.status == 303:
                url = response.msg.dict['location']
                logger.debug("Response was a redirect to {0}".format(url))
                conn = httplib.HTTPConnection(self.host,self.port)
            elif response.status == 504:    #gateway timeout
                #if we're getting timeouts, apply an exponential backoff
                if self._delay==0:
                    self._delay = 1
                else:
                    self._delay *= 2
                self._delayedcounter+=1
                self._undelayedcounter=0

                logger.warning("Gateway timeout error communicating with {0}. Waiting {1} seconds before trying again.".format(url,self._delay))
                time.sleep(self._delay)
            else:
                self._undelayedcounter+=1
                if self._delay>0 and self._undelayedcounter>10*self._delayedcounter:
                    logger.warning("{0} attempts have now suceeded with no delay, so removing the delay.".format(self._undelayedcounter))
                    self._delay=0
                    self._delayedcounter=0
                break

        return response

    def chunked_upload_request(self,upload_io,total_size,chunk_size,
                               path,transferPriority=500,throttle=True,method="GET",matrix=None,query=None,
                               filename=None,
                               accept="application/xml",content_type='application/octet-stream',extra_headers={}):
        """
        Performs a chunked upload
        :param upload_io: io base class to get data from
        :param total_size: total size of the object being uploaded, in bytes
        :param chunk_size: size of each chunk, in bytes
        :param args: other args to request()
        :param kwargs:  other kwargs to request()
        :return:
        """
        from uuid import uuid4
        
        transfer_id = uuid4().get_hex()
        
        query_params={
            'transferId': transfer_id,
            'transferPriority': transferPriority,
            'throttle'        : throttle,
        }
        if filename is not None:
            query_params['filename'] = filename
            
        if query is not None:
            query_params.update(query)
            
        #fix for older versions of python not having io.SEET_SET but putting it in os
        if hasattr(io,'SEEK_SET'):
            my_seek_set = io.SEEK_SET
        elif hasattr(os, 'SEEK_SET'):
            my_seek_set = os.SEEK_SET
        else:
            raise RuntimeError("neither io nor os has SEEK_SET, this should not happen. Check your python interpreter")

        if content_type == 'application/octet-stream':
            raw_data = True
        else:
            raw_data = False

        total_uploaded = 0
        self.logger.debug("Commencing upload from {0} in chunks of {1}".format(upload_io,chunk_size))
        self.logger.debug("uploading to {0} with account {1}".format(self.host,self.user))

        for startbyte in range(0,total_size,chunk_size):
            headers = {
                'size': total_size,
                'index': startbyte
            }
            upload_io.seek(startbyte,my_seek_set)
            body_buffer = upload_io.read(chunk_size)
            request = self.raw_request(path,method=method,matrix=matrix,query=query_params,body=body_buffer,
                             content_type=content_type,rawData=raw_data,extra_headers=headers)
            self.logger.debug("Uploaded a total of {0} bytes".format(startbyte+chunk_size))

        return request
            
    def request(self,path,method="GET",matrix=None,query=None,body=None, accept='application/xml'):
        """
        Send a request to Vidispine, returning a parsed XML element tree if XML content is returned or raising VSExceptions
        if not successful.  Automatically retries at 10s intervals if a 503 Server Unavailable is returned.
        :param path: URL path to send the request to, not including /API
        :param method: GET, PUT, POST, DELETE, etc. - the HTTP method to request
        :param matrix: A dictionary of "matrix parameters" for the API call. Consult Vidispine documentation for valid
        parameters for each call.
        :param query: A dictionary of "query parameters" for the API call.  Consult Vidispine documentation for valid
        parameters for each call
        :param body: String representing the raw request body to send. Normally this will be representation of an XML or JSON document.
        :param accept: String representing the MIME type of data to accept in return. Default is application/xml.
        :return: A parsed XML element tree if data is returned or the string "Success" if there is no data. Raises VSException
        subclasses if an error occurs.
        """
        from xml.parsers.expat import ExpatError
        n=0
        raw_body=""
        while True:
            try:
                n+=1
                raw_body=self.raw_request(path.replace(' ', '%20'),method=method,matrix=matrix,query=query,body=body,accept=accept)
                break
            except HTTPError as e:
                if e.code==503: #server unavailable
                    self.logger.warning("Server not available error when contacting Vidispine. Waiting {0}s before retry.".format(self.retry_delay))
                    sleep(self.retry_delay)
                    if n>self.retry_attempts:
                        self.logger.error("Did not work after %d retries, giving up" % self.retry_attempts)
                        raise e
                else:
                    raise e
            except httplib.BadStatusLine as e: #retry if we got a bad status line
                logging.warning("Bad status line: {0}".format(unicode(e)))
                sleep(self.retry_delay)
                if n>self.retry_attempts:
                    self.logger.error("Did not work after %d tries, giving up" % self.retry_attempts)
                    raise e

        if raw_body.__len__() > 0:
            try:
                if accept=='application/xml':
                    return ET.fromstring(unicode(raw_body,errors='ignore'))
                else:
                    return raw_body
            except ExpatError:
                logging.error("XML that caused the error: ")
                logging.error(raw_body)
                raise
        else:
            return "Success"

    @staticmethod
    def _escape_for_query(value):
        if isinstance(value,basestring):
            try:
                toprocess = value.encode("UTF-8")
            except UnicodeDecodeError:
                toprocess = value
        else:
            toprocess = str(value)
        return urllib.pathname2url(toprocess).replace("/", "%2F")

    @staticmethod
    def _get_param_list(key, value):
        if not isinstance(value,list):
            toprocess = [value]
        else:
            toprocess = value

        return map(lambda item: "{0}={1}".format(key, VSApi._escape_for_query(item)), toprocess)

    def raw_request(self,path,method="GET",matrix=None,query=None,body=None,accept="application/xml",
                    content_type='application/xml',rawData=False,extra_headers={}):
        """
        Internal method to build request parameters.  Callers should use request() instead.
        :param path:
        :param method:
        :param matrix:
        :param query:
        :param body:
        :return:
        """
        base_headers={ 'Accept': accept, }
        if body is not None:
            base_headers['Content-Type'] = content_type

        base_headers.update(extra_headers)

        if matrix:
            matrixpart = ";"+ ";".join(flatmap(lambda (k,v): self._get_param_list(k,v), matrix.items()))
        else:
            matrixpart=""

        if query:
            querypart = "&".join(flatmap(lambda (k,v): self._get_param_list(k,v), query.items()))
        else:
            querypart = ""

        url="/API"+path+matrixpart
        if(len(querypart)> 0):
            url+='?'+querypart

        if method == "POST" and body is None:
            body = ""

        response=self.sendAuthorized(method,url,body,base_headers,rawData=rawData)

        if response.status<200 or response.status>299:
            raise HTTPError(response.status,method,url,response.status,response.reason,response.read()).to_VSException(method=method,url=url,body=body)

        return response.read()

    def xml_content(self):
        """
        Returns a string representing the XML of the VSApi object
        :return: a String
        """
        return ET.tostring(self.dataContent,encoding='utf8')

    def set_metadata(self,path,md,mode="default"):
        """
        Set "simple metadata" on the object. This is suitable for regular objects but not for Items and other things that
        have advanced metadata.
        :param path: Path to the object to set
        :param md: Dictionary of metadata key/value pairs to set
        :return: Result of the request() call
        """
        doc='<SimpleMetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine">'
        for key,value in md.items():
            if mode == "add":
                doc=doc+'\n<field><key>%s</key><value mode="add">%s</value></field>' % (key,value)
            else:
                doc=doc+"\n<field><key>%s</key><value>%s</value></field>" % (key,value)
        doc=doc+'</SimpleMetadataDocument>'

        path=path+'/metadata'
        self.request(path,method="PUT",body=doc)

    def get_metadata(self,path):
        """
        Get a dictionary representing "simple metadata" for the object. This is suitable for regular objects but not for
        Items and other things that have advanced metadata.
        :param path: Path of the object to get
        :return: Dictionary of metadata key/value pairs
        """
        path=path+'/metadata'
        dataContent=self.request(path,method="GET")

        rtn={}

        for nodeset in dataContent.findall('{0}field'.format("{http://xml.vidispine.com/schema/vidispine}")):
            #print ET.dump(nodeset)
            try:
                key=nodeset.find('{0}name'.format("{http://xml.vidispine.com/schema/vidispine}")).text
                val=nodeset.find('{0}value'.format("{http://xml.vidispine.com/schema/vidispine}")).text
                rtn[key]=val
            except AttributeError as e:
                self.logger.warning(str(e))

        for nodeset in dataContent.findall('{0}timespan/{0}field'.format("{http://xml.vidispine.com/schema/vidispine}")):
            try:
                key=nodeset.find('{0}name'.format("{http://xml.vidispine.com/schema/vidispine}")).text
                val=nodeset.find('{0}value'.format("{http://xml.vidispine.com/schema/vidispine}")).text
                rtn[key]=val
            except AttributeError as e:
                self.logger.warning(str(e))

        return rtn

    def dump_xml(self):
        return ET.tostring(self.dataContent)

    def as_xml(self):
        """
        Return a string representing the XML document that is encapsulated by this object
        :return: String representing XML
        """
        return ET.tostring(self.dataContent)

    def findPortalDataNode(self,node,should_create=False):
        foundKey = False
        if node is None:
            return None

        for child in node:
            if child.tag.endswith("key") and child.text == "extradata":
                foundKey = True

            if foundKey and child.tag.endswith("value"):
                return child

        if should_create:
            keynode =  ET.SubElement(node,"{0}key".format(self.xmlns))
            keynode.text = "extradata"
            valnode = ET.SubElement(node,"{0}value".format(self.xmlns))
            return valnode
        return None

    def findPortalData(self, node, ns=None):
        """
        Returns a dictionary representing Portal "extra_data" associated with the object
        :param node: ElementTree node to examine
        :param ns: XML Namespace of the document, normally keep this to the default.
        :return: Dictionary representing the contents of the Portal-specific data, or None if no such data is present
        """
        child = self.findPortalDataNode(node)

        if child==None:
            return None

        value = child.text
        if value is None:
            return None
        else:
            self.portalData = json.loads(value)
            return self.portalData


    def updatePortalData(self,node,should_create=False):
        """
        Update the JSON string of portal data from the broken-out version.
        :param node: ElementTree node of the Vidispine object
        :param ns: XML Namespace of the document, normally keep this to the default.
        :return: None
        """
        child=self.findPortalDataNode(node,should_create=should_create)

        child.text=json.dumps(self.portalData)
