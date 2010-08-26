#!/usr/bin/env python

from TrackPlot import *			# for plotting tracks
from TrackFileUtils import *		# for reading track files
from TrackUtils import *		# for CreateSegments(), FilterMHTTracks(), DomainFromTracks()
import ParamUtils           # for ReadSimulationParams()

import argparse                         # Command-line parsing
import os				# for os.sep.join()
import glob				# for globbing
import matplotlib.pyplot as pyplot


parser = argparse.ArgumentParser(description="Produce an animation of the tracks")
parser.add_argument("trackFiles", nargs='*',
                    help="Use TRACKFILE for track data",
                    metavar="TRACKFILE")
parser.add_argument("-t", "--truth", dest="truthTrackFile",
                  help="Use TRUTHFILE for true track data",
                  metavar="TRUTHFILE", default=None)
parser.add_argument("-d", "--dir", dest="directory",
          help="Base directory to work from when using --simName",
          metavar="DIRNAME", default=".")
parser.add_argument("-s", "--simName", dest="simName",
          help="Use data from the simulation SIMNAME",
          metavar="SIMNAME", default=None)

args = parser.parse_args()

# FIXME: Currently, the code allows for trackFiles to be listed as well
#        as providing a simulation (which trackfiles are automatically grabbed).
#        Both situations can not be handled right now, though.
trackFiles = []
trackTitles = []

if args.simName is not None :
    simParams = ParamUtils.ReadSimulationParams(os.sep.join([args.directory + os.sep + args.simName, "simParams.conf"]))
    trackFiles = [args.directory + os.sep + simParams['result_file'] + '_' + aTracker for aTracker in simParams['trackers']]
    trackTitles = simParams['trackers']

    if args.truthTrackFile is None :
        args.truthTrackFile = args.directory + os.sep + simParams['noisyTrackFile']

trackFiles += args.trackFiles
trackTitles += args.trackFiles


if len(trackFiles) == 0 : print "WARNING: No trackFiles given or found!"

trackerData = [FilterMHTTracks(*ReadTracks(trackFile)) for trackFile in trackFiles]


# TODO: Dependent on the assumption that I am doing a comparison between 2 trackers
theFig = pyplot.figure(figsize = (11, 5))

# store the animations in this list to prevent them from going out of scope and GC'ed
anims = []

# A common timer for all animations for syncing purposes.
theTimer = None

if args.truthTrackFile is not None :
    (true_tracks, true_falarms) = FilterMHTTracks(*ReadTracks(args.truthTrackFile))

    (xLims, yLims, tLims) = DomainFromTracks(true_tracks + true_falarms)

    true_AssocSegs = CreateSegments(true_tracks)
    true_FAlarmSegs = CreateSegments(true_falarms)

    for (index, aTracker) in enumerate(trackerData) :
        trackAssocSegs = CreateSegments(aTracker[0])
        trackFAlarmSegs = CreateSegments(aTracker[1])
        truthtable = CompareSegments(true_AssocSegs, true_FAlarmSegs, trackAssocSegs, trackFAlarmSegs)

        curAxis = theFig.add_subplot(1, len(trackFiles), index + 1)

        l = Animate_Segments(truthtable, tLims, axis=curAxis, speed=0.1, loop_hold=3.0, event_source=theTimer)

        if theTimer is None :
            theTimer = l.event_source

        anims.append(l)

        curAxis.set_xlim(xLims)
        curAxis.set_ylim(yLims)
        curAxis.set_aspect("equal", 'datalim')
        curAxis.set_title(trackTitles[index])
        curAxis.set_xlabel("X")
        curAxis.set_ylabel("Y")


else :
    for (index, aTracker) in enumerate(trackerData) :
        # TODO: Need to have consistent domains, maybe?
        (xLims, yLims, tLims) = DomainFromTracks(aTracker[0] + aTracker[1])
	
        curAxis = theFig.add_subplot(1, len(trackFiles), index + 1)
        curAxis.hold(True)

        l = Animate_PlainTracks(aTracker[0], aTracker[1], tLims, axis=curAxis, speed=0.1, loop_hold=3.0, event_source=theTimer)
        
        if theTimer is None :
            theTimer = l.event_source

        anims.append(l)
	    

        curAxis.set_xlim(xLims)
        curAxis.set_ylim(yLims)
        curAxis.set_aspect("equal", 'datalim')
        curAxis.set_title(trackTitles[index])
        curAxis.set_xlabel("X")
        curAxis.set_ylabel("Y")

pyplot.show()
