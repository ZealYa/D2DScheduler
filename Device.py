from Tag import Tag
from Content import Content
from WiFiInformation import WiFiInformation    
from PrintHelper import PrintHelper 
 
class Device(object):
    
    WIFI_MODE_ANY    = "WIFI_MODE_ANY"
    WIFI_MODE_NONE   = "WIFI_MODE_NONE"
    WIFI_MODE_AP     = "WIFI_MODE_AP"
    WIFI_MODE_CLIENT = "WIFI_MODE_CLIENT"
    
    def __init__(self, uuid):
        super().__init__()
        
        self.uuid = uuid
        self.isWishFulConfirmed = False
        
        # list of tags
        self.interestList   = []
        self.contentList    = []
        
        
        # WiFi Mode of the device
        self.wifiMode = self.WIFI_MODE_NONE
        # Wifi Information object required to setup / join a network
        self.wifiInformation = None
        # if the device is in AP mode, the list of assigned clients is store here (currently not used)
        self.clientList = []
        # if device is in CLIENT mode, the device AP is stored here
        self.deviceAP = None
        
        # priority counter used in the scheduling
        # increased each time a device interested in available content cannot be scheduled
        # devices may not be scheduled due to 
        # -- topology (e.g. only neighbor is already client to an AP)
        # -- full superframe, no time left to schedule exchange
        self.idleCounter = 0
        
        # if the device is provider of content the corresponding schedule entries are stored
        # used for sending a list of exchange in D2DExchangeContentCommandEvent
        self.providingExchangeList = []
        self.d2dExchangeCommandSent = False
        
        # used for idle increase check
        self.consumingExchangeList = []
        
          # if set to true, the wifiMode is not be allowed to change in the ongoing schedule round
        wifiModeLocked = False
        
        # List of commands that have to be transmitted to the devices after schedule is generated
        # (e.g. startnetwork, exchangeContent...)
        self.commandList = []
  
        # list on schedule content to be exchanged in the ongoing schedule generation
        # used to store the scheduled content to prevent obtaining identical content from multiple providers
        self.consumerScheduledContentList = []
  
        # if there is interested content in the neighborhood, however exchange may not be possible
        self.interestedContentAvailable = False
        
        #if multiple wifi commands have to be executed, the start time for the next command is stored
        # e.g. stop a network and join another
        self.nextCommandStartTime = 0
        
        
    def __eq__(self, other):
        return self.uuid == other.uuid
    
    def add_interest(self, tag):   
        if tag not in self.interestList:
            print("\tadd interest \""+tag+"\" to device "+ self.uuid)
            self.interestList.append(tag)
         
    def remove_interest(self, tag):      
        if tag in self.interestList:
            print("\tremove interest \""+tag+"\" from device "+ self.uuid)
            self.interestList.remove(tag)
            
    def add_content(self, content):    
        for c in self.contentList:
            if c.id == content.id:
                # we overwrite all meta data
                c.size = content.size
                c.tagList = content.tagList
                return
   
        print("\tadd content ",content.to_string(), "to device", self.uuid)
        self.contentList.append(content)
    
    def remove_content(self, contentId):    
        for content in self.contentList:
            if content.id == contentId:
                print("\tremove content ",content.to_string(), "from device", self.uuid)
                self.contentList.remove(content)
                return             
  
    # AP functionality may be dependent 
    # - on the hardware of a device 
    # - on the software (e.g. Android7 problem)
    # - on device parameters (e.g. battery level)
    def is_capable_AP(self):
        if "Android7" in self.uuid:
            return False
        return True
  
    def print(self, indent):
        apID = "None"
        if self.deviceAP is not None:
            apID = self.deviceAP.uuid
        PrintHelper.print("ID "+self.uuid+" <> wifiMode "+self.wifiMode+" <> AP "+apID+" <> idleCounter "+str(self.idleCounter), indent)
        intList = "["
        for interest in self.interestList:
            if len(intList) > 1:
                intList += ", "
            intList += "\""+interest+"\""
        intList += "]"
        
        PrintHelper.print("interestList: " + intList, indent + 1)
        PrintHelper.print("contentList : ", indent + 1)
        for content in self.contentList:
            content.print(indent+2)