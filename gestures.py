#!/usr/bin/env python
# encoding: utf-8
"""
gestures.py

"""

import os
import sys
import getopt
import serial
import pickle
import atexit
from copy import deepcopy


help_message = '''
Use -l, --limits to set the min and max limits for the sensor
Use -c or --calibrate with additional flags
-a, --attack
-b, --build
-s, --scan
'''

# global stuff
try:
    ser = serial.Serial('/dev/tty.usbserial-A7004INu', 9600)
    ser.flush()
except:
    print "cant connect to serial"

# these are used to define the limits of the sensor
maxData = [0,0,0]
minData = [255,255,255]
areas = {}

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hg:casbl", ["help", "calibrate", "attack", "build", "scan", "limits", "getSample="])
        except getopt.error, msg:
            raise Usage(msg)
            
        for option, value in opts:
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option in (("-c", "--calibrate") and ("-a", "--attack")):
                calibrateAttack()
            if option in (("-c", "--calibrate") and ("-b", "--build")):
                calibrateBuild()
            if option in (("-c", "--calibrate") and ("-s", "--scan")):
                calibrateScan()
            if option in ("-l", "--limits"):
                defineLimits()
            if option in ("-g", "--getSample"):
                getSampleData(value)
                
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 2

def calibrateAttack():
    print "calibrate attack"

def calibrateBuild():
    print "calibrate build"
    minData, maxData, areas = loadLimits()
    print minData
    print maxData
    print areas

def calibrateScan():
    print "calibrate scan"


def defineLimits():
    """
    Run this function to find the limits of the accelerometer. Constantly reads the values and keeps track of the min
    and mac on each access. When keyboard interrupts, the min and max values are used to create a range and three regions
    on each axis. the regions are used later on when creating patterns and sample data
    """
    atexit.register(resetLimits)
    while 1:
        try:
            ser.flush()
            data = ser.readline().split()
            for i in range(len(data)):
                data[i] = int(data[i])
                
                # findRange(data, minData, maxData)
            for i in range(len(maxData)):
                if data[i] < 255 and data[i] > maxData[i]:
                    maxData[i] = data[i]
                
                if data[i] < minData[i]:
                    minData[i] = data[i]
            
            printResults(minData, maxData)
        
        except (KeyboardInterrupt, SystemExit):
            raise
        
        except NameError:
            sys.exit("bad serial data")


def getSampleData(sampleLength):
    """
    Follow the position of the sensor, increment time series only when position has left a region (created in resetLimits)
    Returns a nested dictionary with tuple for keys
    To find the number of times the sensor has transitioned from one region to another, access the dictionary
    with the before and after regions as tuples, eg:
    number of times sensor transitioned from one region to another = sampleData[0,2,1][2,0,1]
    """
    #TODO Need to take sampleData and transform totals to percentage by dividing the number of occurances by sampleLength
    sampleData = initPattern(1)
    lastPosition = (0,0,0)
    areas = loadPattern("pickles/areas.pickle")
    counter = 0
    while counter < sampleLength:
        try:
            ser.flush()
            rawData = ser.readline().split()
        except:
            rawData = None
            print "can't read serial"
        if rawData:
            for i in range(len(rawData)): rawData[i] = int(rawData[i])
            
        keys = ["x","y","z"]
        data = {"x":rawData[0], "y":rawData[1], "z":rawData[2]}
        results = {}
        for k in keys:          
            for index, value in enumerate(areas[k]):
                if data[k] < value:
                    results[k] = index
                else: results[k] = 2
        
        currentPosition = (results['x'], results['y'], results['z'])
                
        if lastPosition != currentPosition:
            print "here is current position: " + repr(currentPosition)
            sampleData[lastPosition][currentPosition]+=1
            currentPosition = lastPosition
            counter+=1
    print "done taking samples"
    temp = deepcopy(sampleData)
    for i1, v1 in enumerate(temp):
        for i2, v2 in enumerate(v1):
            sampleData[i1][i2] = temp[i1][i2] / sampleLength
    savePattern(sampleData, "pickles/sampleData.pickle")


def printResults(*arg):
    os.system('clear')
    for value in arg:
        print repr(value)



def savePattern(pattern, fileName):
    with open(str(fileName), 'wb') as f:
        pickle.dump(pattern, f)


def loadPattern(fileName):
    with open(str(fileName), 'rb') as f:
        return pickle.load(f)


def initPattern(level):
    p = {}
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if level > 0:
                    p[i,j,k] = initPattern(level-1)
                else:
                    p[i,j,k] = 0
                    
    return p

def resetLimits():
    """
    Quantize the range on each axis of the accelerometer, save range and areas to three seperate pickles
    areas is a dictionary that defines the minimum, 1/3, 2/3 and maximum of the range on each axsis of the accelererometer
    
    """
    xRange = maxData[0] - minData[0]
    yRange = maxData[1] - minData[1]
    zRange = maxData[2] - minData[2]
    
    areas["x"] = (minData[0] + (xRange/3), minData[0] + (xRange/3)*2)
    areas["y"] = (minData[1] + (yRange/3), minData[1] + (yRange/3)*2)
    areas["z"] = (minData[2] + (zRange/3), minData[2] + (zRange/3)*2)
    
    savePattern(minData, "pickles/minData.pickle")
    savePattern(maxData, "pickles/maxData.pickle")
    savePattern(areas, "pickles/areas.pickle")
    print "everything saved"

def loadLimits():
    minData = loadPattern("pickles/minData.pickle")
    maxData = loadPattern("pickles/maxData.pickle")
    areas = loadPattern("pickles/areas.pickle")
    return minData, maxData, areas



if __name__ == "__main__":
    sys.exit(main())
