from .vidispine_api import VSApi
import logging

logger = logging.getLogger('vidispine.vs_notifications')


class NotificationBase(object):
    """
    Base class with common functionality for notification actions.
    """
    xmlns = "{http://xml.vidispine.com/schema/vidispine}"

    def __init__(self, xmldoc):
        self.dataContent = xmldoc

    def new(self, parent = None):
        """
        Initialises a new notification document
        :return: self
        """
        from xml.etree.cElementTree import Element
        if parent is None:
            self.dataContent = Element("ns0:action")
        else:
            self.dataContent = parent
        return self

    def _safe_get_nodecontent(self, xpath, default=""):
        """
        Returns the content of the node identified by xpath, or the value identified by default= if it cannot be found
        """
        node = self.dataContent.find(xpath)
        if node is not None:
            return node.text
        return default

    def _safe_set_nodecontent(self, xpath, newval, parent=None):
        """
        Sets the value of the node identified by xpath to newval, or if the parent= parameter is set to an ElementTree
        node will attempt to create it if it does not already exist.
        """
        from xml.etree.cElementTree import SubElement
        if parent is None:
            parent = self.dataContent
        if not isinstance(newval,str):
            newval = str(newval)

        node = self.dataContent.find(xpath)
        if node is not None:
            node.text = newval
        else:
            if parent is None:
                raise KeyError("Node {xp} is not found and no parent node specified to create".format(xp=xpath))
            node = SubElement(parent,xpath)
            node.text = newval


class HttpNotification(NotificationBase):
    """
    This class represents an HTTP notification action in Vidispine, expressing the various xml parameters as object
    properties
    """
    def __init__(self,*args,**kwargs):
        super(HttpNotification,self).__init__(*args,**kwargs)
        self.type = 'http'
        
    @property
    def synchronous(self):
        val = self.dataContent.attrib['synchronous']
        if val=='true':
            return True
        else:
            return False

    @synchronous.setter
    def synchronous(self, newval):
        if not isinstance(newval,bool):
            raise ValueError("Value for .synchronous must be boolean")
        if newval:
            self.dataContent.attrib['synchronous'] = "true"
        else:
            self.dataContent.attrib['synchronous'] = "false"

    @property
    def retry(self):
        return int(self._safe_get_nodecontent('{0}retry'.format(self.xmlns), default="-1"))

    @retry.setter
    def retry(self, newval):
        if not isinstance(newval,int):
            raise ValueError("Value for .retry must be integer")
        self._safe_set_nodecontent('{0}retry'.format(self.xmlns),str(newval))

    @property
    def contentType(self):
        return self._safe_get_nodecontent('{0}contentType'.format(self.xmlns))

    @contentType.setter
    def contentType(self,newval):
        self._safe_set_nodecontent('{0}contentType'.format(self.xmlns), newval)

    @property
    def url(self):
        return self._safe_get_nodecontent('{0}url'.format(self.xmlns))

    @url.setter
    def url(self,newvalue):
        self._safe_set_nodecontent('{0}url'.format(self.xmlns), newvalue)

    @property
    def method(self):
        return self._safe_get_nodecontent('{0}method'.format(self.xmlns))

    @method.setter
    def method(self,newval):
        self._safe_set_nodecontent('{0}method'.format(self.xmlns),newval)
        
    @property
    def timeout(self):
        return int(self._safe_get_nodecontent('{0}timeout'.format(self.xmlns), default="-1"))

    @timeout.setter
    def timeout(self,newval):
        if not isinstance(newval,int):
            raise ValueError()
        self._safe_set_nodecontent('{0}timeout'.format(self.xmlns), str(newval))
        
    def __str__(self):
        return '{method} to {url} via {contenttype}'.format(method=self.method,
                                                            url=self.url,
                                                            contenttype=self.contentType)

    def __unicode__(self):
        return str(self).encode('UTF-8')


