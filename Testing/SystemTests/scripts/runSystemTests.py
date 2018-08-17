#!/usr/bin/env python

from __future__ import (absolute_import, division, print_function)
import optparse
import os
import sys

from multiprocessing import Process, Array
from multiprocessing.managers import BaseManager

# Function to spawn one test manager per CPU
def testProcess(testDir,saveDir,runner,testsInclude, testsExclude, exclude_in_pr_builds,
                results_array,process_number,ncores):

    reporter = stresstesting.XmlResultReporter(showSkipped=options.showskipped)

    mgr = stresstesting.TestManager(testDir,runner,output=[reporter],testsInclude=testsInclude,
                                    testsExclude=testsExclude, exclude_in_pr_builds=exclude_in_pr_builds,
                                    process_number=process_number,ncores=ncores)
    try:
        mgr.executeTests()
    except KeyboardInterrupt:
        mgr.markSkipped("KeyboardInterrupt")

    # Update the test results in the array shared accross cpus
    results_array[process_number] = mgr.skippedTests
    results_array[process_number + ncores] = mgr.failedTests
    results_array[process_number + 2*ncores] = mgr.totalTests
    results_array[process_number + 3*ncores] = int(reporter.reportStatus())

    # report the errors
    xml_report = open(os.path.join(saveDir, "TEST-systemtests-%i.xml" % process_number),'w')
    xml_report.write(reporter.getResults())
    xml_report.close()

    return

#==============================================================================

# set up the command line options
VERSION = "1.1"
THIS_MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
DEFAULT_FRAMEWORK_LOC = os.path.realpath(os.path.join(THIS_MODULE_DIR, "..","lib","systemtests"))
DATA_DIRS_LIST_PATH = os.path.join(THIS_MODULE_DIR, "datasearch-directories.txt")
SAVE_DIR_LIST_PATH = os.path.join(THIS_MODULE_DIR, "defaultsave-directory.txt")

info = []
info.append("This program will configure mantid run all of the system tests located in")
info.append("the 'tests/analysis' directory.")
info.append("This program will create a temporary 'Mantid.user.properties' file which")
info.append("it will rename to 'Mantid.user.properties.systest' upon completion. The")
info.append("current version of the code does not print to stdout while the test is")
info.append("running, so the impatient user may ^C to kill the process. In this case")
info.append("all of the tests that haven't been run will be marked as skipped in the")
info.append("full logs.")


parser = optparse.OptionParser("Usage: %prog [options]", None,
                               optparse.Option, VERSION, 'error', ' '.join(info))
parser.add_option("", "--email", action="store_true",
                  help="send an email with test status.")
parser.add_option("-x", "--executable", dest="executable",
                  help="The executable path used to run each test. Default is the sys.executable")
parser.add_option("-a", "--exec-args", dest="execargs",
                  help="Arguments passed to executable for each test Default=[]")
parser.add_option("", "--frameworkLoc",
                  help="location of the stress test framework (default=%s)" % DEFAULT_FRAMEWORK_LOC)
parser.add_option("", "--disablepropmake", action="store_false", dest="makeprop",
                  help="By default this will move your properties file out of the "
                  + "way and create a new one. This option turns off this behavior.")
parser.add_option("-R", "--tests-regex", dest="testsInclude",
                  help="String specifying which tests to run. Simply uses 'string in testname'.")
parser.add_option("-E", "--excluderegex", dest="testsExclude",
                  help="String specifying which tests to not run. Simply uses 'string in testname'.")
loglevelChoices=["error", "warning", "notice", "information", "debug"]
parser.add_option("-l", "--loglevel", dest="loglevel",
                  choices=loglevelChoices,
                  help="Set the log level for test running: [" + ', '.join(loglevelChoices) + "]")
parser.add_option("-j", "--parallel", dest="parallel",
                  help="The number of instances to run in parallel, like the -j option in ctest. Default is 1")
parser.add_option("", "--showskipped", dest="showskipped", action="store_true",
                  help="List the skipped tests.")
parser.add_option("-d", "--datapaths", dest="datapaths",
                  help="A semicolon-separated list of directories to search for data")
