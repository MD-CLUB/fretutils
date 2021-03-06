#!/usr/bin/env python

from FRETUtils.Run import runReconstruction
from optparse import OptionParser, OptionGroup, SUPPRESS_HELP
import sys, os

program_version = "1.0"


def getCmdlineOptions():
    """Commandline parser, see -- long description for each option"""
    parser = OptionParser()

    group1 = OptionGroup(parser, "Required input options")
    group1.add_option("-e", "--efficiencies", dest = "efficiencyfile",
                      help = "file with burst efficiencies", default = "effs.txt")
    group1.add_option("-c", "--config", dest = "configfile",
                      help = "reconstruction configuration file, will be written with default options if file does not exist", default = "reconstruct.conf")

    group2 = OptionGroup(parser, "Optional input")
    group2.add_option("-k", "--expbursts", dest = "expbfile",
                      help = "experimental bursts size distribution file", default = None, metavar = "exp.dat")
    group2.add_option("-r", "--rkappa", dest = "rkappafile",
                      help = "file with r kappa (and probabilities)", default = None, metavar = 'rkappaprb.dat')
    group2.add_option("-s", "--seed", dest = "rseed",
                      help = "random number generator seed", default = None, type = "int" , metavar = "python_default")

    group3 = OptionGroup(parser, "Output options")
    group3.add_option("-o", "--output-distances", dest = "outdistfile",
                      help = "distance histogram output file", default = "distout.txt")
    group3.add_option("-x", "--output-tm", dest = "tmplotfile", default = None,
                      help = "transfer matrix plot", metavar = "tmplot.pdf")

    group4 = OptionGroup(parser, "Required FRET Matrix input options")
    group4.add_option("-d", "--directory", dest = "trajdirectory",
                      help = "directory with R-Kappa trajectories", default = ".", metavar = "RKDIR")
    group4.add_option("-f", "--fretconfigfile", dest = "fretconfigfilename",
                      help = "configuration filename, default file will be written if file does not exist", default = "fret.conf", metavar = "fret.conf")
    group4.add_option("-p", "--probabilites", dest = "pbfile",
                      help = "definition and probability of trajectory classes", default = "probabilities.dat", metavar = "probabilities.dat")

    group5 = OptionGroup(parser, "Optional input")
    group5.add_option("-r", "--trajformat", default = "npz", dest = "trajformat",
                      help = "trajectory format: npz (numpy), dat (plaintext)")

    parser.add_option_group(group1)
    parser.add_option_group(group2)
    parser.add_option_group(group3)

    return parser.parse_args()

def main():
    (options, args) = getCmdlineOptions()
    runReconstruction(options)
    print """
# %s - %s
# (C) 2012 Martin Hoefling and Helmut Grubmueller
#
# Please cite the usage as:
#
# Hoefling M, Lima N, Haenni D, Seidel CAM, Schuler B, Grubmueller H,  
# Structural Heterogeneity and Quantitative FRET Efficiency Distributions 
# of Polyprolines through a Hybrid Atomistic Simulation and Monte Carlo 
# Approach. (2011) PLoS ONE 6(5): e19791. doi:10.1371/journal.pone.0019791
#
# and
#
# Hoefling M, Grubmueller H,
# In silico FRET from simulated dye dynamics. (2012), Computer Physics 
# Communications 184(3):814-852
#
    """ % (os.path.basename(sys.argv[0]), program_version)

if __name__ == "__main__":
    main()
