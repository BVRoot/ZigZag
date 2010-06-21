import numpy

def SaveTracks(simTrackFile, tracks, falarms = []) :
    dataFile = open(simTrackFile, 'w')
    
    dataFile.write("%d\n" % (len(tracks)))
    dataFile.write("%d\n" % (len(falarms)))

    for (index, track) in enumerate(tracks) :
        dataFile.write("%d %d\n" % (index, len(track)))
        for centroid in track :
	    dataFile.write("%(types)s %(xLocs).10f %(yLocs).10f 0.0 0.0 0.0 0 %(frameNums)d CONSTANT VELOCITY\n" % 
                            centroid)

    for false_alarm in falarms :
        dataFile.write("%(xLocs).10f %(yLocs).10f %(frameNums)d\n" % false_alarm[0])
        
    dataFile.close()


def ReadTracks(fileName) :
    contourCnt = None
    falseAlarmCnt = None

    trackCounter = 0
    centroidCnt = 0
    trackLen = 0
    trackID = None
    
    tracks = []
    falseAlarms = []

    for line in open(fileName) :
        line = line.strip()

        if (line.startswith('#')) : continue

        if contourCnt is None :
            contourCnt = int(line)
            continue

        if falseAlarmCnt is None :
            falseAlarmCnt = int(line)
            continue

        tempList = line.split()
    
        if len(tracks) == trackCounter and trackCounter < contourCnt :
            #print "Reading Begining of track   curTrackCnt: %d   trackCounter: %d    contourCnt: %d" % (len(tracks['tracks']), trackCounter, contourCnt)
            centroidCnt = 0
            trackID = int(tempList[0])
            trackLen = int(tempList[1])

	    tracks.append(numpy.empty(trackLen, dtype=[('types', 'a1'),
						       ('xLocs', 'f4'),
						       ('yLocs', 'f4'),
						       ('frameNums', 'i4')]))
	    continue

        if contourCnt > 0 and centroidCnt < trackLen :
            #print "Reading Track Element   contourCnt: %d   curTrackLen: %d    trackLen: %d" % (contourCnt, len(tracks['tracks'][-1]['types']), tracks['lens'][-1])
            tracks[-1]['types'][centroidCnt] = tempList[0]
	    tracks[-1]['xLocs'][centroidCnt] = float(tempList[1])
	    tracks[-1]['yLocs'][centroidCnt] = float(tempList[2])
	    tracks[-1]['frameNums'][centroidCnt] = int(tempList[7])
            centroidCnt += 1
            if centroidCnt == trackLen :
		trackCounter += 1
	    continue

        if len(falseAlarms) < falseAlarmCnt :
            #print "Reading FAlarm"
	    falseAlarms.append(numpy.array([('F', float(tempList[0]), float(tempList[1]), int(tempList[2]))],
					   dtype=[('types', 'a1'),
                                                  ('xLocs', 'f4'),
                                                  ('yLocs', 'f4'),
                                                  ('frameNums', 'i4')]))

    #print "\n\n\n"

    return(tracks, falseAlarms)


def SaveCorners(inputDataFile, corner_filestem, frameCnt, volume_data) :
    startFrame = volume_data[0]['volTime']
    dataFile = open(inputDataFile, 'w')
    dataFile.write("%s %d %d\n" % (corner_filestem, frameCnt, startFrame))

    for (frameNo, aVol) in enumerate(volume_data) :
        outFile = open("%s.%d" % (corner_filestem, frameNo + startFrame), 'w')
        for strmCell in aVol['stormCells'] :
            outFile.write("%(xLoc).10f %(yLoc).10f " % (strmCell) + ' '.join(['0'] * 25) + '\n')
        outFile.close()
        dataFile.write(str(len(aVol['stormCells'])) + '\n')

    dataFile.close()

def ReadCorners(inputDataFile) :
    dataFile = open(inputDataFile, 'r')
    headerList = dataFile.readline().split()
    corner_filestem = headerList[0]
    frameCnt = int(headerList[1])
    startFrame = int(headerList[2])

    volume_data = []
    dataFile.close()

    for frameNum in range(startFrame, frameCnt + startFrame) :
        aVol = {'volTime': frameNum, 'stormCells': None}
        aVol['stormCells'] = numpy.loadtxt("%s.%d" % (corner_filestem, frameNum),
					   dtype=[('xLoc', 'f4'), ('yLoc', 'f4')],
                                           usecols=(0, 1))

        volume_data.append(aVol)
	

    return({'corner_filestem': corner_filestem, 'frameCnt': frameCnt, 'volume_data': volume_data})


