import logging
import random
import json
import re
import time
import sys

from time import gmtime, strftime

from uniflex.core import modules
from uniflex.core import events
from uniflex.core.timer import TimerEventSender
from common import CommandEvent
from common import WiFiJoinNetworkCommandEvent
from common import WiFiLeaveNetworkCommandEvent
from common import WiFiStartNetworkCommandEvent
from common import WiFiStopNetworkCommandEvent
from common import TestEvent
from common import D2DInfoRequestCommandEvent
from common import D2DAddInterestNotificationEvent
from common import D2DRemoveInterestNotificationEvent
from common import D2DAddContentNotificationEvent
from common import D2DRemoveContentNotificationEvent
from common import D2DExchangeContentCommandEvent

from Tag import Tag
from Content import Content
from Config import Config
from Device import Device
from ScheduleEntry import ScheduleEntry
from WiFiInformation import WiFiInformation
from TestEntry import TestEntry
from PrintHelper import PrintHelper
    
    
class PeriodicSchedulerTimeEvent(events.TimeEvent):
    def __init__(self):
        super().__init__()

class PeriodicDisplayTimeEvent(events.TimeEvent):
    def __init__(self):
        super().__init__()     

class TestTimeEvent(events.TimeEvent):
    def __init__(self):
        super().__init__()           
        
