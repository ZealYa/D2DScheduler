class WiFiInformation(object):
    def __init__(self, networkName, passphrase, channelIndex):
        super().__init__()
        self.networkName  = networkName
        self.passphrase   = passphrase
        self.channelIndex = channelIndex
        
    def to_string(self):
        return 'SSID '+self.networkName+' PW '+self.passphrase+' Ch '+str(self.channelIndex)