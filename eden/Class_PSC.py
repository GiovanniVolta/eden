"""
Class to virtualize the Hardware of the Delta electronica 
Power supply controller
Code written by Mona Piotter
(Modified by Florian Jörg)
mona.piotter@mpi-hd.mpg.de
florian.joerg@mpi-hd.mpg.de
"""

import serial
#from eden import fake_serial as serial

class PSC:
    def __init__(self,port,channel):
        self.reader_thread = None
        self.board_busy = False
    
        self.port = port
        self.response_timeout = 5
        self.baudrate = 9600
        self.rtscts=False
        self.stopbits=1
        self.serial_conn=None
        self.is_connected = False
        self.board_active = False
        
        self.channel = channel
        self.power_output = float('nan')
        self.set_vol = float('nan')
        self.set_cu = float('nan')
        self.max_vol = float('nan')
        self.mea_vol = float('nan')
        self.mea_cu = float('nan')
        self.remote = float('nan')
        self.remote_CV = float('nan')
        self.remote_CC = float('nan')
        self.local = float('nan')
        self.local_CC = float('nan')
        self.local_CV = float('nan')
        self.mea_speed = float('nan')
        
    def set_readerthread(self, thread):
        self.reader_thread = thread
        
    def set_baudrate(self,baudrate):
        self.baudrate=baudrate
    
    def set_timeout(self, timeout):
        self.timeout=timeout
         
    def establish_connection(self):
        self.serial_conn = serial.Serial(port=self.port, baudrate= self.baudrate, timeout=self.response_timeout, 
                                         parity=serial.PARITY_NONE, rtscts=self.rtscts, stopbits=self.stopbits)
        if self.serial_conn.is_open:
            self.is_connected = True
    
    
    def activate_chan (self):

        self.serial_conn.write(b"CH "+str(self.channel).encode()+b"\n")
        answer = self.read()
        if answer is self.channel:
            self.board_active = True
        
    def read (self):
        a=self.serial_conn.read_until(b'\n\r\x04')
        a=a.split(b'\n\r\x04')
        a=a[0]  
        return a.decode()

    
    def get_channel (self):
        self.channel = self.serial_conn.write(b"CH?\n")
        return self.read()
    
    def get_set_vol (self):
        self.serial_conn.write(b"SO:VO?\n")
        try:
            self.set_vol = float(self.read())
        except (TypeError, ValueError):
            print("Wrong data type returned from board!")
    
    def get_set_cu (self):
        self.serial_conn.write(b"SO:CU?\n")
        try:
            self.set_cu = float(self.read())
        except (TypeError, ValueError):
            print("Wrong data type returned from board!")        

    
    def get_mea_vol (self):
        self.serial_conn.write(b"ME:VO?\n")
        try:
            self.mea_vol = float(self.read())
        except (TypeError, ValueError):
            print("Wrong data type returned from board!")    

   
    def get_mea_cu (self):
        self.serial_conn.write(b'ME:CU?\n') 
        try:
            self.mea_cu = float(self.read())
        except (TypeError, ValueError):
            print("Wrong data type returned from board!")    

    
    def get_max_vol (self):
        self.serial_conn.write(b"SO:VO:MA?\n")
        try:
            self.max_vol = float(self.read())
        except (TypeError, ValueError):
            print("Wrong data type returned from board!")            
        
    def get_max_cu (self):
        self.serial_conn.write(b"SO:CU:MA?\n")
        try:
            self.max_cu = float(self.read())
        except (TypeError, ValueError):
            print("Wrong data type returned from board!")  

    
    def get_remote (self):                         
        self.serial_conn.write(b"REM?\n")
        try:
            self.remote = int(self.read())
        except (TypeError, ValueError):
            print("Wrong data type returned from board!")  

        if self.remote == 1:
            print('remote because')
        elif self.remote == 0:
            print('local mode because')
        else:
            print('error')

    # modify functinos from here on!!
    def get_remote_CC (self):
        self.remote_CC = self.serial_conn.write(b"REM:CC?\n")
        a=self.read()
        a=int(a)
        if a == '1':
            print('remote because')
        elif a==0:
            print('local mode because')
        else:
            print('error')
        return a
        
    def get_remote_CV (self):
        self.remote_CV = self.serial_conn.write(b"REM:CV?\n")
        a=self.read()
        a=int(a)
        if a == 1:
            print('remote because')
        elif a==0:
            print('local mode because')
        else:
            print('error')
        return a
    
    def get_mea_speed (self):
        self.mea_speed = self.serial_conn.write(b"SP?\n")
        return self.read()
 
    def set_max_vol (self,set_max_vol):
        self.serial_conn.write(b"SO:VO:MA "+str(set_max_vol).encode()+b"\n")
 
    
    def set_max_cu (self,set_max_cu):
        self.serial_conn.write(b"SO:CU:MA "+str(set_max_cu).encode()+b"\n")
        
        
    def set_set_vol (self, set_vol):
        self.serial_conn.write(b"SO:VO "+str(set_vol).encode()+b"\n")

    def set_set_cu (self, set_cu):
        self.serial_conn.write(b"SO:CU "+str(set_cu).encode()+b"\n")
        
    def set_speed (self, speed):
        self.serial_conn.write(b"SP "+str(speed).encode()+b"\n")
        
    def set_to_local (self):  #This command sets both CV and CC to local so that they can be adjusted by the front panel knobs (potentiometers).
        self.local = self.serial_conn.write(b"LOC\n") 
        
    def set_to_local_CC (self):
        self.local_CC = self.serial_conn.write(b"LOC:CC\n") 
        
    def set_to_local_CV (self):
        self.local_CV = self.serial_conn.write(b"LOC:CV\n")     
    
    def set_to_remote (self): #This command sets both CV and CC to remote so that they can be adjusted by the PSC.
        self.remote = self.serial_conn.write(b"REM\n") 
        self.remote = self.serial_conn.write(b"REM?\n")
        a=self.read()
        a=int(a)
        if a == 1:
            print('remote because')
        elif a==0:
            print('local mode because')
        else:
            print('error')
        return a
        
    def set_to_remote_CC (self):
        self.remote_CC = self.serial_conn.write(b"REM:CC\n")
        self.remote_CC = self.serial_conn.write(b"REM:CC?\n")
        a=self.read()
        a=int(a)
        if a == 1:
            print('remote because')
        elif a==0:
            print('local mode because')
        else:
            print('error')
        return a
        
    def set_to_remote_CV (self):
        self.remote_CV = self.serial_conn.write(b"REM:CV\n")
        self.remote_CV = self.serial_conn.write(b"REM:CV?\n")
        a=self.read()
        a=int(a)
        if a == 1:
            print('remote because')
        elif a==0:
            print('local mode because')
        else:
            print('error')
        return a
         
   # def set_power_supply_output (self,output):
       # self.power_output = self.serial_conn.write(b"SO:FU:OUTP "+str(output).encode()+b"\n")
        #return self.read()
    
    def close_connection(self):
        self.serial_conn.close()
        if not self.serial_conn.is_open:
            self.is_connected = False

