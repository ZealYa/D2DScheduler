import json

from Tag import Tag
from Content import Content
from WiFiInformation import WiFiInformation
from ScheduleEntry import ScheduleEntry

from uniflex.core import events

class TestEvent(events.EventBase):

    def __init__(self):
        super().__init__()
        self.time = 0
            
    def serialize(self):
        return {"time": self.time}

    @classmethod
    def parse(cls, buf):
        time = buf.get("time", None)
        return cls(time)

class CommandEvent(events.EventBase):

    def __init__(self):
        super().__init__()
        self.time = 0

    def serialize(self):
        return {"time": self.time}
        

class WiFiJoinNetworkCommandEvent(CommandEvent):
    
    def __init__(self, wifiInformation):
        super().__init__()
        self.wifiInformation = wifiInformation
        self.time            = 0
    
    #def __init__(self, wifiInformation, time):
    #    super().__init__()
    #    self.wifiInformation = wifiInformation
    #    self.time            = time

    def serialize(self):
        return {"time": self.time, "networkName": self.wifiInformation.networkName, "passphrase": self.wifiInformation.passphrase, "channelIndex": self.wifiInformation.channelIndex}

class WiFiLeaveNetworkCommandEvent(CommandEvent):
    
    def __init__(self):
        super().__init__()
        self.time = 0
        
    #def __init__(self, time):
    #    super().__init__()
    #    self.time = time
        
    def serialize(self):
        return {"time": self.time}

        
class WiFiStartNetworkCommandEvent(CommandEvent):
    
    def __init__(self, wifiInformation):
        super().__init__()
        self.wifiInformation = wifiInformation
        self.time            = 0
    
    #def __init__(self, wifiInformation, time):
    #   super().__init__()
    #   self.wifiInformation = wifiInformation
    #   self.time            = time

    def serialize(self):
        return {"time": self.time, "networkName": self.wifiInformation.networkName, "passphrase": self.wifiInformation.passphrase, "channelIndex": self.wifiInformation.channelIndex}

class WiFiStopNetworkCommandEvent(CommandEvent):
    
    def __init__(self):
        super().__init__()
        self.time = 0

    def serialize(self):
        return {"time": self.time}

class D2DExchangeContentCommandEvent(CommandEvent):
    
    def __init__(self, exchangeList):
        super().__init__()
        self.exchangeList = exchangeList

    def serialize(self):

        arrayList = []
        for entry in self.exchangeList:
            subDict = {}
            subDict['destDeviceId'] = entry.consumer.uuid
            subDict['contentId'] = entry.content.id
            subDict['time'] = str(entry.startTime)
            arrayList.append(subDict)
            
        print(arrayList)
        return {"scheduleList": arrayList, "time": "0"}

class D2DInfoRequestCommandEvent(CommandEvent):        
    def __init__(self):
        super().__init__()
        self.time = 0

    def serialize(self):
        return {"time": self.time}
        
class D2DAddInterestNotificationEvent(events.EventBase):
    
    #def __init__(self):
    #    super().__init__()
    #    self.deltaUpdate = False
    #    self.srcDevUUID = ''
    #    self.interestList = []
        
    def __init__(self, srcDevUUID, deltaUpdate, interestList):
        super().__init__()
        self.srcDevUUID     = srcDevUUID
        self.deltaUpdate    = deltaUpdate
        self.interestList   = interestList

    # will not be serialized...
    def serialize(self):
        return {}

    @classmethod
    def parse(cls, buf):
        buf = str(buf)
        buf = buf.replace("'", '"')    
        
        data  = json.loads(buf)   
        srcDevUUID  = data['srcDevUUID']
        deltaUpdate = data['deltaUpdate']
        
        tagListJSON = data['tagList']
        tagList = []
        for tag in tagListJSON:
            tagList.append(tag)

        return cls(srcDevUUID, deltaUpdate, tagList)
        
class D2DRemoveInterestNotificationEvent(events.EventBase):
    
    #def __init__(self):
    #   super().__init__()
    #    self.srcDevUUID = ''
    #    self.interestList = []
         
    def __init__(self, srcDevUUID, deltaUpdate, interestList):
        super().__init__()   
        self.srcDevUUID = srcDevUUID
        self.deltaUpdate    = deltaUpdate
        self.interestList = interestList

    # will not be serialized...
    def serialize(self):
        return {}

    @classmethod
    def parse(cls, buf):
        buf = str(buf)
        buf = buf.replace("'", '"') 
        
        data  = json.loads(buf)   
        srcDevUUID  = data['srcDevUUID']
        deltaUpdate = data['deltaUpdate']
        
        tagListJSON = data['tagList']
        tagList = []
        for tag in tagListJSON:
            tagList.append(tag)

        return cls(srcDevUUID, deltaUpdate, tagList)
        
class D2DAddContentNotificationEvent(events.EventBase):
    
    #def __init__(self):
    #    super().__init__()
    #    self.srcDevUUID = ''
    #    self.contentList = []
        
    def __init__(self, srcDevUUID, deltaUpdate, contentList):
        super().__init__()
        self.srcDevUUID  = srcDevUUID
        self.deltaUpdate = deltaUpdate
        self.contentList = contentList
    
    # will not be serialized...
    def serialize(self):
        return {}

    @classmethod
    def parse(cls, buf):
        buf = str(buf)
        buf = buf.replace("'", '"') 
        
        data  = json.loads(buf)   
        srcDevUUID  = data['srcDevUUID']
        deltaUpdate = data['deltaUpdate']
        
        contentListJSON = data['contentList']
        contentList = []
        for c in contentListJSON:
           
            contentId   = c['contentId']
            size        = c['size']
    
            tagListJSON = c['tagList']
            tagList = []
            for t in tagListJSON:
                newTag = Tag(t['name'], t['quality']) 
                tagList.append(newTag)
                    
            newContent = Content(contentId, size)
            newContent.tagList = tagList
            contentList.append(newContent)
            
        return cls(srcDevUUID, deltaUpdate, contentList)
        
class D2DRemoveContentNotificationEvent(events.EventBase):
    
    #def __init__(self):
    #    super().__init__()
    #    self.srcDevUUID = ''
    #    self.contentIdList = []
   
    def __init__(self, srcDevUUID, deltaUpdate, contentIdList):
        super().__init__()
        self.srcDevUUID     = srcDevUUID
        self.deltaUpdate    = deltaUpdate
        self.contentIdList  = contentIdList

    # will not be serialized...
    def serialize(self):
        return {}

    @classmethod
    def parse(cls, buf):
        buf = str(buf)
        buf = buf.replace("'", '"') 
        
        data  = json.loads(buf)   
        srcDevUUID  = data['srcDevUUID']
        deltaUpdate = data['deltaUpdate']
        
        contentListJSON = data['contentIdList']
        contentIdList = []
        for cId in contentListJSON:
            contentIdList.append(cId)

        return cls(srcDevUUID, deltaUpdate, contentIdList)