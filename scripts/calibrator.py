import sys
import grbl
import time
import DistanceSensor
import serial
import csv

def main():
    # Calibration bounds
    x_min = 0
    x_max = 120
    x_step = 10
    z_min = 0
    z_max = 360
    z_step = 10
    y_value = 0

    X_UPPER_LIMIT = 200
    sensor_offset = 38
    x_offset = 55
    y_axis_offset = 170

    if x_max + x_offset > X_UPPER_LIMIT:
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
    g.goTo(x_offset, y_value, z_min)
    sensor.poll()

    cal = []

    # Genereate the calibration toolpath
    for x in range(x_min + x_offset, x_max + x_offset + x_step, x_step):
        for z in range(z_min, z_max, z_step):

            # Go to the target pose
            if (x/x_step) % 2 == 1:
                g.goTo(x, y_value, (z_max-z_step) - z)
            else:
                g.goTo(x, y_value, z)

            if z == z_min:
                sensor.poll() # clear out the first reading

            # Query the ToF sensor        
            distance = sensor.poll()
            z_val  = (y_axis_offset + sensor_offset) - distance
            print('Reading: ' + str(distance) + ' mm')
            cal.append([x, z, z_val])

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
