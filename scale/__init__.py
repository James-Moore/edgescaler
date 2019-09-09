#####################################
#####################################

docker_socket="docker.socket"   #Linux service name used to restart the service
docker_service="docker.service" #Linux service name used to restart the service
dockerOp="docker"               #Operation name used by scaler
cpOp="cp"                       #Operation name used by scaler
execOp="exec"                   #Operation name used by scaler
logsOp="logs"                   #Operation name used by scaler
aflag = 'anax'                  #Flag used by scaler to save flags recieved through click api
oflag = 'organization'          #Flag used by scaler to save flags recieved through click api
hznprefix = 'horizon'           #Docker container prefix for anax-in-container (AIC).  Node is horizon[agentindex]
hzncmd = 'hzn'                  #Horizon command (cli)
env_hznurl = "HORIZON_URL"      #Scaler environment variable used to address AIC agent container
env_hzncontainer = "HZN_SCALER_CONTAINER"  #Scaler environment variable used to dyamically set AIC target
baseport = 8080                 #HORIZON_URL base port.  Container URLS are baseport+container_index
syslogs_capturedir="syslogs"    #Used as global key for identifying syslog directory

#####################################
#From anaxremote.py - REFACTORING
#####################################

json_env = 'env'                        #Environment section key for scaler's run configuration json file
json_endpoints = 'endpoints'            #Endpoints section key for scaler's run configuration json_file
env_scaler_dir = "HZN_SCALER_DIR"       #Environment variable used to acquire scaler's home directory
env_scaler_name = "HZN_SCALER_NAME"     #Environment variable used to acquire scaler's cli command
env_scaler_workerpseudodelay = "HZN_SCLR_WORKER_PSEUDODELAY"    #Environment variable used to acqurie run pseudo delay
rflag = "remotelog"                     #Flag used to acquire remote logging level for slaves
cflag = "count"                         #Flag used to acquire the number of AIC agents on each slave host
mmflag = "mmode"                        #Flag used to acquire the master node run mode (Parallel, Pseudo, Serial)
smflag = "smode"                        #Flag used to acquire the slave node run mode (Parallel, Pseudo, Serial)
efflag = "eventlogflags"                #Flag used to acquire the eventlogs
hpdflag = "headpseudodelay"             #Flag used to acquire the master pseudodelay for run mode Pseudo
wpdflag = "workerpseudodelay"           #Flag used to acquire the slave pseudodelay for run mode Pseudo
mode_parallel = 0                       #Flag used to acquire the runmode (parallel)
mode_pseudoserial = 1                   #Flag used to acquire the runmode (pseudo)
mode_serial = 2                         #Flag used to acquire the runmode (serial)
pseudoDelay=.2                          #Default delay for runmode (pseudo)

startOp = "start"                       #Operation name to start docker containers
stopOp = "stop"                         #Operation name to stop docker containers
restartOp = "restart"                   #Operation name to restart docker containers
registerOp = "register"                 #Operation name to register agents
unregisterOp = "unregister"             #Operation name to unregister agents
eventlogOp = "eventlog"                 #Operation name to acquire agent event logs
queryRunningOp = "queryrunning"         #Operation name to query the number of running containers
validateRunningOp = "validaterunning"   #Operation name to validate containers are running
agreementsOp = "agreements"             #Operation name to acquire agent agreements
nodesOp = "node list"                   #Operation name to acquire the list of nodes on a slave
pruneOp = "prune"                       #Operation name to prune docker containers
dockercpOp = "dockercp"                 #Operation name to execute cp on docker containers
dockerexecOp = "dockerexec"             #Operation name to execute exec on docker containers
agentlogsOp = "agentlogs"               #Operation name to execute get agent syslogs
forcekillallOp ="forcekillall"          #Operation name to perform a forced kill
containerconfigupdateOp = "containerconfigupdate"   #Operation name to update anax config within docker containers

##########################################################################
##########################################################################

pythonkey="python3"                     #Python 3 command (cli)
anaxremotekey="scale.anaxremote"        #Scaler master module
flagmodule ="-m"                        #Flag for Python 3 module delcaration
flaglocalloglevel="-l"                  #Flag for Scaler slave logging level
flagremoteloglevel="-r"                 #Flag for Scaler master logging level
flagconfigfile="-f"                     #Flag for Scaler run configuration file
flagcount="-c"                          #Flag for Scaler slave container quantity
flagmasterparallelism="-m"              #Flag for Scaler master parallelism mode
flagslaveparallelism="-s"               #Flag for Scaler slave parallelism mode

containerskey = "containers"            #Flag for Scaler defining the key associated with container operations


##########################################################################
#Used for next gen scaler job processing - not used in production scaler
##########################################################################

jobskey="jobs"                          #Flag for all Scaler jobs
jobkey="job"                            #Flag for an individual Scaler job
jobdefkey="jobdef"                      #Flag for defining a Scaler job definition

configurationkey="configuration"        #Scaler key used to obtain the configuration data from click ctx
confdirkey="configdirectory"            #Scaler key used to obtain the configuration directory from click ctx
conffilekey="configfile"                #Scaler key used to obtain the configuration file from click ctx

logdirkey="logdir"                      #Scaler key used to obtain the log directory from click ctx
logfilekey="logfile"                    #Scaler key used to obtain the log file from click ctx
phaseskey="phases"                      #Scaler key used to obtain the run phases from click ctx
operationkey="operation"                #Scaler key used to obtain a run phase operation from click ctx
behaviorkey="behavior"                  #Scaler key used to obtain a run phase behavior from click ctx


cleankey="clean"                        #Scaler key used to define clean operation
anaxharnesloglevel="anaxharnesloglevel" #Scaler key used to define clean operation
anaxremoteloglevel="anaxremoteloglevel" #Scaler key used to define clean operation
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
