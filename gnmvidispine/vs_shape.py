from vidispine_api import VSApi,VSException,HTTPError, VSNotFound
from vs_storage_rule import VSStorageRule,VSStorageRuleCollection
import logging
import xml.etree.cElementTree as ET

class VSShape(VSApi):
    def __init__(self, *args,**kwargs):
        super(VSShape, self).__init__(*args,**kwargs)
        self.dataContent = None
        self.name = "INVALIDNAME"
        self.contentDict = {}

    def populate(self,itemid,id):
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        self.name = id
        self.dataContent = self.request("/item/%s/shape/%s" % (itemid,id))
        self.itemid = itemid

        for key in ['id','essenceVersion','tag','mimeType']:
            nodeName = "{0}%s" % key
            node = self.dataContent.find(nodeName.format(ns))

            if node is not None:
                self.contentDict[key] = node.text

    def tag(self):
        return self.contentDict['tag']

    def mimeType(self):
        return self.contentDict['mimeType']

    def fileURIs(self):
        #logging.debug("in fileURIs")
        if self.dataContent is not None:
            ns = "{http://xml.vidispine.com/schema/vidispine}"
            #logging.debug("got dataContent")
            for node in self.dataContent.findall("{0}containerComponent/{0}file".format(ns)):
                #logging.debug("got file element")
                n = node.find("{0}uri".format(ns))
                if n is not None:
                    #logging.debug("got uri")
                    yield n.text

    def files(self):
        """
        Generator that yields populated VSFile objects for all containerComponents on the shape
        :return:
        """
        from vs_storage import VSFile
        if self.dataContent is not None:
            ns = "{http://xml.vidispine.com/schema/vidispine}"
            #logging.debug("got dataContent")
            for node in self.dataContent.findall("{0}containerComponent/{0}file".format(ns)):
                f = VSFile(None,node,conn=self)
                yield f

    def download(self):
        """
        Initiate download of a file
        :return: HTTPResponse object. Call .read() on this to get the data
        """
        import httplib
        #import xml.etree.cElementTree as ET
        from pprint import pprint

        if self.dataContent is None:
            raise ValueError("You must populate a shape before calling download()")

        for componentType in ['containerComponent','binaryComponent']:
            for node in self.dataContent.findall("{0}{1}/{0}file".format(self.xmlns,componentType)):
                try:
                    #logging.debug(ET.tostring(node))
                    fileId = node.find('{0}id'.format(self.xmlns)).text
                    storageId = node.find('{0}storage'.format(self.xmlns)).text

                    logging.debug("trying to download {0} from storage {1}".format(fileId,storageId))

                    conn=httplib.HTTPConnection(self.host, self.port)
                    response = self.sendAuthorized(conn,'GET','/API/storage/file/{0}/data'.format(fileId),'',{'Accept': '*'})
                    if response.status < 200 or response.status > 299:
                        pprint(response.msg.__dict__)
                        raise HTTPError(response.status,'GET','/API/storage/file/{0}/data'.format(fileId),response.status,response.reason,response.read()).to_VSException(method='GET',url='/storage/file/{0}/data'.format(fileId),body="")

                    return response
                except TypeError as e:
                    logging.warning(e)
                except AttributeError as e:
                    logging.warning(e)
                except VSNotFound as e:
                    logging.warning(e)

    @property
    def mime_type(self):
        if self.dataContent is None:
            raise ValueError("You must populate a shape before calling mime_type")

        try:
            return self.dataContent.find('{0}mimeType'.format(self.xmlns)).text
        except AttributeError:
            return None

    @property
    def essence_version(self):
        if self.dataContent is None:
            raise ValueError("You must populate a shape before calling essence_version")

        try:
            return int(self.dataContent.find('{0}essenceVersion'.format(self.xmlns)).text)
        except ValueError:
            return None
        except AttributeError:
            return None

    def storageRuleXML(self):
        path = "/item/{0}/shape/{1}/storage-rule".format(self.itemid,self.name)
        data = self.request(path,method="GET",query={'all': 'true'})

        return data

    def storageRule(self):
        """
        DEPRECATED. Use storage_rules() instead.
        :return:
        """
        ret = VSStorageRule(host=self.host,port=self.port,user=self.user,passwd=self.passwd)
        ret.populateFromXml(self.storageRuleXML())
        return ret

    def storage_rules(self):
        ret = VSStorageRuleCollection(self.host,self.port,self.user,self.passwd)
        ret.populate_from_xml(self.storageRuleXML())
        return ret

    def _analyzeDocFragment(self,parentElem,fragname,threshold=None,percentage=None,time=None):
        fragroot = ET.SubElement(parentElem,fragname)
        if threshold is not None:
            thresElem = ET.SubElement(fragroot,"threshold")
            thresElem.text = str(threshold)
        if percentage is not None:
            percElem = ET.SubElement(fragroot,"percentage")
            percElem.text = str(percentage)
        if time is not None:
            timeElem = ET.SubElement(fragroot, "time")
            timeElem.text = str(time)
        return fragroot
    
    def analyze(self,blackThreshold=0.1,blackPercentage=95,
                freezeThreshold=0.05,freezeTime=4.0,
                barsThreshold=0.05,barsPercentage=10,priority="MEDIUM"):
        """
        Requests that Vidispine perform loudness, black frame etc. analysis of the shape
        :param priority: optional - job priority for the analyse
        :return: A VSJob representing the analyze job, or an exception
        """
        from vs_job import VSJob
        path = "/item/{0}/shape/{1}/analyze".format(self.itemid,self.name)
        
        analyzeDocRoot = ET.Element("AnalyzeJobDocument",{'xmlns': 'http://xml.vidispine.com/schema/vidispine'})
        self._analyzeDocFragment(analyzeDocRoot,"black",threshold=blackThreshold,percentage=blackPercentage)
        self._analyzeDocFragment(analyzeDocRoot,"freeze",threshold=freezeThreshold,time=freezeTime)
        self._analyzeDocFragment(analyzeDocRoot,"bars",threshold=barsThreshold,percentage=barsPercentage)
        
        print ET.tostring(analyzeDocRoot)
        data = self.request(path,method="POST",query={'priority': priority},body=ET.tostring(analyzeDocRoot,encoding="UTF-8"))
        j = VSJob(host=self.host,port=self.port,user=self.user,passwd=self.passwd,run_as=self.run_as)
        j.fromResponse(data)
        return j
    
    def __unicode__(self):
        return u'Vidispine shape {0}: tag {1} type {2} version {3}'.format(self.name,self.tag(),self.mime_type,self.essence_version)