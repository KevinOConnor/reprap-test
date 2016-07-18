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
import sys, math

# Ratio of e-steps to x/y steps, and extruder Z height.
FILAMENTWIDTH=1.75
EXTRUDEWIDTH=0.40
EXTRUDEZ=0.3
EXTRUSIONMULT=(EXTRUDEZ * EXTRUDEWIDTH) / (math.pi * (FILAMENTWIDTH/2)**2)
# Size of bed (used to center print after homing printer.
BEDX=200
BEDY=250
EXTRAZ=0.0
# Speeds, lengths, and counts for each extrusion test.
TESTSPEEDS=[20., 40., 60., 80., 100., 120.]
TESTLENGTH=20
TESTTRY=3

# Details of "ruler" markings at top and bottom.
LANEWIDTH=5.
RULERSPEED=10.
SEMICIRCLEPOINTS=10
# Speed and details of non-extrusion head movements
REPOSITIONSPEED=40.
REPOSITIONZSPEED=10.
REPOSITIONZ=1.0

STARTG="""
; This is a calibration print for testing extruder springiness.
G21
G90
G92 E0
"""

ENDG="""
M104 S0 ; turn off temperature
M140 S0 ; turn of HBP
M84     ; disable motors
"""

class ToolPos:
    baseX = baseY = 0.
    currentX = currentY = currentE = 0.

def output(msg):
    sys.stdout.write(msg + "\n")

def setspeed(speed):
    output("G1 F%f" % (speed*60.,))

def moveabs(coord, x, y, e=None):
    if e is None:
        output("G1 X%f Y%f" % (coord.baseX + x, coord.baseY + y))
        coord.currentX = x
        coord.currentY = y
    else:
        output("G1 X%f Y%f E%f" % (coord.baseX + x, coord.baseY + y, e))
        coord.currentX = x
        coord.currentY = y
        coord.currentE = e

def moverel(coord, x, y, ext=None):
    if ext is not None:
        ext = coord.currentE + math.sqrt(x*x+y*y)*EXTRUSIONMULT
    moveabs(coord, coord.currentX + x, coord.currentY + y, ext)

def semicircle(coord, x, y, ext=None):
    startx, starty = coord.currentX, coord.currentY
    rads = math.pi / (SEMICIRCLEPOINTS+1)
    for i in range(SEMICIRCLEPOINTS):
        pos = rads * (i+1)
        xpos, ypos = math.sin(pos) * x, math.cos(pos) * -y/2. + y/2.
        moverel(coord, startx+xpos-coord.currentX, starty+ypos-coord.currentY
                , ext)
    moverel(coord, startx-coord.currentX, starty+y-coord.currentY, ext)

def reposition(coord, x, y):
    setspeed(REPOSITIONZSPEED)
    output("G1 Z%f" % (EXTRUDEZ+EXTRAZ+REPOSITIONZ,))
    setspeed(REPOSITIONSPEED)
    moveabs(coord, x, y)
    setspeed(REPOSITIONZSPEED)
    output("G1 Z%f" % (EXTRUDEZ+EXTRAZ,))

def main():
    numlanes = len(TESTSPEEDS)
    totaly = (numlanes * 2 + 1 + 3) * LANEWIDTH
    totalx = TESTLENGTH * (TESTTRY*2 + 1) + 4 * LANEWIDTH
    coord = ToolPos()
    coord.baseX = (BEDX-totalx)/2.
    coord.baseY = (BEDY-totaly)/2.

    output(STARTG)
    output("; Prime extruder")
    reposition(coord, 0, 0)
    setspeed(RULERSPEED)
    moverel(coord, totalx-LANEWIDTH, 0, ext=1)

    semicircle(coord, LANEWIDTH, 2*LANEWIDTH, ext=1)
    moverel(coord, -LANEWIDTH, 0, ext=1)

    output("; Start ruler")
    for i in range(TESTTRY):
        moverel(coord, 0, -LANEWIDTH, ext=1)
        moverel(coord, -TESTLENGTH, 0, ext=1)
        moverel(coord, 0, LANEWIDTH, ext=1)
        moverel(coord, -TESTLENGTH, 0, ext=1)
    moverel(coord, 0, -LANEWIDTH, ext=1)
    moverel(coord, -TESTLENGTH, 0, ext=1)
    moverel(coord, 0, LANEWIDTH, ext=1)
    moverel(coord, -LANEWIDTH, 0, ext=1)

    semicircle(coord, -LANEWIDTH/2.0, LANEWIDTH, ext=1)
    moverel(coord, LANEWIDTH, 0, ext=1)

    for i in range(numlanes):
        output("; Start run %d" % (i,))
        setspeed(TESTSPEEDS[i])
        for j in range(TESTTRY):
            moverel(coord, TESTLENGTH, 0)
            moverel(coord, TESTLENGTH, 0, ext=1)
        moverel(coord, TESTLENGTH, 0)

        setspeed(RULERSPEED)
        moverel(coord, LANEWIDTH, 0, ext=1)
        semicircle(coord, LANEWIDTH/2.0, LANEWIDTH, ext=1)
        moverel(coord, -LANEWIDTH, 0, ext=1)

        setspeed(TESTSPEEDS[i])
        for j in range(TESTTRY):
            moverel(coord, -TESTLENGTH, 0)
            moverel(coord, -TESTLENGTH, 0, ext=1)
        moverel(coord, -TESTLENGTH, 0)

        setspeed(RULERSPEED)
        moverel(coord, -LANEWIDTH, 0, ext=1)
        semicircle(coord, -LANEWIDTH/2.0, LANEWIDTH, ext=1)
        moverel(coord, LANEWIDTH, 0, ext=1)

    output("; Start ruler")
    for i in range(TESTTRY):
        moverel(coord, 0, LANEWIDTH, ext=1)
        moverel(coord, TESTLENGTH, 0, ext=1)
        moverel(coord, 0, -LANEWIDTH, ext=1)
        moverel(coord, TESTLENGTH, 0, ext=1)
    moverel(coord, 0, LANEWIDTH, ext=1)
    moverel(coord, TESTLENGTH, 0, ext=1)
    moverel(coord, 0, -LANEWIDTH, ext=1)
    moverel(coord, LANEWIDTH*2, 0, ext=1)

    output(ENDG)

if __name__ == '__main__':
    main()