class D2DController(modules.ControlApplication):

    # number of rounds for a consumers in which not exchange is scheduled even though suitable content would be available
    # if threshold is reached, other networks are modified/ disbandoned to enable exchange with consumer
    idleThreshold = 1
    
    defaultChannelList = list(range(1,12,1)) 

    def __init__(self, mode):
        super(D2DController, self).__init__()
        self.log = logging.getLogger('D2DController')
        self.mode           = mode
        self.running        = False
        
        PrintHelper.print("Seed "+str(Config.SEED))
        random.seed(Config.SEED)
        
        self.debugSchedule  = True
        self.isSimulation   = False
                 
        self.displayInterval = 10
        self.displayTimer = TimerEventSender(self, PeriodicDisplayTimeEvent)
        self.displayTimer.start(self.displayInterval)
        
        self.cmdTransmitted = False
        self.testTimer = TimerEventSender(self, TestTimeEvent)

        self.scheduleTimer = TimerEventSender(self, PeriodicSchedulerTimeEvent)
        self.scheduleList = []
        
        self.availableChannels = list(D2DController.defaultChannelList)
            
        # list of known devices
        self.deviceList = []
        
        self.testList = []
        
        self.test()
              
        PrintHelper.print("Init D2DController")
        
    def test(self):
        PrintHelper.print("testing.......")
        self.print_devices()
        
        #self.test_add_remove()
        
        #self.test_schedule()
        #self.test_schedule_rnd() 
    
        #self.test_schedule_diversity()
        
     
    def test_client_to_client(self):
        dev_client1 = self.add_device('client1')
        dev_client2 = self.add_device('client2')
        dev_ap = self.add_device('ap')
        
        # add content to AP and interest to client1
        c = Content('birdContent', 1e6)
        c.add_tag('bird', 1.0)
        self.testList.append(TestEntry(TestEntry.ACTION_ADD_CONTENT, dev_ap, c, 0))      
        self.testList.append(TestEntry(TestEntry.ACTION_ADD_INTEREST, dev_client1, 'bird', 0))
        
        c = Content('catContent', 1e6)
        c.add_tag('cat', 1.0)
        self.testList.append(TestEntry(TestEntry.ACTION_ADD_CONTENT, dev_client1, c, 2))   
       
        self.testList.append(TestEntry(TestEntry.ACTION_ADD_INTEREST, dev_client2, 'cat', 2))
        
        self.run_schedule() 
     
    def test_schedule(self):
     
        devProv1 = self.add_device('devProv1')
        catCont = Content('catCont', 1e6)
        catCont.add_tag('cat', 1.0)
        catCont.add_tag('other', 0.01)
        self.testList.append(TestEntry(TestEntry.ACTION_ADD_CONTENT, devProv1, catCont, 0))    
        self.testList.append(TestEntry(TestEntry.ACTION_ADD_INTEREST, devProv1, 'bird', 0))    
                
        devCon1 = self.add_device('devCon1')
        self.testList.append(TestEntry(TestEntry.ACTION_ADD_INTEREST, devCon1, 'cat', 0))
        self.testList.append(TestEntry(TestEntry.ACTION_ADD_INTEREST, devCon1, 'bird', 0))
        self.testList.append(TestEntry(TestEntry.ACTION_ADD_INTEREST, devCon1, 'dog', 0))

        devCon2 = self.add_device('devCon2')
        self.testList.append(TestEntry(TestEntry.ACTION_ADD_INTEREST, devCon2, 'cat', 0))
        
        devProv2 = self.add_device('devProv2')
        birdCont = Content('birdCont', 1e6)
        birdCont.add_tag('bird', 1.0)
        self.testList.append(TestEntry(TestEntry.ACTION_ADD_CONTENT, devProv2, birdCont, 0))    
        self.testList.append(TestEntry(TestEntry.ACTION_ADD_INTEREST, devProv2, 'bird', 0))   
        
        self.run_schedule() 

    def test_schedule_diversity(self):
        dev_consumerBird = self.add_device('consumerBird')
        self.testList.append(TestEntry(TestEntry.ACTION_ADD_INTEREST, dev_consumerBird, 'bird', 0))
        
        dev_providerBird = self.add_device('providerBird')
        c = Content('birdContent', 1e6)
        c.add_tag('bird', 1.0)
        self.testList.append(TestEntry(TestEntry.ACTION_ADD_CONTENT, dev_providerBird, c, 0))    
      
        # second network
        dev_consumerCat = self.add_device('consumerCat')
        self.testList.append(TestEntry(TestEntry.ACTION_ADD_INTEREST, dev_consumerCat, 'cat', 0))

        dev_providerCat = self.add_device('providerCat')
        c = Content('catContent', 1e6)
        c.add_tag('cat', 1.0)
        self.testList.append(TestEntry(TestEntry.ACTION_ADD_CONTENT, dev_providerCat, c, 0))   
             
        testCase = 2
        # test reconfiguring
        if testCase == 1:
            # in the second round, add interest for bird, client has to join the other network
            self.testList.append(TestEntry(TestEntry.ACTION_ADD_INTEREST, dev_consumerCat, 'bird', 1))
        
        elif testCase == 2:
            # test reconfiguring an ap
            c = Content('dogContent', 1e6)
            c.add_tag('dog', 1.0)
            self.testList.append(TestEntry(TestEntry.ACTION_ADD_CONTENT, dev_providerCat, c, 0))   
            self.testList.append(TestEntry(TestEntry.ACTION_ADD_INTEREST, dev_providerBird, 'dog', 1))
        
            self.testList.append(TestEntry(TestEntry.ACTION_ADD_INTEREST, dev_consumerBird, 'dog', 2 + D2DController.idleThreshold))
        
        self.print_devices() 
        self.run_schedule() 

    def test_schedule_rnd(self):        
        tagList = ['cat','dog','bird']
        
        numContent  = 5
        numDevs     = 5
              
        # create random content
        contentList = []
        for c in range(0,numContent):
            content = Content('content'+str(c), 1e6 + random.randrange(1e6))
            numInterest = random.randrange(len(tagList)-1) + 1
            tmpList = list(tagList)
            for i in range(0,numInterest):
                tag = tmpList.pop(random.randrange(len(tmpList)))        
                content.add_tag(tag,random.randrange(100)/100)
            contentList.append(content)
           
        # assign interest and content to devices
        for d in range(0,numDevs):
            
            dev = self.add_device('device'+str(d)) 
            
            numInterest = random.randrange(len(tagList))
            tmpList = list(tagList)
            for i in range(0,numInterest):
                tag = tmpList.pop(random.randrange(len(tmpList)))        
                dev.add_interest(tag)
            
            tmpList = list(contentList)
            numContent = random.randrange(len(contentList))
            for c in range(0,numContent):
                content = tmpList.pop(random.randrange(len(tmpList)))  
                dev.add_content(content)
        
        self.run_schedule()

    def test_add_remove(self):
        self.remove_device('unknownDev')
        
        d2 = self.add_device('1234')      
        d = self.add_device('123')
        self.remove_device('1234')
        d.add_interest('cat')
        d.add_interest('bird')
        d.add_interest('dog') 
        self.print_devices()
        
        d.remove_interest('duck')
        d.remove_interest('cat')
        self.print_devices()
        
        d3 = self.add_device('abc')
        c = Content('contentId', 100)
        c.add_tag('testTag', 1.0)
        c.add_tag('testTag2', 0.01)
        d.add_content(c)
   
        self.print_devices()
        
        self.remove_device('abc')
        d.remove_content(c.id)
        self.print_devices()
        
    def run_schedule(self):
        round = 0
        idleRound = 0
        
        while(True):
              
            PrintHelper.print("\nStarting round "+str(round)) 
              
            for entry in self.testList[:]:
                if entry.roundToExecute == round:
                    if entry.action == TestEntry.ACTION_ADD_INTEREST:
                        entry.device.add_interest(entry.interest)
                        
                    elif entry.action == TestEntry.ACTION_REM_INTEREST:
                        entry.device.remove_interest(entry.interest)
                    
                    elif entry.action == TestEntry.ACTION_ADD_CONTENT:
                        entry.device.add_content(entry.content)
                     
                    elif entry.action == TestEntry.ACTION_REM_CONTENT:
                        entry.device.remove_content_content(entry.content)
                        
                    else:
                        self.print_error("run_schedule() unknown action "+entry.action)
                        
                    self.testList.remove(entry)
                    
            self.print_devices() 
            self.generate_schedule(False)   

            if len(self.scheduleList) == 0 and len(self.testList) == 0:              
                if idleRound > D2DController.idleThreshold:
                    break     
                idleRound += 1                   
            else:
                idleRound = 0
            
            time.sleep(1)     
            for exchange in self.scheduleList:
                exchange.consumer.add_content(exchange.content)            
                
            self.scheduleList = []
            round += 1

        PrintHelper.print("FINISHED !")   
        
        
    ###### Internal functions afterwards ######     
      
    def add_device(self, newUUID):  
        for dev in self.deviceList:
            if dev.uuid == newUUID:
                PrintHelper.print("add device "+newUUID+" already known")
                return dev
               
        PrintHelper.print("add device "+ newUUID)
        newDev = Device(newUUID)
        self.deviceList.append(newDev)
        return newDev
        
    def remove_device(self, remUUID):
        for dev in self.deviceList:
            if dev.uuid == remUUID:
                PrintHelper.print("remove device "+ remUUID)
                
                if dev.wifiMode == Device.WIFI_MODE_CLIENT:
                    self.reset_client(dev)
                    
                elif dev.wifiMode == Device.WIFI_MODE_AP:
                    self.reset_ap(dev)
                
                self.deviceList.remove(dev)
                return 
                
    def get_device(self, uuid):
        for dev in self.deviceList:
            if dev.uuid == uuid:
                return dev
        return None
    
    # no location used yet, we assume fully meshed network
    def get_neighbors(self, device, wifiMode):
        neighborList = []
        for dev in self.deviceList:
            # do not add device asking for neighbor as neighbor
            if device.uuid == dev.uuid:
                continue
            # if a neighbor is not yet confirmed by wishful, dont add
            if (not self.isSimulation) and (not dev.isWishFulConfirmed):
                continue
            
            if (not wifiMode == Device.WIFI_MODE_ANY) and (not dev.wifiMode == wifiMode):
                continue
            
            neighborList.append(dev)
            
        return neighborList
        
    # for now, full meshed network    
    def is_neighbor(self, device1, device2):
        return True

                        
    def print_devices(self):
        PrintHelper.print("Number Devs: "+ str(len(self.deviceList)))
        for dev in self.deviceList:
            dev.print(1)
    
    def print_schedule(self, string):
        if self.debugSchedule:
            PrintHelper.print(string)
    
    def print_error(self, errorstring):
        print("ERRROR")
        print(" ********************** ")
        print(errorstring)
        print(" ********************** ")
        sys.exit(0)
    
    def send_info_request(self, device):
        infoRequest = D2DInfoRequestCommandEvent()
        self.send_command(infoRequest, device)
 
  
    def get_ap_ready_time(self, device):
        for command in device.commandList:
            if isinstance(command, WiFiStartNetworkCommandEvent):
                return command.time + Config.TIME_START_AP
                break
        
        # we did not find a start command, therefore the AP is aleady running
        # connect immediately
        return 0
        
    # returns a list of suitable content that is offered by the provider and in which the consumer is interested in
    # filters out those content that the consumer already has and that is not yet scheduled in consumerScheduledContentList
    def get_suitable_content_list(self, provider, consumer):
        
        suitableContentList = []
        
        for interest in consumer.interestList:
            for content in provider.contentList:
                
                # check if consumer has already this content    
                hasAlreadyContent = False                
                for i in consumer.contentList:                     
                    if i.id == content.id:    
                        hasAlreadyContent = True
                        break
                        
                # continue with next content entry
                if hasAlreadyContent:
                    continue
                    
                # check if we already get the content from another provider or same provider (from another tag)
                isAlreadyScheduled = False
                for i in consumer.consumerScheduledContentList:
                    if content.id == i.id:
                        isAlreadyScheduled = True
                        break
                
                # continue with next content entry
                if isAlreadyScheduled:
                    continue                            
                 
                # content is yet not known to the consumer
                # check if content has a tag matching the interest of the consumer
                for tag in content.tagList:                       
                    if interest == tag.name:
                        suitableContentList.append(content)
                    
        return suitableContentList
    
    def add_content_exchange(self,  provider, consumer, content):

        # Currently all startTime are set to zero
        # Y1 demonstrator is not supporting prioritization of messages
        newEntry = ScheduleEntry(provider, consumer, content, 0, 0)
        
        self.scheduleList.append(newEntry)
        consumer.consumerScheduledContentList.append(content)   
        
        # store the entry also in the provider to generate D2D D2DExchangeContentCommandEvent 
        provider.providingExchangeList.append(newEntry)  

        # store the entry in the consumer to check after schedule generation if idle counter has to be increased
        consumer.consumingExchangeList.append(newEntry)
        
        # in case of multihop (client -> ap -> client) a client might not be locked yet
        provider.wifiModeLocked = True
        consumer.wifiModeLocked = True

    def add_command(self, device, command, timeOffset):
    
        device.nextCommandStartTime += timeOffset
        command.time = device.nextCommandStartTime
        
        device.commandList.append(command)
        
        # increase start time for next command depending on type of command
        if isinstance(command, WiFiJoinNetworkCommandEvent):
            PrintHelper.print("join_network \n\t Device "+device.uuid+" AP "+device.deviceAP.uuid+"  "+device.deviceAP.wifiInformation.to_string()+" time "+str(command.time))   
            device.nextCommandStartTime += Config.TIME_JOIN_AP
            
        elif isinstance(command, WiFiLeaveNetworkCommandEvent):
            PrintHelper.print("leave_network \n\t Device "+device.uuid+" AP "+device.deviceAP.uuid+"  "+device.deviceAP.wifiInformation.to_string()+" time "+str(command.time)) 
            device.nextCommandStartTime += Config.TIME_LEAVE_AP
            
        elif isinstance(command, WiFiStartNetworkCommandEvent):
            PrintHelper.print("start_network \n\t Device "+device.uuid+" "+device.wifiInformation.to_string()+" time "+str(command.time))  
            device.nextCommandStartTime += Config.TIME_START_AP
            
        elif isinstance(command, WiFiStopNetworkCommandEvent):
            PrintHelper.print("stop_network \n\t Device "+device.uuid+" "+device.wifiInformation.to_string()+" time "+str(command.time))      
            device.nextCommandStartTime += Config.TIME_STOP_AP
            
        else:
            print_error("add_command unknown command "+command)

    def start_network(self, ap, timeOffset):
        if ap.wifiMode != Device.WIFI_MODE_NONE:
            self.print_error("start_network but ap "+ap.uuid+" is wifiMode "+ap.wifiMode)
            
        ap.wifiMode     = Device.WIFI_MODE_AP    
        ap.clientList   = []
        ap.deviceAP     = None
        
        ap.wifiModeLocked = True
        
        # set wifi information for new network
        self.get_wifi_info(ap)
        startNetworkCmd = WiFiStartNetworkCommandEvent(ap.wifiInformation)
        self.add_command(ap, startNetworkCmd, timeOffset)  

    def reset_ap(self, ap):
        # abandon network, send leave to all clients
        for client in ap.clientList:                                  
            self.leave_network(client, 0)
            
        # release the channel
        self.availableChannels.append(ap.wifiInformation.channelIndex)                    
        ap.clientList       = []     
        ap.wifiMode         = Device.WIFI_MODE_NONE
        ap.wifiInformation  = None        
   
    def stop_network(self, ap, timeOffset):
        
        if ap.wifiMode != Device.WIFI_MODE_AP:
            self.print_error("start_network but ap "+ap.uuid+" is wifiMode "+ap.wifiMode)
            
        self.add_command(ap, WiFiStopNetworkCommandEvent(), timeOffset + Config.TIME_STOP_AP)      
        self.reset_ap(ap)
            
    def join_network(self, client, ap, timeOffset):
        
        if client.wifiMode != Device.WIFI_MODE_NONE:
            self.print_error("join_network but client "+client.uuid+" is wifiMode "+client.wifiMode)
            
        client.deviceAP = ap
        client.deviceAP.clientList.append(client)
        client.wifiMode = Device.WIFI_MODE_CLIENT
        
        client.wifiModeLocked           = True   
        client.deviceAP.wifiModeLocked  = True
        
        startTime = self.get_ap_ready_time(ap) + timeOffset
        self.add_command(client, WiFiJoinNetworkCommandEvent(ap.wifiInformation), startTime)  
   
   
    def reset_client(self, client):
        client.deviceAP.clientList.remove(client)   
        client.deviceAP = None     
        client.wifiMode = Device.WIFI_MODE_NONE
    
    def leave_network(self, client, timeOffset):
        
        if client.wifiMode != Device.WIFI_MODE_CLIENT:
            self.print_error("leave_network but client "+client.uuid+" is wifiMode "+client.wifiMode)
        
        self.add_command(client, WiFiLeaveNetworkCommandEvent(), timeOffset)        
        self.reset_client(client)
        
    # returns the expected transmission speed in bit/sec between provider and consumer
    # for now we assume a fixed speed between all devices
    def get_transmission_speed(self, provider, consumer):
        
        return 1e7

    def check_generate_schedule(self):
        # timer is not running, lets generate a schedule
        if not self.scheduleTimer.is_running():
            self.generate_schedule(True)
            
        # timer is running but all scheduled exchanged have been performed successfully
        elif len(self.scheduleList) == 0:
            self.scheduleTimer.cancel()
            self.generate_schedule(True)
            
    def schedule_exchange_in_network(self, consumer, ap):
          
        client_list = []               
        if consumer.wifiMode == Device.WIFI_MODE_AP:
            client_list = consumer.clientList
        elif consumer.wifiMode == Device.WIFI_MODE_CLIENT:
            
            if Config.P2P_CLIENT_TO_CLIENT:
                client_list = consumer.deviceAP.clientList
            
            # if client to client is not possible, we only add the ap to possible content providers
            else:
                client_list = []
                client_list.append(consumer.deviceAP)
        else:
            self.print_error("consumer mode "+consumer.wifiMode+" but not AP nor CLIENT")
            
        for provider in client_list:
            
            # do not exchange 
            # - when provider is equal to consumer
            if provider == consumer or (ap is not None and provider == ap):
                continue

            suitableContentList = self.get_suitable_content_list(provider, consumer)
                
            # continue with next provider if no suitable content is available
            if len(suitableContentList) == 0:
                continue
            else:
                # mark that suitable content is avaiable
                consumer.interestedContentAvailable = True
                
            # mark that this network will not be disbandoned by other consumers in this round !
            # keep AP running, other clients might be reconfigured
            if provider.wifiMode == Device.WIFI_MODE_AP:
                provider.wifiModeLocked = True      
                
            # provider is a client -> we have to lock associated AP as well
            elif provider.wifiMode == Device.WIFI_MODE_CLIENT:                     
                provider.wifiModeLocked             = True       
                provider.deviceAP.wifiModeLocked    = True       
             
            # Todo for now we dont care about size and time estimation for the exchange
            # schedule  exchange for all suitable content      
            for content in suitableContentList:
                self.add_content_exchange(provider, consumer, content);
   
    @modules.on_event(PeriodicSchedulerTimeEvent)
    def schedulerTimeEvent(self):
        self.generate_schedule(True)
    
    # startTimer flag restarts the timer after schedule generation
    # should not be set in debug simulation mode
    def generate_schedule(self, startTimer):
        PrintHelper.print("generate_schedule()...")
        
        # scheduleList should be empty
        # if not a scheduled content exchanged has not been executed successfully 
        if len(self.scheduleList) > 0:
            PrintHelper.print("scheduleList not empty!",1)
            for entry in self.scheduleList:
                PrintHelper.print(entry.to_string(),2)
        
        # reset list of schedule entries
        self.scheduleList = []
        
        # reset previous schedule information
        for device in self.deviceList:
            device.d2dExchangeCommandSent = False
            device.providingExchangeList = []
            device.consumingExchangeList = []
  
            device.commandList                  = []
            device.consumerScheduledContentList = []
            device.wifiModeLocked               = False
            device.interestedContentAvailable   = False
            device.nextCommandStartTime         = 0
         
        consumerList = self.deviceList
    
        # find the highest priority / highest idle counter 
        # (= number of scheduling rounds a device has not been assigned a content exchange even though new content was available from device in range (or via AP))
        maxIdleCounter = -1
        for consumer in consumerList:
            if consumer.idleCounter > maxIdleCounter:
                maxIdleCounter = consumer.idleCounter
    
        currentIdleCounter = maxIdleCounter
        # iterating through different levels of priority, starting with the highest
        while currentIdleCounter >= 0:
        
            PrintHelper.print("processing devices with idleCounter "+str(currentIdleCounter), 1)
        
            # searching for consumers having assinged the current priority / idle counter value 
            for consumer in consumerList:
            
                #consumer is not yet confirmed by wishful, do not process unless its a simulation
                if (not self.isSimulation) and (not consumer.isWishFulConfirmed):
                    continue
            
                # only process consumers with currentIdleCounter
                if consumer.idleCounter != currentIdleCounter:
                    continue
                                       
                # check if any content can be provided from devices in the existing network (if network exists and consumer is not in mode WIFI_MODE_NONE)    
                if consumer.wifiMode != Device.WIFI_MODE_NONE:        
                    self.schedule_exchange_in_network(consumer, None)
                    
                # check if consumer has any neighbors which could be potential providers
                # neighborList may be a subset of the client_list (e.g. devices with WIFI_MODE_NONE)
                neighborList = self.get_neighbors(consumer, Device.WIFI_MODE_ANY)   

                # schedule content exchanges with devices that are in wifi mode NONE
                for provider in neighborList:
                    # if content exchange is schedule
                    # it may not be possible depending on WifiModes of provider and consumer
                    scheduleExchange  = False
                    
                    suitableContentList = self.get_suitable_content_list(provider, consumer)
           
                    # continue with next neighbor provider if no suitable content is available
                    if len(suitableContentList) == 0:
                        continue
                    else:
                        # mark that suitable content is avaiable
                        consumer.interestedContentAvailable = True 
          
                    # both are not yet assigned a mode, provider will be AP (if capable)
                    if provider.wifiMode == Device.WIFI_MODE_NONE and consumer.wifiMode == Device.WIFI_MODE_NONE:  
                        
                        newAP       = None
                        newClient   = None
                        if provider.is_capable_AP():
                            newAP       = provider
                            newClient   = consumer
                              
                        elif consumer.is_capable_AP():
                            newAP       = consumer
                            newClient   = provider
                        
                        # no one is capable of running AP, continue with next provider
                        else:
                            continue
                         
                        self.start_network(newAP, 0)    
                        self.join_network(newClient, newAP, 0)                                                         
                        scheduleExchange = True
                                                     
                    elif provider.wifiMode == Device.WIFI_MODE_NONE:
                        # provider will be connected as CLIENT to the AP of the consumer if in range
                        if consumer.wifiMode == Device.WIFI_MODE_CLIENT:
                            
                            if not Config.P2P_CLIENT_TO_CLIENT:
                                continue
                                
                            if self.is_neighbor(provider, consumer.deviceAP):
                                self.join_network(provider, consumer.deviceAP, 0)     
                                scheduleExchange = True                             
                        
                        # consumer can be AP if it was scheduled before as a provider for another device  
                        # connect current provider to consumer                                       
                        elif consumer.wifiMode == Device.WIFI_MODE_AP:                             
                            self.join_network(provider, consumer, 0)      
                            scheduleExchange = True
                            
                        else:
                            self.print_error("State mismatch, provider ",provider.wifiMode," consumer ",consumer.wifiMode)
                                                        
                    elif consumer.wifiMode == Device.WIFI_MODE_NONE:
                        # connect consumer to provider
                        if provider.wifiMode == Device.WIFI_MODE_AP:                         
                            self.join_network(consumer, provider, 0)
                            scheduleExchange = True
                                  
                        # connect consumer to the AP of the provider if in range
                        elif provider.wifiMode == Device.WIFI_MODE_CLIENT:
                            
                            # no client to client possible
                            if not Config.P2P_CLIENT_TO_CLIENT:
                                continue
                        
                            if self.is_neighbor(consumer, provider.deviceAP):
                                self.join_network(consumer, provider.deviceAP, 0)
                                scheduleExchange = True
                       
                        else:
                            self.print_error("State mismatch, provider ",provider.wifiMode," consumer ",consumer.wifiMode)
                    
                    else:
                        PrintHelper.print("scheduling without reconf not possible consumer "+consumer.uuid+"("+consumer.wifiMode+") provider "+provider.uuid+"("+provider.wifiMode+")", 1)
                                               
                    if scheduleExchange:     
                        for content in suitableContentList:    
                            self.add_content_exchange(provider, consumer, content);
  

                # we have found content to be scheduled for the consumer in its current network
                # following checks are performed with neighors that are currently not in the same network
                # and would require reconfiguration 
                # reconfiguration is only allowed when idleThreshold is hit
                if consumer.interestedContentAvailable and consumer.idleCounter < D2DController.idleThreshold:
                    continue

                # no new content can be received 
                # -- in the current associated network (if any)
                # -- from any device with mode WIFI_MODE_NONE
                # check neighbors again for suitable content and if necessary disband their current network  
          
                neighborList = self.get_neighbors(consumer, Device.WIFI_MODE_AP)   

                for provider in neighborList:
  
                    suitableContentList = self.get_suitable_content_list(provider, consumer)
                                  
                    # continue with next neighbor provider if no suitable content is available
                    if len(suitableContentList) == 0:       
                        continue
                        
                    # consumer has already scheduled content, we will not do reconfiguration
                    if len(consumer.consumerScheduledContentList) > 0:
                        break
                  
                    # we hit the threshold and there is no new content in the current network (checked before)             
                    # -> cancel an ongoing network and create a new one to obtain new content
                    if consumer.idleCounter >= D2DController.idleThreshold:
                        self.schedule_reconfig(consumer, provider, suitableContentList)   
                                                   
                # content exchange is sceheduled, do not continue to reconfig devices
                if len(consumer.consumerScheduledContentList) > 0:       
                    continue
                    
                neighborList = self.get_neighbors(consumer, Device.WIFI_MODE_ANY)   
                for provider in neighborList:
  
                    suitableContentList = self.get_suitable_content_list(provider, consumer)
                                  
                    # continue with next neighbor provider if no suitable content is available
                    if len(suitableContentList) == 0:       
                        continue
                        
                    # consumer has already scheduled content, we will not do reconfiguration
                    if len(consumer.consumerScheduledContentList) > 0:
                        break
                  
                    # we hit the threshold and there is no new content in the current network (checked before)             
                    # -> cancel an ongoing network and create a new one to obtain new content
                    if consumer.idleCounter >= D2DController.idleThreshold:
                        self.schedule_reconfig(consumer, provider, suitableContentList)   
                
            # process devices with next lower priority value                                    
            currentIdleCounter -= 1
        
        # go through all devices and check if exchange is schedules and if interestedContent flag is set, if not increase idlecounter
        # no content exchange scheduled even though we have found at least one neighbour with at least one content we are interested in
        # increase the idle counter to give this consumer a higher priority in the next round
        maxTime = -1
        PrintHelper.print("modifying idleCounter ", 1)
        idleCounterIncreased = False
        for device in self.deviceList:
            
            #modifiy idle counter
            # exchange is scheduled, reset counter
            if len(device.consumingExchangeList) > 0:
                PrintHelper.print(device.uuid+" reset!", 2)
                device.idleCounter = 0
            else:
                # no exchange scheduled, but content available, increase counter
                if device.interestedContentAvailable: 
                    idleCounterIncreased = True
                    device.idleCounter += 1
                    PrintHelper.print(device.uuid+" increased to "+str(device.idleCounter)+"!", 2)
            
            #determine maximum required transmission time
            # start time for possible content exchange is nextCommandStartTime
            timeSum = device.nextCommandStartTime
            for exchange in device.providingExchangeList:
                timeSum += (exchange.content.size / self.get_transmission_speed(exchange.provider, exchange.consumer))
            if timeSum > 0 and timeSum > maxTime:
                maxTime = timeSum
        
            #send out all wifi commands
            for command in device.commandList:
                if not self.isSimulation:
                    self.send_command(command, device)
            device.commandList = []
        
        # process scheduled exchanges and send out exchange commands
        PrintHelper. print("list of schedule entries: (num "+str(len(self.scheduleList))+")", 1)
        for entry in self.scheduleList:
           
            PrintHelper.print(entry.to_string(), 2)
                 
            if not entry.provider.d2dExchangeCommandSent:
                entry.provider.d2dExchangeCommandSent = True
                if not self.isSimulation:
                    self.send_d2d_content_exchange(entry.provider)
       
       
        if startTimer and self.scheduleTimer.is_running():
            self.scheduleTimer.cancel()
                
        PrintHelper.print("schedule next generate_schedule()", 1)
        if maxTime == -1:
            # if there are no exchanges schedule but at least one device could perform an exchange (by using reconfiguration)
            # we will reschedu le immediately
            if idleCounterIncreased:
                if startTimer:
                    self.scheduleTimer.start(1)
                PrintHelper.print("set to now!", 2)
          
            else:
                PrintHelper.print("not set", 2)
        else:
            # add some seconds buffer time
            #maxTime += 10
            maxTime = 15
            PrintHelper.print("set to "+str(maxTime), 2)
            if startTimer:
                self.scheduleTimer.start(maxTime)
                
    def schedule_reconfig(self, consumer, provider, suitableContentList):
       
       # wifi mode is locked, we are not allowed to modify it           
        if provider.wifiModeLocked:
            #if the consumer is locked as well, we cannot do anything
            if consumer.wifiModeLocked:
                return
            
            newAP = None                         
            # since provider is client, we cannot join the network
            if provider.wifiMode == Device.WIFI_MODE_CLIENT:
                
                #provider is a client, reconfigure as AP
                if not Config.P2P_CLIENT_TO_CLIENT:
                    return
                
                else:
                    # AP of the provider and the consumer are not in range, we cannot schedule exchange
                    if not self.is_neighbor(provider.deviceAP, consumer): 
                        return                               
                    newAP = provider.deviceAP                              
             
            # provider is already AP, we just join
            elif provider.wifiMode == Device.WIFI_MODE_AP:    
                newAP = provider
                                         
            else:
                self.print_error("idleCounter threshold hit, wifiMode provider locked, consumer not locked, provider unknown wifimode "+provider.wifiMode)   
                                     
            # consumer is currently connected to a different AP 
            # it has to leave network and join the newAP
            if consumer.wifiMode == Device.WIFI_MODE_CLIENT:                                 
                self.leave_network(consumer, 0) 
                                     
            # consumer is currently AP, has to quit role to connect as client to provider AP
            elif consumer.wifiMode == Device.WIFI_MODE_AP:  
                self.stop_network(consumer, 0)
              
            else:
                self.print_error("idleCounter threshold hit, wifiMode provider locked, consumer not locked, consumer unknown wifimode "+consumer.wifiMode)
                    
            self.join_network(consumer, newAP, 0)     
                                                 
        #provider.wifimode not locked, reconfigure network
        else:         
            if consumer.wifiModeLocked:
            
                newAP = None
                if consumer.wifiMode == Device.WIFI_MODE_CLIENT: 
                      
                    # P2P not allowed, provider cannot communicate with consumer
                    if not Config.P2P_CLIENT_TO_CLIENT:
                        return
                      
                    if not self.is_neighbor(consumer.deviceAP, provider):  
                        return
                    # provider is in range of the AP of the consumer
                    # force provider to leave its current network and join consumer AP network
                    newAP = consumer.deviceAP
                        
                elif consumer.wifiMode == Device.WIFI_MODE_AP:    
                    newAP = consumer
                    
                else:
                    self.print_error("idleCounter threshold hit, wifiMode provider not locked, consumer locked, consumer unknown wifimode "+provider.wifiMode)                                              
                if provider.wifiMode == Device.WIFI_MODE_CLIENT:  
                    # provider cannot be client, if P2P_CLIENT_TO_CLIENT is not enabled
                    
                    self.leave_network(provider, 0)
                    
                elif provider.wifiMode == Device.WIFI_MODE_AP:                                          
                    self.stop_network(provider, 0)
                    
                else:
                    self.print_error("idleCounter threshold hit, wifiMode provider not locked, consumer locked, provider unknown wifimode "+provider.wifiMode)
                
                self.join_network(provider, newAP, 0) 
            
            # consumer wifiMode is not locked and provider also not locked
            # provider CLIENT   consumer AP     -> consumer AP and provider has to join
            # provider CLIENT   consumer NONE   -> provider leave network, start AP and consumer join
            # provider AP       consumer AP     -> provider AP and consumer has to stop network and join
            # provider AP       consumer CLIENT -> provider AP and consumer has to join
            # provider CLIENT   consumer CLIENT ->
            # provider NONE     consumer CLIENT -> provider AP and consumer has to join (state possible if P2P_CLIENT_TO_CLIENT is disabled)
            #           -> if consumer is in range of AP of producer -> consumer leave network and join producer network
            #           -> else if producer is in range of consumer sp -> producer leave network and join consumer network
            #           -> else producer starts ap and consumer joins
            else:
                newAP     = None
                newClient = None
                
                if consumer.wifiMode == Device.WIFI_MODE_AP:
                    
                    if provider.wifiMode == Device.WIFI_MODE_AP:
                        self.stop_network(consumer, 0)
                        newAP     = provider
                        newClient = consumer
                    
                    elif provider.wifiMode == Device.WIFI_MODE_CLIENT:
                        self.leave_network(provider, 0)
                        newAP     = consumer
                        newClient = provider
                    
                    else:
                        self.print_error("idleCounter threshold hit, wifiMode provider not locked, consumer not locked with mode "+consumer.wifiMode+", provider unknown wifimode "+provider.wifiMode)
                    
                elif consumer.wifiMode == Device.WIFI_MODE_CLIENT or (consumer.wifiMode == Device.WIFI_MODE_NONE and not Config.P2P_CLIENT_TO_CLIENT):

                    if provider.wifiMode == Device.WIFI_MODE_AP or (provider.wifiMode == Device.WIFI_MODE_NONE and not Config.P2P_CLIENT_TO_CLIENT):
                        if consumer.wifiMode == Device.WIFI_MODE_CLIENT:
                            self.leave_network(consumer, 0)  
                        if provider.wifiMode == Device.WIFI_MODE_NONE:
                            self.start_network(provider, 0)
                        newAP     = provider
                        newClient = consumer
                    
                    elif provider.wifiMode == Device.WIFI_MODE_CLIENT:
                    
                        # check if consumer is in range of AP of provider
                        # consumer will join the network of the provider
                        if Config.P2P_CLIENT_TO_CLIENT and self.is_neighbor(consumer, provider.deviceAP):  
                            if consumer.wifiMode == Device.WIFI_MODE_CLIENT:
                                self.leave_network(consumer, 0)   
                            newAP     = provider.deviceAP
                            newClient = consumer 
                        
                        # consumer not in range of ap of provder,
                        # check if provider is in range of ap of consumer
                        elif Config.P2P_CLIENT_TO_CLIENT and self.is_neighbor(provider, consumer.deviceAP):  
                            self.leave_network(provider, 0)  
                            newAP     = consumer.deviceAP
                            newClient = provider 
                        
                        # consumer not in range of ap of provder or P2P_CLIENT_TO_CLIENT disabled
                        # provider will start AP (if capable) and consumer joins as client
                        else:
                            #provider is capable of running AP
                            if provider.is_capable_AP():
                                self.leave_network(provider, 0)  
                                self.start_network(provider, 0)
                                if consumer.wifiMode == Device.WIFI_MODE_CLIENT:
                                    self.leave_network(consumer, 0)
                                newAP     = provider
                                newClient = consumer 
                           
                            # provider is not able to run AP, check the consumer
                            elif consumer.is_capable_AP():
                                if consumer.wifiMode == Device.WIFI_MODE_CLIENT:
                                    self.leave_network(consumer, 0)  
                                self.start_network(consumer, 0)
                                self.leave_network(provider, 0)
                                newAP     = consumer
                                newClient = provider 
                                
                            # no one is capable of running an AP
                            else:
                                PrintHelper.print("neither provider "+provider.uuid+" nor consumer "+consumer.uuid+" capable of starting AP", 2)
                                return                            
                    else:
                        self.print_error("idleCounter threshold hit, wifiMode provider not locked, consumer not locked, provider unknown wifimode "+provider.wifiMode)
                
                else:
                    self.print_error("idleCounter threshold hit, wifiMode provider not locked, consumer not locked, consumer unknown wifimode "+consumer.wifiMode)
          
                self.join_network(newClient, newAP, 0)
                               
        for content in suitableContentList:    
            self.add_content_exchange(provider, consumer, content);
          
    # generates a new WiFiInformation including a network name, passphrase and channel index out of the list of available channels
    def get_wifi_info(self, device):
           
            
        # check if its a known device
        if device.uuid == "TKN_G2-1":
            networkName = "someSSID"
            passphrase  = "somepassphrase"
       
        else:
            warn = "WARNING: get_wifi_info() cannot find credentials for "+device.uuid
            
            if (self.isSimulation):
                PrintHelper.print(warn)
            else:
                self.print_error(warn)
            # use the first 8 characaters of the device id as SSID
            networkName  = device.uuid[:8]
            #networkName = "testtest"
            
            # to do generate random passphrase?
            passphrase   = "12345678"
       
        # no available channels, use a random from default list
        if (len(self.availableChannels) == 0):
            PrintHelper.print("get_wifi_info availableChannels is empty...")
            channelIndex = D2DController.defaultChannelList[random.randrange(len(D2DController.defaultChannelList))]
            
        else:
            # random or first
            # channelIndex = self.availableChannels[random.randrange(len(self.availableChannels))]
            channelIndex = self.availableChannels[0]
            
            #remove channel from available list
            self.availableChannels.remove(channelIndex)
            
        device.wifiInformation = WiFiInformation(networkName, passphrase, channelIndex)
    
    def send_command(self, command, device):
        PrintHelper.print("send command")
        PrintHelper.print(type(command).__name__ +" to dev "+self.deviceList[0].uuid+ " execTime "+str(command.time), 1)
        self.send_event(command, device)
  
    def send_d2d_content_exchange(self, device):
        d2dContentCmd = D2DExchangeContentCommandEvent(device.providingExchangeList)
        self.send_command(d2dContentCmd, device)
   
    ### Timers ###    
    
    @modules.on_event(TestTimeEvent)
    def test_timer(self, event):
        self.test()
        
    @modules.on_event(PeriodicDisplayTimeEvent)
    def periodic_display(self, event):

        self.print_devices()
        self.displayTimer.start(self.displayInterval)
        
        if self.cmdTransmitted:
            return
        
        if len(self.deviceList) == 0:
            return 
                     
        return
        
   
    #################
    ### Events    ###
    #################    
         
    @modules.on_event(TestEvent)
    def process_test_event(self, event):
        self.log.info("Received test event")
        
    @modules.on_event(D2DAddInterestNotificationEvent)
    def process_D2DAddInterestNotificationEvent(self, event):
        tagString = "["
        for t in event.interestList:
            if len(tagString) > 1:
                tagString += ", "  
            tagString += "\""+t+"\""
        tagString += "]"            
        PrintHelper.print("* Rx D2DAddInterestNotificationEvent tagList "+tagString+" from dev "+event.srcDevUUID, 1)
        
        dev = self.get_device(event.srcDevUUID)
        if dev is None:
            dev = self.add_device(event.srcDevUUID)
            
        for t in event.interestList:
            dev.add_interest(t)

        if len(event.interestList) > 0:
            self.check_generate_schedule();
        
    @modules.on_event(D2DRemoveInterestNotificationEvent)
    def process_D2DRemoveInterestNotificationEvent(self, event):
        tagString = "["
        for t in event.interestList:
            if len(tagString) > 1:
                tagString += ", "  
            tagString += "\""+t+"\""
        tagString += "]"
        PrintHelper.print("* Rx D2DRemoveInterestNotificationEvent tagList "+ tagString+ " from dev "+ event.srcDevUUID, 1)
        
        dev = self.get_device(event.srcDevUUID)
        if dev is None:
            dev = self.add_device(event.srcDevUUID)
            
        for t in event.interestList:
            dev.remove_interest(t)
   
    @modules.on_event(D2DAddContentNotificationEvent)
    def process_D2DAddContentNotificationEvent(self, event):
        contentString = "["
        for content in event.contentList:
            if len(contentString) > 1:
                contentString += ", "        
            contentString += "\""+content.id+"\""            
        contentString += "]"        
        PrintHelper.print("* Rx D2DAddContentNotificationEvent contentList "+ contentString+ " from dev "+ event.srcDevUUID, 1)
        
        dev = self.get_device(event.srcDevUUID)
        if dev is None:
            dev = self.add_device(event.srcDevUUID)
            
        for content in event.contentList:
            dev.add_content(content)      
            # remove schedule entry if the content exchanged was scheduled
            for entry in self.scheduleList[:]:
                #maybe the content was scheduled to be transmitted from multiple sources, remove all entries
                if dev.uuid == entry.consumer.uuid and content.id == entry.content.id:
                    self.scheduleList.remove(entry)
                
        if len(event.contentList) > 0:
            self.check_generate_schedule()
     
    @modules.on_event(D2DRemoveContentNotificationEvent)
    def process_D2DRemoveContentNotificationEvent(self, event):
        contentString = "["
        for id in event.contentIdList:
            if len(contentString) > 1:
                contentString += ", "       
            contentString = id+" "
        contentString += "]" 
        PrintHelper.print("* Rx D2DRemoveContentNotificationEvent contentList "+ contentString+ " from dev "+ event.srcDevUUID, 1)

        dev = self.get_device(event.srcDevUUID)
        # todo or should we add unknown device?
        if dev is None:
            return
            
        for id in event.contentIdList:  
            dev.remove_content(id)      
         
    ###########
    ## Uniflex events
    ###########  
    
    @modules.on_start()
    def my_start_function(self):
        PrintHelper.print("start control app")
        self.running = True

    @modules.on_exit()
    def my_stop_function(self):
        PrintHelper.print("stop control app")
        self.running = False

    @modules.on_event(events.NewNodeEvent)
    def add_node(self, event):
        node = event.node

        self.log.info("Added new node: {}, Local: {}".format(node.uuid, node.local))
        self._add_node(node)

        for dev in node.get_devices():
            PrintHelper.print("Dev: "+ dev.name)
            PrintHelper.print(dev)

        for m in node.get_modules():
            PrintHelper.print("Module: "+ m.name)
            PrintHelper.print(m)

        for app in node.get_control_applications():
            PrintHelper.print("App: "+ app.name)
            PrintHelper.print(app)

        newDev = self.add_device(node.uuid)
        newDev.isWishFulConfirmed = True
                       
        # send info request to device to obtain the current state
        self.send_info_request(newDev)

    @modules.on_event(events.NodeExitEvent)
    @modules.on_event(events.NodeLostEvent)
    def remove_node(self, event):
        self.log.info("Node lost".format())
        node = event.node
        reason = event.reason
        
        self.remove_device(node.uuid)
        
        self.cmdTransmitted = False
        
        if self._remove_node(node):
            self.log.info("Node: {}, Local: {} removed reason: {}".format(node.uuid, node.local, reason))