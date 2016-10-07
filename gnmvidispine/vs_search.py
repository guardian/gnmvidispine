__author__ = 'Andy Gallagher <andy.gallagher@theguardian.com>'

from vidispine_api import VSApi,VSBadRequest,VSException,VSNotFound
from vs_timecode import VSTimecode
from vs_item import VSItem
from vs_collection import VSCollection

import xml.etree.ElementTree as ET
import logging
import datetime

logger = logging.getLogger(__name__)


class VSSearchRange:
    def __init__(self,start=None,end=None):
        self.start=start
        self.end=end

    def to_xml(self,parentNode):
        rangeNode=ET.SubElement(parentNode,'range')
        startNode=ET.SubElement(rangeNode,'value')
        if isinstance(self.start, datetime.datetime):
            startNode.text=self.start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        elif isinstance(self.start, int):
            startNode.text=str(self.start)
        elif isinstance(self.start, VSTimecode):
            startNode.text=self.start.to_vidispine()
        else:
            startNode.text=self.start

        endNode=ET.SubElement(rangeNode,'value')
        if isinstance(self.end, datetime.datetime):
            endNode.text=self.end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        elif isinstance(self.end, int):
            endNode.text=str(self.end)
            #if self.end==0: star
        elif isinstance(self.end, VSTimecode):
            endNode.text = self.end.to_vidispine()
        else:
            endNode.text=self.end

    def to_facet_xml(self,parentNode):
        rangeNode=ET.SubElement(parentNode,'range')
        if isinstance(self.start,datetime):
            rangeNode.attrib['start']=self.start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        else:
            rangeNode.attrib['start']=self.start
        if isinstance(self.end,datetime):
            rangeNode.attrib['end']=self.end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        else:
            rangeNode.attrib['end']=self.end


class VSSearchOperator(object):
    def __init__(self,operation):
        self._criteria = {}
        self.operation = operation

    def addCriterion(self,crit):
        if not isinstance(crit, dict): raise ValueError

        for k,v in crit.items():
            self._criteria[k] = v

    def to_xml(self,parentNode):
        opNode = ET.SubElement(parentNode, 'operator', attrib={'operation': self.operation})
        for k,v in self._criteria.items():
            if isinstance(v,VSSearchOperator):
                v.to_xml(opNode)
            else:
                fieldEl = ET.SubElement(opNode,'field')
                nameEl = ET.SubElement(fieldEl,'name')
                nameEl.text = unicode(k)

                if isinstance(v,VSSearchRange):
                    v.to_xml(fieldEl)
                elif isinstance(v,list):
                    for value in v:
                        valueEl = ET.SubElement(fieldEl,'value')
                        valueEl.text = unicode(value)
                else:
                    valueEl = ET.SubElement(fieldEl,'value')
                    valueEl.text = unicode(v)


class VSFacet(object):
    def __init__(self,field=None,count=False):
        self.fieldName=field
        self.shouldCount=count
        self.ranges=[]

    def addRange(self,range):
        if not isinstance(range,VSSearchRange):
            raise TypeError("When adding a range to a facet it must be a VSSearchRange")
        self.ranges.append(range)

    def to_xml(self,parentNode):
        facetNode=ET.SubElement(parentNode,'facet')
        if self.shouldCount:
            facetNode.attrib['count']="true"
        else:
            facetNode.attrib['count']="false"

        fieldNode=ET.SubElement(facetNode,'field')
        fieldNode.text=self.fieldName
        for r in self.ranges:
            r.to_facet_xml(facetNode)