parser.add_option("-s", "--savedir", dest="savedir",
                  help="A directory to use for the Mantid save path")
parser.add_option("", "--archivesearch", dest="archivesearch", action="store_true",
                  help="Turn on archive search for file finder.")
parser.add_option("", "--exclude-in-pull-requests", dest="exclude_in_pr_builds",action="store_true",
                  help="Skip tests that are not run in pull request builds")
parser.set_defaults(frameworkLoc=DEFAULT_FRAMEWORK_LOC, executable=sys.executable, makeprop=True,
                    loglevel="information",parallel="1")
(options, args) = parser.parse_args()

# import the stress testing framework
sys.path.append(options.frameworkLoc)
import stresstesting

# Configure mantid
# Parse files containing the search and save directories, unless otherwise given
data_paths = options.datapaths
if data_paths is None or data_paths == "":
    with open(DATA_DIRS_LIST_PATH, 'r') as f_handle:
        data_paths = f_handle.read().strip()

save_dir = options.savedir
if save_dir is None or save_dir == "":
    with open(SAVE_DIR_LIST_PATH, 'r') as f_handle:
        save_dir = f_handle.read().strip()
# Configure properties file
mtdconf = stresstesting.MantidFrameworkConfig(loglevel=options.loglevel,
                                              data_dirs=data_paths, save_dir=save_dir,
                                              archivesearch=options.archivesearch)
if options.makeprop:
    mtdconf.config()

# run the tests
execargs = options.execargs
runner = stresstesting.TestRunner(executable=options.executable, exec_args=execargs, escape_quotes=True)
# xml_file_root = "TEST-systemtests"
# reporter = stresstesting.XmlResultReporter(showSkipped=options.showskipped)


# BaseManager.register('XmlReporterClass', stresstesting.XmlResultReporter(showSkipped=options.showskipped))
# manager = BaseManager()
# manager.start()
# reporter = manager.XmlReporterClass
# print(reporter)
# reporter2 = stresstesting.XmlResultReporter(showSkipped=options.showskipped)
# print(reporter2)

# Multi-core processes
ncores = int(options.parallel)
processes = []
# Prepare a shared array to hold skipped, failed and total number of tests + status
results_array = Array('i', 4*ncores)
# Prepare ncores processes
for ip in range(ncores):
    processes.append(Process(target=testProcess,args=(mtdconf.testDir, mtdconf.saveDir, runner,
        options.testsInclude, options.testsExclude,options.exclude_in_pr_builds,results_array,ip,ncores)))
# Start and join processes
for p in processes:
    p.start()
for p in processes:
    p.join()

# # merge reports to master xml file
# xml_master_file = open(os.path.join(mtdconf.saveDir, xml_file_root)+".xml", 'w')
# for i in range(ncores):
#     with open(os.path.join(mtdconf.saveDir, xml_file_root)+"-%i.xml" % i, mode='r') as xml_file:
#         xml_content = xml_file.read()
#     xml_file.close()
#     xml_master_file.write(xml_content)
#     print(xml_content)
# xml_master_file.close()

# success = reporter.reportStatus()
# xml_report = open(os.path.join(mtdconf.saveDir, "TEST-systemtests.xml"),'w')
# xml_report.write(reporter.getResults())
# xml_report.close()

# put the configuration back to its original state
if options.makeprop:
    mtdconf.restoreconfig()

# Gather sums over ncores
skippedTests = sum(results_array[:ncores])
failedTests = sum(results_array[ncores:2*ncores])
totalTests = sum(results_array[2*ncores:3*ncores])
# Find minimum of status: if min = 0, then success is False
success = bool(min(results_array[3*ncores:4*ncores]))

print()
if skippedTests == totalTests:
    print("All tests were skipped")
    success = False # fail if everything was skipped
else:
    percent = 1.-float(failedTests)/float(totalTests-skippedTests)
    percent = int(100. * percent)
    print("%d%s tests passed, %d tests failed out of %d (%d skipped)" %
          (percent, '%', failedTests, (totalTests-skippedTests), skippedTests))
print('All tests passed? ' + str(success))
if not success:
    sys.exit(1)
