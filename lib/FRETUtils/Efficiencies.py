'''
Created on 24.06.2010

@author: mhoefli
'''
from FRETUtils.Bursts import genPowerlawTable, getAcceptRejectBurst, \
    getBurstSizes, readBurstSizes
from FRETUtils.Ensemble import pickFromEnsemble
from FRETUtils.Photons import getPhoton
from FRETUtils.Trajectories import getRandomTrajectory
from Bursts import Burst
import random as pyrand
import numpy.random as nprand
import sys

def calcKineticRatesFromConfig(config):
    """calculates and sets the donor and acceptor kinetic rate constants in configuration, based on quantum yield and lifetime set in configuration"""
    print "Calculating the rates for the kinetics:"
    QD=config.getfloat("Dye Constants","QD")
    tauD=config.getfloat("Dye Constants","tauD")
    QA=config.getfloat("Dye Constants","QA")
    tauA=config.getfloat("Dye Constants","tauA")
    kDtot=1/tauD
    kAtot=1/tauA
    kD=QD/tauD
    kA=QA/tauA
    kDi=(1-QD)/tauD
    kAi=(1-QA)/tauA
    config.set("Dye Constants","kDtot","%g"%kDtot)
    config.set("Dye Constants","kAtot","%g"%kAtot)
    config.set("Dye Constants","kD","%g"%kD)
    config.set("Dye Constants","kA","%g"%kA)
    config.set("Dye Constants","kDi","%g"%kDi)
    config.set("Dye Constants","kAi","%g"%kAi)
    print "#################### DYE CONSTANTS ################"
    print "Type  \tDonor   \tAcceptor  "
    print "Qy    \t%8.2f\t%8.2f\t"%(QD,QA)
    print "Tau   \t%8.2f\t%8.2f\t [ps]"%(tauD,tauA)
    print "kTot  \t%8.2e\t%8.2e\t [ps^-1]"%(kDtot,kAtot)
    print "kPhot \t%8.2e\t%8.2e\t [ps^-1]"%(kD,kA)
    print "kThrm \t%8.2e\t%8.2e\t [ps^-1]"%(kDi,kAi)

def efficiencyDeltaFix(efficiencies,delta=0.00001):
    """returns an efficiency array with small offset delta in both direction, preventing problems at bin borders"""
    return efficiencies+nprand.rand(len(efficiencies))*2*delta-delta
    
def calculateBursts(traj,eprob,conf,nbursts,randseed,verbose):
    """calculates efficiencies from trajectories with given probabilities and given configuration, here the burst sizes are determined"""  
    pyrand.seed(randseed)
    nprand.seed(pyrand.randint(0,sys.maxint))
    conf.set("System","verbose","%d"%verbose)
    if verbose:
        print "Will calculate efficiencies from",nbursts,"bursts."
        print "Setting up burst generator."
    #chose burst size generation method
    if conf.get("Burst Size Distribution","method") == "analytical":
        if verbose:
            print "-> Generating burst sizes from analytical function (powerlaw)"
        mina=conf.getint("Burst Size Distribution","llimit")
        maxa=conf.getint("Burst Size Distribution","ulimit")              
        bstable=genPowerlawTable(mina,maxa,conf.getfloat("Burst Size Distribution","lambda"))
        burstGenerator = lambda : getAcceptRejectBurst(bstable,mina,maxa)
        
    elif conf.get("Burst Size Distribution","method") == "file":
        if verbose:
            print "-> Using burst sizes from file",conf.get("Burst Size Distribution","bsdfile")
        if conf.get("Burst Size Distribution","apply")=="corrected":
            bsizes=readBurstSizes(conf.get("Burst Size Distribution","bsdfile"))
        else:
            bsizes=readBurstSizes(conf.get("Burst Size Distribution","bsdfile"),corrected=False)
        burstGenerator = lambda : pyrand.choice(bsizes)
        
    else:
        raise ValueError("-> Unkown BSD generation method.")
        
    
    if verbose:
        print "Calculating bursts sizes."
    burstsizelist=getBurstSizes(nbursts,burstGenerator)
    return getBursts(traj,eprob,conf,burstsizelist)

