import unittest
from gnmvidispine.vidispine_api import VSApi
from gnmvidispine.vs_item import VSItem
import io
import os.path
import logging
LOGFORMAT = '%(asctime)-15s - %(levelname)s - Thread %(thread)s - %(funcName)s: %(message)s'
logging.basicConfig(level=logging.DEBUG,format=LOGFORMAT)


class TestChunkedUpload(unittest.TestCase):
    def __init__(self,*args,**kwargs):
        super(TestChunkedUpload,self).__init__(*args,**kwargs)
        self.host="localhost"
        self.user="admin"
        self.port=8080
        self.passwd=""
        
        self.vsclient = VSApi(host=self.host,port=self.port,user=self.user,passwd=self.passwd)
        
    # def test_chunked_upload(self):
    #     filename = "testfile.mp4"
    #     testfile = io.FileIO(filename)
    #     #attempt upload in 1meg chunks
    #     self.vsclient.chunked_upload_request(testfile,os.path.getsize(filename),1024*1024,
    #                                          "/import/raw",method="POST",filename=filename)
    #
    
    def test_placeholder_upload(self):
        filename = "testfile.mp4"
        
        item=VSItem(host=self.host,port=self.port,user=self.user,passwd=self.passwd)
        item.createPlaceholder(metadata={'title': 'test import'},group='Asset')
        item.streaming_import_to_shape(filename,shape_tag='original',essence=True,thumbnails=True)
        
if __name__ == '__main__':
    unittest.main()