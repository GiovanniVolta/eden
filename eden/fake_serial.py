import time
from random import gauss

PARITY_NONE = None

class Serial:

    ## init(): the constructor.  Many of the arguments have default values
    # and can be skipped when calling the constructor.
    
    def __init__( self, port='COM1', baudrate = 19200, timeout=1,
                  bytesize = 8, parity = 'N', stopbits = 1, xonxoff=0,
                  rtscts = 0):
                  
        self.name     = port
        self.port     = port
        self.timeout  = timeout
        self.parity   = parity
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.stopbits = stopbits
        self.xonxoff  = xonxoff
        self.rtscts   = rtscts
        self.is_open  = True
        self._receivedData = ''
        self.sum_receivedData = ""

        self.time_last_command = 0
        
        self.u = 0
        self.i = 0
        self.v_set = 0
        self.i_set = 0
        self.u_max = 0
        self.i_max = 0

    def refresh_board(self):    
    # this functino is activated when communication with board and refreshes all values
    # this function simulates the Hardware
        now_time = time.time()
        t_delta = now_time - self.time_last_command
        self.u = gauss(self.v_set,0.1)
        self.i = gauss(self.i_set,0.1)
               
        self.time_last_command = now_time        
        return

    ## isOpen()
    # returns True if the port to the Arduino is open.  False otherwise
    def isOpen( self ):
        return self.is_open
    ## open()
    # opens the port
    def open( self ):
        self.is_open = True

    ## close()
    # closes the port
    def close( self ):
        self.is_open = False

    def write( self, string ):

        self._receivedData = string.decode()
        self.sum_receivedData += self._receivedData
        if "SO:VO " in self.sum_receivedData:
            self.v_set = float(self.sum_receivedData.split(' ')[1])
            self.sum_receivedData = ""
            return None
            
        if "SO:CU " in self.sum_receivedData:
            self.i_set = float(self.sum_receivedData.split(' ')[1])
            self.sum_receivedData = ""
            return None     
            
        if "SO:VO:MA " in self.sum_receivedData:
            self.u_max = float(self.sum_receivedData.split(' ')[1])
            self.sum_receivedData = ""
            return None   
            
        if "SO:CU:MA " in self.sum_receivedData:
            self.i_max = float(self.sum_receivedData.split(' ')[1])
            self.sum_receivedData = ""
            return None                            
        

    ## read()
    # reads n characters from the fake Arduino. Actually n characters
    # are read from the string _data and returned to the caller.
    def read( self, n=1 ):
        time.sleep(0.02)
        return self._receivedData.encode()
        
        
    def read_until( self , until):
        answer = "????"
        self.refresh_board()
        if not "\n" in self.sum_receivedData:
            return self.read()
        
        if self.sum_receivedData == "CH?\n":
            answer = "1"
        if self.sum_receivedData == "SO:VO?\n":
            answer = str(self.v_set)
        if self.sum_receivedData == "SO:CU?\n":
            answer = str(self.i_set)
            
        if self.sum_receivedData == "ME:VO?\n":
            answer = str(self.u)
        if self.sum_receivedData == "ME:CU?\n":
            answer = str(self.i)

        if "CH " in self.sum_receivedData:
            answer = ""                         
                                                                                     
        answer = str(answer) +"\n\r\x04"
        self.sum_receivedData = ""
        time.sleep(0.1)
        return answer.encode()
