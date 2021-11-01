import os
import sys
import csv
import cv2
import argparse
import numpy as np

def main():
    # Determine the correct calibration file to use
    calibration_path = 'calibration.csv'
    bit_offset_mm = 47
    axis_offset = 168

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help ='Image file to process')
    parser.add_argument('-c', '--calibrationFile', help ='Use path to supplied calibration file')
    parser.add_argument('-b', '--bitOffset', help ='Offset from the collet to the bit')
    args = parser.parse_args()

    # check for input file
    if args.file:
        if not os.path.exists(args.file): 
            sys.exit('ERROR: Input file %s does not exist' % args.file)
    else:
        sys.exit('ERROR: Input file not provided')
        
    # load in calibration file 
    if args.calibrationFile:
        print('Using calibration file at: %s' % args.calibrationFile)
        calibration_path = args.calibrationFile
    else:
        print('Using default calibration file at: %s' % calibration_path)

    calibration, x_max, x_min = ingest_calibration(calibration_path)
    x_height = x_max - x_min
    print('Calibration loaded sucessfully')

    # update the bit offset if needed
    if args.bitOffset:
        bit_offset_mm = int(args.bitOffset)
        print('Using supplied bit offset of %d' % bit_offset_mm)
    else:
        print('Using default bit offset of %d' % bit_offset_mm)

    # load input image
    img = cv2.imread(args.file)
    IMG_WIDTH = img.shape[1]
    IMG_HEIGHT = img.shape[0]

    # generate the pruned contours
    pruned_contours, contours = detect_contours(img)
    img_cont = draw_pruned_contours(img, pruned_contours, contours)

    # convert paths to pumkin coordinates
    paths = []
    for path in pruned_contours:
        path_mm = []
        for point in path:
            # convert to pumpkin space
            x_mm = ((IMG_HEIGHT - point[1]) * (x_height/IMG_HEIGHT)) + x_min
            y_mm = (IMG_WIDTH - point[0]) / (IMG_WIDTH/360)
            path_mm.append([x_mm, y_mm, 0]) 
        path_mm.append(path_mm[0]) # close the loop
        paths.append(path_mm)
    
    # generate toolpath from paths
    toolpath = generate_gcode(paths, calibration, bit_offset_mm, axis_offset)
    #TODO: use the name of the input file for the gcode
    
    # write gcode to file
    gcode_filename = 'output.gcode'
    f = open(gcode_filename, 'w')
    for line in toolpath:
        f.write(line)
    f.close()

    # show image
    cv2.imshow('Detected contours', img_cont)
    while True:
        if cv2.waitKey(33) == ord('q'):
            sys.exit('Closing...')

def ingest_calibration(filename):
    # TODO: return full calibration array with interpolated points
    raw = np.genfromtxt(filename, delimiter=',')
    
    # convert to mm/deg
    x_max = raw.max(axis=0)[0]
    x_min = raw.min(axis=0)[0]
    cal = np.full(shape = (int(x_max - x_min) + 1, 360), fill_value=-1 )

    for point in raw:
        cal[int(point[0] - x_min), int(point[1])] = point[2]
        # TODO: Fill out interpolated points 

    return raw, x_max, x_min

def detect_contours(img):
    # color transform
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    # detect contours
    contours, hierarchy = cv2.findContours(image=thresh, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)
    print('Detected %d contours' % len(contours))

    # Iterate through the contours to prune
    contour_num = 0
    pruned_contours = []
    for contour in contours:
        pruned_contour = contour.copy().squeeze()

        i = 0
        while i < len(pruned_contour) -2:
            p0 = pruned_contour[i]
            p1 = pruned_contour[i+1]
            p2 = pruned_contour[i+2]

            if collinearity_check( p0, p1, p2, 10): 
                pruned_contour = np.delete(pruned_contour, i+1, 0)
            else:
                i += 1

        print('Pruned contour %d from %d points to %d' % (contour_num, len(contour), len(pruned_contour)))
        pruned_contours.append(pruned_contour)
        contour_num += 1

    return pruned_contours, contours

def draw_pruned_contours(img, pruned_contours, contours):
    image_copy = img.copy()
    cv2.drawContours(image=image_copy, contours=contours, contourIdx=-1, color=(0, 255, 0), thickness=1, lineType=cv2.LINE_AA)
    cv2.drawContours(image=image_copy, contours=pruned_contours, contourIdx=-1, color=(255, 0, 0), thickness=1, lineType=cv2.LINE_AA)

    # interate through and draw the pruned verticies in red
    for contour in pruned_contours:
        for point in contour:
            cv2.circle( image_copy, (point[0], point[1]), 2, (0,0,255), 1)

    return image_copy

def collinearity_check(p0, p1, p2, epsilon = 1e-3):
    p0_ = np.insert(p0, 0, 1, axis =0)
    p1_ = np.insert(p1, 0, 1, axis =0)
    p2_ = np.insert(p2, 0, 1, axis =0)

    m = np.stack((p0_, p1_, p2_), 0)
    det = np.linalg.det(m)

    return abs(det) < epsilon

def generate_gcode(paths, cal, bit_offset, axis_offset):
    #TODO: Remove dependence on nominal cylinder and use actual calibration
    #TODO: add mechanism to pass parameters as an arguement efficiently

    # cut params
    cut_depth = 30
    cut_feed_x = 50    
    cut_feed_y = 0.5    
    cut_feed_diag = 50    
    fudge = 14 #TODO: calibrate ToF sensor and remove this value

    # find the z value that puts the bit in contact with the nominal cylinder
    r_nom = cal.max(axis=0)[2] + fudge
    z_surface = int(axis_offset - (bit_offset + r_nom))
    print('Nominal cylinder surface Z value: %d' % z_surface)

    gcode = [] 
    gcode.append('S10000\n') # set the spindle speed

    # process each contour
    for path in paths:
        
        # Add gcode to setup the contour
        gcode.append('G0 X%.3f Y%.3f Z%.3f\n' % (path[0][0], path[0][1], 0)) # Go to starting point at full speed
        gcode.append('M3\n') # Turn on spindle
        gcode.append('G0 Z%.3f\n' % z_surface) #plunge to surface

        # iterate over path at each depth
        for depth in range(z_surface, z_surface + cut_depth + 2, 2):
            prev_point = None
            for point in path:
                # determine the cut speed based on the direction
                feed = cut_feed_x

                if prev_point:
                    y_motion = prev_point[1] != point[1]
                    x_motion = prev_point[0] != point[0]

                    if y_motion and x_motion:
                        feed = cut_feed_diag
                    elif y_motion:
                        feed = cut_feed_y
                    elif x_motion:
                        feed = cut_feed_x

                # close the loop if needed and return to the first point
                gcode.append('G1 X%.3f Y%.3f Z%.3f F%.3f\n' % (point[0], point[1], depth, feed))

                prev_point = point
            
            # close the loop and head back to the first point 
            gcode.append('G1 X%.3f Y%.3f Z%.3f F%.3f\n' % (path[0][0], path[0][1], depth, cut_feed_y))

        # add the gcode to finish the contour
        gcode.append('G0 Z0\n') # retract spindle for travel
        gcode.append('M5\n') # disable spindle for travel

    # Finish by returning to the home position
    gcode.append('G0 X0 Y0 Z0\n')

    return gcode

if __name__ == '__main__':
    main()