class VSTriggerEntry(NotificationBase):
    """
    Represents the entry for a notification trigger.
    Set the following properties then call as_xml() to get an XML fragment:
      @trigger_class - the item class to trigger on (item, metadata, collection, shape, job, etc.)
      @action - the system action to trigger on (create, modify, delete, stop, etc.)
      @filter - dictionary of filter terms.  Consult the Vidispine documentation for details of valid filtering.
      As an example, consider the documentation example <modify><field>field_a, field_b</field><language>en_*</language>;
      this would be represented as {'field': ['field_a','field_b'], 'language': 'en_*'}
    """
    known_actions = ['create','modify','delete','start','stop']

    def __init__(self,*args,**kwargs):
        """
        Initialise a new VSTriggerEntry.
        :param args:
        :param kwargs:
        :return:
        """
        super(VSTriggerEntry,self).__init__(*args,**kwargs)
        from xml.etree.cElementTree import Element
        self.dataContent = Element('trigger')
        #set these properties then call as_xml() to get a document
        self.trigger_class = None
        self.action = None
        self.filter = {}

    def as_xml_node(self):
        """
        Returns the document content as an ElementTree element
        :return: Element
        """
        from xml.etree.cElementTree import Element, SubElement
        trigger_el = Element('{0}trigger'.format(self.xmlns))
        class_el = SubElement(trigger_el, '{0}{1}'.format(self.xmlns,self.trigger_class))
        action_el = SubElement(class_el, '{0}{1}'.format(self.xmlns,self.action))
        if len(self.filter)>0:
            filter_el = SubElement(class_el, '{0}filter'.format(self.xmlns))
            for k,v in list(self.filter.items()):
                name_el = SubElement(filter_el,'{0}{1}'.format(self.xmlns,k))
                if not isinstance(v,list):
                    v = [v]
                name_el.text = ",".join(v)
        return trigger_el

    def as_xml(self):
        """
        Returns the doucment content as a UTF-8 string
        :return:
        """
        from xml.etree.cElementTree import tostring
        return tostring(self.as_xml_node(), encoding="UTF-8")


class VSNotification(VSApi):
    """
    This class represents a Vidispine notification definition
    """
    class UnknownActionType(Exception):
        """
        Raised if an action type is found that we don't support
        """
        pass

    def __init__(self,*args,**kwargs):
        super(VSNotification, self).__init__(*args, **kwargs)
        from xml.etree.cElementTree import Element
        self.name = None
        self.objectclass = None
        self.dataContent = Element('NotificationDocument', {'xmlns:ns0': self.xmlns[1:-1]})

    def populate(self, objectclass, vsid):
        """
        Populates with data from Vidispine about the given notification
        :param objectclass: Type of vidispine object we're looking at, e.g. item, collection, etc.
        :param vsid: VS ID of the notification in question. Use VSNotificationCollection to list instead
        :return: None (but populates object)
        """
        self.name = vsid
        self.objectclass = objectclass

        url = "/{cls}/notification/{vsid}".format(cls=objectclass, vsid=vsid)
        self.dataContent = self.request(url)

    def save(self):
        """
        Saves the notification.  This is done by DELETING the old one, and then saving a new one, so the name property
        will change
        :return: None
        """
        from xml.etree.cElementTree import tostring
        from .vidispine_api import VSNotFound
        from pprint import pprint
        
        try:
            self.delete()
        except VSNotFound: #if it does not exist yet or has not been set up, then ignore
            pass
            
        url = "/{cls}/notification".format(cls=self.objectclass)
        content = self.as_xml()
        response_content = self.request(url, method="POST", body=content)
        pprint(response_content)
        #FIXME: need to update the name property from the reply
        #raise StandardError("testing")

    def as_xml(self):
        from xml.etree.cElementTree import tostring
        import re
        
        #strip_attributes(self.dataContent, 'xmlns', 'xmlns:ns0')
        str = tostring(self.dataContent, encoding="UTF-8")
        str = re.sub(r'xmlns[^\s>]*','',str)
        str = re.sub(r'ns\d:','',str)
        str = re.sub(r'[^/]NotificationDocument',
                     '<NotificationDocument xmlns="{0}"'.format(self.xmlns[1:-1]),
                     str)
        
        return str

    def delete(self):
        """
        Deletes the notification in question
        :return: None
        """
        if self.name is None:
            return
            
        url = "/{cls}/notification/{vsid}".format(cls=self.objectclass, vsid=self.name)
        self.request(url, method="DELETE")

    def __unicode__(self):
        #raise StandardError("testing")
        return 'Notification {n} to {act} on {trig}'.format(n=self.name,
        act=','.join([str(x) for x in self.actions]),trig=self.trigger)
    
    @property
    def actions(self):
        """
        Generator that yields objects for every action associated with this notification
        :return: yields HttpNotification or similar subclass
        """
        from xml.etree.cElementTree import SubElement
        action_node = self.dataContent.find('{0}action'.format(self.xmlns))
        if action_node is None:
            action_node = SubElement(self.dataContent,'{0}action'.format(self.xmlns))
            #FIXME: shouldn't be hardcoded!
            type_node = SubElement(action_node,'{0}http'.format(self.xmlns), {'synchronous': 'false'})
            yield HttpNotification(type_node)
        else:
            for n in action_node:
                if n.tag == "{0}http".format(self.xmlns):
                    yield HttpNotification(n)
                else:
                    raise self.UnknownActionType(n.tag)

    def add_action(self, act):
        """
        Adds an action to the notification.
        :param act: Action to add.  This should be a NotificationBase subclass, e.g. HttpNotification
        :return:
        """
        from xml.etree.cElementTree import SubElement
        if not isinstance(act,NotificationBase):
            raise TypeError("add_action must be given a notification action")