class VSSearchResult(VSApi):
    def __init__(self, search_url="", body="",searchType="",debug=False, pageSize=100, *args,**kwargs):
        super(VSSearchResult, self).__init__(*args,**kwargs)
        self.searchURL = search_url
        #self.searchParam = urllib.pathname2url(body.replace('/','%2F'))
        self.searchParam = body
        self.itemsRetrieved = 0
        self.pageSize = pageSize
        self.totalItems = -1
        self.debug = debug
        self.cachedData = None
        self.searchType = searchType

    def _nextPage(self, page_number=-1):
        #ns = "{http://xml.vidispine.com/schema/vidispine}"
        start_at = self.itemsRetrieved+1
        if page_number>=0:
            start_at = page_number*self.pageSize
            if start_at<1:
                start_at=1
        if self.searchType == "search":
            xmlData = self.request(self.searchURL,method="PUT",
                                   matrix={'first': start_at, 'number': self.pageSize},
                                   body=self.searchParam
                                   )
        else:
            logger.debug("VSSearchResult::_nextPage: url is {0} first is {1} number is {2} method is PUT body is {3}".format(
                self.searchURL,start_at,self.pageSize,self.searchParam
            ))
            xmlData = self.request(self.searchURL,method="PUT",
                         matrix={'first': start_at, 'number': self.pageSize },
                         #query={'q': self.searchParam }
                        body=self.searchParam,
            )

        hitsNode = xmlData.find('{0}hits'.format(self.xmlns))
        if hitsNode is not None:
            self.totalItems = int(hitsNode.text)
            #self.itemsRetrieved += self.pageSize
        else:
            logger.debug(ET.tostring(xmlData))
            raise AssertionError("Invalid XML returned from search request (no hits node)")

        return xmlData

    def setup(self,page_number=-1):
        self.cachedData = self._nextPage(page_number=page_number)
        return self

    def facets(self):
        #ns = "{http://xml.vidispine.com/schema/vidispine}"
        if self.cachedData is not None:
            pageData = self.cachedData
        else:
            logger.debug("getting next page of results...")
            pageData = self._nextPage()
            self.cachedData = pageData

        for node in pageData.findall('{0}facet'.format(self.xmlns)):
            rtn={}
            for countNode in node.findall('{0}count'.format(self.xmlns)):
                rtn[countNode.attrib['fieldValue']] = int(countNode.text)
            try:
                rtn['facet_field_name']=node.find('{0}field'.format(self.xmlns)).text
            except Exception:
                pass
            yield rtn

    def _namedChildNode(self,parent,child_name):
        return parent.find('{0}{1}'.format(self.xmlns,child_name))

    def _page_node_generator(self,pageDataRoot,shouldPopulate=False):
        rtn=None
        for childnode in pageDataRoot:
            # pprint(childnode)
            if childnode.tag.endswith('hits'):
                nhits = int(childnode.text)
                logger.debug("Hits: {0}".format(nhits))
                if self.totalItems<0:
                    self.totalItems = nhits
                #print "Hits: {0}".format(int(childnode.text))
            elif childnode.tag.endswith('item'):
                itemid = childnode.attrib['id']
                itemstart = childnode.attrib['start']
                itemend = childnode.attrib['end']
                logger.debug("Item: {0} ({1} -> {2})".format(itemid, itemstart, itemend))
                rtn = VSItem(self.host,self.port,self.user,self.passwd)
                if shouldPopulate:
                    rtn.populate(itemid)
                else:
                    rtn.name = itemid
            elif childnode.tag.endswith('collection'):
                rtn = VSCollection(self.host,self.port,self.user,self.passwd)
                try:
                    if shouldPopulate:
                        rtn.populate(childnode.attrib['id'])
                    else:
                        rtn.name = childnode.attrib['id']
                except KeyError:  # no attrib['id'], so look for the id as a subnode
                    node = self._namedChildNode(childnode, 'id')
                    if node is not None:
                        if shouldPopulate:
                            rtn.populate(node.text)
                        else:
                            rtn.name = node.text
                    else:  # no <id> node either
                        logger.error("Invalid data received - no <id> attribute or node for <collection>")
            elif childnode.tag.endswith('entry'):
                if childnode.attrib['type']=="Collection":
                    rtn = VSCollection(self.host,self.port,self.user,self.passwd)
                    if shouldPopulate:
                        rtn.populate(childnode.attrib['id'])
                    else:
                        rtn.name = childnode.attrib['id']
                elif childnode.attrib['type']=="Item":
                    rtn = VSItem(self.host,self.port,self.user,self.passwd)
                    if shouldPopulate:
                        rtn.populate(childnode.attrib['id'])
                    else:
                        rtn.name = childnode.attrib['id']
            elif childnode.tag.endswith('facet'):
                pass
            else:
                raise AssertionError("Unexpected node type in document: {0}".format(childnode.tag))
            # if rtn is None:
            #     raise AssertionError("Search type is not item, collection, etc.")
            if rtn is not None:
                self.itemsRetrieved += 1
                yield rtn

    def results(self,shouldPopulate=True):
        while(self.totalItems<0 or self.itemsRetrieved<self.totalItems):
            if self.cachedData is not None:
                pageData = self.cachedData
                self.cachedData = None
            else:
                logger.debug("getting next page of results...")
                pageData = self._nextPage()

            for i in self._page_node_generator(pageData,shouldPopulate=shouldPopulate):
                yield i

    def results_page(self,page_number,shouldPopulate=True):
        if self.cachedData is not None:
            pageData = self.cachedData
            self.cachedData = None
        else:
            pageData = self._nextPage(page_number)
        for i in self._page_node_generator(pageData,shouldPopulate=shouldPopulate):
            yield i


