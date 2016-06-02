from vidispine_api import HTTPError,VSApi,VSException,VSNotFound
import string

configheader="""<ConfigurationPropertyDocument xmlns="http://xml.vidispine.com/schema/vidispine">
    """
configbody="""<key>{{ keyname }}</key>
    <value>{{ value }}</value>
    """
configfooter="""</ConfigurationPropertyDocument>"""

class VSConfiguration(VSApi):
    def get(self,key):
        try:
            dataContent=self.request('/configuration/properties/%s' % key,method="GET")
        except HTTPError as e:
                raise VSNotFound("Configuration property %s was not found in the system" % key)
        
        #print dataContent
        #print dataContent.tag, dataContent.attrib
        
        namespace="{http://xml.vidispine.com/schema/vidispine}"
        
        el=dataContent.find('ExceptionDocument')
        if el is not None:
            errors=""
            for child in el:
                errorstring="%s %s: %s" % ( child.find('type'), child.find('id'), child.tag)
                errors=errors+errorstring
            raise VSException(errors)
    
    #el=dataContent.find('{0}ConfigurationPropertyDocument'.format(namespace))
    #   if not el:
    #       return "root node not found"
        el=dataContent.find('{0}value'.format(namespace))
        #print el
        if el is None:
            raise VSNotFound("value node not found")

        return el.text

    def set(self,values):
        if not isinstance(values,dict):
            raise TypeError("You need to pass a dictionary to VSConfiguration::set")
    
        myconfig=configheader
        for key,value in values.iteritems():
            element=string.replace(configbody,'{{ keyname }}',key)
            element=string.replace(element,'{{ value }}',value)
            myconfig+=element
        myconfig+=configfooter
        
        print myconfig
    
        return

