#!/usr/bin/env python


import ZigZag.TrackUtils as TrackUtils			# for ClipTracks(), CreateVolData(), CleanupTracks(), track_dtype
import numpy as np				# for Numpy
import os				# for os.makedirs(), os.path.exists()

import ZigZag.Sim as Sim
import ZigZag.ParamUtils as ParamUtils     # for SaveSimulationParams(), SetupParser()
from ZigZag.TrackFileUtils import *		# for writing the track data


###################################################
#  Track Maker Functions
trackMakers = {}

def MakeTrack(cornerID, initModel, motionModel, deltaT, probTrackEnds, maxLen) :
    aPoint = Sim.TrackPoint(cornerID, probTrackEnds, deltaT,
                            initModel, motionModel, maxLen)
    return np.fromiter(aPoint, TrackUtils.track_dtype)

trackMakers['MakeTrack'] = MakeTrack
#################################################


def MakeTracks(trackGens, noiseModels,
               procParams, currGen, trackCnt,
               deltaT, prob_track_ends, maxTrackLen,
               cornerID=0, simState=None, trackTags=None) :
    theTracks = []
    theFAlarms = []

    noisesToApply = procParams.get('noises', [])
    trackCnt = int(procParams.get('cnt', trackCnt))
    prob_track_ends = float(procParams.get('prob_track_ends', prob_track_ends))
    maxTrackLen = int(procParams.get('maxTrackLen', maxTrackLen))

    if simState is None :
        simState = {'theTracks': [],
                    'theFAlarms': [],
                    'theTrackLens': []}

    # Generate this model's set of tracks
    startID = cornerID
    tracks, falarms, cornerID = currGen(cornerID, trackCnt, simState,
                                        deltaT, prob_track_ends, maxTrackLen)
    if trackTags is not None :
        trackTags['ids'] = range(startID, cornerID)

    TrackUtils.CleanupTracks(tracks, falarms)
    trackLens = [len(aTrack) for aTrack in tracks]

    # Add them to this node's set of tracks
    theTracks.extend(tracks)
    theFAlarms.extend(falarms)

    # Add them to this branch's set tracks
    # currState collects the tracks in a way that
    # any subnodes are aware of those tracks.
    # This "memory" does not carry across parallel branches.
    currState = {'theTracks': simState['theTracks'] + tracks,
                 'theFAlarms': simState['theFAlarms'] + falarms,
                 'theTrackLens': simState['theTrackLens'] + trackLens}

    # Loop over the node's sub-branch generators
    for aGen in procParams.sections :
        # Recursively perform track simulations using this loop's simulation
        #   This is typically done to restrict splits/merges on only the
        #   storm tracks and allow for clutter tracks to be made without
        #   any splitting/merging done upon them.
        # This will also allow for noise models to be applied to specific
        #   subsets of the tracks.
        subTags = {} if trackTags is not None else None

        (subTracks, subFAlarms,
         cornerID) = MakeTracks(trackGens, noiseModels,
                                procParams[aGen],
                                trackGens[aGen], trackCnt,
                                deltaT, prob_track_ends, maxTrackLen,
                                cornerID, currState, trackTags=subTags)

        if trackTags is not None :
            trackTags[aGen] = subTags

        # Add this branch's tracks to this node's set of tracks
        theTracks.extend(subTracks)
        theFAlarms.extend(subFAlarms)


    # Noisify the all the tracks of this node
    for aNoise in noisesToApply :
        noiseModels[aNoise](theTracks, theFAlarms)
        TrackUtils.CleanupTracks(theTracks, theFAlarms)

    return theTracks, theFAlarms, cornerID


#############################################

def MakeModels(modParams, modelList) :
    models = {}
    defType = modParams.get("type", None)

    for modname in modParams.sections :
        # We need to pop off the 'type' so that it won't be
        # sent to the constructor of the model.
        typename = modParams[modname].pop('type', defType)
        models[modname] = modelList[typename][0](**modParams[modname])
        # Restore the value after creating the model
        modParams[modname]['type'] = typename

    return models

def MakeGenModels(modParams, initModels, motionModels,
                  gen_modelList, trackMakers) :
    models = {}
    defMotion = modParams.get("motion", None)
    defInit = modParams.get("init", None)
    defType = modParams.get("type", None)
    defMaker = modParams.get("trackmaker", None)

    for modname in modParams.sections :
        params = modParams[modname]
        # We need to pop off these off so that it won't be
        # sent to the constructor of the model.
        typename = params.pop('type', defType)
        initName = params.pop('init', defInit)
        motName = params.pop('motion', defMotion)
        makeName = params.pop('trackmaker', defMaker)

        genType = gen_modelList[typename][0]

        models[modname] = genType(initModels[initName],
                                  motionModels[motName],
                                  trackMakers[makeName],
                                  **params)

        # Restore those values after creating the model
        params['type'] = typename
        params['init'] = initName
        params['motion'] = motName
        params['trackmaker'] = makeName

    return models