#         action_node = self.dataContent.find('{0}action'.format(self.xmlns))
#         if action_node is None:
#             action_node = SubElement(self.dataContent,'{0}action'.format(self.xmlns))
        #for subnode in act.dataContent
        #action_node.append(act.dataContent)
        self.dataContent.append(act.dataContent)
        return self

    @property
    def trigger(self):
        """
        Returns a dictionary representing the trigger
        """
        import re
        nsstrip = re.compile(r'^\{.*\}(.*)$')

        rtn = {}
        for n in self.dataContent.find('{0}trigger'.format(self.xmlns)):
            real_name = nsstrip.match(n.tag)
            rtn[real_name.group(1)] = []
            for ev in n:
                event_name = nsstrip.match(ev.tag)
                rtn[real_name.group(1)].append(event_name.group(1))
        return rtn

    @trigger.setter
    def trigger(self,newval):
        """
        Sets a new trigger value
        :param newval: Populated VSTriggerEntry representing the trigger value
        """
        from xml.etree.cElementTree import SubElement
        if not isinstance(newval,VSTriggerEntry):
            raise ValueError("trigger must be a VSTriggerEntry")

        #node = self.dataContent.find('{0}trigger'.format(self.xmlns))
        #if node is None:
        #    node = SubElement(self.dataContent, '{0}trigger'.format(self.xmlns))
        node = newval.as_xml_node()
        try:
          del node.attrib['xmlns']
        except KeyError:
          pass
        try:
          del node.attrib['xmlns:ns0']
        except KeyError:
          pass          
        self.dataContent.append(node)


class VSNotificationCollection(VSApi):
    """
    This class allows search and enumeration of Vidispine notifications
    """
    def __init__(self, objectclass="item", *args, **kwargs):
        super(VSNotificationCollection, self).__init__(*args,**kwargs)
        self.objectclass=objectclass

    def populate(self):
        """
        duplicate old incorrect behaviour for compatibility
        """
        for i in self.notifications():
            yield i
            
    def notifications(self, objectclass=None):
        import re
        if objectclass is None:
            objectclass = self.objectclass

        url = "/{cls}/notification".format(cls=objectclass)
        self.dataContent = self.request(url)

        xtractor = re.compile(r'\/(\w{2}-\d+)$')
        for node in self.dataContent.findall('{0}uri'.format(self.xmlns)):
            parts = xtractor.search(node.text)
            logger.debug("found notification {0}".format(parts.group(1)))
            n=VSNotification(self.host,self.port,self.user,self.passwd)
            n.populate(self.objectclass, parts.group(1))
            yield n