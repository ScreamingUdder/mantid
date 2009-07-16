import re
import smtplib
import os
import socket
from shutil import move
from time import strftime
import buildNotification

#Email settings
smtpserver = 'outbox.rl.ac.uk'

#RECIPIENTS = ['nick.draper@stfc.ac.uk']
RECIPIENTS = ['mantid-buildserver@mantidproject.org']
#,'mantid-developers@mantidproject.org'
SENDER = 'BuildServer1@mantidproject.org'

localServerName = 'http://' 
if (os.name =='nt'):
     SENDER = 'Win' + SENDER
     localServerName = localServerName + os.getenv('COMPUTERNAME') + '/'

else:
     SENDER = 'Linux' + SENDER
     localServerName = localServerName + os.getenv('HOSTNAME') + '/'

tracLink = 'http://trac.mantidproject.org/mantid/'
#Set up email content 
buildSuccess = False
testsBuildSuccess = False
sconsResult = ''
testsResult = ''
testsPass = True
doxyWarnings = True

mssgScons = ''
mssgSconsErr = ''
mssgTestsBuild = ''
mssgTestsErr = ''
mssgTestsRunErr = ''
mssgTestsResults = ''
mssgSvn  = ''
mssgDoxy = ''
ticketList = []
svnRevision = ''
logDir = '../../../../logs/Mantid/'

testCount = 0
failCount = 0
warnCount = 0

#create archive directory
archiveDir = logDir + strftime("%Y-%m-%d_%H-%M-%S")
os.mkdir(archiveDir)


#Get scons result and errors
fileScons = logDir+'scons.log'
f = open(fileScons,'r')

for line in f.readlines():
     sconsResult = line
     mssgScons = mssgScons + line
     
f.close()
move(fileScons,archiveDir)

if sconsResult.startswith('scons: done building targets.'):
	buildSuccess = True	

# Count compilation warnings
reWarnCount = re.compile(": warning")
wc = reWarnCount.findall(mssgScons)
compilerWarnCount = len(wc)

fileSconsErr = logDir+'sconsErr.log'
mssgSconsErr = open(fileSconsErr,'r').read()
move(fileSconsErr,archiveDir)

#Get tests scons result and errors
filetestsBuild = logDir+'testsBuild.log'
f = open(filetestsBuild,'r')

for line in f.readlines():
     testsResult = line
     mssgTestsBuild = mssgTestsBuild + line
     
f.close()
move(filetestsBuild,archiveDir)

if testsResult.startswith('scons: done building targets.'):
	testsBuildSuccess = True	
	
filetestsBuildErr = logDir+'testsBuildErr.log'
mssgTestsErr = open(filetestsBuildErr,'r').read()
move(filetestsBuildErr,archiveDir)

filetestsRunErr = logDir+'testsRunErr.log'
f = open(filetestsRunErr,'r')

for line in f.readlines():
	temp = line
	if temp.startswith('TestsScript.sh:'):
		testsBuildSuccess = False
		mssgTestsRunErr  = mssgTestsRunErr + temp[0:temp.find('>>')] + '\n'
     
f.close()
move(filetestsRunErr,archiveDir)

#Get tests result
filetestsRun = logDir+'testResults.log'
f = open(filetestsRun,'r')

reTestCount = re.compile("Running\\s*(\\d+)\\s*tests", re.IGNORECASE)
reCrashCount = re.compile("OK!")
reFailCount = re.compile("Failed\\s*(\\d+)\\s*of\\s*(\\d+)\\s*tests", re.IGNORECASE)
for line in f.readlines():
        m=reTestCount.search(line)
        if m:
            testCount += int(m.group(1))
            m=reCrashCount.search(line)
            if not m:
                failCount += 1
                testsPass = False
        m=reFailCount.match(line)
        if m:
            # Need to decrement failCount because crashCount will have incremented it above
            failCount -= 1
            failCount += int(m.group(1))
            testsPass = False
        mssgTestsResults = mssgTestsResults + line
     
f.close()
move(filetestsRun,archiveDir)

#Read svn log
filesvn = logDir+'svn.log'
mssgSvn = open(filesvn,'r').read()
move(filesvn,archiveDir)
#attempt to parse out the svn revision and ticket number
reSvnRevision = re.compile("r(\\d+)\\s\\|", re.IGNORECASE)
m=reSvnRevision.search(mssgSvn)
if m:
  svnRevision = m.group(1)
  
reTicket = re.compile("#(\\d+)", re.IGNORECASE)
mList=reTicket.findAll(mssgSvn)
while m in mList:
  ticketList.append(m.group(1))
  
#Read doxygen log
filedoxy = logDir+'doxy.log'
mssgDoxy = open(filedoxy,'r').read()
reWarnCount = re.compile("Warning:")
m=reWarnCount.findall(mssgDoxy)
if m:
  warnCount = len(m)
  if warnCount >0:
    doxyWarnings = False
