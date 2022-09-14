#!/bin/sh
#  ALTRAN_PROLOG_BEGIN_TAG
#  This is an automatically generated prolog.
#
#  Copyright (C) Altran ACT S.A.S. 2020,2021,2022.  All rights reserved.
#
#  ALTRAN_PROLOG_END_TAG
#
# %Z%  %ci%  %fn%, %R%, %t%, %G% %U%

# Verify whether python is installed or not before executing python utility
#----------------------------------------------------------------------------
# PYTHON BOOTSTRAP START
#----------------------------------------------------------------------------
shell_script=0<<0000
'''
0000
PATH=$(/usr/es/sbin/cluster/utilities/cl_get_path all)
export PATH

# See if python is already in the system PATH
PYBIN=$(cl_get_python_version)
if [[ -z "$PYBIN" ]]
then
    cl_dspmsg -s 44 scripts.cat 76 "Python must be installed on the node, to execute \"%1\$s\" command." $0
    exit 5
fi

# Run this script with a supported shell
exec $PYBIN "$0" "$@"
'''
#----------------------------------------------------------------------------
# PYTHON BOOTSTRAP END
#----------------------------------------------------------------------------

# include standard modules
import sys,os,re,logging,threading,argparse,fcntl,getopt
import logging.config
import time
import shutil
from os import path
from subprocess import Popen,PIPE
from threading import current_thread
from time import sleep
from signal import SIGKILL
import collections
import json
import subprocess
try:
    # For Python 3.0 and later versions
    from subprocess import getstatusoutput
except:
    # Fall back to Python 2 version
    from commands import getstatusoutput

#Retrieve python version
version=sys.version_info[0]+(sys.version_info[1]*.1)
#Check for the python version,import imp module depricated from python version3.1 onwards
if  version < 3.1:
    import imp
    cl_utilities=imp.load_source('cl_utilities','/usr/es/lib/python/cl_utilities')
