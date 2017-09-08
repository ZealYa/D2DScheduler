from Tag import Tag       

from Config import Config
from PrintHelper import PrintHelper 
       
class Content(object):


    def __init__(self, id, size):
        super().__init__()
        self.tagList = []
        self.id = id
        self.size = size
    
    def __eq__(self, other):
        return self.id == other.id    
        
    def add_tag(self, n, q):
        tag = Tag(n,q)
        self.tagList.append(tag)
        
    def add_tag_list(self, list):
        self.tagList.extend(list)
     
    def to_string(self):
        
        id = self.id
        if Config.PRINT_CONTENT_ID_CHAR_LIMIT > 0:
            id = id[:Config.PRINT_CONTENT_ID_CHAR_LIMIT]+"..."
            
        out = "ID "+id+" size "+str(self.size)+" tagList "
        tagList = "["
        for tag in self.tagList:
            if len(tagList) > 1:
                tagList += ", "
            tagList += tag.to_string()
        tagList += "]"
        
        out += tagList
        return out 
         
    def print(self, indent):
        PrintHelper.print(self.to_string(), indent)