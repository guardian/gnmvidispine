from vidispine_api import VSApi,VSException,VSNotFound
from vs_field import VSField
import xml.etree.ElementTree as ET


class VSMDGroup(VSApi):
    def __init__(self,*args,**kwargs):
        super(VSMDGroup, self).__init__(*args,**kwargs)
        self.dataContent=None
        self.name=""
        self.portalData={}
        self.fields=[]

    def populate(self,groupname):
        self._populate_from_node(self.request('/metadata-field/field-group/%s' % groupname))

    def _populate_from_node(self, xmlnode, quick=False):
        self.dataContent = xmlnode

        self.name = self.dataContent.find('{0}name'.format(self.xmlns)).text

        self.portalData=self.findPortalData(self.dataContent.find('{0}data'.format(self.xmlns)),ns=self.xmlns)

        if not quick and self.portalData:
            for fieldname in self.portalData['field_order']:
                try:
                    newfield=VSField(self.host,self.port,self.user,self.passwd)
                    newfield.debug = True
                    newfield.populate(fieldname.replace(' ','%20'))
                    self.fields.append(newfield)
                except VSNotFound as e:
                    print "Warning: %s was not found as a field (might be a sub-group)" % fieldname

    def has_field(self, fieldname):
        if fieldname in self.portalData['field_order']: return True
        return False

    def add_field(self, fieldname):
        """
        Adds the given field ID to the group.  If the field is already present does nothing. Raises VSNotFound if the field
        does not exist.
        :param fieldname: Vidispine field ID to add
        :return: self
        """
        self.request("/metadata-field/field-group/{0}/{1}".format(self.name,fieldname),method="PUT")
        return self

    def remove_field(self, fieldname):
        """
        Removes the given field ID from the group.  Raises VSNotFound if the field is not already in the group.
        :param fieldname: Vidispine field ID to remove
        :return: self
        """
        self.request("/metadata-field/field-group/{0}/{1}".format(self.name, fieldname), method="DELETE")
        return self

    def add_subgroup(self, groupname):
        """
        Adds the given group to this group as a subgroup
        :param groupname: group name to add
        :return: self
        """
        self.request("/metadata-field/field-group/{0}/group/{1}".format(self.name, groupname), method="PUT")
        return self

    def remove_subgroup(self, groupname):
        """
        Removes the given group from this group as a subgroup. Raises VSNotFound if the group is not a subgroup of this one.
        :param groupname: group name to add
        :return: self
        """
        self.request("/metadata-field/field-group/{0}/group/{1}".format(self.name, groupname), method="DELETE")
        return self

    def subgroups(self, quick=False):
        for node in self.dataContent.findall('{0}group'.format(self.xmlns)):
            #try:
                #name = node.find('{0}name'.format(self.xmlns)).text
                new_mdgroup = VSMDGroup(self.host,self.port,self.user,self.passwd)
                new_mdgroup._populate_from_node(node,quick=quick)
                yield new_mdgroup

    def subgroup_for_field(self,fieldname):
        for g in self.subgroups(quick=True):
            if g.has_field(fieldname):
                return g

    #changes the field name in the field_order spec and updates the xml
    def updateFieldOrder(self,currentname,newname):
        i=0
        for name in self.portalData['field_order']:
            if(name==currentname):
                self.portalData['field_order'][i]=newname
            i+=1

        namespace = "{http://xml.vidispine.com/schema/vidispine}"
        self.updatePortalData(self.dataContent.find('{0}data'.format(namespace)))

    def findInternalFieldDef(self,name):
        for node in self.dataContent: #.find('{0}field'.format(self.namespace)):
            if(node.tag.endswith('field')):
                namenode=node.find('{0}name'.format(self.xmlns))

                if namenode.text==name:
                    print "%s" % node.text
                    return node

        return None

    def updateInternalFieldDef(self,currentname,newname):
        fd=self.findInternalFieldDef(currentname)

        if fd==None:
            raise VSNotFound("Field '%s' does not appear to exist in metadata group %s",currentname,self.name)

        fd.find('{0}name'.format(self.xmlns)).text=newname
        schemanode=fd.find('{0}schema'.format(self.xmlns))
        schemanode.set('name', newname)

    #this method replaces the given field with a new one with the given name, but everything else identical.as
    #WARNING: this will DELETE the old field!
    def replace_field(self,currentname,newname,dry_run=False):
        target_field=None
        for f in self.fields:
            if(f.name==currentname):
                target_field=f
                break

        if(target_field==None):
            msg="Field %s does not exist in this metadata group" % currentname
            raise VSNotFound(msg)
            #try:

        if not dry_run:
            target_field.delete()

        target_field.name = newname

        self.updateInternalFieldDef(currentname,newname)
        if not dry_run:
            target_field.commitXML()
        self.updateFieldOrder(currentname,newname)
        if not dry_run:
            self.commitXML()
            #except Exception as e:

    def commitXML(self):
        self.request("/metadata-field/field-group/%s" % self.name,method="PUT",body=ET.tostring(self.dataContent))

    def dump_text(self, *fields):
        print "Metadata Group:"
        print "\tName: %s" % (self.name)

    #    for f in fields:
    #        print "\t%s: %s" % (f, self.contentDict[f])

        print "\tPortal data:\n"
        for f, v in self.portalData.items():
            print "\t%s: %s" % (f, v)

        print "\tField count: %d" % self.fields.__len__()
