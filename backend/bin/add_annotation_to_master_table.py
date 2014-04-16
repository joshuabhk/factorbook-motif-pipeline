#!/usr/bin/env python

import os, sys, glob

def get_motif_names( fn ) :
	fp = open( fn )
	header = fp.readline()
	motif_names = [None] * 5  #5 motifs should be tested!
	for l in fp :
		line = l.split()
		motif_id = int(line[0])-1 #0 start adjust!

		#Save the first motif name found by tomtom
		if motif_names[motif_id] :
			continue
		else :
			motif_names[motif_id] = line[1]
	for i, n in enumerate(motif_names) :
		if n :
			pass
		else :
			motif_names[i] = 'No match'

	fp.close()
	return motif_names
	

master_table_fn = 'master_table_template.txt'
fp = open( master_table_fn )

#target_dir_prefix = '/home/kimb/scratch/gr_pipeline_test/jobs/spp.idrOptimal.bf.'
tomtom_fn_template = 'top500.center.meme_tomtom_out/tomtom.txt'

print >>sys.stderr, 'header line is passed'
header = fp.readline().strip()
motif_index = 4

print header

for l in fp :
	line = l.strip().split( '\t' )
	name = line[0]

	#
	#tomtom_fn = tomtom_fn_template%name
	file_list = glob.glob( tomtom_fn_template )
	if len(file_list) == 1 :
		tomtom_fn = file_list[0]
	else :
		print >>sys.stderr, 'Error: multiple tomtom files found!', file_list
		print >>sys.stderr, name
		sys.exit()

	#check if the tomtom file exists!
	if not os.path.exists( tomtom_fn ) :
		print >>sys.stderr, "Error! %s not found!" % tomtom_fn
		continue

	motif_names = get_motif_names( tomtom_fn )
	
	for i,j in enumerate(xrange( motif_index, len(motif_names) + motif_index )) :
		line[j] = motif_names[i]

	print '\t'.join( line )
