import serial
import time

'''
A wrapper class to send high-level commands to a GRBL
CNC controller.
'''
class grbl:
    def __init__( self, portname):
        # Initialize the serial port
        print('Connecting grbl to port: ' + portname)
        self.portname = portname
        self.port = serial.Serial(portname, 115200)
        
    def wake(self):
        self.port.write(b'\r\n\r\n')
        time.sleep(2)
        self.port.flushInput()

    def unlock(self):
        print("Unlocking machine")
        self.port.write(b'$X\n')
        grbl_out = self.port.readline()
        print('Response: ' + grbl_out.decode().strip())

    def home(self):
        print('Homing machine')
        self.port.write(b'$H\n')
        grbl_out = self.port.readline()
        print('Response: ' + grbl_out.decode().strip())

    def goTo(self, x_pos, y_pos, z_pos):
        command = 'G0 X{} Y{} Z{} G4P0\n'.format(x_pos, y_pos, z_pos)
        print('Sending: ' + command.rstrip())
        self.port.write(command.encode())
        grbl_out = self.port.readline()
        print('Response: ' + grbl_out.decode().strip())

    def goToSpeed(self, x_pos, y_pos, z_pos, speed):
        command = 'G1 X{} Y{} Z{} F{}\n'.format(x_pos, y_pos, z_pos, speed)
        self.port.write(command.strip().encode())
        grbl_out = self.port.readline()
        print('Response: ' + grbl_out.decode().strip())

    def runFile(self, filename):
        # Open the gcode file
        f = open(filename, 'r')
        
        # make sure GRBL is awake
        self.wake()
        self.unlock()        

        #Stream each line of the file
        for line in f:
            l = line.strip()
            print( 'Sending: ' + l )
            self.port.write((l + ' G4P0\n').encode())
            grbl_out = port.readline()
            print('Response: ' + str(grbl_out).strip())
            
        # close the file
        f.close()

    def close(self):
        self.port.close()
