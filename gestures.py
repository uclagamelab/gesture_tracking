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


help_message = '''
Use -l, --limits to set the min and max limits for the sensor

Use -c or --calibrate with additional flags
-a, --attack
-b, --build
-s, --scan

'''

# global stuff

# ser = serial.Serial('/dev/tty.usbserial-A7004INu', 9600)
# ser.flush()

# these are used to define the limits of the sensor
maxData = [0,0,0]
minData = [255,255,255]
areas = {}

#positions
currentPosition = (0,0,0)
lastPosition = (0,0,0)

# #patterns
# attack = initPattern(1)
# scan = initPattern(1)
# build = initPattern(1)
# sampleData = initPattern(1)



class Usage(Exception):
	def __init__(self, msg):
		self.msg = msg


def main(argv=None):
	if argv is None:
		argv = sys.argv
	try:
		try:
			opts, args = getopt.getopt(argv[1:], "h:casbvl", ["help", "calibrate", "attack", "build", "scan", "limits"])
		except getopt.error, msg:
			raise Usage(msg)
		
		# option processing
		for option, value in opts:
			
			if option == "-v":
				verbose = True
			
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
	atexit.register(resetLimits)
	while 1:
		try:
			data = ser.readline().split()
			for i in range(len(data)):
				data[i] = int(data[i])
				
			findRange(data, minData, maxData)
			printResults(minData, maxData)
			
		except (KeyboardInterrupt, SystemExit):
			raise
			
		except:
			sys.exit("bad serial data")			





def getSampleData(samples):
	"""
	Follow the position of the sensor, increment time series only when position has left a region (creted in resetlimits)
	Returns a nested dictionary with tuples for keys
	To find the number of times the sensor has transitioned from one region to another, access the dictionary
	with the before and after regions as tuples, eg:
	number of times sensor transitioned from one region to another = sampleData[0,2,1][2,0,1]
	"""
	temp = initPattern()
	
	if counter < samples:
		data = ser.readline().split()
		for i in range(len(data)):
			data[i] = int(data[i])
		
		setCurrentPosition()
		
		if(currentPosition != lastPosition):
		    currentPosition = lastPosition
		    counter+=1
		    updateSampleData()

		
		

def findRange(data, minData, maxData):
	for i in range(len(maxData)):
		if data[i] < 255 and data[i] > maxData[i]:
			maxData[i] = data[i]
		
		if data[i] < minData[i]:
			minData[i] = data[i]


def printResults(minData, maxData):
	os.system('clear')
	print minData
	print maxData


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
	"""Quantize the range on each axis of the accelerometer, save range and areas to three seperate pickles
	
	areas is a dictionary that defines the minimum, 1/3, 2/3 and maximum of the range on each axsis of the accelererometer
	
	"""
	xRange = maxData[0] - minData[0]
	yRange = maxData[1] - minData[1]
	zRange = maxData[2] - minData[2]
	
	areas["x"] = (minData[0], minData[0] + (xRange/3), minData[0] + (xRange/3)*2, maxData[0])
	areas["y"] = (minData[1], minData[1] + (yRange/3), minData[1] + (yRange/3)*2, maxData[1])
	areas["z"] = (minData[2], minData[2] + (zRange/3), minData[2] + (zRange/3)*2, maxData[2])
	
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