else:
    import importlib.util
    def import_path(path):
        module_name = os.path.basename(path)
        spec = importlib.util.spec_from_loader(module_name,importlib.machinery.SourceFileLoader(module_name, path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[module_name] = module
        return module
    cl_utilities=import_path('/usr/es/lib/python/cl_utilities')
from collections import OrderedDict
from cl_utilities import *
import datetime
"""
This script is used to collect disk and network statistics of a VM.
As per current implementation the script will do the following:
1. Make a list of all VGs (except system VGs) and their corresponding disks
2. invoke cl_perfstat_collect binary to collect:
        i. disk I/O statistics for above disks
        ii. network interface statistics for all interfaces
"""


# GLobal Definitions
CLODMGET = "/usr/es/sbin/cluster/utilities/clodmget"
LSLPP = "/usr/bin/lslpp"
PHA_FILESETS = ("cluster.es.server.rte",)
# Following VG lists needs to be skipped for any processing. The list needs to
# be updated as and when new system specific VGs are introduced.
GLVM_FILESETS = ("glvm.rpv.client", "glvm.rpv.server", "glvm.rpv.util")
SKIP_VGS = ("rootvg", "caavg_private", "altinst_rootvg", "old_rootvg")
TMPFILE = "/var/log/glvmtmpfile"
LOGDIR = "/var/hacmp/log/clsurvey"
DATADIR = "{logdir}/data".format(logdir=LOGDIR)
LOGFILE = "{logdir}/survey.log".format(logdir=LOGDIR)
DEBUGFILE = "{logdir}/survey.debug".format(logdir=LOGDIR)
DISKSTATFILE = "{datadir}/diskStats.log".format(datadir=DATADIR)  # File where disk I/O stats will be dumped
REMOTESTATSFILE = "{datadir}/remoteStats.log".format(datadir=DATADIR)
STATISTICSFILE="{datadir}/StatsInfo.log".format(datadir=DATADIR)
NETSTATFILE = "{datadir}/netInterfaceStats.log".format(datadir=DATADIR)  # File where network I/O stats will be dumped
ANALYSISFILE = "{datadir}/analysis.log".format(datadir=DATADIR)  # File where stats analysis will be dumped
LOCKFILE = "{datadir}/lock".format(datadir=DATADIR)  # File to be locked, to check if another instance is running or not 
COLLECTTHREAD = "CollectThread"
DISKTHREAD = "DiskThread"
RUNANALYSIS="{logdir}/Clsurvey_Run_Analysis_information".format(logdir=LOGDIR)

cl_survey_cat = "cl_survey.cat"

HEADER = "=======================Disk Info======================"
FOOTER = "===================End of disk info==================="
site_a = ""
site_b = ""
site_a_nodes = []
site_b_nodes = []
localnode = ""
clustername = ""
bytesWrittenVG = dict()
diskAttributes = dict() # Will hold disk and its different attributes like
                        # block size, VG name, etc.
file_name_list = list()
class analysisInstanceAttributes :
    def __init__(self,Datadict,flag):
        if flag == 1:
            self.vgdiskdict = Datadict
        elif flag == 2:
            self.diskAttributes = Datadict
         
analysisInstanceAttributesList = []



########################## FUNCTIONS ###########################

########################################################################
# Function    : init_log
#
# Description : This function initialize logging mechanism.
#               LOGFILE -> message having level >= INFO goes here i.e. info,warn.error,critical
#               DEBUGFILE -> every message goes here i.e. debug,info,warn,error,critical
#               logcon -> message goes  to console, debug file, log file based on log level
#               logfile -> message goes to debug file, log file based on log level
#
# Arguments   : None
#
# Return      : 0  = Logs successfully initialized
#               !0 = Error scenario
#
########################################################################
def init_log():
    # init_log

    # Check if log dir exists. If not create it.
    if not path.exists(LOGDIR):
        os.makedirs(LOGDIR, 0o755)

    if not path.exists(LOGDIR):
        print("Error: Unable to create log directory. Exiting.")
        return 1


    GLVM_LOGGING = {
        'version':1,
        'formatters':{
            # thread name should be within 14 characters to align with the log format.
            # function name should be within 20 characters to align with the log format.
            # if there is need to have more than above specified sizes, then we need to change the below format line. 
            'glvmfmt':{'format':'[%(threadName)-14s:%(funcName)20s():%(lineno)s:%(asctime)s:%(levelname)8s]-%(message)s', 'datefmt':'%Y-%m-%dT%H-%M-%S'}, 
            'glvmconsolefmt':{'format':'%(message)s'}
            },
        'handlers':{
            'console':{
                'level':'DEBUG',
                'class':'logging.StreamHandler',
                'formatter':'glvmconsolefmt',
                'stream':'ext://sys.stdout'
                },
            'debugfile':{
                'level':'DEBUG',
                'class':'logging.handlers.RotatingFileHandler',
                'formatter':'glvmfmt',
                'filename':DEBUGFILE,
                'maxBytes':10240000,
                'backupCount':4
                },
            'logfile':{
                'level':'INFO',
                'class':'logging.handlers.RotatingFileHandler',
                'formatter':'glvmfmt',
                'filename':LOGFILE,
                'maxBytes':10240000,
                'backupCount':4
                }
                
            },
        'loggers':{
            'glvmlogconsole':{
                'level':'DEBUG',
                'handlers':['console','debugfile','logfile']
                },
            'glvmlogfile':{
                'level':'DEBUG',
                'handlers':['debugfile','logfile']
                }
            },
        'disable_existing_loggers': False
        }

    logging.config.dictConfig(GLVM_LOGGING)
    global logcon
    logcon = logging.getLogger('glvmlogconsole')
    global logfile
    logfile = logging.getLogger('glvmlogfile')

    logfile.info("Initializing log.")
    return 0


########################################################################
# Function    : usage
#
# Description : This function shows the usage and syntax of the script
#
# Arguments   : None
#
# Return      : None
#
########################################################################
def usage():
    Usage="""
Usage:-
    cl_survey -t <total time> -i <interval>
    cl_survey -h [--help]
Options:-
    -t [--time] <total time>   : Total duration in [60 - 31536000]seconds for which program will run and collect data.
    -i [--interval] <interval> : Interval in [2 - 3600]seconds between two consecutive data collections.
    -h [--help]                : Displays Usage
Example:
    1. cl_survey -t 3600 -i 30
    cl_survey runs for 3600 seconds where it will collect disk and network statistics
    every 30 seconds ,analyses the statistics and provides recommendation.
    2. nohup cl_survey -t 3600 -i 30 &
    cl_survey runs in background. Command behavior is same as above.
    Better to run this utility in the background with nohup to avoid killing when the terminal is lost.
    This is the preferred way to use this tool."""
    print(Usage)
    return 0


########################################################################
# Function    : IsThreadAlive
#
# Description : This function checks if given thread is alive or not
#
# Arguments   : Thread name
#
# Return      : True if alive
#               False if not
#
########################################################################
def IsThreadAlive(threadname):
    for th in threading.enumerate():
        if threadname is th.name:
            # No need to check explicitly if thread is alive or not.
            # enumerate() returns only alive threads
            return True
    return False



########################################################################
# Function    : IsInstanceAlreadyRunning
#
# Description : This function checks if an other instance is already
#               running           
#
# Arguments   : 
#
# Return      : True if an other instance is already running 
#               False if not
#
########################################################################
def IsInstanceAlreadyRunning():
    # Check if data dir exists. If not create it.
    if not path.exists(DATADIR):
        os.makedirs(DATADIR, 0o755)
    if not path.exists(DATADIR):
        print("Error: Unable to create data directory. Exiting.")
        return True 

    try:
        lockfd = os.open( LOCKFILE, os.O_RDWR|os.O_CREAT )
    except IOError as err:
        print("Cannot create or open file {}. Exiting".format(err))
        return True

    # Lock exclusively on LOCKFILE. If an other instance has already acquired
    # lock, an exception is thrown. This allows us to know that an instance 
    # is already running. Lock is automatically removed, when the
    # process terminates.
    try:
        fcntl.lockf(lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError as err:
        defMsg="Error : Multiple instances cannot be started.\n"
        displayMsg2(LOGFILE,1,cl_survey_cat,1,defMsg)

        return True

    return False

########################################################################
# Function    : isPHA_Configured
#
# Description : This function checks if PHA is installed and configured.
#
# Arguments   : None
#
# Return      : 0  = PHA configured
#               !0 = PHA not configured
#
########################################################################
def isPHA_Configured():
    # Check if PHA is installed or not
    missing_filesets = ""
    # For time being there is only one fileset to check, but I am
    # still keeping the loop so that in future if fileset is added
    # to the tuple, this code will work.
    for flst in PHA_FILESETS:
        command = "{lslpp} -l {fileset}".format(lslpp=LSLPP, fileset=flst)
        status,output = getstatusoutput(command)
        if status != 0:
            missing_filesets = flst + missing_filesets

    if missing_filesets:
        logfile.warning("PowerHA SystemMirror is not installed. Missing fileset = {fileset}".format(fileset=missing_filesets))
        return 1
    else:
        logfile.info("PowerHA SystemMirror is installed.")

    # PHA is installed, check if its configured.
    command = "{odmget} -f name,nodename,handle -n HACMPcluster".format(odmget=CLODMGET)
    status,output = getstatusoutput(command)
    if status == 0 and output:
        logfile.debug("Got cluster information.\nCMD = {cmd}\nOUTPUT =\n{out}".format(cmd=command, out=output))
    else:
        logfile.warning("Unable to get HACMPcluster information.\nCMD = {cmd}\nOUTPUT =\n{out}".format(cmd=command, out=output))
        return 1

    # Get cluster name, handle and nodename
    try:
        clustername = output.split(':')[0]
        localnode = output.split(':')[1]
        handle = output.split(':')[2]
    except:
        logfile.warning("Unable to get clustername,localnode,handle information. Cluster name = {clstrname}, Local node = {locnode}, Handle = {handle}".format(clstrname=clustername, locnode=localnode, handle=handle))
        return 1

    logfile.info("Cluster name = {clstrname}, Local node = {locnode}, Handle = {handle}".format(clstrname=clustername, locnode=localnode, handle=handle))

    if handle != 0:
        logfile.info("PHA Cluster is configured.\nCMD = {cmd}\nOUTPUT =\n{out}".format(cmd=command, out=output))
    else:
        logfile.warning("PHA Cluster is not configured or not synced.\nCMD = {cmd}\nOUTPUT =\n{out}".format(cmd=command, out=output))
        return 1

    # PHA is installed, cluster is configured. Check if sites are configured or not.
    command = "{odmget} -f name -n HACMPsite".format(odmget=CLODMGET)
    status,output = getstatusoutput(command)
    if not output:
        logfile.warning("PHA Cluster site is not configured.\nCMD = {cmd}\nOUTPUT =\n{out}".format(cmd=command, out=output))
        return 1
    else:
        logfile.info("PHA Cluster site is configured.\nCMD = {cmd}\nOUTPUT =\n{out}".format(cmd=command, out=output))

    # Store site names
    try:
        site_a=output.split('\n')[0]
        site_b=output.split('\n')[1]
    except:
        logfile.error("Unable to get PHA site names. OUTPUT = {out}".format(out=OUTPUT))
        return 1

    # Sites are configured. Check for node names.
    command = "{odmget} -n -q name={site} -f nodelist HACMPsite".format(odmget=CLODMGET, site=site_a)
    status,output = getstatusoutput(command)
    # Store site_a nodes in list
    site_a_nodes = output.split(" ")
    command = "{odmget} -n -q name={site} -f nodelist HACMPsite".format(odmget=CLODMGET, site=site_b)
    status,output = getstatusoutput(command)
    # Store site_b nodes in list
    site_b_nodes = output.split(" ")

    # If any site node list is empty return error
    if not site_a_nodes or not site_b_nodes:
        logfile.warning("PHA sites are defined but the node list is incomplete. site_a_nodes = %s, site_b_nodes = %s" % (site_a_nodes, site_b_nodes))
        return 1

    # If we reached this point, means, PHA is configured
    # and we have site and node details.

    # TODO get persistent IPs
    return 0

########################################################################
# Function    : isGLVM_Configured
#
# Description : This function checks if GLVM already configured and
#               GLVM VG is present.
#
# Arguments   : None
#
# Return      : 0  = GLVM VG is configured
#               !0 = GLVM VG is not configured
#
########################################################################
def isGLVM_Configured():
    # Check if GLVM is installed or not
    missing_filesets = ""
    for flst in GLVM_FILESETS:
        command = "{lslpp} -l {fileset}".format(lslpp=LSLPP, fileset=flst)
        status,output = getstatusoutput(command)
        if status != 0:
            missing_filesets = flst + missing_filesets

    if missing_filesets:
        logfile.warning("Not all GLVM filesets are installed. Missing fileset = {fileset}".format(fileset=missing_filesets))
        return 1
    else:
        logfile.info("GLVM is installed.")

    # GLVM is installed, check if its configured.
    command = "/usr/sbin/ckglvm > {tmpfile}".format(tmpfile=TMPFILE)
    status,output = getstatusoutput(command)
    if status != 0:
        logfile.warning("Unable to get GLVM info.")
        return 1

    # TODO parse ckglvm output
    return 0


########################################################################
# Function    : get_VGandDisk_List
#
# Description : This function gets list of all VGs and their corresponding
#               disks.
#
# Arguments   : None
#
# Return      : 0  = when able to create a dictionary with VG and disk list
#               !0 = Unable to get any VGs
#
########################################################################
def get_VGandDisk_List():
    #Try to fetch the VG and disk information from existing DISKSTATFILE 
    #if it is already available when -a passed, don't continue if file is not exist . 
    #if -a is not used, continue fetching VG and disk information using AIX commands.
    global vglist
    vglist = []
    global vgdiskdict
    vgdiskdict ={}
    global Total_Instance
    Total_Instance = 0
    vgdiskdictFlag = False
    disk_info = False
    if diskAnalysis:
        for fileNmae in file_name_list: 
            if not os.path.isfile(fileNmae):
                logfile.critical("Analysis failed: '{}' not found, First collect Disk I/O statistics to get analysis.".format(fileNmae))
                sys.exit(1)
                
            command = "cat " + fileNmae
            try:
                p1 = Popen(command, shell=True, stdout=PIPE)
            except:
                logfile.critical("Execution failed: {error}. CMD = {cmd}".format(error=sys.exc_info(),cmd=command))
                sys.exit(1)
         
            pid = p1.pid
            logfile.info("{} file opened with process ID = {pid}".format(fileNmae,pid=pid))
            
            while True:
                vgdisklist = list()
                #readline returned data as a string fromat for python version 2, else it returns in byte format.
                if sys.version_info[0] == 2:
                    data = p1.stdout.readline()
                else:
                    data = p1.stdout.readline().decode('ascii')
                
                #Closing the DISKSTATFILE read process once all VG disk information colected.
                if len(data) == 0 :
                    break
                if data.find(HEADER) != -1:
                    disk_info = True
                    vgdiskdict = dict()
                    continue
                if data.find(FOOTER) != -1:
                    disk_info = False
                    analysisInstanceAttributesList.append(analysisInstanceAttributes(vgdiskdict,1))
                    if vgdiskdict:
                        vgdiskdictFlag = True
                    Total_Instance += 1
                    continue                    
                if data.find("None") != -1:
                    continue
                if disk_info:
                    regex_vg = re.findall("VG=.*", data)
                    if regex_vg:
                        Vg = regex_vg[0].split('"')[1]
                    else:
                        continue
                    if Vg in SKIP_VGS:
                        continue
                    vgdisklist.append(data.split(" ")[0])
                    if Vg in vgdiskdict:
                        vgdiskdict[Vg].append(data.split(" ")[0])
                    else:
                        vgdiskdict[Vg] = vgdisklist
    elif Run:
        # Get VG list
        vgdiskdict = dict()
        command = "lsvg -o"
        status,output = getstatusoutput(command)
        if not output:
            logfile.error("No VG is defined or unable to get VG list.")
            return 1
        vglist = output.split('\n')  # ALL VG lists

        # Remove some specific VGs from lists like rootvg, caavg_private
        for vg in SKIP_VGS:
            if vg in vglist:
                vglist.remove(vg)

        # if list is empty return error
        if not vglist:
            defMsg="No user Volume Group is defined or active. Can not continue further.\n"
            displayMsg2(LOGFILE,1,cl_survey_cat,8,"Error : "+defMsg)
            logfile.error(defMsg)
            return 1
        logfile.info("VG list =\n{vgs}".format(vgs=vglist))

        # We got the VG list. Now get corresponding disks.
        command = "lspv"
        status,output = getstatusoutput(command)
        if not output:
            logfile.error("Unable to get hdisk list.")
            return 1
        logfile.info("lspv output =\n{out}".format(out=output))
        for vg in vglist:
            # e.g. hdisk6           00f7bf1c07aef86c                     rootvg           active
            vgdisk_regex = re.compile(r"""
            (\w+)           # group construct - having disk name e.g. hdisk6
            \s+             # one of more space
            \w+             # one or more alphanumeric word for PVID e.g. 00f7bf1c07aef86c
            \s+             # one of more space
            (?={vgname})    # group construct - variable for vg name
            \w+             # one or more alphanumeric word for VG name e.g. rootvg
            \s+             # one of more space
            \w*             # 0 or more word for VG status e.g. active (if not active, then no word)
            """.format(vgname=vg), re.VERBOSE)
            vgdisklist = vgdisk_regex.findall(output) # list of all disks for that VG
            vgdiskdict[vg] = vgdisklist     # Store in global dictionary
        vg_dict=vgdiskdict.copy()
        if vgdiskdict:
            vgdiskdictFlag = True
    if vgdiskdictFlag:
        logfile.info("VG and corresponding disk list =\n{vgdisks}".format(vgdisks=vgdiskdict))
        return 0
    else:
        logfile.error("Unable to get any VG and disk list.")
        return 1

########################################################################
# Function    : collectStatThFn
#
# Description : Thread function which calls cl_perfstat_collect binary
#               collect disk and network stats
#
# Arguments   : noOfIterations = number of times data will be collected in
#               single execution
#               timeinterval = duration between two successive data collection
#
# Return      : 0  = when able to execute cl_perfstat_collect
#               !0 = Any error scenario
#
########################################################################
def collectStatThFn(noOfIterations, timeinterval):
    logfile.info("Thread {tname} started.".format(tname=current_thread().getName()))
    command = "/usr/es/sbin/cluster/utilities/cl_perfstat_collect -s {time} -c {iter} -f".format(time=timeinterval, iter=noOfIterations)
    # Convert command string to list and pass to Popen
    try:
        p1 = Popen(command.split(), stdout=PIPE, stderr=PIPE)
    except:
        logfile.critical("Execution failed: {error}. CMD = {cmd}".format(error=sys.exc_info(),cmd=command))
        sys.exit(1)

    pid = p1.pid
    logfile.info("cl_perfstat_collect started with process ID = {pid}, time interval = {td}, iterations = {it}".format(pid=pid,td=timeinterval,it=noOfIterations))
    out,err = p1.communicate()
    rc = p1.returncode
    logfile.info("cl_perfstat_collect finished with RC = {rc}, OUTPUT = {out}, ERROR = {err}".format(rc=rc,out=out,err=err))

    # Check if cl_perfstat_collect completed successfully
    if rc != 0:
        logfile.error("cl_perfstat_collect could not be executed successfully. RC = {tmprc}".format(tmprc=rc))
        return 1

    return 0

########################################################################
# Function    : startIOCollection
#
# Description : This function starts thread which will do all stat collection.
#
# Arguments   : duration = Total time for which data will be collected in
#               single execution
#               timegap = duration between two successive data collection
#
# Return      : 0  = when able to collect stats
#               !0 = Any error scenario
#
########################################################################
def startIOCollection(duration, timegap):
    # Calculate total no of iterations the tool will run with
    # timegap as interval between each iterations
    # timegap is in seconds and duration is in minutes.
    # To get total no of iterations, convert duration from minutes
    # to seconds and divide by timegap
    try:
        totalNoOfIterations = duration / timegap
    except ZeroDivisionError as zerr:
        logfile.error("Division by ZERO not allowed. timegap={}".format(timegap))
        return 1
    if duration < timegap:
        logfile.error("Provided interval '{}' cannot be more than total duration '{}'.".format(timegap,duration))
        return 1
    logfile.debug("Create thread for stat collection.")

    # Create thread which will internally call cl_perfstat_collect
    # binary to collect disk IO and network stats
    try:
        localstats_thread = threading.Thread(target=collectStatThFn, args=(totalNoOfIterations, timegap))
        localstats_thread.name = "LOCAL_STATS_THREAD"

        Remotestats_thread = threading.Thread(target=collectRemoteStatThFn, args=(totalNoOfIterations, timegap))
        Remotestats_thread.name = "REMOTE_STATS_THREAD"
    except:
        logfile.critical("Unable to create stat collection thread. Exiting.")
        return 1

    # Start the thread and no need to wait for the thread to finish
    localstats_thread.start()
    Remotestats_thread.start()
    localstats_thread.join()
    Remotestats_thread.join()

    return 0


########################################################################
# Function    : analyze_DiskFn
#
# Description : Thread function which will parse DISKSTATFILE and analyze
#               disk I/O
#
# Arguments   : None
#
# Return      : 0  = when able to analyze disk I/O
#               !0 = Any error scenario
#
########################################################################
def analyze_DiskFn():
    count = 0
    DISK_NAME_COL = 0
    DISK_SIZE_COL = 1
    DISK_FREE_COL = 2
    BLOCKS_READ_COL = 3
    BLOCKS_WRITE_COL = 4
    READ_TIMEOUT_COL = 5
    WRITE_TIMEOUT_COL = 6
    READ_FAILED_COL = 7
    WRITE_FAILED_COL = 8
    QDEPTH_COL = 9
    bytes_written = -1
    disk_info = True
    InsNumber = -1

    # Below are the default ranges for disk I/O according to VG.
    for itr in range(Total_Instance):
        analysisRanges = dict()
        insCount = dict()
        for key,value in bytesWrittenVG.items():
            analysisRanges[key]={'firstAvgHalf':0,'avg':0,'secondAvgHalf':0,'max':0,'count':0,'r1':0,'r2':0,'r3':0,'r4':0,'exist':0}
            insCount[key] = 0;
    
    # Opening ANALYSISFILE file to log all the analysis.
    f = None
    try:
        if sys.version_info[0] == 2:
            f = open(ANALYSISFILE, 'w',0)
        else:
            f = open(ANALYSISFILE, 'w')
    except IOError as err:
        logfile.critical("Cannot open file {}. Error = {}".format(ANALYSISFILE, err))
        sys.exit(1)
    f.write("This file contains the details about the data written to disks in 4 ranges.\nThe frequency indicates the number of intervals in which the specific size of data written.\n")

    for fileNmae in file_name_list:
        #Below Reading DISKSTATFILE to analyse the disk I/O.
        command = "cat " + fileNmae
        try:
            p1 = Popen(command, shell=True, stdout=PIPE)
        except:
            logfile.critical("Execution failed: {error}. CMD = {cmd}".format(error=sys.exc_info(),cmd=command))
            sys.exit(1)
        
        pid = p1.pid
        logfile.info("cat command started with process ID = {pid}".format(pid=pid))
        
        while True:
            if sys.version_info[0] == 2:
                data = p1.stdout.readline()
            else:
                data = p1.stdout.readline().decode('ascii')
            if len(data) == 0:
                break
            if data.find(FOOTER) != -1:
                disk_info = False
                InsNumber += 1
                continue
            elif data.find(HEADER) != -1:
                count = 0
                disk_info = True
                continue
            elif disk_info or InsNumber == -1:
                continue
                
            if data.find('---------------') != -1:
                count += 1
                for key,val in bytesWrittenVG.items():
                    analysisRanges[key]['exist'] = 0
                    
            #Collecting total number of bytes written for every Volume Group.
            for key,val in analysisInstanceAttributesList[InsNumber].diskAttributes.items():
                if data.startswith(key + '  ') and val['VG'] in bytesWrittenVG.keys():
                    data = re.sub(' +',' ',data)  #Remove multiple whitespaces
                    if not analysisRanges[val['VG']]['exist']:
                        blocks_written = 0
                    blocks_written += int(data.split(' ')[BLOCKS_WRITE_COL]) #Reading no. of blocks written
                    blocks_written_list.append(blocks_written * int(val['BS']) )
                    bytesWrittenVG[val['VG']] += blocks_written * int(val['BS'])
                    if count == 1 and not analysisRanges[val['VG']]['exist']:
                        insCount[val['VG']] = analysisRanges[val['VG']]['count']
                    analysisRanges[val['VG']]['exist'] = 1
                    analysisRanges[val['VG']]['count'] = insCount[val['VG']] + count;
                    if analysisRanges[val['VG']]['max'] < (blocks_written * int(val['BS'])):
                        analysisRanges[val['VG']]['max'] = int(blocks_written * int(val['BS']))

    headingCover = "-"
    for key,value in list(bytesWrittenVG.items()):
        if analysisRanges[key]['max'] == 0:
            del bytesWrittenVG[key]
            del analysisRanges[key]
            continue

        # Defining dynamic ranges for disk I/O:
        InsCount = analysisRanges[key]['count']
        avgValue = int(value/InsCount)
        analysisRanges[key]['firstAvgHalf'] = int(avgValue/2)
        analysisRanges[key]['secondAvgHalf'] = int((analysisRanges[key]['max']+avgValue)/2)
        analysisRanges[key]['avg'] = avgValue

        headingLen = len("Ranges for {} in bytes:".format(key))
        f.write("\nRanges for {} in bytes:\n{}\n".format(key,headingCover*headingLen))
        f.write("Range 1 : 0 to {} bytes".format(analysisRanges[key]['firstAvgHalf']) + "\n")
        f.write("Range 2 : {} to {} bytes".format(analysisRanges[key]['firstAvgHalf'],analysisRanges[key]['avg']) + "\n")
        f.write("Range 3 : {} to {} bytes".format(analysisRanges[key]['avg'],analysisRanges[key]['secondAvgHalf']) + "\n")
        f.write("Range 4 : {} to {} bytes".format(analysisRanges[key]['secondAvgHalf'],analysisRanges[key]['max']) + "\n")
        bytesWrittenVG[key] = 0
    f.write("\nDisk stats analysis:\n--------------------\n")

    InsNumber = -1
    disk_info = True
    TimeStamp = ""
    for fileNumber,fileNmae in enumerate(file_name_list):
        #Below Reading DISKSTATFILE to analyse the disk I/O.
        command = "cat " + fileNmae
        try:
            p1 = Popen(command, shell=True, stdout=PIPE)
        except:
            logfile.critical("Execution failed: {error}. CMD = {cmd}".format(error=sys.exc_info(),cmd=command))
            sys.exit(1)
        logfile.info("cat command started with process ID = {pid}".format(pid=pid))
        bytes_written=0
        count = 0
        
        #Below analysing the bytes written by VG in which range and logging in ANALYSISFILE with time stamp.
        while True:
            if sys.version_info[0] == 2:
                data = p1.stdout.readline()
            else:
                data = p1.stdout.readline().decode('ascii')
            
            if data.find(FOOTER) != -1:
                disk_info = False
                InsNumber += 1
                continue
            elif data.find(HEADER) != -1:
                disk_info = True
                continue
            elif disk_info or InsNumber == -1:
                continue
            
            if(data.find('TimeOut') != -1):
                TimeStamp += "{},".format(data.split(' ')[-2].replace("\n","")) 
        
            if ((data.find('---------------') != -1) and (bytes_written != 0) or len(data) == 0):
                for key,val in bytesWrittenVG.items():
                    if not analysisRanges[key]['exist']:
                        continue
                    analysisRanges[key]['exist'] = 0
                    if bytesWrittenVG[key] <= analysisRanges[key]['firstAvgHalf']:
                        analysisRanges[key]['r1'] +=1
                    elif bytesWrittenVG[key] <= analysisRanges[key]['avg']:
                        analysisRanges[key]['r2'] +=1
                    elif bytesWrittenVG[key] <= analysisRanges[key]['secondAvgHalf']:
                        analysisRanges[key]['r3'] +=1
                    elif bytesWrittenVG[key] <= analysisRanges[key]['max']:
                        analysisRanges[key]['r4'] +=1
                    bytesWrittenVG[key] = 0
                count += 1

            if len(data) == 0:
                if len(file_name_list) == fileNumber+1 :
                    f.write("Time stamp : {} - {}\n".format(TimeStamp.split(',')[0],TimeStamp.split(',')[-2]))
                    for key,val in bytesWrittenVG.items():
                        f.write("Range 1 frequency of {}: {}\n".format(key,analysisRanges[key]['r1']))
                        f.write("Range 2 frequency of {}: {}\n".format(key,analysisRanges[key]['r2']))
                        f.write("Range 3 frequency of {}: {}\n".format(key,analysisRanges[key]['r3']))
                        f.write("Range 4 frequency of {}: {}\n\n".format(key,analysisRanges[key]['r4']))
                break

            #Collecting total bytes written by VG for one time stamp.
            for key,val in analysisInstanceAttributesList[InsNumber].diskAttributes.items():
                if data.startswith(key + '  ') and val['VG'] in bytesWrittenVG.keys():
                    data = re.sub(' +',' ',data)  #Remove multiple whitespaces
                    blocks_written = int(data.split(' ')[BLOCKS_WRITE_COL]) #Reading no. of blocks written
                    bytesWrittenVG[val['VG']] += blocks_written * int(val['BS'])
                    analysisRanges[val['VG']]['exist'] = 1
                    bytes_written += blocks_written * int(val['BS'])
    return 0



########################################################################
# Function    : Retrieve_DiskBS
#
# Description : This function retrieves the block size of our disks and
#               prepares final list of disks to be analyzed.
#
# Arguments   : None. vg and disk list is accessed from global variable.
#
# Return      : 0  = Got block size for all disks
#               !0 = Unable to get blocksize of one or more disks
#
########################################################################
def Retrieve_DiskBS():
    global block_info
    block_info={}
    disk_info = False
    itr = 0
    for fileNmae in file_name_list:
        try:
            with open(fileNmae, 'r') as fd:
                # Read line by line. Blocksize info is always present in the
                # very beginning of this file.
                for index, line in enumerate(fd):                    
                    if line.find(HEADER) != -1:
                        disk_info = True
                        # Retreive all lines having block size info at one go.
                        bs_lines = ""   # String containing all block size lines
                        # Regular expression to filter out the lines with Blocksize info
                        bs_regex1 = re.compile(r"^hdisk.*\bBlocksize\b=(\w+)")
                        # Open file having disk statistics information
                        continue
                    elif line.find(FOOTER) != -1:
                        disk_info = False
                        logfile.debug("Disk's blocksize information =\n{lines}".format(lines=bs_lines))
                        # Now update the diskAttributes with blocksize information
                        # of each disk
                        # each line is of below format -
                        # hdisk1 "MPIO IBM 2076 FC Disk" VG="None" Blocksize=512
                        for kdisk in analysisInstanceAttributesList[itr].diskAttributes:
                            diskbs_regex = re.compile(r"""
                            (?={disk}\s)   # Variable for disk name
                            (\w+)          # Group to capture disk name
                            .*             # matches zero or more any character except \n
                            \bBlocksize\b  # matches word 'Blocksize' separated by non-alphanumeric char
                            =              # matches '='
                            (\w+)          # group construct to capture blocksize
                            """.format(disk=kdisk), re.VERBOSE)
                            disk_list = diskbs_regex.findall(bs_lines)
                            if disk_list:
                                analysisInstanceAttributesList[itr].diskAttributes[kdisk]["BS"] = disk_list[0][1]
                    
                        logfile.debug("Initial diskAttributes dict : {dskdct}".format(dskdct=analysisInstanceAttributesList[itr].diskAttributes))
                        # diskAttributes may have remote glvm disks also which are not part of
                        # this system and no statistics are available for them. Hence we need
                        # to remove these disks. These disks will not appear in the disk statistics
                        # file and will not have any blocksize info. Hence whichever disk does not
                        # have block size info, we can remove them from our analysis list.
                        disks_removed = []
                        for key in analysisInstanceAttributesList[itr].diskAttributes:
                            if "BS" not in analysisInstanceAttributesList[itr].diskAttributes[key]:
                                disks_removed.append(key)
                        logfile.debug("Disks to be removed from analysis: {dskrm}".format(dskrm=disks_removed))
                        for disk in disks_removed:
                            analysisInstanceAttributesList[itr].diskAttributes.pop(disk)
                            
                        logfile.info("Final diskAttributes list for analysis:{dskdct}".format(dskdct=analysisInstanceAttributesList[itr].diskAttributes))
                        itr += 1
                        continue

                    elif not disk_info:
                        continue
                    match = bs_regex1.search(line)
                    if match != None:
                        # This line has blocksize info
                        bs_lines += line
                    else:
                        # We reached part of file after which there will be no
                        # Blocksize info. Hence we can safely exit the loop and
                        # stop parsing the file.
                        break
        except IOError as err:
            logfile.critical("Cannot open file {}. Error = {}".format(fileNmae, err))
            sys.exit(1)
    block_info=analysisInstanceAttributesList[0].diskAttributes
    if analysisInstanceAttributesList[0].diskAttributes:
        return 0
    else:
        return 1

########################################################################
# Function    : get_Fileslist
#
# Description : This function retrieve the all diskstat files name.
#
# Arguments   : None
#
# Return      : list of files  = validation success
#               NULL = Any errors
#
########################################################################
def get_Fileslist(file_name,mode):
    logfile.info("Obtaining the number of diskstats file list .")
    if not os.path.isfile(file_name) and mode==diskAnalysis:
        logfile.critical("Error: '{}' not found, First collect Disk I/O statistics to get analysis.".format(file_name))
        sys.exit(1)
    if not os.path.isfile(file_name) and mode==cleanUp:
        logfile.Info("Info: '{}' File deleted successfully .".format(file_name))
        return 0
    else:
        logfile.critical("Error: '{}' not found to delete".format(file_name))
    
   
    files = list()
    command = "ls {}*".format(file_name)
    # Convert command string to list and pass to Popen
    try:
        p1 = Popen(command, shell=True, stdout=PIPE)
    except:
        logfile.critical("Execution failed: {error}. CMD = {cmd}".format(error=sys.exc_info(),cmd=command))
        sys.exit(1)

    while True:
        if sys.version_info[0] == 2:
            data = p1.stdout.readline()
        else:
            data = p1.stdout.readline().decode('ascii')
        if len(data) == 0:
            break
        data = data.replace("\n","")
        files.append(data)
    files.sort(reverse = True)

    return files

    
########################################################################
# Function    : validate_args
#
# Description : This function validates user arguments
#
# Arguments   : None
#
# Return      : 0  = validation success
#               !0 = Any errors
#
########################################################################
def validate_args():
    # Check if duration falls between 1 minute to 1 year
    min_duration = 60 # seconds
    max_duration = 31536000 #seconds
    min_interval = 2 #seconds
    max_interval = 3600 #seconds
    errcnt = 0
    if (total_time < min_duration or total_time > max_duration):
        logcon.error("Provided total duration {dur} is not in allowed range({min} - {max} seconds). Please enter valid duration.".format(dur=total_time,min=min_duration,max=max_duration))
        errcnt += 1
    if (time_interval < min_interval or time_interval > max_interval):
        logcon.error("Provided interval {intv} is not in allowed range({min} - {max} seconds). Please enter valid interval.".format(intv=time_interval,min=min_interval,max=max_interval))
        errcnt += 1
    return errcnt

########################################################################
# Function    : Get Cache Size 
#
# Description : This function caclulates the Async glvm cache size
#
# Arguments   : None
#
# Return      : 0  = validation success
#               !0 = Any errors
#
########################################################################
def Get_cache_size(vol_grp):
    lv_cache_list=[]
    if len(vol_grp) > 9:
        VOL=vol_grp[:9]
        vol_grp=VOL

    lv_lst=[vol_grp+"ALV",vol_grp+"ALV1"]
    for lv_ext in lv_lst:
        command="/usr/es/sbin/cluster/utilities/clmgr -cS -a SIZE,PP_SIZE query logical_volume "+lv_ext
        status,output = getstatusoutput(command)
        if status==0:
            cache_size=output.split(':')[0]
            lv_cache_list.append(cache_size)
        else:
            return 1
    cacheSize= max(lv_cache_list)
    return cacheSize

########################################################################
# Function    : get_rpvstat_statistics
#
# Description : This function get the following data.
#               rpvstat -A : Remote site data writes.
#               rpvstat -C : Maximum Cache utilisation .
#               rpvstat -G : No of times cache got full.
# Arguments   : None
#
# Return      : remote_writes,cache_max_used,cache_fulls  = Data is fetched and returned .
#               !0 = Failed to fetch data.
#
########################################################################
def get_rpvstat_statistics():
    global remote_writes
    cache_fulls   = []
    remote_writes = []
    cache_max_used   = []
    temp=[]
    #---------------------Max Cache utilised-------------------------------------------
    for key in vg_remote_disks.keys():
        command = "rpvstat -C | grep "+key+" | awk '{print $4}' "
        status,output = getstatusoutput(command)
        if status == 0:
            temp=output.split('\n')
            cache_max_used.append(temp[0])
            continue
        else:
            logfile.error("Failed to fetch the cache utilisation information.")
            return 1
    #---------------------Remote write data----------------------------------------------
    for key in vg_remote_disks.values():
        if len(key) > 1:
            disk="|".join(key)
            key='"'+disk+'"'
            command = "rpvstat -A | egrep "+key+" | awk '{print $4}' "
            status,output = getstatusoutput(command)
            if status == 0:
                temp=output.split('\n')
                t=0
                for i in temp:
                    t=t+int(i)
                else:
                    remote_writes.append(t)
            else:
                logfile.error("Failed to fetch the remote site data writes information.")
                return 1
        else:
            command = "rpvstat -A | grep "+key[0]+" | awk '{print $4}' "
            status,output = getstatusoutput(command)
            if status == 0:
                remote_writes.append(output)
            else:
                logfile.error("Failed to fetch the remote site data writes information.")
                return 1
    #---------------------No of cache fulls----------------------------------------------
    command = "rpvstat -G"
    status,output = getstatusoutput(command)
    if status == 0:
        temp=[]
        temp= output.split('GMVG name ')
        y=temp[1:]
        for key in vg_remote_disks.keys():
            for line in y:
                if key in line:
                    fetch=line.split('\n')[19]
                    regex = re.compile('Number of cache fulls detected ............... ([0-9]*)')
                    temp=regex.findall(fetch)
                    cache_fulls.append(temp[0])
                    temp=[]
                    break
    else:
        logfile.error("Failed to fetch the cache fulls information.")
        return 1
    return remote_writes,cache_max_used,cache_fulls

########################################################################
# Function    : collectRemoteStatThFn
#
# Description : Thread function which uses the rpvstat command output
#               to collect remote site  statistics
#
# Arguments   : noOfIterations = number of times data will be collected in
#               single execution
#               timeinterval = duration between two successive data collection
#
# Return      : 0  = when able to execute cl_perfstat_collect
#               !0 = Any error scenario
#
########################################################################
def collectRemoteStatThFn(noOfIterations, timeinterval):
    logfile.info("Thread {tname} started.".format(tname=current_thread().getName()))
    # Opening REMOTESTATSFILE file to log all the analysis.
    f = None
    try:
        if sys.version_info[0] == 2:
            f = open(REMOTESTATSFILE, 'w',0)
        else:
            f = open(REMOTESTATSFILE, 'w')
    except IOError as err:
        logfile.critical("Cannot open file {}. Error = {}".format(REMOTESTATSFILE, err))
        sys.exit(1)
    f.write("This file contains the details about the remote data written to disks .\n")


    # Convert command string to list and pass to Popen
    total_time=noOfIterations * timeinterval
    f.write("                Completd Completed   Cached   Cached      Pending  Pending\n")
    f.write("                Async    Async       Async    Async       Async    Async\n")
    f.write("RPV Client   ax Writes   KB Writes   Writes   KB Writes   Writes   KB Writes\n")
    f.write("----------   -- -------- ---------- --------  ----------  -------  ----------")
    for iter in range(0,int(noOfIterations)):
        command="rpvstat -A -t"
        status,output = getstatusoutput(command)
        f.write(output.split('------------ -- -------- ----------- -------- ----------- -------- -----------')[1])
        if status != 0:
            logfile.error("Failed to fetch remote statistics ")
            return 1
        time.sleep(timeinterval)
        iter=iter+timeinterval
    return 0

########################################################################
# Function    : find_remote_disks
#
# Description : This function finds the remote site disks
#
# Arguments   : None
#
# Return      : 0  = validation success
#               !0 = Any errors
#
########################################################################
def find_remote_disks():
    global vg_remote_disks
    global vg_lst
    global Asyncvg_lst
    vg_lst=[]
    vg_remote_disks = {}
    value=[]
    remote_pvids =[]
    local_pvids  =[]
    defMsg="Either No Async glvm volume group is configured or the rpvstat is not updated ,Please check the configuration and try again.\n"

    #check for the list of asyncvg glvm volume group configured
    Asyncvg_lst=[]
    command="rpvstat -C  | awk '{print $1}'"
    status,output = getstatusoutput(command)
    if status == 0:
        all_asyncvg=output.split('----------------')
        if len(all_asyncvg) > 1:
            Asyncvg_lst=all_asyncvg[1].strip().split('\n')
        else:
            logfile.error(defMsg)
            displayMsg2(LOGFILE,1,cl_survey_cat,5,"Error : "+defMsg)
            return 1
    else:
        logfile.error(defMsg)
        displayMsg2(LOGFILE,1,cl_survey_cat,5,"Error : "+defMsg)
        return 1

    #check if the list of asyncvg glvm volume group is not empty
    if  not Asyncvg_lst or Asyncvg_lst==([''] or [' ']):
        logfile.error(defMsg)
        displayMsg2(LOGFILE,1,cl_survey_cat,5,"Error : "+defMsg)
        return 1

    #search for all gmvg
    try:
        # Fall back to Python 2 version
        for key in vg_dict.keys():
            if key not in Asyncvg_lst:
                vg_dict.pop(key)
    except:
        # For Python 3.0 and later versions
        for Key in list(vg_dict.keys()):
            if Key not in Asyncvg_lst:
                vg_dict.pop(Key)

    for key in vg_dict.keys():
        command="/usr/es/sbin/cluster/utilities/clmgr query resource_group "+key+"_RG | grep CURRENT_SECONDARY_NODE"
        status,output = getstatusoutput(command)
        if status != 0:
            logfile.error("Failed to query current secondary node ")
            return 1
        else:
            remote_primary_node=output.split('=')[1]

        command=" cl_rsh  "+remote_primary_node+" lspv | grep -w "+key+" | awk '{print $2}'"
        status,output = getstatusoutput(command)
        if status != 0:
            logfile.error("Failed to fetch rpv client disk pvid ")
            return 1
        else:
            remote_pvids=output.split('\n')

        command="lspv | grep -w "+key+" | awk '{print $2}'"
        status,output = getstatusoutput(command)
        if status != 0:
            logfile.error("Failed to fetch rpv server disk pvid")
            return 1
        else:
            local_pvids=output.split('\n')

        for pvid in remote_pvids:
            command="lspv | grep -w "+key+" | awk '{print $1,$2}' | grep "+pvid
            status,output = getstatusoutput(command)
            if status != 0:
                logfile.error("Failed to fetch client pvid on server node ")
                return 1
            else:
                value.append(output.split(' ')[0]) 

        vg_remote_disks[key]=value
        value=[]

    return 0


########################################################################
# Function    : analyze_remote_data_writes
#
# Description : Thread function which will parse REMOTESTATSFILE and analyze
#               Network I/O
#
# Arguments   : None
#
# Return      : 0  = when able to analyze disk I/O
#               !0 = Any error scenario
#
########################################################################
def analyze_remote_data_writes(vg):
    global max_remote_write
    max_remote_write2=[]
    total_remote_data_written=[]
    dw=[]
    max_remote_write1=[]
    keys=vg_remote_disks[vg]
    if len(keys) > 1:
        for key in keys:
            command = "cat /var/hacmp/log/clsurvey/data/remoteStats*  | grep "+key+" | awk '{print $4}' "
            status,output = getstatusoutput(command)
            if status == 0:
                remote_writes=output.split('\n')
                lst=[]
                if len(remote_writes) > 1:
                    for writes in range(0,len(remote_writes)-1):
                        d=int(remote_writes[writes+1])-int(remote_writes[writes])
                        lst.append(d)
                        dw.append(d)
                        max_remote_write1=str(max(lst))
                else:
                    C_utilisation,C_fulls,C_writes=analyze_final_statistics(vg)
                    d=float(C_writes)
                    max_remote_write=d
                    total_remote_data_written=d
                    return max_remote_write,total_remote_data_written
            else:
                logfile.error("Failed to fetch the remote site data writes information.")
                return 1
            max_remote_write2.append(max_remote_write1)
        max_remote_write=str(max(max_remote_write2))
    else:
        command = "cat /var/hacmp/log/clsurvey/data/remoteStats* | grep "+keys[0]+" | awk '{print $4}' " 
        status,output = getstatusoutput(command)
        if status == 0:
            remote_writes=output.split('\n')
        else:
            logfile.error("Failed to fetch the remote site data writes information.")
            return 1

        lst=[]
        if len(remote_writes) > 1 :
            for writes in range(0,len(remote_writes)-1):
                d=int(remote_writes[writes+1])-int(remote_writes[writes])
                lst.append(d)
                dw.append(d)
            max_remote_write=str(max(lst))
        else:
            C_utilisation,C_fulls,C_writes=analyze_final_statistics(vg)
            d=float(C_writes)
            max_remote_write=d
            total_remote_data_written=d
            return max_remote_write,total_remote_data_written
    total_remote_data_written=sum(dw)
    return max_remote_write,total_remote_data_written


########################################################################
# Function    : analyze_final_statistics
#
# Description : Function will parse StatsInfo.log and fetch
#               the DR sizing run statistics information of volume_group
#
# Arguments   : None
#
# Return      : C_utilisation,C_fulls,C_writes  = when able to analyze StatsInfo.log
#               !0 = Any error scenario
#
########################################################################
def analyze_final_statistics(vg):
    C_utilisation=0
    C_fulls=0
    C_writes=0
    stats_info=[]
    command="cat /var/hacmp/log/clsurvey/data/StatsInfo.log "
    status,output = getstatusoutput(command)
    if status == 0:
        stats_info=output.split('\n')[1:]
    else:
        logfile.error("Failed to fetch the StatsInfo.log")
        return 1

    for line in range(0,len(stats_info)):
        if 'Cache Utilised for '+vg in stats_info[line]:
            C_utilisation = stats_info[line].split(':')[1]
        if 'Remote write completed in KB '+vg in stats_info[line] :
            C_writes=stats_info[line].split(':')[1]
        if 'No of cache fulls for '+vg in stats_info[line]:
            C_fulls=stats_info[line].split(':')[1]
    return C_utilisation,C_fulls,C_writes

########################################################################
# Function    : Provide_recommendation.
#
# Description : This function Analyses the Remote and Local statistics
#               Proivdes recommendation to user.
# Arguments   : None
#
# Return      : 0  = validation success
#               !0 = Any errors
#
########################################################################
def Provide_recommendation():
    global f_values
    f_values=[]
    cache_size=[]
    size=0
    keys   = list(vg_remote_disks.keys())
    for i in range(len(keys)):
        config_dict={}
        Run_Msg={}
        Cache_recommend='No'
        Bandwidth_recommend='No'
        logfile.info("---------------------------------------------------------------------------------")
        #---------------Bandwidth recommendation--------------------------------
        cache_max_used,cache_fulls,remote_writes=analyze_final_statistics(keys[i])
        value,total_remote_writes=analyze_remote_data_writes(keys[i])
        total_local_writes=analyze_LocalFn(keys[i])
        if float(cache_fulls) > 0:
            logfile.critical("The bandwidth configuration is not sufficient for volume group {} , Try increasing the bandwidth 2 times".format(keys[i]))
            Run_Msg.update({'Bandwidth Recommendation':"The bandwidth configuration is not sufficient for volume group {} , Try increasing the bandwidth 2 times.".format(keys[i])})
            Bandwidth_recommend='Increase 2 Times '
        elif float(cache_max_used) > 90 :
            Bandwidth_recommend='Increase 2 Times'
            logfile.critical("The bandwidth configuration is not sufficient for volume group {} , Try increasing the bandwidth 2 times.".format(keys[i]))
            Run_Msg.update({'Bandwidth Recommendation':"The bandwidth configuration is not sufficient for volume group {} , Try increasing the bandwidth 2 times ".format(keys[i])})
        elif float(cache_max_used) > 70 :
            logfile.critical("The current bandwidth between sites is sufficient for the volume group {} , however there is a chance of cache fulls which might leads to data loss. Hence increase the bandwidth to 1.5 times and try the operation again...".format(keys[i]))
            Bandwidth_recommend='Increase 2 Times'
            Run_Msg.update({'Bandwidth Recommendation':"The current bandwidth between sites is sufficient for the volume group {} , however there is a chance of cache fulls which might leads to data loss. Hence increase the bandwidth to 1.5 times and try the operation again...".format(keys[i])})
        else:
            logfile.info("The bandwidth configuration is sufficient for volume group {}. ".format(keys[i]))
            Run_Msg.update({'bandwidth_recommendation':"The bandwidth configuration is sufficient for volume group {} .".format(keys[i])})

        #Cache size is in MB
        ret = Get_cache_size(keys[i])
        if ret != 1:
            cache_size.append(ret)
            size=ret
            condition_1 = float(size)/4
            condition_2 = float(size)/2
        else:
            logfile.error("Failed to fetch Async cache size information ")
            return 1

        #-----------------------Cache Recommendation----------------------------------------
        #Cache size is in MB : converted to Bytes
        #local write value is in Bytes
        #remote write value is in KB : converted to Bytes

        if ((total_local_writes/2)  > (total_remote_writes * 1024) + (float(size) * 1024 * 1024)) and (float(value)/1024 >  condition_2) :
            logfile.critical("The data rate is more than the ideal cache:data rate ratio for volume group {} , Try increasing the cache size 4 times".format(keys[i]))
            Run_Msg.update({'Cache Recommendation':"The data rate is more than the ideal cache:data rate ratio for volume group {} , Try increasing the cache size 4 times".format(keys[i])})
            Cache_recommend='Increase 4 Times'
        elif ((total_local_writes/2)  > (total_remote_writes * 1024) + (float(size) * 1024 * 1024)) and (float(value)/1024 > condition_1):
            logfile.critical("The data rate is more than the ideal cache:data rate ratio for volume group {} , Try increasing the cache size 2 times ".format(keys[i]))
            Run_Msg.update({'Cache Recommendation':"The data rate is more than the ideal cache:data rate ratio for volume group {} , Try increasing the cache size 2 times ".format(keys[i])})
            Cache_recommend='Increase 2 Times'
        else :
            logfile.info("The cache configuration is sufficient for volume group {} ".format(keys[i]))
            Run_Msg.update({'cache_recommendation':"The cache configuration is sufficient for volume group {} ".format(keys[i])})

        config_dict={"async_vg_name":keys[i],"configuration":{'cache_max_utilisation':float(cache_max_used),'cache_fulls':float(cache_fulls),'remote_writes_MB':float(total_remote_writes)/1024,'local_writes_MB':(total_local_writes/2)/(1024*1024),'max_data_rate_MB':float(value)/1024,'cache_size_MB':float(size),'cache_recommend':Cache_recommend,'bandwidth_recommend':Bandwidth_recommend},"recommendation": Run_Msg}
        f_values.append(config_dict)
    logfile.info("---------------------------------------------------------------------------------")
    logfile.info("run ,analysis and recommendation is completed")
    return 0

def run_time():
    r_time=0
    command='grep "Survey Run time :" /var/hacmp/log/clsurvey/data/StatsInfo.log'
    status,output = getstatusoutput(command)
    if status == 0:
        value1=output.split(':')[1]
        r_time=int(value1)
    else:
        logfile.error("Failed to fetch the StatsInfo.log")
        return 1
    return r_time

########################################################################
# Function    : find_local_disks 
#
# Description : This function finds the local site disks
#
# Arguments   : None
#
# Return      : 0  = validation success
#               !0 = Any errors
#
########################################################################
def find_local_disks():
    global vg_local_disks
    global vg_lst
    vg_lst=[]
    vg_local_disks = {}
    value=[]
    remote_pvids =[]
    local_pvids  =[]

    #search for all gmvg
    for key in vg_dict.keys():
        command="/usr/es/sbin/cluster/utilities/clmgr query resource_group "+key+"_RG | grep CURRENT_SECONDARY_NODE"
        status,output = getstatusoutput(command)
        if status != 0:
            logfile.error("Failed to query current secondary node ")
            return 1
        else:
            remote_primary_node=output.split('=')[1]

        command=" cl_rsh  "+remote_primary_node+" lspv | grep -w "+key+" | awk '{print $2}'"
        status,output = getstatusoutput(command)
        if status != 0:
            logfile.error("Failed to fetch rpv client disk pvid ")
            return 1
        else:
            remote_pvids=output.split('\n')

        command="lspv | grep -w "+key+" | awk '{print $2}'"
        status,output = getstatusoutput(command)
        if status != 0:
            logfile.error("Failed to fetch rpv server disk pvid")
            return 1
        else:
            local_pvids=output.split('\n')

        for pvid in local_pvids:
            if pvid not in remote_pvids:
                command="lspv | grep -w "+key+" | awk '{print $1,$2}' | grep "+pvid
                status,output = getstatusoutput(command)
                if status != 0:
                    logfile.error("Failed to fetch client pvid on server node ")
                    return 1
                else:
                    value.append(output.split(' ')[0])
                    vg_local_disks[key]=value
        value=[]
    return 0

########################################################################
# Function    : analyze_LocalFn
#
# Description : Thread function which will parse diskstats.log and analyze
#               Network I/O
#
# Arguments   : None
#
# Return      : 0  = when able to analyze disk I/O
#               !0 = Any error scenario
#
########################################################################
def analyze_LocalFn(vg):
    global max_local_write
    max_local_write2=[]
    total_local_data_written=[]
    dw=[]
    keys=vg_local_disks[vg]

    temp=[]
    temp=vg_local_disks[vg]
    if len(keys) > 1:
        for key in keys:
            BS=block_info[key]['BS']
            command = "cat /var/hacmp/log/clsurvey/data/diskStats*  | grep "+key+" | awk '{print $5}' "
            status,output = getstatusoutput(command)
            if status == 0:
                local_writes=output.split('\n')
                local_writes = [lw for lw in local_writes if lw.strip()!="FC"]
                lst=[]
                for writes in local_writes:
                    lst.append(int(writes) * int(BS))
                max_local_write2.append(sum(lst))
            else:
                logfile.error("Failed to fetch the local site data writes information.")
                return 1
        total_local_data_written=sum(max_local_write2)
    else:
        BS=block_info[temp[0]]['BS']
        command = "cat /var/hacmp/log/clsurvey/data/diskStats*  | grep "+keys[0]+" | awk '{print $5}' "
        status,output = getstatusoutput(command)
        if status == 0:
            local_writes=output.split('\n')
        else:
            logfile.error("Failed to fetch the local site data writes information.")
            return 1
        lst=[]
        local_writes = [lw for lw in local_writes if lw.strip()!="FC"]
        for writes in local_writes:
            lst.append(int(writes) * int(BS))
        total_local_data_written=sum(lst)
    return total_local_data_written

########################################################################
# Function    : state_check
#
# Description : state_check function verify the state of cluster on all nodes
#
#
# Arguments   : None
#
# Return      : 0  = when cluster state is stable on all cluster nodes
#               !0 = Any error scenario
#
########################################################################
def state_check():
    state=""
    node_list=[]
    dd=[]
    command = "{odmget} -n -f name HACMPnode | sort -u".format(odmget=CLODMGET)
    status,output = getstatusoutput(command)
    if status==0:
        node_list=output.split('\n')
    else:
        logfile.error("Failed to fetch the cluster node list")
        return 1

    for node in node_list:
        command="cl_rsh "+node+" lssrc -ls clstrmgrES | grep state"
        status,output = getstatusoutput(command)
        if status == 0:
            state=output.split(':')[1]
            if state!=' ST_STABLE':
                logfile.error("Cluster Services are not Online on Node {}, Please start services and try again".format(node))
                return 1
            else:
                logfile.info("The cluster state is stable on node {} ".format(node))
        else:
            logfile.error("Failed to fetch cluster state on node {} ".format(node))
            return 1

    return 0

def terminate(err):
    response=err
    fvalues=[]
    resources={}
    cmd=subprocess.Popen('odmget HACMPcluster | grep -w id',stdout=subprocess.PIPE,shell=True)
    output, err = cmd.communicate()
    if sys.version_info[0] == 2:
        value1=output.split('=')[1].strip()
    else:
        value1=str(output).split('=')[1].strip().split('\n')[0][:-3]
    f = None
    try:
        if sys.version_info[0] == 2:
            f = open(RUNANALYSIS, 'a',0)
        else:
            f = open(RUNANALYSIS, 'a')
    except IOError as err:
        logfile.critical("Cannot open file {}. Error = {}".format(RUNANALYSIS, err))

    if response==True:
        e = datetime.datetime.now()
        reference_stop_time=e.strftime("%I:%M:%S %p %a %b %d %Y")
        f_keys=["cluster_id","cluster_run_Info","status"]
        Run_Info={"start_time":reference_start_time,"stop_time":reference_stop_time,"run_duration":total_time,"interval":time_interval}
        run_status={"response":"failure","info":"the last dr sizing run is unscuccessfull .Please check /var/hacmp/log/clsurvey/survey.log for more information."}
        fvalues.extend([value1,Run_Info,run_status])

        for count in range(0,len(f_keys)):
            resources[f_keys[count]]=fvalues[count]
        my_json_str = json.dumps(resources,sort_keys=True)
        f.write("--------------------------------------------------------------\n")
        f.write("{}\n".format(my_json_str))
        f.close()

        #to remove the temporary files before exiting.
        shutil.rmtree(DATADIR)
        sys.exit(1)
    else:
        f_keys=["cluster_id","cluster_run_Info","configuration_recommendation","status"]
        run_status={"response":"success","info":"run , analysis and recommendation is completed"}
        value2={"start_time":start_time,"run_duration":total_time,"interval":time_interval,"stop_time":stop_time}
        fvalues.extend([value1,value2,f_values,run_status])
        for count in range(0,len(f_keys)):
            resources[f_keys[count]]=fvalues[count]

        my_json_str2 = json.dumps(resources,sort_keys=True)
        f.write("--------------------------------------------------------------\n")
        f.write("{}\n".format(my_json_str2))
        f.close()
    return 0

##############################################################################################
# MAIN Main main
#
##############################################################################################
def main(argv):
    """
    Function    : main
    Description : This is main function which is invoked when cl_survey tool is executed
    Arguments   : command line arguments passed to script
    Return      : 0  = success
                  !0 = failure
    """

    # Place holders for command line arguments
    # Total duration in seconds for which statistics will be collected. Mandatory argument, no default value.
    global total_time
    # Gap in seconds between two successive data collection. Mandatory argument, no default value.
    global time_interval
    # Flag to check fuction called for analysis.
    global diskAnalysis
    diskAnalysis = False
    global cleanUp
    cleanUp = False
    global Run
    Run = False
    global prog_name # script name
    prog_name = os.path.basename(sys.argv[0])
    rc = 0
    global Run_Msg
    Run_Msg ={}
    global resources
    global Run_Info
    Run_Info ={}
    global err
    err =False
    global total_time
    global interval
    global cache_size
    global noOfIterations
    global timeinterval
    global remote_writes
    global cache_max_used
    global cache_fulls
    global vg_remote_disks
    global blocks_written_list
    global vgdiskdict
    global help
    global vg_dict
    global args
    global parser
    global start_time
    global stop_time
    global reference_start_time
    global reference_stop_time
    e = datetime.datetime.now()
    reference_start_time=e.strftime("%I:%M:%S %p %a %b %d %Y")

    vg_dict={}
    help=False
    remote_writes=[]
    cache_max_used=[]
    cache_fulls=[]
    vgdiskdict = {}
    vg_remote_disks={}
    blocks_written_list = []

    # Initialize log
    rl = init_log()
    if rl != 0:
        sys.exit(1)
   
    modes=['run','analyse','clean']
    for arg in sys.argv:
        if arg == "-h" :
            usage()
            sys.exit(0)

    parser = argparse.ArgumentParser(prog=prog_name, description='Tool to capture and analyze disk and network statistics.')
    parser.add_argument('-t','--time',help='Total duration in [60 - 31536000]seconds for which program will run and collect data. This option is requied to run DR sizing tool .',required=True,type=int)
    parser.add_argument('-i','--interval',help='Interval in [2 - 3600]seconds between two consecutive data collections. This option is requied to run DR sizing tool . ',required=True,type=int)
    args = parser.parse_args()
    
    for mode in modes:
        if mode=='run':
            Run = True
            total_time = args.time
            time_interval = args.interval
            logfile.info("{prog} called with time duration = {dur}, interval = {intv}".format(prog=prog_name, dur=total_time, intv=time_interval))
            
            cmd=subprocess.Popen('clodmget HACMPcluster',stdout=subprocess.PIPE,shell=True)
            output, err = cmd.communicate()
            if not output :
                defMsg="PowerHA cluster is not configured, please verify the cluster configuration and rerun the survey tool.\n"
                logfile.critical(defMsg)
                displayMsg2(LOGFILE,1,cl_survey_cat,9,"Error : "+defMsg)
                shutil.rmtree(DATADIR)
                sys.exit(1)

            if IsInstanceAlreadyRunning():
                terminate(err=True)
                sys.exit(1)
        
            rc=state_check()
            if rc !=0:
                defMsg="PowerHA SystemMirror cluster services are not online, please verify the cluster configuration and rerun the survey tool.\n"
                logfile.critical(defMsg)
                displayMsg2(LOGFILE,1,cl_survey_cat,4,"Error : "+defMsg)
                terminate(err=True)

            # Validate arguments passed by user
            rc = validate_args()
            if rc != 0:
                defMsg="Failed to validate arguments.\n"
                logfile.critical(defMsg)
                displayMsg2(LOGFILE,1,cl_survey_cat,7,"Error : "+defMsg)
                terminate(err=True)

            # Check if PHA is installed/configured or not
            # Ignore any errors as we do not depend on PHA (at least not now)
            rc = isPHA_Configured()
            if rc != 0:
                defMsg="PowerHA SystemMirror configuration is not proper, please verify the cluster configuration and rerun the survey tool.\n"
                logfile.critical(defMsg)
                displayMsg2(LOGFILE,1,cl_survey_cat,2,"Error : "+defMsg)
                terminate(err=True)

            # Check if GLVM is configured or not.
            # Ignore any errors as we do not depend on GLVM (at least not now)
            rc = isGLVM_Configured()
            if rc != 0:
                defMsg="PowerHA with GLVM is not configured in the cluster, please verify the cluster configuration and rerun the survey tool.\n"
                logfile.critical(defMsg)
                displayMsg2(LOGFILE,1,cl_survey_cat,3,"Error : "+defMsg)

                terminate(err=True)

            # Get list of all disks and VGs
            # If we do not find any custom VG and disks, exit
            rc = get_VGandDisk_List()
            if rc != 0:
                logfile.critical("Unable to get the vg and disks list. RC = {} , please verify the cluster configuration and rerun the survey tool.".format(rc))
                terminate(err=True)
            vg_dict=vgdiskdict.copy()

            #Get the rpv disk details
            rc=find_remote_disks()
            if rc != 0:
                logfile.critical("Unable to get remote site disks. RC = {}, please verify the cluster configuration and rerun the survey tool.".format(rc))
                terminate(err=True)

            #Get the Pre run statistics
            Pre_remote_writes,Pre_cache_max_used,Pre_cache_fulls=get_rpvstat_statistics()
            if Pre_remote_writes and Pre_cache_max_used and Pre_cache_fulls == 0 :
                logfile.critical("Unable to get the pre run statistics . , please verify the cluster configuration and rerun the survey tool.")
                terminate(err=True)
            
            defMsg="INFO : cluster configuration checks are passed and data collection is in progress...\n"
            displayMsg2(LOGFILE,1,cl_survey_cat,6,defMsg)
            # displayMsg2(LOGFILE,1,cl_survey_cat,1,defMsg)

            e = datetime.datetime.now()
            start_time=e.strftime("%I:%M:%S %p %a %b %d %Y")

            # Parse command line arguments
            # Initially record the remote statistics
            # call below function to start disk and network I/O stat collection
            rc = startIOCollection(total_time, time_interval)
            if rc != 0:
                logfile.critical("Unable to collect the disks and I/O statstics. RC = {}, please verify the cluster configuration and rerun the survey tool.".format(rc))
                terminate(err=True)

            e1 = datetime.datetime.now()
            stop_time=e1.strftime("%I:%M:%S %p %a %b %d %Y")

            #Get the post run statistics
            Post_remote_writes,Post_cache_max_used,Post_cache_fulls=get_rpvstat_statistics()
            if Post_remote_writes and Post_cache_max_used and Post_cache_fulls == 0 :
                logfile.critical("Unable to get the pre run statistics . RC = {}, please verify the cluster configuration and rerun the survey tool.".format(rc))
                terminate(err=True)
            else:
                # Opening StatsInfo file to log all the analysis.
                f = None
                try:
                    if sys.version_info[0] == 2:
                        f = open(STATISTICSFILE, 'w',0)
                    else:
                        f = open(STATISTICSFILE, 'w')
                except IOError as err:
                    logfile.critical("Cannot open file {}. Error = {}".format(STATISTICSFILE, err))
                    terminate(err=True)

                f.write("--------Run Statistics----------\n")
                f.write("Survey Run time : {} \n".format(total_time))
                for count,key in enumerate(vg_remote_disks.keys()):
                    f.write("Cache Utilised for {} : {}\n".format(key,float(Post_cache_max_used[count])-float(Pre_cache_max_used[count])))
                    f.write("No of cache fulls for {}: {}\n".format(key,float(Post_cache_fulls[count])-float(Pre_cache_fulls[count])))
                    f.write("Remote write completed in KB {}: {}\n".format(key,float(Post_remote_writes[count])-float(Pre_remote_writes[count])))
                f.close()
                logfile.info("Run Completed and run information is logged into StatsInfo.log file")

        elif mode=='analyse':
            diskAnalysis = True
            global file_name_list

            #Get the last clsurvey run time from StatsInfo.log file
            total_time=run_time()
            if total_time == 1:
                logfile.critical("Unable to fetch the run time, please verify the cluster configuration and rerun the survey tool.")
                terminate(err=True)

            # Get list of all diskstats file
            file_name_list = get_Fileslist(DISKSTATFILE,diskAnalysis)

            # Get list of all disks and VGs
            # If we do not find any custom VG and disks, exit
            rc = get_VGandDisk_List()
            if rc != 0:
                logfile.critical("Unable to get the vg and disks list. RC = {}, please verify the cluster configuration and rerun the survey tool.".format(rc))
                terminate(err=True)

            # Populate diskAttributes dictionary with disk names as key and VG name as
            # values.
            for obj in analysisInstanceAttributesList:
                diskAttributes = dict()
                for vg,disks in obj.vgdiskdict.items():
                    for disk in disks:
                        diskAttributes[disk] = {"VG":vg}
                        bytesWrittenVG[vg] = 0
                obj.diskAttributes = diskAttributes

            # Now get block size for each disk and update diskAttributes
            rc = Retrieve_DiskBS()
            if rc != 0:
                logfile.critical("Unable to get blocksize of disks for analysis. RC = {}, please verify the cluster configuration and rerun the survey tool.".format(rc))
                terminate(err=True)

            # Start analysis on the collected data
            rc = analyze_DiskFn()
            if rc != 0:
                logfile.critical("Unable to perform analysis. RC = {}, please verify the cluster configuration and rerun the survey tool.".format(rc))
                terminate(err=True)

            #Get the local site disk details
            rc =  find_local_disks()
            if rc !=0:
                logfile.critical("Unable to get local site disks. RC = {}, please verify the cluster configuration and rerun the survey tool.".format(rc))
                terminate(err=True)

            #Get the remote site disk details
            rc = find_remote_disks()
            if rc !=0:
                logfile.critical("Unable to get remote site disk. RC = {}, please verify the cluster configuration and rerun the survey tool.".format(rc))
                terminate(err=True)

            #Analyse the data collected and provide recommendation.
            rc = Provide_recommendation()
            if rc !=0 :
                logfile.critical("failed to perform recommendation, please verify the cluster configuration and rerun the survey tool.")
                terminate(err=True)
            else:
                terminate(err=False)
        else:
            cleanUp = True
            # Remove all temporary data files
            shutil.rmtree(DATADIR)
            logfile.info("Clean up is successfully completed and run information is logged into Run_Analysis_information_record file")

    return 0


#----------------------------------------------------------------------------
# Calling main() function
#----------------------------------------------------------------------------
if __name__ == "__main__":
    displayMsg2(LOGFILE,1,cl_survey_cat,1,"hello World i am displaying")
    # exclude script name in the argument list passed to main()
    main(sys.argv[1:])
