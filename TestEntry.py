from Device import Device 
from Content import Content

class TestEntry(object):

    ACTION_ADD_INTEREST = "ACTION_ADD_INTEREST"
    ACTION_REM_INTEREST = "ACTION_REM_INTEREST"
    
    ACTION_ADD_CONTENT = "ACTION_ADD_CONTENT"
    ACTION_REM_CONTENT = "ACTION_REM_CONTENT"

    def __init__(self, action, device, entity, round):
        super().__init__()
        
        self.action = action
        if (action == TestEntry.ACTION_ADD_INTEREST) or (action == TestEntry.ACTION_REM_INTEREST):
            self.interest = entity
            self.content  = None
            
        if (action == TestEntry.ACTION_ADD_CONTENT) or (action == TestEntry.ACTION_REM_CONTENT):
            self.interest = None
            self.content  = entity         
       
        self.device = device
        self.roundToExecute = round
        
        
          