#!/usr/bin/env python
# Script to generate a g-code test to measure "extruder springiness".
#
# Copyright (C) 2012  Kevin O'Connor <kevin@koconnor.net>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
#
# This script will generate g-code.  To use run:
#  ./test-extruder-spring.py > test.g
# Before running the g-code be sure to inspect and modify at least the
# EXTRUSIONMULT, EXTRUDEZ, BEDX, and BEDY variables.  It is also
# recommended to inspect the output g-code to validate it makes sense
# for the printer it will be run on.
import math

# Ratio of e-steps to x/y steps, and extruder Z height.
EXTRUSIONMULT=(.375**2)/(1.75**2)
EXTRUDEZ=0.3
# Size of bed (used to center print after homing printer.
BEDX=200
BEDY=250
# Speeds, lengths, and counts for each extrusion test.
TESTSPEEDS=[20., 40., 60., 80., 100., 120.]
TESTLENGTH=20
TESTTRY=3

# Details of "ruler" markings at top and bottom.
LANEWIDTH=5
RULERWIDTH=5
RULERSPEED=10.
# Speed and details of non-extrusion head movements
REPOSITIONSPEED=40.
REPOSITIONZSPEED=10.
REPOSITIONZ=1.3
# Time (in ms) to wait before/after an extrusion.
ENDDWELL=500
STARTDWELL=500

STARTG="""
; This is a calibration print for testing extruder springiness.
G90
G28
G92 X0 Y0 Z0 E0
"""

ENDG="""
M104 S0 ; turn off temperature
M140 S0 ; turn of HBP
M84     ; disable motors
"""

class ToolPos:
    baseX = baseY = 0.
    currentX = currentY = currentE = 0.

def setspeed(speed):
    print "G1 F%f" % (speed*60.,)

def moveabs(coord, x, y, e=None):
    if e is None:
        print "G1 X%f Y%f" % (coord.baseX + x, coord.baseY + y)
        coord.currentX = x
        coord.currentY = y
    else:
        print "G1 X%f Y%f E%f" % (coord.baseX + x, coord.baseY + y, e)
        coord.currentX = x
        coord.currentY = y
        coord.currentE = e

def moverel(coord, x, y, ext=None):
    if ext is not None:
        ext = coord.currentE + math.sqrt(x*x+y*y)*EXTRUSIONMULT
    moveabs(coord, coord.currentX + x, coord.currentY + y, ext)

def reposition(coord, x, y):
    print "G4 P%d" % (ENDDWELL,)
    setspeed(REPOSITIONZSPEED)
    print "G1 Z%f" % (REPOSITIONZ,)
    setspeed(REPOSITIONSPEED)
    moveabs(coord, x, y)
    setspeed(REPOSITIONZSPEED)
    print "G1 Z%f" % (EXTRUDEZ,)
    print "G4 P%d" % (STARTDWELL,)

def main():
    numlanes = len(TESTSPEEDS)
    totaly = (numlanes * 2 + 1) * LANEWIDTH + 3 * RULERWIDTH
    totalx = TESTLENGTH * (TESTTRY*2 + 1)
    coord = ToolPos()
    coord.baseX = (BEDX-totalx)/2.
    coord.baseY = (BEDY-totaly)/2.
    teststartx = totalx/2
    testendx = -teststartx

    print STARTG
    print "; Prime extruder"
    reposition(coord, totalx, totaly)
    setspeed(RULERSPEED)
    moverel(coord, -totalx, 0, ext=1)

    print "; Start ruler"
    rulery = totaly-RULERWIDTH*2
    for i in range(TESTTRY*2):
        reposition(coord, (i+1)*TESTLENGTH, rulery)
        setspeed(RULERSPEED)
        moverel(coord, 0, RULERWIDTH, ext=1)

    for i in range(numlanes):
        print "; Start run %d" % (i,)
        reposition(coord, totalx, rulery-(i*2+1)*LANEWIDTH)
        setspeed(TESTSPEEDS[i])
        for j in range(TESTTRY):
            moverel(coord, -TESTLENGTH, 0)
            moverel(coord, -TESTLENGTH, 0, ext=1)
        moverel(coord, -TESTLENGTH, 0)
        reposition(coord, 0, rulery-(i*2+2)*LANEWIDTH)
        setspeed(TESTSPEEDS[i])
        for j in range(TESTTRY):
            moverel(coord, TESTLENGTH, 0)
            moverel(coord, TESTLENGTH, 0, ext=1)
        moverel(coord, TESTLENGTH, 0)

    print "; Start ruler"
    rulery = RULERWIDTH
    for i in range(TESTTRY*2):
        reposition(coord, totalx-(i+1)*TESTLENGTH, rulery)
        setspeed(RULERSPEED)
        moverel(coord, 0, -RULERWIDTH, ext=1)
    print ENDG

if __name__ == '__main__':
    main()
