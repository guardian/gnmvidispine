from vidispine_api import VSApi
import re
from pprint import pprint

class URLError(StandardError):
    pass


class VSThumbnailCollection(VSApi):
    def __init__(self,*args,**kwargs):
        super(VSThumbnailCollection,self).__init__(*args,**kwargs)

        self._resource_list = []
        self.thumbnail_urls = []
        self.parent_item = None

    def populate(self, item):
        url = "/item/{0}/thumbnailresource".format(item.name)

        self.parent_item = item

        self.dataContent = self.request(url)
        for node in self.dataContent.findall('{0}uri'.format(self.xmlns)):
            self._resource_list.append(node.text)

        print "DEBUG: got resource list {0}".format(self._resource_list)
        self.thumbnail_urls = []

    @staticmethod
    def _abs_to_relative_url(url):
        """
        chops off the fist part of the url
        :param url:
        :return:
        """
        url_removers = [
            re.compile(r'^\w+://[\w\d\-\.:]+/API'),
            re.compile(r'^\w+://[\w\d\-\.:]+/')
            ]
        for rm in url_removers:
            new_url = re.sub(rm,'',url)
            if new_url is not None and new_url != url:
                return new_url

        raise URLError("{0} does not look like an absolute Vidispine API URL".format(url))

    def count(self):
        """
        Returns the total number of thumbnails associated with this resource
        :return: integer
        """
        n = 0
        if len(self.thumbnail_urls)>0:
            return len(self.thumbnail_urls)

        #pprint(self._resource_list)
        for uri in self._resource_list:
            baseurl = self._abs_to_relative_url(uri)
            #print "DEBUG: connecting to {0}".format(self._abs_to_relative_url(uri))
            content = self.request(baseurl)

            for node in content.findall('{0}uri'.format(self.xmlns)):
                #print "got {0}".format(node.text)
                self.thumbnail_urls.append(baseurl + '/' + node.text)

        return len(self.thumbnail_urls)

    def refresh(self):
        """
        Reloads relevant data from the server
        :return: None
        """
        if self.parent_item is None:
            return
        self.populate(self.parent_item)

    def regenerate(self, shape_tag='original', priority='MEDIUM'):
        """
        Requests the server to regenerate thumbnails, using the given shape_tag as a source
        :param shape_tag: shape to use as a source. Will raise VSNotFound if this does not exist on the item.  Optionally,
        specify a list to try multiple tags. No validation will be performed, and the server will default to 'original'
        if none of the specified shape tags can be found.
        :param priority: job priority for the thumbnailing job
        :return: VSJob object
        """
        from vs_job import VSJob
        if self.parent_item is None:
            raise ValueError("You need to populate a thumbnail collection from a valid item before regenerating")

        #will raise VSNotFound if the shape does not exist
        if isinstance(shape_tag,list):
            shape_tag_list = ",".join(shape_tag)
        else:
            shape = self.parent_item.get_shape(shape_tag)
            shape_tag_list = shape_tag

        url = "/item/{i}/thumbnail".format(i=self.parent_item.name)
        response = self.request(url,method="POST",query={
            'createThumbnails': 'true',
            'priority': priority,
            'sourceTag': shape_tag_list
        })
        j = VSJob(self.host,self.port,self.user,self.passwd)
        j.fromResponse(response)
        return j