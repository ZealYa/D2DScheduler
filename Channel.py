from ScheduleEntry import ScheduleEntry
from Channel import Channel
    
class Channel(object):

    def __init__(self, id):
        super().__init__()
        self.id = id
        
        self.scheduleEntryList = []
        
    def get_earliest_tx_time(self, duration, slotLimit):
        lastAvailTime = 0
        for entry in self.scheduleEntryList:
            
    
    # sort the entries according to starttime
    # no check is performed if entries are overlapping
    def add_schedule_entry(self, entry):
        index = 0
        
        for tmpEntry in self.scheduleEntryList:
            if tmpEntry.startTime > entry.startTime:
                break
            index += 1
        
        self.scheduleEntryList.insert(index, entry)
        
        
        