#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################
#      Bayesian Optimization based on Gaussian Processes
#  Find the optimal geometry of a duct with an integrated HEX
#            s.t. the pressure drop is minimized.
###############################################################
# Erik Hasselwander, erikhass@chalmers.se

# %% libraries
import os
import logging
import pathlib
import numpy as np

# %% logging
# create logger
logger = logging.getLogger("Driver")
if logger.hasHandlers():
    logger.handlers.clear()
logger.setLevel(logging.INFO)


def add_handler():
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(name)s - %(funcName)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)


add_handler()

# %% SETTINGS
iStart = 1  # Starting iteration
iEnd = 50  # < 100
# assert iEnd < 100

# %% path
current_dir = pathlib.Path.cwd()
PATH2FIGS = current_dir / "figs"
PATH2GPLIST = current_dir / "gpOptim/workDir/gpList.dat"
REFFILES_PATH = current_dir / "refFiles"
CFD_PATH = current_dir / "cfd"
CFD_DATABASE_PATH = CFD_PATH / "database.csv"

PATH2FIGS.mkdir(parents=True, exist_ok=True)
PATH2GPLIST.parent.mkdir(parents=True, exist_ok=True)
CFD_PATH.mkdir(parents=True, exist_ok=True)

# %% misc.
minInd, minR, minQ = 0, np.inf, [np.inf, np.inf]

# %% MAIN
if __name__ == "__main__":
    from gpOptim import gpOpt_TBL as X
    from case_config import StarManager

    # initialiization
    # subprocess.call('clear')
    logger.info("CHECK KERBEROS VALIDITY !!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    logger.info("process id = %d" % os.getpid())
    logger.info("pwd = %s" % current_dir)
    X.printSetting()

    # clean remaining data
    # TODO: if database > 0 (exists?). Continue or break or whatever.
    # MAIN LOOP
    for i in range(iStart, iEnd + 1):
        logger.info("############### START LOOP i = %d #################" % i)
        # 1. Generate a sample from the parameters space
        newQ = X.nextGPsample(
            PATH2GPLIST
        )  # "gpOptim/workDir/gpList.dat") # path2gpList

        manager = StarManager()
        obj = manager.runSingleCase(str(f"case_{i}"), newQ, CFD_PATH, REFFILES_PATH)

        # update minInd
        if obj < minR:
            minR = obj
            minInd = i
            minQ = newQ

        # 5. Post-process optimization
        isConv = X.BO_update_convergence(
            newQ, obj, path2gpList=PATH2GPLIST, path2figs=PATH2FIGS
        )
        #  os.chdir(current_dir)

        # 6. check convergence
        if isConv:
            break

    logger.info("################### MAIN LOOP END ####################")
    logger.info("The iteration gave the smallest R: %d" % minInd)
    logger.info(f"Result: x1={minQ[0]}, x2={minQ[1]}, y={minR}")

    logger.info("FINISHED")
