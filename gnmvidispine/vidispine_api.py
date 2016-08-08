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
            else:
                return self
        except Exception as e:
            logging.error(e.message)
            return self


class VSException(StandardError):
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

        try:
            exceptionData = ET.fromstring(xmldata)
            #root = exceptionData.getroot()

            for child in exceptionData:
                self.exceptionType = child.tag
                self.exceptionType = re.sub(r'{[^}]+}','',self.exceptionType)
                self.exceptionWhat = self.getNodeContent(child,'{0}explanation'.format('{http://xml.vidispine.com/schema/vidispine}'),default="no explanation provided")
                self.exceptionID = self.getNodeContent(child,'{0}id'.format('{http://xml.vidispine.com/schema/vidispine}'),default="no id provided")
                self.exceptionContext = self.getNodeContent(child,'{0}context'.format('{http://xml.vidispine.com/schema/vidispine}'),default="no context provided")
        except Exception as e:
            #raise InvalidData("Not given Vidispine exception XML")
            raise e

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

    def __init__(self,host="localhost",port=8080,user="",passwd="",url=None,run_as=None):
        """
        Initialise a new Vidispine connection.
        :param host: Hostname to connect to Vidispine on
        :param port: Port number to connect to Vidispine on
        :param user: Username to connect to Vidispine
        :param passwd: Password for the given user
        """
        from urlparse import urlparse
        self.user=user
        self.passwd=passwd
        self.host=host
        self.run_as=run_as
        self._delay=0
        self._delayedcounter = 0
        self._undelayedcounter = 0
        if port:
            self.port=port

        if url is not None:
            bits = urlparse(url)
            if ':' in bits.netloc:
                self.host, self.port = bits.netloc.split(':')
            else:
                self.host = bits.netloc

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

    def debug(self, dodebug):
        self.debug=dodebug


    def sendAuthorized(self,conn,method,url,body,headers):
        """
        Internal method to sign requests. Callers should use request() instead
        :param conn:
        :param method:
        :param url:
        :param body:
        :param headers:
        :return:
        """
        import time
        auth = base64.encodestring('%s:%s' % (self.user, self.passwd)).replace('\n', '')
        #conn.putheader("Authorization", "Basic %s" % auth)
        #conn.endheaders()
        #if headers.__class__ != "<type 'dict'>":
        #	raise TypeError("VSApi::sendAuthorized: you need to specify a dictionary of headers. Use {} for blank. Type was %s" % headers.__class__)

        headers['Authorization']="Basic %s" % auth
        if self.run_as is not None:
            headers['RunAs'] = self.run_as

        response = None
        while True:
            conn.request(method,url,body,headers)

            response = conn.getresponse()
            if response.status == 303:
                #pprint(response.msg.dict)
                url = response.msg.dict['location']
                logger.debug("Response was a redirect to {0}".format(url))
                conn = httplib.HTTPConnection(self.host,self.port)
                #return self.sendAuthorized(newConn,method,newURL,body,headers)
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
        #return conn

    def request(self,path,method="GET",matrix=None,query=None,body=None):
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
        :return: A parsed XML element tree if data is returned or the string "Success" if there is no data. Raises VSException
        subclasses if an error occurs.
        """
        n=0
        raw_body=""
        while True:
            try:
                n+=1
                raw_body=self.raw_request(path.replace(' ', '%20'),method=method,matrix=matrix,query=query,body=body)
                break
            except HTTPError as e:
                if e.code==503: #server unavailable
                    logging.warning("Server not available error when contacting Vidispine. Waiting {0}s before retry.".format(self.retry_delay))
                    sleep(self.retry_delay)
                    if n>self.retry_attempts:
                        logging.error("Did not work after %d retries, giving up" % self.retry_attempts)
                        raise e
                else:
                    raise e
            except httplib.BadStatusLine as e: #retry if we got a bad status line
                logging.warning("Bad status line: {0}".format(unicode(e)))
                sleep(self.retry_delay)
                if n>self.retry_attempts:
                    logging.error("Did not work after %d tries, giving up" % self.retry_attempts)
                    raise e

        if raw_body.__len__() > 0:
            return ET.fromstring(raw_body)
        else:
            return "Success"

    def raw_request(self,path,method="GET",matrix=None,query=None,body=None,accept="application/xml"):
        """
        Internal method to build request parameters.  Callers should use request() instead.
        :param path:
        :param method:
        :param matrix:
        :param query:
        :param body:
        :return:
        """
        base_headers={ 'Accept': accept,
                    'Content-Type': 'application/xml' }

        matrixpart=""

        if matrix:
            #if matrix.__class__ != "<type 'dict'>":
            #	raise TypeError("Matrix argument must be a dictionary, if it is specified")
            for key,value in matrix.items():
                #if isinstance(value,basestring):
                #value=value.replace(' ', '%20') #if you leave this in, then the % sign gets encoded by the next step!
                if isinstance(value,basestring):
                    value=urllib.pathname2url(value)
                    value=value.replace("/", "%2F")
                if isinstance(key,basestring):
                    key=urllib.pathname2url(key)
                tmp=";%s=%s" % (key, value)
                matrixpart=matrixpart+tmp

        querypart=""
        if query:
            #if query.__class__ != "<type 'dict'>":
            #	raise TypeError("Query argument must be a dictionary, if it is specified")
            for key,value in query.items():
                #value=value.replace(' ', '%20') #if you leave this in, then the % sign gets encoded by the next step!
                if isinstance(value,basestring):
                    value=urllib.pathname2url(value)
                    value=value.replace("/", "%2F")
                if isinstance(key,basestring):
                    key=urllib.pathname2url(key)
                querypart+="%s=%s&" % (urllib.pathname2url(key), value)

            #querypart.replace("?", "&", 1)

        url="/API"+path+matrixpart
        if(len(querypart)> 0):
            url+='?'+querypart[:-1]

        if self.debug==True:
            print "Performing %s on %s..." % (method, url)

        if method == "POST" and body is None:
            body = ""
        #print body

        conn=httplib.HTTPConnection(self.host,self.port)

        response=self.sendAuthorized(conn,method,url,body,base_headers)
        #response=conn.getresponse()
        #if response.status==404:
        #    replyData = response.read()
        #    if replyData:
        #        raise VSNotFound(replyData)
        #    else:
        #        raise VSNotFound("%s was not present",path)

        if response.status<200 or response.status>299:
            #raise HTTPError("Request was: %s to %s\n\nServer returned %d (%s)\n%s" % (method,url,response.status, response.reason, response.read()))
            #self,code,method,url,status,reason,body
            raise HTTPError(response.status,method,url,response.status,response.reason,response.read()).to_VSException(method=method,url=url,body=body)

        return response.read()

    def xml_content(self):
        """
        Returns a string representing the XML of the VSApi object
        :return: a String
        """
        return ET.tostring(self.dataContent,encoding='utf8')

    def set_metadata(self,path,md):
        """
        Set "simple metadata" on the object. This is suitable for regular objects but not for Items and other things that
        have advanced metadata.
        :param path: Path to the object to set
        :param md: Dictionary of metadata key/value pairs to set
        :return: Result of the request() call
        """
        doc='<SimpleMetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine">'
        for key,value in md.items():
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

#ET.dump(dataContent)
        for nodeset in dataContent.findall('{0}field'.format("{http://xml.vidispine.com/schema/vidispine}")):
            #print ET.dump(nodeset)
            try:
                key=nodeset.find('{0}name'.format("{http://xml.vidispine.com/schema/vidispine}")).text
                val=nodeset.find('{0}value'.format("{http://xml.vidispine.com/schema/vidispine}")).text
                rtn[key]=val
            except AttributeError as e:
                print "WARNING: %s" % e.message

        for nodeset in dataContent.findall('{0}timespan/{0}field'.format("{http://xml.vidispine.com/schema/vidispine}")):
            #print ET.dump(nodeset)
            try:
                key=nodeset.find('{0}name'.format("{http://xml.vidispine.com/schema/vidispine}")).text
                val=nodeset.find('{0}value'.format("{http://xml.vidispine.com/schema/vidispine}")).text
                rtn[key]=val
            except AttributeError as e:
                print "WARNING: %s" % e.message

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
            #logging.debug("findPortalData: tag %s\n" % child.tag)

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
        :return: Dictionary representing the contents of the Portal-specific data
        """
        child = self.findPortalDataNode(node)

        if child==None:
            return None

        value = child.text
        #print "got extradata: %s" % value
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