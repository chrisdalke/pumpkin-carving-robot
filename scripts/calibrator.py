import sys
import grbl
import time
import DistanceSensor
import serial
import csv

def main():
    # Calibration bounds
    x_min = 20
    x_max = 100
    x_step = 10

    y_min = 0
    y_max = 360
    y_step = 10

    z_value = 0

    X_UPPER_LIMIT = 200
    sensor_offset_z = 38
    sensor_offset_x = 53
    axis_offset = 168

    if x_max + sensor_offset_x > X_UPPER_LIMIT:
        sys.exit('ERROR: calibration window larger than machine work area')

    # Select the correct ports 
    grbl_port = ''
    tof_port = ''
    port_list = list(serial.tools.list_ports.comports())

    if len(port_list) < 2:
        sys.exit('ERROR: Less than two USB devices connected')
    else:
        # Find the ToF port
        for port in port_list:
            if port[1] == 'Arduino Leonardo':
                tof_port = port[0]
        if not tof_port:
            sys.exit('ERROR: Could not find Leonardo with ToF sensor')

        # Find the GRBL port
        for port in port_list:
            if port[0] != tof_port:
                grbl_port = port[0]
        if not grbl_port:
            sys.exit('ERROR: Could not find GRBL port')

    # Initialize hardware
    g = grbl.grbl(grbl_port)
    sensor = DistanceSensor.DistanceSensor(tof_port) 

    # Run calibration sequence
    g.wake()
    g.home()
    g.goTo(sensor_offset_x, z_value, y_min)
    sensor.poll()

    cal = []

    # Genereate the calibration toolpath
    for x in range(x_min + sensor_offset_x, x_max + sensor_offset_x + x_step, x_step):
        for y in range(y_min, y_max, y_step):

            if ((x - sensor_offset_x)/x_step) %2 == 1:
                g.goTo(x, (y_max - y_step) - y, z_value)
            else:
                g.goTo(x, y, z_value)
                

            if y == y_min:
                sensor.poll() # clear out the first reading

            # Query the ToF sensor        
            distance = sensor.poll()
            y_val  = (axis_offset + sensor_offset_z) - distance
            print('Reading: ' + str(distance) + ' mm')
            cal.append([x - sensor_offset_x, y, y_val])

    # Write calibration to file
    filename = 'calibration.csv'
    print('Scan complete, writing results to ' + filename)
    
    with open(filename, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerows(cal)

    sensor.close()
    g.close()    

    print('Calibration file written, calibration routine complete') 

if __name__ == '__main__':
    main()
