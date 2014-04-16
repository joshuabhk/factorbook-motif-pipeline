#!/usr/bin/env python

import sys, os
from os.path import join, basename, dirname, exists
from os import system, chdir, makedirs
from glob import glob

from pwm import PWM
from xml.etree import ElementTree as et
from copy import copy

bin_dir = dirname( sys.argv[0] )

user_info_fn = 'user_info.txt'
master_template_fn = 'master_table_template.txt'
meme_chip_cmd = join( bin_dir, 'meme-chip.sh' )
add_annotation_cmd = join( bin_dir, 'add_annotation_to_master_table.py' )
master_table_fn = 'master.table.final.test'
top500_meme_fn = join( 'top500.center.meme_out','meme.txt' )
logo_summary_fn = 'logo_rc.summary'
memechip_summary_r = join( bin_dir, 'meme-chip.signalvalue.pct.dis.summary.R' )
memechipx_summary_r = join( bin_dir, 'meme-chip.signalvalue.pct.dis.summary.xTop500.R' )
peaknumber_fn = 'peak_numbers.txt' 
memechip_combine_cmd = join( bin_dir, 'combine_meme-chip.signal_value.pct.dis.summaries.py' )
plot_r = join( bin_dir, 'plot.meme-chip.signalvalue.pct.dis.sge.R' )

tomtom_dir = 'top500.center.meme_tomtom_out'
tomtom_result_fn = join( tomtom_dir, 'tomtom.xml' )

def mark_job_start() :
	fp = open( 'job_started', 'w' )
	print >>fp, 'job started!'
	fp.close()
	

def read_user_info() :
	fn = user_info_fn
	fp = open( fn )
	
	d = {}
	for l in fp :
		i, j = l.split(":")
		d[i] = j.strip()
	return d

def build_master_table_template( user_info ) :
	fn = master_template_fn
	fp = open( fn, 'w' )
	
	#user_info
	print >>fp, "spp_filename\tHGNC.ID\tCommon.Name\tcanonical.motif\tMOTIF1\tMOTIF2\tMOTIF3\tMOTIF4\tMOTIF5\tcell\ttreatment\tlab\textended_id\tmajor_class"
	print >>fp, "%(jobid)s\t%(jobname)s\t%(jobname)s\t\t\t\t\t\t\t%(cell)s\t%(treatment)s\t%(lab)s\t\tTFBS" % user_info
	fp.close()

def run_meme_chip( user_info ) :
	jobid = user_info['jobid']
	db = user_info['db']
	normtype = user_info['normtype']
	fileformat = user_info['fileformat']
	summitcol = user_info['summitcol']
	if summitcol and summitcol.starswith( 'col' ) :
		summitcol = str( int(sumitcol[3:]) )

	if normtype in ['center', 'summit'] :
		pass
	else :
		raise Exception( 'Normalization type is not recognized!', normtype )

	if fileformat in ['narrowpeak', 'bed'] :
		pass
	else :
		raise Exception( 'File format is not recognized!', fileformat )

	if fileformat == 'narrowpeak' :
		summitcol = '10'
		
	cmd = ' '.join( (meme_chip_cmd, jobid, '1', db, normtype, summitcol) )
	system( cmd )

def generate_tomtom_png( user_info ) :
	#the tomtom result file should be available in the current working direcotry

	jobid = user_info['jobid']

	motifs = []
	for l in open( logo_summary_fn  ) :
		l = l.split()
		print l
		if l and l[0] == jobid :
			motifs = l
			break

	orientations = [ 'r' if 'rc' in m else 'f' for m in motifs ]

	if not exists( tomtom_dir ) :
		raise Exception( tomtom_dir + ' does not exists!' )
	#chdir( tomtom_dir )

	tomtom = et.parse( tomtom_result_fn )
	motifs = {}
	for motif in tomtom.iter( 'motif' ) :
		motifs[ motif.attrib['id'] ] = motif

	#debug
	#for motif in motifs :
		#print motif.tag, motif.attrib

	#target_files = tomtom.iter( 'target_file' )
	queries = tomtom.iter( 'query' )

	for query in queries :
		query_motif = query.find('motif')

		qpwm = PWM( query_motif )
		querynum = int( query_motif.attrib['id'].split('_')[1] )

		print querynum, orientations
		if orientations[querynum] == 'f' :
			qpwm.generate_png( join( tomtom_dir, '%s_f.png'%query_motif.attrib['id'] ) )
			qpwm.reverse()
			qpwm.generate_png( join( tomtom_dir, '%s_r.png'%query_motif.attrib['id'] ) )
		else :
			qpwm.generate_png( join( tomtom_dir, '%s_r.png'%query_motif.attrib['id'] ) )
			qpwm.reverse()
			qpwm.generate_png( join( tomtom_dir, '%s_r.png'%query_motif.attrib['id'] ) )

		for i, match in enumerate( query.iter( 'match' ) ) :

			#print '*'*30
			#print i,":", match.attrib
			targetid = match.attrib['target']
			offset = int(match.attrib['offset']) #target offset
			orientation = match.attrib['orientation'] #target orientation

			target_motif = motifs[targetid]
			tpwm = PWM( target_motif )
			if orientation == 'forward' :
				pass
			elif orientation == 'reverse' :
				tpwm.reverse()

			qpwm = PWM( query_motif )
			qpwm.match( tpwm, offset )

			if orientations[querynum] == 'f' :
				qpwm.generate_png( join( tomtom_dir, '%s_m_%s_f.png' % (query_motif.attrib['id'],i) ) )
				tpwm.generate_png( join( tomtom_dir, '%s_m_%s_f_t.png' % (query_motif.attrib['id'],i) ) )
				#reversed
				qpwm.reverse()
				tpwm.reverse()
				qpwm.generate_png( join( tomtom_dir, '%s_m_%s_r.png' % (query_motif.attrib['id'],i) ) )
				tpwm.generate_png( join( tomtom_dir, '%s_m_%s_r_t.png' % (query_motif.attrib['id'],i) ) )
				#print '*'*30
				#print
			else :
				qpwm.generate_png( join( tomtom_dir, '%s_m_%s_r.png' % (query_motif.attrib['id'],i) ) )
				tpwm.generate_png( join( tomtom_dir, '%s_m_%s_r_t.png' % (query_motif.attrib['id'],i) ) )
				qpwm.reverse()
				tpwm.reverse()
	
				qpwm.generate_png( join( tomtom_dir, '%s_m_%s_f.png' % (query_motif.attrib['id'],i) ) )
				tpwm.generate_png( join( tomtom_dir, '%s_m_%s_f_t.png' % (query_motif.attrib['id'],i) ) )