def getBursts(traj,eprob,conf,burstsizelist):
    """uses given burstsizes and calls for each burst the calculation of efficiencies using trajectories, probabilities and configuration."""
    verbose=conf.getint("System","verbose")
    if verbose:
        print "Initializing bursts"
    bursts=[]
    for bs in burstsizelist:
        bursts.append(Burst(bs)) 
    
    if verbose:
        print "Calculating",len(bursts),"Bursts"
    for i in range(len(bursts)):
        generateBurst(traj,eprob,conf,bursts[i])
        if verbose and not i%100:
            sys.stderr.write("%6.2f complete\r"%(float(i)/len(bursts)*100))
    if verbose:
        sys.stderr.write("%6.2f complete\n"%(100))
        
    return bursts

def generateBurst(trajs,eprob,conf,burst):
    """calculates efficiency according to a single given burst length using trajectories, configuration and probabilities and given method."""
    #select method
    
    #use all trajectories per burst
    if conf.get("Burst Accumulation","method") == "all":
        generateBurstFromAllTraj(eprob,trajs,conf,burst)
                    
    #select species once but allow all trajectories
    elif conf.get("Burst Accumulation","method") == "same-species":
        generateBurstFromSameClassTraj(eprob,trajs,conf,burst)
                               
    #select species and trajectory once
    elif conf.get("Burst Accumulation","method") == "trajectory":
        generateBurstFromSingleTraj(eprob,trajs,conf,burst)
                
    else:
        raise ValueError("Invalid accumulation method.")    


def setUpBurstGeneration(conf):
    try:
        globalreject = conf.getint("Monte Carlo","globalrejectretry")
    except:
        globalreject = 100000
    QD = conf.getfloat("Dye Constants", "QD")
    QA = conf.getfloat("Dye Constants", "QA")
    if conf.get("Burst Size Distribution", "apply") == "corrected":
        applycorrectedcutoff = True
    elif conf.get("Burst Size Distribution", "apply") == "true-photon":
        applycorrectedcutoff = False
    else:
        raise ValueError("Invalid Burst cutoff application method: %s" % conf.get("Burst Size Distribution", "apply"))
    return QD, QA, globalreject, applycorrectedcutoff

def generateBurstFromAllTraj(eprob,trajs,conf,burst):
    QD, QA, globalreject, applycorrectedcutoff = setUpBurstGeneration(conf)

    while True:
        success=False
        while not success:
            try:
                species=pickFromEnsemble(eprob)
                traj=getRandomTrajectory(trajs,species)
                photon=getPhoton(traj,conf)
                photon.checkThermal(QD, QA)
                burst.appendPhoton(photon)                  
                success=True
            except ValueError:                        
                globalreject-=1
                if globalreject==0: 
                    raise ValueError("Too many global rejects, probably no trajectories that can fulfill the rejection criteria - giving up.")
                
        if burst.checkSizeReached(QD,QA,QYcorrected=applycorrectedcutoff):
            break
          

def generateBurstFromSameClassTraj(eprob,trajs,conf,burst):
    QD, QA, globalreject, applycorrectedcutoff = setUpBurstGeneration(conf)
    
    success=False
    while not success:
        try:
            species=pickFromEnsemble(eprob)
            while True:
                traj=getRandomTrajectory(trajs,species)
                photon=getPhoton(traj,conf)
                photon.checkThermal(QD, QA)
                burst.appendPhoton(photon)
                
                if burst.checkSizeReached(QD,QA,QYcorrected=applycorrectedcutoff):
                    break
                
            success=True
        except ValueError:
            globalreject-=1
            if globalreject==0:
                raise ValueError("Too many global rejects, probably no ensemble species can fulfill the rejection criteria - giving up")


def generateBurstFromSingleTraj(eprob,trajs,conf,burst):
    QD, QA, globalreject, applycorrectedcutoff = setUpBurstGeneration(conf)
    
    success=False
    while not success:
        try:
            species=pickFromEnsemble(eprob)
            traj=getRandomTrajectory(trajs,species)
            while True:
                photon=getPhoton(traj,conf)
                photon.checkThermal(QD, QA)
                burst.appendPhoton(photon)
                if burst.checkSizeReached(QD,QA,QYcorrected=applycorrectedcutoff):
                    break
                        
            success=True
        except ValueError:
            globalreject-=1
            if globalreject==0:
                raise ValueError("Too many global rejects, not even single trajectories can fulfill the rejection criteria - giving up")
    

    