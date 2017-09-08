class Tag(object):
    def __init__(self, n, q):
        super().__init__()
        self.name = n
        self.quality = q
        
    def to_string(self):
        return "\""+self.name+"\"-"+str(self.quality)
        
        