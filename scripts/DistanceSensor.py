import serial
import time
import struct
import serial.tools.list_ports

class DistanceSensor:
    def __init__( self, portname):
        # Initialize the serial port
        print('Connecting ToF to port: ' + portname)
        self.portname = portname
        self.port = serial.Serial(portname, 115200)

    def poll(self):
        # Send request for data
        request=bytearray(1)
        request[0] = 0x0F
        self.port.write(request)

        # Wait until reaponse has been received
        while self.port.in_waiting < 2:
            pass
        
        # Read response
        sample = 0xFFFF
        if ( ord(self.port.read()) == 0x0F ):
            in_bytes = bytearray(2)
            in_bytes[0] = ord(self.port.read())
            in_bytes[1] = ord(self.port.read())
            sample = struct.unpack(">H", in_bytes)[0]
        else:
            print('Corrupted packet, flushing buffer')
            self.port.flush()

        return sample

    def close(self):
        self.port.close()

def main():

    portname = ''
    port_list = list(serial.tools.list_ports.comports())

    if len(port_list) == 0:
        print('No device connected')
    elif len(port_list) == 1:
        print('Found one device, connecting to ' + port_list[0][0])
        portname = port_list[0][0]
    else:
        for port in port_list:
            if port[1] == 'Arduino Leonardo':
                portname = port[0]
        
        # If no Leonardo was found, try the first port
        if not portname:
            portlist = port_list[0]

        print('Found multiple devices, selecting' + portname)
                
    # create port
    sensor = DistanceSensor(portname)

    # poll sensor indefinitly
    while True:
        print('Reading: ' + str(sensor.poll()) + ' mm')

if __name__ == '__main__':
    main()
