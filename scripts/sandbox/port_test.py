import serial.tools.list_ports

portList = list(serial.tools.list_ports.comports())

for port in portList:
    print(port[0])
    print(port[1])
    print(port[2])

