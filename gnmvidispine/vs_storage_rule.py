__author__ = 'Andy Gallagher <andy.gallagher@theguardian.com>'

from vidispine_api import VSApi,VSException,VSNotFound
#from vidispine.vs_storage import VSStorage
from xml.etree import ElementTree as ET
from pprint import pprint


class VSStorageRuleNew(VSApi):
    def __init__(self,*args,**kwargs):
        super(VSStorageRuleNew,self).__init__(*args,**kwargs)
        self.xmlDOM = None

    def populate_from_xml(self,xmlNode):
        self.xmlDOM = xmlNode

    def assert_populated(self):
        if self.xmlDOM is None: raise ValueError("You must call populate_from_xml before trying to read values")

    @property
    def name(self):
        self.assert_populated()
        try:
            return self.xmlDOM.attrib['id']
        except AttributeError:
            return None
        except KeyError:
            return None

    @name.setter
    def name(self, newvalue):
        pass    #this is a null opt, to allow for compatibility for initialisation in vidispine_api
    
    @property
    def storage_count(self):
        self.assert_populated()
        try:
            return int(self.xmlDOM.find('{0}storageCount'.format(self.xmlns)).text)
        except AttributeError:
            return 0
        except TypeError:
            return None

    @storage_count.setter
    def storage_count(self,value):
        self.assert_populated()
        if not isinstance(value,int): raise TypeError

        node = self.xmlDOM.find('{0}storageCount'.format(self.xmlns))
        if node is None:
            node = ET.SubElement(self.xmlDOM,'{0}storageCount'.format(self.xmlns))
        node.text = str(value)

    @property
    def applies_to(self):
        self.assert_populated()
        o_class = None
        o_id = None
        try:
            o_class = self.xmlDOM.find('{0}appliesTo/{0}type'.format(self.xmlns)).text
            o_id = self.xmlDOM.find('{0}appliesTo/{0}id'.format(self.xmlns)).text
        except AttributeError:
            pass
        return (o_class,o_id)

    @property
    def precedence(self):
        self.assert_populated()
        try:
            return self.xmlDOM.find('{0}precedence'.format(self.xmlns)).text
        except AttributeError:
            return ""
        except TypeError:
            return None

    @precedence.setter
    def precedence(self,value):
        self.assert_populated()
        if not isinstance(value,basestring): raise TypeError
        value = value.upper()

        node = self.xmlDOM.find('{0}precedence'.format(self.xmlns))
        if node is None:
            node = ET.SubElement(self.xmlDOM, '{0}precedence'.format(self.xmlns))
        node.text = value

    def _generic_get_ref(self,type,invert=False):
        self.assert_populated()
        xps = '{0}{1}'.format(self.xmlns,type)
        if invert:
            xps = "{0}not/".format(self.xmlns) + xps
        
        return map(lambda x: x.text,self.xmlDOM.findall(xps))
    
    def storages(self,inverted=False):
        return self._generic_get_ref('storage',inverted)

    def groups(self,inverted=False):
        return self._generic_get_ref('group',inverted)
    
    def as_dict(self):
        return {
            'storages': self.storages(),
            'not_storages': self.storages(inverted=True),
            'groups': self.groups(),
            'not_groups': self.groups(inverted=True),
            'name': self.name,
            'storage_count': self.storage_count,
            'applies_to': self.applies_to,
            'precedence': self.precedence,
        }
    
    def __unicode__(self):
        o_class,o_id = self.applies_to
        return u'Storage rule {n} copy to {c} storages. Applies to {t} {i}. Precedence {p}.'.format(n=self.name,
                                                                                    c=self.storage_count,
                                                                                    t=o_class,
                                                                                    i=o_id,
                                                                                    p=self.precedence)


class VSStorageRuleCollection(VSApi):
    def __init__(self,*args,**kwargs):
        super(VSStorageRuleCollection,self).__init__(*args,**kwargs)
        self.xmlDOM = None

    def assert_populated(self):
        if self.xmlDOM is None: raise ValueError("You must call populate_from_xml before trying to read values")

    def populate_from_xml(self,xmlNode):
        self.xmlDOM = xmlNode

    def rules(self):
        for basenode in self.xmlDOM.findall('{0}tag'.format(self.xmlns)):
            rule = VSStorageRuleNew(self.host,self.port,self.user,self.passwd)
            rule.populate_from_xml(basenode)
            yield rule

    def add(self, newrule):
        if not isinstance(newrule,VSStorageRuleNew): raise TypeError("add() accepts only a VSStorageRuleNew object")
        newrule.assert_populated()


class VSStorageRule(VSApi):
    def __init__(self, *args,**kwargs):
        super(VSStorageRule, self).__init__(*args,**kwargs)
        self.content = {}

    def _parseContent(self,node,parentKey='include',rtn={}):
        if not parentKey in rtn:
            rtn[parentKey]={}

        rtn[parentKey]['storages']=[]
        rtn[parentKey]['groups']=[]

        for child in node:
            if child.tag.endswith('storage'):
                rtn[parentKey]['storages'].append(child.text)
            elif child.tag.endswith('group'):
                rtn[parentKey]['groups'].append(child.text)
            elif child.tag.endswith('not'):
                self._parseContent(child,parentKey='exclude',rtn=rtn)
            elif child.tag.endswith('storageCount'):
                rtn[parentKey]['storageCount']=int(child.text)
            elif child.tag.endswith('precedence'):
                rtn['precedence']=child.text
            elif child.tag.endswith('priority'):
                rtn['priority']=child.text
            elif child.tag.endswith('appliesTo'):
                pass
            else:
                print "warning: unrecognised tag in storage rule definition: %s" % child.tag
        return rtn

    def populateFromXml(self,response):
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        self.dataContent = response

        for tagNode in response.findall("{0}tag".format(ns)):
            tagName = tagNode.attrib['id']

            ruleContent = self._parseContent(tagNode)
            self.content[tagName] = ruleContent

    def toXml(self):
        return ET.tostring(self.dataContent, encoding="UTF-8")

    def isEmpty(self):
        if self.content == {}:
            return True
        return False

    def dump(self):
        pprint(self.content)