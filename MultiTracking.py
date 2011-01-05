#!/usr/bin/env python

import os
import Trackers
from DoTracking import SingleTracking
import ParamUtils     # for reading simParams files
from ListRuns import Sims_of_MultiSim

def MultiTrack(multiSim, trackConfs, path='.') :
    simNames = Sims_of_MultiSim(multiSim, path)
    multiDir = path + os.sep + multiSim

    for simName in simNames :
        print "Sim:", simName
        paramFile = multiDir + os.sep + simName + os.sep + "simParams.conf"
        simParams = ParamUtils.ReadSimulationParams(paramFile)

        # A copy of trackConfs is used here because the tracker calls could
        # modify the contents of trackConfs, and we don't want those changes
        # to propagate to subsequent calls to SingleTracking()
        SingleTracking(paramFile, simParams, trackConfs.copy(), path=multiDir)


if __name__ == '__main__' :
    import argparse       # Command-line parsing


    parser = argparse.ArgumentParser(description='Track the given centroids')
    parser.add_argument("multiSim",
                      help="Generate Tracks for MULTISIM",
                      metavar="MULTISIM")
    parser.add_argument("trackconfs", nargs='+',
                      help="Config files for the parameters for the trackers",
                      metavar="CONF")
    parser.add_argument("-d", "--dir", dest="directory",
                        help="Base directory to find MULTISIM",
                        metavar="DIRNAME", default='.')

    args = parser.parse_args()

    trackConfs = ParamUtils.LoadTrackerParams(args.trackconfs)
    MultiTrack(args.multiSim, trackConfs.dict(), path=args.directory)