#############################
#   Track Simulator
#############################
def TrackSim(simConfs, frameCnt, tLims,
             totalTracks, endTrackProb,
             **simParams) :
    """
    totalTracks acts as the top-most default value to use for the
    sim generators. prob_track_ends also acts as the top-most default value.
    """
    initModels = MakeModels(simConfs['InitModels'], Sim.init_modelList)
    motionModels = MakeModels(simConfs['MotionModels'], Sim.motion_modelList)
    noiseModels = MakeModels(simConfs['NoiseModels'], Sim.noise_modelList)

    simGens = MakeGenModels(simConfs['TrackGens'], initModels, motionModels,
                            Sim.gen_modelList, trackMakers)

    rootGenerator = Sim.NullGenerator()
    rootNode = simConfs['SimModels']['Processing']

    # These are global defaults
    trackCnt = int(rootNode.get("cnt", totalTracks))
    endTrackProb = float(rootNode.get("prob_track_ends", endTrackProb))
    maxTrackLen = int(rootNode.get("maxTrackLen", frameCnt))

    if frameCnt == 1 :
        deltaT = 0.0
    else :
        deltaT = (tLims[1] - tLims[0]) / float(frameCnt - 1)

    trackTags = {}

    true_tracks, true_falarms, cornerID = MakeTracks(simGens, noiseModels,
                                                     rootNode, rootGenerator,
					                                 trackCnt,
                                                     deltaT, endTrackProb,
                                                     maxTrackLen,
                                                     trackTags=trackTags)

    return true_tracks, true_falarms, trackTags

def SingleSimulation(simConfs, frameCnt,
                     xLims, yLims, tLims,
                     seed, **simParams) :
    frames = np.arange(frameCnt) + 1
    # Seed the PRNG
    np.random.seed(seed)

    (true_tracks, true_falarms,
     trackTags) = TrackSim(simConfs, frameCnt, tLims, **simParams)

    # Clip tracks to the domain
    (clippedTracks,
     clippedFAlarms) = TrackUtils.ClipTracks(true_tracks,
                                             true_falarms,
                                             xLims, yLims,
                                             frameLims=(1, frameCnt))

    
    volume_data = TrackUtils.CreateVolData(true_tracks, true_falarms,
                                           frames, tLims, xLims, yLims)


    noise_volData = TrackUtils.CreateVolData(clippedTracks, clippedFAlarms,
                                             frames, tLims, xLims, yLims)

    return {'true_tracks': true_tracks, 'true_falarms': true_falarms,
            'noisy_tracks': clippedTracks, 'noisy_falarms': clippedFAlarms,
            'true_volumes': volume_data, 'noisy_volumes': noise_volData,
            'trackTags': trackTags}



def SaveSimulation(theSimulation, simParams, simConfs,
                   automake=True, autoreplace=True, path='.') :

    # Use '' in os.path.join() to make the directory name explicity
    # have a path separator at the end of the name for testing
    # by os.path.exists().
    simDir = os.path.join(path, simParams['simName'], '')
    # Create the simulation directory.
    if (not os.path.exists(simDir)) :
        if automake :
            os.makedirs(simDir)
        else :
            raise ValueError("%s does not exist and automake==False"
                             " in SaveSimulation()" % simDir)
    else :
        if not autoreplace :
            raise ValueError("%s already exists and autoreplace==False"
                             " in SaveSimulation()" % simDir)
    
    ParamUtils.SaveSimulationParams(simDir + "simParams.conf", simParams)
    SaveTracks(os.path.join(simDir, simParams['simTrackFile']),
               theSimulation['true_tracks'], theSimulation['true_falarms'])
    SaveTracks(os.path.join(simDir, simParams['noisyTrackFile']),
               theSimulation['noisy_tracks'], theSimulation['noisy_falarms'])
    SaveCorners(os.path.join(simDir, simParams['inputDataFile']),
                simParams['corner_file'], theSimulation['noisy_volumes'],
                path=simDir)
    ParamUtils.SaveConfigFile(os.path.join(simDir, simParams['simConfFile']),
                              simConfs)

    res = theSimulation['trackTags'].pop('ids', [])
    assert len(res) == 0, "The base tag list shouldn't have anything!"

    ParamUtils.SaveConfigFile(os.path.join(simDir, simParams['simTagFile']),
                              theSimulation['trackTags'])


def main(args) :

    simParams = ParamUtils.ParamsFromOptions(args)

    simConfFiles = args.simConfFiles if args.simConfFiles is not None else \
                                ["InitModels.conf", "MotionModels.conf",
                                 "GenModels.conf", "NoiseModels.conf",
                                 "SimModels.conf"]

    simConfs = ParamUtils.LoadSimulatorConf(simConfFiles)

    print "Sim Name:", args.simName
    print "The Seed:", simParams['seed']

    theSimulation = SingleSimulation(simConfs, **simParams)

    SaveSimulation(theSimulation, simParams, simConfs, path=args.directory)


		    
if __name__ == '__main__' :
    from ZigZag.zigargs import AddCommandParser
    import argparse	                    # Command-line parsing

    parser = argparse.ArgumentParser(description="Produce a track simulation")
    AddCommandParser('TrackSim', parser)
    ParamUtils.SetupParser(parser)

    args = parser.parse_args()

    main(args)