move(filedoxy,archiveDir)

lastDoxy = int(open('prevDoxy','r').read())
currentDoxy = open('prevDoxy','w')
currentDoxy.write(str(warnCount))

#Notify build completion
buildErrors =1
testBuildErrors=1
if buildSuccess:
  buildErrors=0
if testsBuildSuccess:
  testBuildErrors=0
buildNotification.sendTestCompleted(project="Mantid", \
                    testCount=testCount,testFail=failCount, \
                    compWarn=compilerWarnCount,docuWarn=warnCount, \
                    buildErrors=buildErrors,testBuildErrors=testBuildErrors)

#Construct Message
httpLinkToArchive = localServerName + archiveDir.replace('../../../../','') + '/'
message = 'Build Completed at: ' + strftime("%H:%M:%S %d-%m-%Y") + "\n"
message += 'Framework Build Passed: ' + str(buildSuccess)
if compilerWarnCount>0:
  message += " (" + str(compilerWarnCount) + " compiler warnings)"
message += '\n'
message += 'Tests Build Passed: ' + str(testsBuildSuccess) + "\n"
message += 'Units Tests Passed: ' + str(testsPass) 
message += ' (' 
if failCount>0:
    message += str(failCount) + " failed out of "
message += str(testCount) + " tests)\n"
message += "Code Documentation Passed: " + str(doxyWarnings)
if warnCount>0:
  message += " ("+str(warnCount) +" doxygen warnings"
  if (warnCount > lastDoxy):
    message += " - " + str(warnCount-lastDoxy) + " MORE FROM THIS CHECK-IN"
  if (lastDoxy > warnCount):
    message += " - " + str(lastDoxy-warnCount) + " fewer due to this check-in"  
  message += ")\n"
else:
  message += "\n"
message += "\n"
if len(svnRevision) > 0:
  message += "SVN Revision: " + svnRevision
  message += " " + tracLink + "changeset/" + svnRevision + "\n"
while ticket in ticketList:
  message += "TRAC ticket: " + ticket 
  message += " " + tracLink + "ticket/" + ticket + "\n"
message += mssgSvn + "\n"
message += 'FRAMEWORK BUILD LOG\n\n'
message += 'Build stdout <' + httpLinkToArchive + 'scons.log>\n'
message += 'Build stderr <' + httpLinkToArchive + 'sconsErr.log>\n'
#message += mssgScons + "\n\n"
#message += mssgSconsErr + "\n"
message += '------------------------------------------------------------------------\n'
message += 'TESTS BUILD LOG\n\n'
message += 'Test Build stdout <' + httpLinkToArchive + 'testsBuild.log>\n'
message += 'Test Build stderr <' + httpLinkToArchive + 'testsBuildErr.log>\n'
#message += mssgTestsBuild + "\n\n"
#message += mssgTestsErr + "\n"
#message += mssgTestsRunErr  + "\n"
message += '------------------------------------------------------------------------\n'
message += 'UNIT TEST LOG\n\n'
message += 'Test Run stdout <' + httpLinkToArchive + 'testResults.log>\n'
message += 'Test Run stderr <' + httpLinkToArchive + 'testsRunErr.log>\n'
#message += mssgTestsResults + "\n"
message += '------------------------------------------------------------------------\n'
message += 'DOXYGEN LOG\n\n'
message += 'Doxygen Log <' + httpLinkToArchive + 'doxy.log>\n'


#Create Subject
subject = 'Subject: '
if (os.name=='nt'):
     subject += "Windows"
else:
     subject += "Linux"
          
subject += ' Build Report: '

if buildSuccess:
	subject += '[Framework Build Successful, '
else:
	subject += '[Framework Build Failed, '
	
if testsBuildSuccess:
	subject += 'Tests Build Successful, '
else:
	subject += 'Tests Build Failed, '
	
if testsPass:
	subject += 'Tests Successful]\n'
else:
	subject += 'Tests Failed]\n'	

#Send Email
session = smtplib.SMTP(smtpserver)
#timeout in seconds
socket.setdefaulttimeout(30)
try:
  smtpresult  = session.sendmail(SENDER, RECIPIENTS, subject  + message)

  if smtpresult:
      errstr = ""
      for recip in smtpresult.keys():
          errstr = """Could not delivery mail to: %s

Server said: %s
%s

%s""" % (recip, smtpresult[recip][0], smtpresult[recip][1], errstr)
      print errstr
except:
  print "Failed to send the build results email"

if not buildSuccess:
     exit(1)
else:
     fileLaunchQTIPlot = logDir+'LaunchQTIPlot.txt'
     f = open(fileLaunchQTIPlot,'w')
     f.write('launch')

