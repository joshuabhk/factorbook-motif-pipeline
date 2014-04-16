#/usr/bin/env python

import sys
from os import listdir, system
from os.path import join, basename, exists
from fabric.api import local, run, env
from fabric.state import output
from psutil import cpu_percent, process_iter, NoSuchProcess
from time import sleep, ctime
from shutil import move

##################################################
#server settings
##################################################
verbose = 0 #0 for quiet output!
check_interval = 10 # in seconds
check_interval_overloaded = 120 # in seconds
submission_interval = 1 # in seconds
overloaded_cutoff_hard = 95 #stops submitting jobs.
overloaded_cutoff_soft = 80 #use overloaded interval to submit jobs

#email address for abnormalities
notify_email = "bonghyun.kim@umassmed.edu" 

#frontend server
server = "bib"
#frontend server user data root dir
server_user_dir = "/home/kimb/factorbook_motif_pipeline/frontend/user_data"


#setting fabric environment
env.hosts= [server]
#make fabric quiet! :)
output.running = False
output.stdout = False

#local root directory
root_dir = '/home/kimb/factorbook_motif_pipeline/backend'
user_dir = join( root_dir, 'user_data' )
failed_dir = join( root_dir, 'user_data_failed' )

#job submission command line template
capture_cmd = 'start_factorbook_motif_pipeline.py'
job_cmd_line = '%(root_dir)s/bin/%(capture_cmd)s %(user_dir)s/%%(jobid)s %(server)s:%(server_user_dir)s/%%(jobid)s > %(user_dir)s/%%(jobid)s/%%(jobid)s.main.log 2>&1 &'%globals()

###########################
#very specific setting to the current 
#command line structure!
#need to be changed if the command line
#arguments are changed.
###########################
#motif pipeline cmd
def parse_jobid( cmdline ):
	'''
	Parse job id from the cmdline of a Process
	if the command does not belong to our server
	None will be returned.
	'''
	if len(cmdline) == 4 :
		#This is because our jobs are using three command lines.
		if 'python' in cmdline[0] and capture_cmd in cmdline[1] :
			jobid = basename(cmdline[2])
			#further sanity check with the job id rule!
			if jobid.startswith( 'fmp' ) :
				return jobid
			else :
				#just warning instead of the Exception!
				print >>sys.stderr, 'WARNING: Job name collision found!', cmdline
				return None
	else :
		return None
###########################

##################################################
#End of server settings
##################################################

def get_current_running_jobs():
	'''check all the running processes
	and find processes used by factorbook motif pipeline server'''

	jobids = []
	for proc in process_iter() :
		try :
			jobid = parse_jobid( proc.cmdline() )
			if jobid :
				if jobid in jobids :
					raise Exception( 'Duplicate running job found', jobid )

				jobids.append( jobid )
		except NoSuchProcess :
			pass
	return jobids

def get_current_job_pool() :
	'''
	list of Job IDs including queued, running and finished Jobs.
	'''
	jobids = [ j for j in listdir( user_dir ) if j.startswith('fmp') ]
	return jobids

def is_completed( jobid ) :
	'''
	Check if the job is completed by the pipeline
	'''
	job_dir = join( user_dir, jobid )
	started_marker = join( job_dir, 'job_started' )
	finished_marker = join( job_dir, jobid+'.completed' )
	if exists( finished_marker ) :
		return True
	elif exists( started_marker ) :
		#raise Exception( 'job failed ' + jobid )
		move( job_dir, failed_dir )
		notify_job_error( jobid )
		return True
	else :
		return False

def get_remote_file_size( fn ) :
	return run( "stat -c '%s' {0}".format( fn ) )

def get_local_file_size( fn ) :
	return local( "stat -c '%s' {0}".format(fn), capture=True )
	
def is_ready( jobid ) :
	'''
	Check if the job is completed copied from the remote server
	by comparing the file sizes of the remote server and local copies.
	'''
	job_dir = join( user_dir, jobid )
	files = listdir( job_dir )

	server_job_dir = join( server_user_dir, jobid )
	
	for fn in files :
		path = join( job_dir, fn )
		server_path = join( server_job_dir, fn )

		size = get_local_file_size(path)
		server_size = get_remote_file_size( server_path )

		if size == server_size :
			pass
		else :
			return False
	else :
		return True
	
def get_todo_jobs() :
	#get total jobs
	total_jobs = set(get_current_job_pool())
	running_jobs = set(get_current_running_jobs())
	
	todo = []
	for jobid in total_jobs - running_jobs :
		if not is_completed( jobid ) :
			todo.append( jobid )
	return todo


def submit_jobs( jobids ) :
	for jobid in jobids :
		print ctime(), '-', jobid, "started."
		val = system( job_cmd_line % {'jobid':jobid} )
		if val != 0 :
			raise Exception( "Job submission failed", jobid, job_cmd_line%{'jobid':jobid} )

		sleep( submission_interval )

def main() :
        while(1) :
		system_usage = cpu_percent( interval=5 )
		if verbose : 
			print ctime()
			print "current system usage", system_usage
			
		if system_usage > overloaded_cutoff_hard :
			if verbose : print "System overloaded: resting..."
			sleep( check_interval_overloaded )
			continue

                todo_list = get_todo_jobs()
		if verbose : print "Todo list:", " ".join( todo_list )
				
                if todo_list :
			if verbose : print "Starting job sumissions", ctime()
                        submit_jobs( todo_list )

		if system_usage > overloaded_cutoff_soft :
			sleep( check_interval_overloaded )
		else :
                	sleep(check_interval)

def notify_problem() :
	import smtplib
	from email.mime.text import MIMEText
	
        email_body = '''
Dear Admin:

Factorbook Motif Pipeline Backend Server stopped running at %s.
If this is not intended, please restart the backend server jobs.
Note that the last running jobs might be damaged and need to be rerun.

Best,

Factorbook Motif Pipeline Server
        '''%ctime()

        msg = MIMEText( email_body )

        # me == the sender's email address
        me = 'factorbookmotifpipeline@umassmed.edu'
        # you == the recipient's email address
        you = notify_email

        msg['Subject'] = 'Factorbook Motif Pipeline Backend Stopped'
        msg['From'] = me
        msg['To'] = you
	# Send the message via our own SMTP server, but don't include the
        # envelope header.
        s = smtplib.SMTP('localhost')
        s.sendmail(me, [you], msg.as_string())
        s.quit()
	

def notify_job_error( jobid ) :
	import smtplib
	from email.mime.text import MIMEText
	
        email_body = '''
Dear Admin:

Factorbook Motif Pipeline Backend Server found a problem 
while running a job (%s) at %s.
The job has been moved to the failed job directory for investigation.

Best,

Factorbook Motif Pipeline Server
        '''%(jobid, ctime())

        msg = MIMEText( email_body )

        # me == the sender's email address
        me = 'factorbookmotifpipeline@umassmed.edu'
        # you == the recipient's email address
        you = notify_email

        msg['Subject'] = 'Factorbook Motif Pipeline Backend Stopped'
        msg['From'] = me
        msg['To'] = you
	# Send the message via our own SMTP server, but don't include the
        # envelope header.
        s = smtplib.SMTP('localhost')
        s.sendmail(me, [you], msg.as_string())
        s.quit()
	
if __name__ == '__main__' :
	try :
		main()
	except :
		raise
	finally :
		notify_problem()
