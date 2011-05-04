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
import time
from copy import deepcopy


help_message = '''
Use -l, --limits to set the min and max limits for the sensor
Use -c or --calibrate with name of pattern you want to calibrate
e.g. scan, build or attack


-l, --limits will set the range of the accelerometer
-g, --getSample will take sample data and compare it with save patterns
'''

# global stuff
try:
#    ser = serial.Serial('/dev/tty.usbserial-A7004INu', 9600)
    ser = serial.Serial('/dev/ttyUSB0', 9600)
    ser.readline()
    ser.readline()
    ser.readline()
    ser.flush()
except serial.serialutil.SerialException as detail:
    print 'Serial error:', detail

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
            opts, args = getopt.getopt(argv[1:], "hc:lm", ["help", "calibrate=", "limits", "match"])
        except getopt.error, msg:
            raise Usage(msg)
            
        for option, value in opts:
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option in ("-c", "--calibrate"):
                calibratePattern(value)
            if option in ("-l", "--limits"):
                defineLimits()
            if option in ("-m", "match"):
                matchPattern()
                
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 2


def calibratePattern(pattern):
    try:
        tempPattern = loadPattern("pickles/"+pattern+"Pattern.pickle")
    except IOError:
        print "can't find saved data"
        tempPattern = None

    if tempPattern: tempPattern = getSampleData(100,tempPattern)
    else: tempPattern = getSampleData(100)

    print "pattern calibrated"
    savePattern(tempPattern, "pickles/"+pattern+"Pattern.pickle")



def matchPattern():
    attackRight = loadPattern("pickles/attackRightPattern.pickle")
    attackLeft = loadPattern("pickles/attackLeftPattern.pickle")
    scan = loadPattern("pickles/scanPattern.pickle")
    build = loadPattern("pickles/buildPattern.pickle")
    bestFit = {}
    sample = None
    while 1:
        sample = getSampleData(2, sample)
        bestFit['attackRight'] = patternDifference(sample, attackRight)
        bestFit['attackLeft'] = patternDifference(sample, attackLeft)
        bestFit['build'] = patternDifference(sample, build)
        bestFit['scan'] = patternDifference(sample, scan)
        print min(bestFit, key=bestFit.get)

def patternDifference(a,b):
    totalDifference = float(sys.maxint)
    for i in a.keys():
        for j in a[i].keys():
            totalDifference -= abs( a[i][j] - b[i][j] )
    totalDifference = sys.maxint - totalDifference
    return totalDifference



def defineLimits():
    """
    Run this function to find the limits of the accelerometer. Constantly reads the values and keeps track of the min
    and mac on each access. When keyboard interrupts, the min and max values are used to create a range and three regions
    on each axis. the regions are used later on when creating patterns and sample data
    """
    atexit.register(resetLimits)
    while 1:
        data = readSerial()
        for i in range(len(maxData)):
            if data[i] < 255 and data[i] > maxData[i]:
                maxData[i] = data[i]

            if data[i] < minData[i]:
                minData[i] = data[i]
                
        printResults(minData, maxData)
        



def getSampleData(sampleLength, averageSoFar=None):
    """
    Get some sample data in the form of a nested dictionary.m length
    Value is the percentage of times a transition happened, transition is defined in the dictionary
    Keys of dictionaries are tuples that represent spacial coordinates.
    """
    sampleData = initPattern(1)
    lastPosition = (0,0,0)
    areas = loadPattern("pickles/areas.pickle")
    counter = 0
    while counter < sampleLength:
        data = readSerial()            
        keys = ['x', 'y', 'z']
        data = {'x': data[0], 'y': data[1], 'z': data[2]}
        results = {}
        for k in keys:
            if data[k] < areas[k][0]: results[k] = 0
            elif data[k] < areas[k][1]: results[k] = 1
            else: results[k] = 2

        currentPosition = (results['x'], results['y'], results['z'])
                
        if lastPosition != currentPosition:
            #print "here is current position: " + repr(currentPosition)
            sampleData[lastPosition][currentPosition]+=1
            lastPosition = currentPosition
            counter+=1

    
    #print "done taking samples"
    temp = deepcopy(sampleData)
    for i in temp.keys():
        for j in temp[i].keys():
            sampleData[i][j] = temp[i][j] / float(sampleLength)
    if averageSoFar:
        temp = deepcopy(sampleData)
        for i in temp.keys():
            for j in temp[i]:
                sampleData[i][j] = (temp[i][j] + averageSoFar[i][j]) / 2.0
    return sampleData
    #savePattern(sampleData, "pickles/sampleData.pickle")


def readSerial():
        try:
            data = ser.readline()
        except (KeyboardInterrupt, SystemExit):
            raise
        except serial.serialutil.SerialException as detail:
            print 'Serial error:', detail
        else:
            data = data.split()
            for i in range(len(data)): data[i] = int(data[i])
            return data

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

    savePattern(areas, "pickles/areas.pickle")
    print "everything saved"

def loadLimits():
    areas = loadPattern("pickles/areas.pickle")
    return areas



if __name__ == "__main__":
    sys.exit(main())