class VSSearch(VSApi):
    def __init__(self,searchType="search",*args,**kwargs):
        super(VSSearch, self).__init__(*args,**kwargs)
        self.dataContent = None
        self.contentDict = {}
        self.criteria = {}
        self.pageSize = 100
        self.facets = []
        self.sorts = []
        self.group = None
        self.container = None
        if searchType is None:
            raise AssertionError("SearchType must identify a type of search")
        self.searchType = searchType

    def addCriterion(self,crit):
        if not isinstance(crit,dict):
            raise TypeError

        for k,v in crit.items():
            self.criteria[k]=v

    def addFacet(self,facet):
        if not isinstance(facet,VSFacet):
            raise TypeError
        self.facets.append(facet)

    def addSort(self,fieldname,order):
        if order!="ascending" and order!="descending":
            raise ValueError("order must be ascending or descending")

        self.sorts.append({'field': fieldname,'order': order})

    def setMasterGroup(self,grp):
        self.group = grp

    def _makeXML(self):
        vs = "{http://xml.vidispine.com/schema/vidispine}"
        root = ET.Element('ItemSearchDocument')
        root.attrib['xmlns'] = "http://xml.vidispine.com/schema/vidispine"

        if self.group is not None:
            groupEl = ET.SubElement(root,'group'.format(vs))
            groupEl.text = self.group

        for k,v in self.criteria.items():
            if isinstance(v,VSSearchOperator):
                v.to_xml(root)
                continue

            fieldEl = ET.SubElement(root,'field'.format(vs))
            nameEl = ET.SubElement(fieldEl,'name'.format(vs))
            nameEl.text = unicode(k)
            if isinstance(v,list):
                for value in v:
                    valueEl = ET.SubElement(fieldEl,'value'.format(vs))
                    valueEl.text = unicode(value)
            elif isinstance(v,VSSearchRange):
                v.to_xml(fieldEl)
            else:
                valueEl = ET.SubElement(fieldEl,'value'.format(vs))
                valueEl.text = unicode(v)

        for f in self.facets:
            f.to_xml(root)

        for s in self.sorts:
            sortEl = ET.SubElement(root,'sort')
            fieldEl = ET.SubElement(sortEl,'field')
            fieldEl.text = s['field']
            orderEl = ET.SubElement(sortEl,'order')
            orderEl.text = s['order']

        return ET.tostring(root)

    def execute(self,page_number=-1):
        xmlBody = self._makeXML()
        logger.debug("VSSearch::execute - request body is %s" % xmlBody)
        if xmlBody is None:
            raise AssertionError("No search XML was generated")
        #if self.debug:
        #    print xmlBody

        if self.container is None:
            url = "/{type}".format(type=self.searchType)
        else:
            url = "/{type}/{container}/item".format(type=self.searchType,container=self.container)

        logger.debug("VSSearch::execute - url is %s" % url)

        #call to .setup retrieves the first page of results and with it information like total number of hits
        rtn= VSSearchResult(host=self.host,port=self.port,user=self.user,passwd=self.passwd,
                        search_url=url,body=xmlBody,searchType=self.searchType,debug=self.debug,pageSize=self.pageSize).setup(page_number=page_number)
        rtn.pageSize = self.pageSize
        return rtn


class VSItemSearch(VSSearch):
    def __init__(self,*args,**kwargs):
        super(VSItemSearch,self).__init__(searchType="item", *args, **kwargs)


class VSCollectionSearch(VSSearch):
    def __init__(self,*args,**kwargs):
        super(VSCollectionSearch,self).__init__(searchType="collection", *args,**kwargs)