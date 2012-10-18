'''
Created on 04.10.2012

@author: mhoefli
'''

import unittest
import shutil
import tempfile
import os
from RunTestsHelpers import FakeOptions,createConstantDummyRKTraj,createProbabilityClassFile,writeConfigFiles,writeBurstFile,writeInvalidBurstFile,createStepFunctionDummyRKTrajWithL,writeInvalidDummyFile
from FRETUtils.Run import runMe
import numpy

class testFullRun(unittest.TestCase):
    
    def createTestTrajectories(self):
        #high, no and average FRET
        createConstantDummyRKTraj("high.npz", 10000, 10, 1, 4, fformat="numpy")
        createConstantDummyRKTraj("low.npz", 10000, 10, 10, 0, fformat="numpy")
        createConstantDummyRKTraj("aver.npz", 10000, 10, 4, 2./3, fformat="numpy")
        createStepFunctionDummyRKTrajWithL("step.npz", 10000, 10, 0.5,4., 2./3, fformat="numpy")
    
        createConstantDummyRKTraj("high.dat", 10000, 10, 1, 4, fformat="plain")
        createConstantDummyRKTraj("low.dat", 10000, 10, 10, 0, fformat="plain")
        createConstantDummyRKTraj("aver.dat", 10000, 10, 4, 2./3, fformat="plain")
        createStepFunctionDummyRKTrajWithL("step.dat", 10000, 10, 0.5,4., 2./3, fformat="plain")

    def createProbabilityClassFiles(self):
        createProbabilityClassFile("high.prb",("high","low","aver","step"),(1.0,0.0,0.0,0.0))    
        createProbabilityClassFile("low.prb",("high","low","aver","step"),(0.0,1.0,0.0,0.0))
        createProbabilityClassFile("aver.prb",("high","low","aver","step"),(0.0,0.0,1.0,0.0))
        createProbabilityClassFile("mixed.prb",("high","low","aver","step"),(0.25,0.25,0.5,0.0))
        createProbabilityClassFile("step.prb",("high","low","aver","step"),(0.0,0.0,0.0,1.0))
        createProbabilityClassFile("invalid.prb",("high",),(1.0,))
    
    def setUp(self):
        self.workdir=tempfile.mkdtemp()
        self.prevdir=os.curdir
        os.chdir(self.workdir)
        self.createTestTrajectories()
        self.createProbabilityClassFiles()
        writeConfigFiles()
        writeBurstFile()
        writeInvalidBurstFile()
        writeInvalidDummyFile()

    def tearDown(self):
        os.chdir(self.prevdir)
        shutil.rmtree(self.workdir)
   
    def test_output(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.binaryofile="binary.pkl"
        options.burstcompofile="burstcomp.txt"
        options.burstsizeofile="burstsizes.txt"
        options.decaytimeofile="decaytimes.txt"
        options.endtimeofile="endtimes.txt"
        options.pbfile="high.prb"
        options.configfilename="standard.conf"
        runMe(options)
        self.assertAlmostEqual(numpy.loadtxt("effs.txt").mean(),1.,delta=0.05)   

    def test_invalidDir(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.pbfile="high.prb"
        options.configfilename="standard.conf"
        os.mkdir(os.path.join(self.workdir,"empty"))
        options.trajdirectory="empty"
        self.assertRaises(ValueError,runMe,options)
   
    def test_profiling(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.pbfile="high.prb"
        options.configfilename="standard.conf"
        options.prffile="profile.log"
        runMe(options)
        self.assertTrue(os.path.exists("profile.log"))
   
    def test_highEff(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.pbfile="high.prb"
        options.configfilename="standard.conf"
        runMe(options)
        self.assertAlmostEqual(numpy.loadtxt("effs.txt").mean(),1.,delta=0.05)

    def test_lowEff(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.pbfile="low.prb"
        options.configfilename="standard.conf"
        runMe(options)
        self.assertAlmostEqual(numpy.loadtxt("effs.txt").mean(),0.,delta=0.05)

            
    def test_averEff(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.pbfile="aver.prb"
        options.configfilename="standard.conf"
        runMe(options)
        self.assertAlmostEqual(numpy.loadtxt("effs.txt").mean(),0.5,delta=0.05)

    def test_samespeciesEff(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.pbfile="aver.prb"
        options.configfilename="same-species.conf"
        runMe(options)
        self.assertAlmostEqual(numpy.loadtxt("effs.txt").mean(),0.5,delta=0.05)

    def test_invalidBurstGenMethod(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.pbfile="aver.prb"
        options.configfilename="invalidburstacc.conf"
        self.assertRaises(ValueError,runMe,options)

    def test_alltrajEff(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.pbfile="aver.prb"
        options.configfilename="all.conf"
        runMe(options)
        self.assertAlmostEqual(numpy.loadtxt("effs.txt").mean(),0.5,delta=0.05)        

    def test_thermalPhot(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.pbfile="aver.prb"
        options.configfilename="thermal.conf"
        runMe(options)
        self.assertAlmostEqual(numpy.loadtxt("effs.txt").mean(),0.5,delta=0.05)    

    def test_correctedPhot(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.pbfile="aver.prb"
        options.configfilename="corrected.conf"
        runMe(options)
        self.assertAlmostEqual(numpy.loadtxt("effs.txt").mean(),0.5,delta=0.05)    

    def test_invalidBSDGen(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.pbfile="aver.prb"
        options.configfilename="invalidbsd.conf"
        self.assertRaises(ValueError,runMe,options)   

    def test_invalidBSCutOff(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.pbfile="aver.prb"
        options.configfilename="invalidbscutoff.conf"
        self.assertRaises(ValueError,runMe,options)          
        
    def test_expBurst(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.pbfile="aver.prb"
        options.configfilename="expbst.conf"
        options.expbfile="expbursts.bst"
        runMe(options)
        self.assertAlmostEqual(numpy.loadtxt("effs.txt").mean(),0.5,delta=0.05)   

    def test_expBurstCorrected(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.pbfile="aver.prb"
        options.configfilename="expbstcorr.conf"
        options.expbfile="expbursts.bst"
        runMe(options)
        self.assertAlmostEqual(numpy.loadtxt("effs.txt").mean(),0.5,delta=0.05)   
    
    def test_cannotAssignClass(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.pbfile="invalid.prb"
        options.configfilename="expbstcorr.conf"
        options.expbfile="expbursts.bst"
        self.assertRaises(ValueError,runMe,options)
       
    def test_invalidMinMaxRange(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.pbfile="aver.prb"
        options.configfilename="wrongminmaxstart.conf"
        options.expbfile="expbursts.bst"
        self.assertRaises(IndexError,runMe,options)

    def test_invalidMinMaxStartTraj(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.pbfile="aver.prb"
        options.configfilename="wrongminmaxstart2.conf"
        options.expbfile="expbursts.bst"
        self.assertRaises(IndexError,runMe,options)
        
    def test_rejectPhotonTest(self):
        for i in ("trajectory","same-species","all"):
            options = FakeOptions()
            options.efficiencyofile="effs.txt"
            options.pbfile="aver.prb"
            options.configfilename="rejecttest-%s.conf"%i
            options.expbfile="expbursts.bst"
            self.assertRaises(ValueError,runMe,options)

    def test_stepFunctionBelowReject(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.pbfile="step.prb"
        options.configfilename="stepreject.conf"
        options.expbfile="expbursts.bst"
        runMe(options)
        self.assertAlmostEqual(numpy.loadtxt("effs.txt").mean(),0.5,delta=0.05)

    def test_trajFormat(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.trajformat="dat"
        options.pbfile="step.prb"
        options.configfilename="stepreject.conf"
        options.expbfile="expbursts.bst"
        runMe(options)
        self.assertAlmostEqual(numpy.loadtxt("effs.txt").mean(),0.5,delta=0.05)
        
    def test_invalidTrajFormat(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.trajformat="inv"
        options.pbfile="step.prb"
        options.configfilename="stepreject.conf"
        options.expbfile="expbursts.bst"
        self.assertRaises(ValueError,runMe,options)

        
    def test_invalidPhotongenerator(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.pbfile="step.prb"
        options.configfilename="invalid_photongenerator.conf"
        options.expbfile="expbursts.bst"
        self.assertRaises(ValueError,runMe,options)
        

    def test_cythonPhotongenerator(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.pbfile="step.prb"
        options.configfilename="cython.conf"
        options.expbfile="expbursts.bst"
        try:
            from FRETUtils.PhotonGenerator import tryGetCythonPhoton
            runMe(options)
            self.assertAlmostEqual(numpy.loadtxt("effs.txt").mean(),0.5,delta=0.05)      
        except ImportError:
            self.assertRaises(ImportError,runMe,options)

    def test_cextensionPhotongenerator(self):
        options = FakeOptions()
        options.efficiencyofile="effs.txt"
        options.pbfile="step.prb"
        options.configfilename="cextension.conf"
        options.expbfile="expbursts.bst"
        try:
            from FRETUtils.PhotonGenerator import tryGetCPhoton
            runMe(options)
            self.assertAlmostEqual(numpy.loadtxt("effs.txt").mean(),0.5,delta=0.05)      
        except ImportError:
            self.assertRaises(ImportError,runMe,options)

        
#disabled due to problems between unittest / nose and multiprocessing (maybe pickling problem)
#    def test_01dualCPU(self):
#        options = FakeOptions()
#        options.efficiencyofile="effs.txt"
#        options.pbfile="aver.prb"
#        options.configfilename="dual.conf"
#        runMe(options)
#        self.assertAlmostEqual(numpy.loadtxt("effs.txt").mean(),0.5,delta=0.05)
#
#    def test_00multiCPU(self):
#        options = FakeOptions()
#        options.efficiencyofile="effs.txt"
#        options.pbfile="aver.prb"
#        options.configfilename="multi.conf"
#        runMe(options)
#        self.assertAlmostEqual(numpy.loadtxt("effs.txt").mean(),0.5,delta=0.05)            