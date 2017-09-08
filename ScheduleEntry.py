from Device import Device 
from Content import Content

class ScheduleEntry(object):
    def __init__(self, provider, consumer, content, startTime, endTime):
        super().__init__()
        self.provider   = provider
        self.consumer   = consumer
        self.content    = content
        self.startTime  = startTime
        self.endTime    = endTime
        
    def to_string(self):
        consumerAP = self.consumer.deviceAP
        if (consumerAP is not None):
            consumerAP = consumerAP.uuid
        providerAP = self.provider.deviceAP
        if (providerAP is not None):
            providerAP = providerAP.uuid

        resultString = self.provider.uuid+ " ("+self.provider.wifiMode+" AP "+str(providerAP)+")";
        resultString += " -> "+self.consumer.uuid+" ("+self.consumer.wifiMode+" AP "+str(consumerAP)+") : "+self.content.id+" time "+str(self.startTime)
        return resultString
        