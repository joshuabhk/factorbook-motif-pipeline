#!/usr/bin/env python

##this script combine two tables using peak_number.txt file.
import os, sys, re

def read_peak_numbers() :
	fp = open( 'peak_numbers.txt' )
	rt = {}
	for l in fp :
		line = l.split()
		peak_num = int(line[0])
		rt[line[-1]] = peak_num
		#m = re.search( 'spp.idrOptimal.mm9.(.*).bam_', line[-1] )
		#if m :
			#debugging
			#print m.group(1)
			#rt[m.group(1)] = peak_num

	return rt


peak_numbers = read_peak_numbers()

fp1 = open( 'meme-chip.signalvalue.pct.dis.xTop500.summary' )
fp2 = open( 'meme-chip.signalvalue.pct.dis.summary' )

save_fp = open( 'meme-chip.signalvalue.pct.dis.combined.summary', 'w' )

for l1, l2 in zip( fp1, fp2 ) :
	line1 = l1.strip().split('\t')
	line2 = l2.strip().split('\t')

	if line1[0] != line2[0] :
		print "error!"
		sys.exit()

	if peak_numbers[line1[0]] < 600 :
		print >>save_fp, '\t'.join(line2)
	else :
		print >>save_fp, '\t'.join(line1)



