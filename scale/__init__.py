docker_socket="docker.socket"
docker_service="docker.service"
dockerOp="docker"
cpOp="cp"
execOp="exec"
logsOp="logs"
aflag = 'anax'
oflag = 'organization'
hznprefix = 'horizon'
hzncmd = 'hzn'
env_hznurl = "HORIZON_URL"
env_hzncontainer = "HZN_SCALER_CONTAINER"
baseport = 8080
uuidlog = open("uuid.log","a+")
syslogs_capturedir="syslogs"




#####################################
#From anaxremote.py - REFACTORING
#####################################

json_env = 'env'
json_endpoints = 'endpoints'
env_scaler_dir = "HZN_SCALER_DIR"
env_scaler_name = "HZN_SCALER_NAME"
env_scaler_workerpseudodelay = "HZN_SCLR_WORKER_PSEUDODELAY"
rflag = "remotelog"
cflag = "count"

mmflag = "mmode"
smflag = "smode"
efflag = "eventlogflags"
hpdflag = "headpseudodelay"
wpdflag = "workerpseudodelay"
mode_parallel = 0
mode_pseudoserial = 1
mode_serial = 2
pseudoDelay=.2

startOp = "start"
stopOp = "stop"
restartOp = "restart"
registerOp = "register"
unregisterOp = "unregister"
eventlogOp = "eventlog"
queryRunningOp = "queryrunning"
validateRunningOp = "validaterunning"
agreementsOp = "agreements"
nodesOp = "node list"
pruneOp = "prune"
dockercpOp = "dockercp"
dockerexecOp = "dockerexec"
agentlogsOp = "agentlogs"
forcekillallOp ="forcekillall"
containerconfigupdateOp = "containerconfigupdate"



#########################################



pythonkey="python3"
anaxremotekey="scale.anaxremote"
flagmodule ="-m"
flaglocalloglevel="-l"
flagremoteloglevel="-r"
flagconfigfile="-f"
flagcount="-c"
flagmasterparallelism="-m"
flagslaveparallelism="-s"

containerskey = "containers"

jobskey="jobs"
jobkey="job"
jobdefkey="jobdef"

configurationkey="configuration"
confdirkey="configdirectory"
conffilekey="configfile"

logdirkey="logdir"
logfilekey="logfile"
phaseskey="phases"
operationkey="operation"
behaviorkey="behavior"


cleankey="clean"
anaxharnesloglevel="anaxharnesloglevel"
anaxremoteloglevel="anaxremoteloglevel"
prunekey="prune"

setupkey="setup"
countkey="count"
listkey="list"
queryrunningkey="queryrunning"
validaterunningkey="validaterunning"

executionkey="execution"
masterparallelismkey="masterparallelism"
slaveparallelismkey="slaveparallelism"
registerkey="register"
agreementskey="agreements"

teardownkey="teardown"
unregisterkey="unregister"

collectionkey="collection"
envvarkey="envvar"
pwkey="EXCHANGE_PW"
anonymizekey="anonymize"
archivekey="archive"
tarkey="tar"
compressionkey="compression"
gunzipkey="gunzip"
packagekey="package"
prefixkey="prefix"
destinationkey="destination"
storekey="store"

startkey="start"
stopkey="stop"
