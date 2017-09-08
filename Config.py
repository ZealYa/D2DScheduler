import time

class Config(object):

    SEED = time.time()
    #SEED = 1488392438.876672

    P2P_CLIENT_TO_CLIENT = False
    
    # Delay timers for WiFi configurations
    TIME_START_AP   = 5000
    TIME_STOP_AP    = 2000
    TIME_JOIN_AP    = 2000
    TIME_LEAVE_AP   = 1000

    TIME_SCHEDULE_LIMIT = 15000
    
    #print parameter
    PRINT_CONTENT_ID_CHAR_LIMIT = 5
