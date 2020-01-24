from .vidispine_api import VSApi,VSException,VSNotFound
import xml.etree.ElementTree as ET
import re
from pprint import pprint


class VSUserGroup(VSApi):
    def __init__(self,*args,**kwargs):
        super(VSUserGroup, self).__init__(*args,**kwargs)
        self.dataContent = None

    def populateFromXML(self,xmlNode):
        self.dataContent = xmlNode

    def __unicode__(self):
        return '{0} {1}'.format(self.groupName,self.description)

    @property
    def groupName(self):
        return self._nodeContentOrNone('groupName')

    @property
    def description(self):
        return self._nodeContentOrNone('description')

    @property
    def role(self):
        #FIXME: not sure of schema under this node. might need more processing.
        return self._nodeContentOrNone('role')

    #return a dict of metadata
    @property
    def metadata(self):
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        rtn = {}
        try:
            for n in self.dataContent.find('{0}metadata'.format(ns)):
                try:
                    key = n.find('{0}key'.format(ns))
                    val = n.find('{0}value'.format(ns))
                    rtn[key] = val
                except:
                    continue

        except:
            pass
        return rtn

    @property
    def originSite(self):
        return self._nodeContentOrNone('origin')

class VSUser(VSApi):
    def __init__(self,*args,**kwargs):
        super(VSUser, self).__init__(*args,**kwargs)
        self.dataContent = None
        self.groupList = None

    class NotPopulatedError(Exception):
        pass

    def populate(self,username):
        if re.search(r'[\/?;]',username):
            raise ValueError

        response = self.request("/user/" + username)
        self.populateFromXML(response)

    def populateFromXML(self,xmlNode):
        self.dataContent = xmlNode
        self._populateGroupList()

    def _populateGroupList(self):
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        groupListNode = self.dataContent.find('{0}groupList'.format(ns))
        #pprint(groupListNode)
        if groupListNode is None:
            return

        if self.groupList is None:
            self.groupList = []

        for groupDef in groupListNode:
            #ET.dump(groupDef)
            g = VSUserGroup(self.host,self.port,self.user,self.passwd)
            g.populateFromXML(groupDef)
            self.groupList.append(g)

    def __unicode__(self):
        return '{0} ({1})'.format(self.userName,self.originSite)

    def dump(self):
        #ET.dump(self.dataContent)
        print("\tUser name: %s" % self.userName)
        print("\tReal name: %s" % self.realName)
        print("\tOrignating site: %s" % self.originSite)
        if self.groupList is not None:
            print("\tGroup memberships:")
            for g in self.groupList:
                print("\t\t%s" % str(g))
                #g.dump()

    @property
    def userName(self):
        return self._nodeContentOrNone('userName')

    @property
    def realName(self):
        return self._nodeContentOrNone('realName')

    #return a dict of metadata
    @property
    def metadata(self):
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        rtn = {}
        try:
            for n in self.dataContent.find('{0}metadata'.format(ns)):
                try:
                    key = n.find('{0}key'.format(ns))
                    val = n.find('{0}value'.format(ns))
                    rtn[key] = val
                except:
                    continue
        except:
            pass
        return rtn

    @property
    def originSite(self):
        return self._nodeContentOrNone('origin')

    @property
    def accountDisabled(self):
        try:
            return self.dataContent.attrib['disabled']
        except:
            return None

    @property
    def groups(self):
        if self.groupList is None:
            return

        for g in self.groupList:
            yield g

    def isMemberOfGroup(self,groupname,caseSensitive=False):
        if self.groupList is None:
            return

        if caseSensitive:
            for g in self.groupList:
                if g.groupName == groupname:
                    return True
        else:
            for g in self.groupList:
                if g.groupName.lower() == groupname.lower():
                    return True
        return False


def getAllUsers(pageSize=10,*args,**kwargs):
    api = VSApi(*args,**kwargs)

    ns = "{http://xml.vidispine.com/schema/vidispine}"
    userRecord = api.request("/user",query={'first': 1,'number': 1})
    nHits = int(userRecord.find('{0}hits'.format(ns)).text)

    u = VSUser(*args,**kwargs)
    u.populateFromXML(userRecord)
    yield u

    for n in range(2,nHits,pageSize):
        response = api.request("/user",query={'first': n,'number': pageSize})
        for userRecord in response.findall('{0}user'.format(ns)):
            u = VSUser(*args,**kwargs)
            u.populateFromXML(userRecord)
            yield u