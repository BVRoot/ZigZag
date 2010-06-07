#!/usr/bin/env python

from TrackPlot import *			# for plotting tracks
from TrackFileUtils import *		# for reading track files
from TrackUtils import *		# for CreateSegments(), FilterMHTTracks(), DomainFromTracks()

from optparse import OptionParser	# Command-line parsing
import os				# for os.sep.join()
import glob				# for globbing
import pylab

parser = OptionParser()
parser.add_option("-t", "--truth", dest="truthTrackFile",
                  help="Use TRUTHFILE for true track data",
                  metavar="TRUTHFILE", default=None)

(options, args) = parser.parse_args()

if len(args) == 0 : print "WARNING: No trackFiles listed!"


trackerData = [FilterMHTTracks(*ReadTracks(trackFile)) for trackFile in args]


# TODO: Dependent on the assumption that I am doing a comparison between 2 trackers
theFig = pylab.figure(figsize = (11, 6))

if options.truthTrackFile is not None :
    (true_tracks, true_falarms) = FilterMHTTracks(*ReadTracks(options.truthTrackFile))

    (xLims, yLims, tLims) = DomainFromTracks(true_tracks + true_falarms)

    true_AssocSegs = CreateSegments(true_tracks)
    true_FAlarmSegs = CreateSegments(true_falarms)

#    trackerAssocSegs = [CreateSegments(trackerTracks[0]) for trackerTracks in trackerData]
#    trackerFAlarmSegs = [CreateSegments(trackerTracks[1]) for trackerTracks in trackerData]

    for (index, aTracker) in enumerate(trackerData) :
	trackAssocSegs = CreateSegments(aTracker[0])
	trackFAlarmSegs = CreateSegments(aTracker[1])
        truthtable = CompareSegments(true_AssocSegs, true_FAlarmSegs, trackAssocSegs, trackFAlarmSegs)

        curAxis = theFig.add_subplot(1, len(args), index + 1)

	# We can only animate one set of axes using the current code,
	# so animate the first axes.
        if index == 0 :
            Animate_Segments(truthtable, xLims, yLims, tLims, axis = curAxis, speed = 0.1, hold_loop = 3.0)
        else :
            PlotSegments(truthtable, xLims, yLims, tLims, axis = curAxis)

        #curAxis.axis("equal")
        curAxis.set_title(args[index])
        curAxis.set_xlabel("X [km]")
        curAxis.set_ylabel("Y [km]")


else :
    for (index, aTracker) in enumerate(trackerData) :
        # TODO: Need to have consistent domains, maybe?
        (xLims, yLims, tLims) = DomainFromTracks(aTracker[0] + aTracker[1])
	
        curAxis = theFig.add_subplot(1, len(args), index + 1)
        curAxis.hold(True)

	# We can only animate one set of axes using the current code,
	# so animate the first axes.
	if index == 0 :
	    theLines = []
            theLines += PlotTrack(aTracker[0], xLims, yLims, tLims, axis = curAxis,
		                  marker = '.', markersize = 6.0, color = 'k', linewidth = 1.5, animated = True)
	    theLines += PlotTrack(aTracker[1], xLims, yLims, tLims, axis = curAxis,
		                  marker = '.', markersize = 6.0, linestyle = ' ', color = 'r', animated = True)
	    AnimateLines(theLines, aTracker[0] + aTracker[1], min(tLims), max(tLims), axis = curAxis)
	else :
            PlotTrack(aTracker[0], xLims, yLims, tLims, axis = curAxis,
		              marker = '.', markersize = 6.0, color = 'k', linewidth = 1.5)
	    PlotTrack(aTracker[1], xLims, yLims, tLims, axis = curAxis,
		              marker = '.', markersize = 6.0, linestyle = ' ', color = 'r')
	    

#        curAxis.axis("equal")
        curAxis.set_title(args[index])
        curAxis.set_xlabel("X [km]")
	curAxis.set_ylabel("Y [km]")

pylab.show()