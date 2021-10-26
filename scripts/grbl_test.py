import grbl
import time
import calibration
import serial

# Setup ToF
tof_port = serial.Serial(port ='/dev/ttyACM1', baudrate=115200)

# Connect to controller
g = grbl.grbl('/dev/ttyACM0')
g.wake()
g.home()

# Calibration bounds
x_min = 0
x_max = 100
x_step = 10
z_min = 0
z_max = 360
z_step = 10
y_value = 0

cal = []

# Genereate the calibration toolpath
for x in range(x_min, x_max, x_step):
    for z in range(z_min, z_max, z_step):

        # Go to the target pose
        if (x/x_step) % 2 == 1:
            g.goTo(x, y_value, (z_max-z_step) - z)
        else:
            g.goTo(x, y_value, z)

        # Query the ToF sensor        
        distance = calibration.poll_data(tof_port)
        print('Reading: ' + str(distance) + ' mm')
        cal.append([x, z, distance])
