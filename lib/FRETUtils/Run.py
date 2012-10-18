'''
Created on 04.10.2012

@author: mhoefli
'''

from FRETUtils.Efficiencies import calculateBursts,calcKineticRatesFromConfig
from FRETUtils.Ensemble import readProbabilities,assignTrajProbabilityClasses,cleanProbabilities
from FRETUtils.Photons import setPhotonGenerator
from FRETUtils.Trajectories import createTrajectoryList,readTrajs,calcFRETRates


import ConfigParser
import random
import sys
import cPickle
import multiprocessing
from numpy import array,savetxt

def getFRETConfig(conffile):
    config = ConfigParser.ConfigParser()
    config.readfp(open(conffile))
    return config

def doMultiprocessRun(options, config, trajectories, eprobabilities):
    ncpu = config.getint("System", "ncpu")

    print "Preparing %d clients for burst generation." % ncpu
    pool = multiprocessing.Pool(ncpu)
    
    results=[]
         
    nbursts = config.getint("Monte Carlo", "nbursts")
    print "Total bursts to calculate:",nbursts
 
    try:
        blocksize = config.getint("System", "blocksize")
    except:
        blocksize = 100
        print "Using default blocksize of", blocksize,"for each job."
 
    blockcount = nbursts // blocksize
    remainder = nbursts % blocksize
    print "Setting up %d jobs to generate %d bursts" % (blockcount,nbursts)
    for i in range(blockcount):
        verbose=0
        options.rseed = random.randint(0, sys.maxint)
        res= pool.apply_async(calculateBursts, (trajectories, eprobabilities, config,remainder + blocksize,random.randint(0,sys.maxint),verbose))
        results.append(res)
        remainder = 0
              
    bursts=[]
    myjob=1
    
    for res in results:
        bursts+=res.get()
        print "\r%6d of %6d jobs processed."%(myjob,blockcount),
        myjob+=1
    
    return bursts

def efficienciesFromBursts(config,bursts):
    QD=config.getfloat("Dye Constants","QD")
    QA=config.getfloat("Dye Constants","QA")

    effs=[]
    for burst in bursts:
        effs.append(burst.getEfficiency(QD,QA))
    return array(effs)
    
def sizesFromBursts(bursts,corrected=False,QD=0.,QA=0.):
    sizes=[]
    for burst in bursts:
        if not corrected:
            sizes.append(burst.bsize)
        else:
            sizes.append(burst.bsizeCorr(QD,QA))
               
    return array(sizes)   

def writeOutputFiles(options, config, bursts):
    print 
    print "================================ Calculation complete ========================="
    print "Preparing output."
    if options.binaryofile:
        print "Binary output requested, this may take a while..."
        fh = open(options.binaryofile, "w")
        cPickle.dump(bursts, fh)
        fh.close()
        print "Binary output (pickled data) written to ", options.binaryofile
    if options.efficiencyofile:
        print "Burst efficiency output requested."
        fh = open(options.efficiencyofile, "w")
        savetxt(fh, efficienciesFromBursts(config, bursts))
        fh.close()
        print "Burst efficiencies written to ", options.efficiencyofile
    if options.burstsizeofile:
        print "Burst size output requested."
        fh = open(options.burstsizeofile, "w")
        norm = sizesFromBursts(bursts)
        corr = sizesFromBursts(bursts, corrected=True, QD=config.getfloat("Dye Constants", "QD"), QA=config.getfloat("Dye Constants", "QA"))
        savetxt(fh, array((norm, corr)).T)
        fh.close()
        print "Burst size written to ", options.burstsizeofile
    if options.burstcompofile:
        print "Burstcomposition output requested."
        fh = open(options.burstcompofile, "w")
        for myburst in bursts:
            fh.write("%d %d %d %d\n" % (myburst.donorphot, myburst.acceptorphot, myburst.donortherm, myburst.acceptortherm))
        
        fh.close()
        print "Burstcomposition written to ", options.burstcompofile
    if options.endtimeofile:
        print "Endtime output requested."
        fh = open(options.endtimeofile, "w")
        for burst in bursts:
            for phot in burst.photons:
                fh.write("%f " % phot.endtime)
            
            fh.write("\n")
        
        fh.close()
        print "Endtimes written to ", options.endtimeofile
    if options.decaytimeofile:
        print "Decaytime output requested."
        fh = open(options.decaytimeofile, "w")
        for burst in bursts:
            for phot in burst.photons:
                fh.write("%f " % phot.duration)
            
            fh.write("\n")
        
        fh.close()
        print "Decaytimes written to ", options.decaytimeofile
    print "Finished!"

def runMe(options):
    print "Reading configuration file \"%s\"."%options.configfilename
    config = getFRETConfig(options.configfilename)
    calcKineticRatesFromConfig(config)
    config.set("System", "verbose", "0")
    config.set("Burst Size Distribution", "bsdfile", options.expbfile)
    if options.rseed:
        print "Setting up RNG seed to %d"%options.rseed
        random.seed(options.rseed)
    setPhotonGenerator(config)
    print "\nReading trajectories recursively from directory \"%s\"."%options.trajdirectory
    trajectories = createTrajectoryList(options.trajdirectory,options.trajformat)
    if len(trajectories)==0:
        raise ValueError("No trajectories found. Did you specify the correct format with the -r switch? Exiting.")
        
    readTrajs(trajectories,options.trajformat)
    calcFRETRates(trajectories, config)
    print "\nReading ensemble probabilities"
    eprobabilities = readProbabilities(options.pbfile)
    assignTrajProbabilityClasses(trajectories, eprobabilities)
    print "Removing empty classes"
    eprobabilities = cleanProbabilities(trajectories, eprobabilities)
    print 
    print "================================ Input prepared ========================="
    print 
    print "Starting efficiency calculation"
    ncpu = config.getint("System", "ncpu")
    if ncpu==-1:
        print "Determining number of available cpu's..."
        print "-> %d cpus detected" % multiprocessing.cpu_count()
        ncpu=multiprocessing.cpu_count()
        config.set("System", "ncpu","%d"%ncpu)
    
    if options.prffile:
        print "THIS IS A PROFILING RUN! - will write to logfile and run with only process", options.prffile
        import cProfile
        cProfile.runctx('bursts = calculateBursts(trajectories,eprobabilities,config,%d,%d,1)'%(config.getint("Monte Carlo", "nbursts"),random.randint(0,sys.maxint)), globals(), locals(), options.prffile)
        print "Profiling runs write not output..."
        
    elif ncpu > 1:
        bursts = doMultiprocessRun(options, config, trajectories, eprobabilities)
    
    else:
        print "Doing single process run."
        bursts = calculateBursts(trajectories, eprobabilities, config,config.getint("Monte Carlo", "nbursts"),random.randint(0,sys.maxint),1)
    
    if not options.prffile:
        writeOutputFiles(options, config, bursts)