def build_master_table( user_info ) :
	cmd = ' '.join( (add_annotation_cmd, master_template_fn, ">", master_table_fn ) )
	system( cmd )


def change_eps_fonts() :
	for eps in glob( join('*','*.eps') ) :
		fp = open( eps )
		old = fp.read()
		fp.close()

		fp = open( eps, 'w' )
		new = old.replace( "Helvetica-Bold", "Helvetica" )
		fp.write( new )
		fp.close()

def select_logo( nt ) :
	g = nt.count( 'G' )
	c = nt.count( 'C' )
	
	if g > c :
		return 'logo'
	elif g == c :
		a = nt.count( 'A' )
		t = nt.count( 'T' )
		if a > t :
			return 'logo'
		else :
			return 'logo_rc'
	else:
		return 'logo_rc'

def select_logo_fonts( user_info ) :
	fp = open( top500_meme_fn )
	motifid = 0
	summary_line = user_info['jobid']
	for l in fp :
		if l.startswith( 'Multilevel' ) :
			motifid += 1
			logo_string = select_logo( l.split()[1] )

			summary_line += '\t%s%d.eps' % (logo_string, motifid)
	fp.close()

	out_fp = open( logo_summary_fn, 'w' )
	print >>out_fp, summary_line
	out_fp.close()


def build_summary_tables( user_info ) :
	jobid = user_info['jobid']

	#get number of peaks
	fp = open(jobid)
	peak_number = len(fp.readlines())
	fp.close()
	
	#write peak number into peak_numbers.txt
	fp = open( peaknumber_fn, 'w' )
	print >>fp, peak_number, jobid
	fp.close()

	system( 'Rscript ' + memechip_summary_r )
	system( 'Rscript ' + memechipx_summary_r )
	system( memechip_combine_cmd )
	

def prepare_pdf( user_info ) :
	jobid = user_info['jobid']
	system( 'Rscript ' + plot_r + ' ' + jobid )

import smtplib
from email.mime.text import MIMEText
def notify( user_info ) :
	# Import smtplib for the actual sending function
	# Import the email modules we'll need

	# Open a plain text file for reading.  For this example, assume that
	# the text file contains only ASCII characters.
	# Create a text/plain message

	user_info['url'] = 'http://bib.umassmed.edu/factorbook/view/%(jobid)s' % user_info
	email_body = '''
Dear User:

Your job (ID:%(jobid)s, Job Name:%(jobname)s) has been completed.
You can check the discovered motifs at the following URL.
%(url)s

Best,

Factorbook Motif Pipeline Server
	''' % user_info

	msg = MIMEText( email_body )

	# me == the sender's email address
	me = 'factorbookmotifpipeline@umassmed.edu'
	# you == the recipient's email address
	you = user_info['email']

	msg['Subject'] = 'Factorbook Motif Pipeline Job %(jobname)s %(jobid)s' % user_info
	msg['From'] = me
	msg['To'] = you

	# Send the message via our own SMTP server, but don't include the
	# envelope header.
	s = smtplib.SMTP('localhost')
	s.sendmail(me, [you], msg.as_string())
	s.quit()

if __name__ == '__main__' :
	job_dir = sys.argv[1]
	return_path = sys.argv[2]

	chdir(job_dir)
	mark_job_start()
	
	jobid = basename( job_dir )

	user_info = read_user_info()
	user_info['jobid'] = jobid
	
	build_master_table_template( user_info )
	run_meme_chip( user_info )
	print "meme-chip.sh finished"
	build_master_table( user_info )
	print "build_master_table finished"
	change_eps_fonts()
	print "change_eps_fonts finished"
	select_logo_fonts( user_info )
	print "select_log_fonts finished"
	generate_tomtom_png( user_info )
	print "generate_tomtom_png finished"
	build_summary_tables( user_info )
	print "build_summary_tables finished"
	prepare_pdf( user_info )
	print "prepare_pdf finished"

	fp = open( jobid + '.completed', 'w' )
	print >>fp, "All done!"
	fp.close()

	#copy the results to frontend
	system( 'rsync -r ../%s/ %s' % (jobid,return_path) )
	#after copying remove the results from the backend
	system( 'rm -rf ../%s' % jobid ) 

	notify( user_info )
