import serial
import time
import struct

def poll_data( port ):
    # Send request for data
    request=bytearray(1)
    request[0] = 0x0F
    port.write(request)

    # Wait until reaponse has been received
    while port.in_waiting < 2:
        pass
    
    # Read response
    sample = 0xFFFF
    if ( ord(port.read()) == 0x0F ):
        in_bytes = bytearray(2)
        in_bytes[0] = ord(port.read())
        in_bytes[1] = ord(port.read())
        sample = struct.unpack(">H", in_bytes)[0]
    else:
        print('Corrupted packet, flushing buffer')
        port.flush()

    return sample

def main():

    # create port
    port = serial.Serial(port ='/dev/ttyACM0', baudrate=115200)
    print('ToF Sensor Connected')

    # poll sensor indefinitly
    while True:
        print('Reading: ' + str(poll_data(port)) + ' mm')

if __name__ == '__main__':
    main()
