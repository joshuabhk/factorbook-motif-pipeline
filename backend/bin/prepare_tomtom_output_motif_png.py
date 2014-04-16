#!/usr/bin/env python

import sys
from os import makedirs, chdir
from os.path import join, exists
from xml.etree import ElementTree as et
from fabric.api import local
from tempfile import NamedTemporaryFile
from copy import copy
#This script will parse the tomtom result xml file and generate png files for matched motifs.
nmotif = 5 #the maximum number of motifs to be parsed and checked!

class PWM :
	def __init__( self, motif ) :
		self.weights = []
		self.tomtom_xml_motif = motif

		self.parse_tomtom_xml_motif( self.tomtom_xml_motif )
		self.orientation = 'forward'


	def __len__( self ) :
		return len(self.weights)

	def get_motifid( self ) :
		return self.tomtom_xml_motif.attrib['id']

	def parse_tomtom_xml_motif( self, motif ) :

		print
		print motif.attrib
		for i, pos in enumerate(motif.iterfind( 'pos' )) :
			#if int(pos.attrib['i']) -1 == i :
				#pass
			#else :
				#raise Exception( 'tomtom XML contains start not 1 or non continuous in the position number', motif.attrib['id'], pos.attrib, i )
			print pos.attrib
			self.weights.append( copy(pos.attrib) )
	
	def to_transfac( self, fp, order=['A','C','G','T'] ) :
		print >>fp, 'PO', ' '.join( order )
		for i, w in enumerate( self.weights ) :
			#print w
			print >>fp, i+1, ' '.join( [ str(w[n]) for n in order ] )

	def push( self, n=1, w={'A':0.25,'C':0.25,'G':0.25,'T':0.25} ) :
		print self.get_motifid, ': pushing', n, 'times'
		for i in xrange(n ) :
			self.weights.insert(0,w)
			print 'pwm length:', len(self)

	def append( self, n=1, w={'A':0.25,'C':0.25,'G':0.25,'T':0.25} ) :
		for i in xrange(n ) :
			self.weights.append(w)

	def reverse( self ) :
		self.weights = self.weights[::-1]
		n = 0
		for w in self.weights :
			if 'i' in w :
				n += 1
				w['i'] = str(n)
				w['A'], w['C'], w['G'], w['T'] = w['T'], w['G'], w['C'], w['A']

		if self.orientation == 'forward' :
			self.orientation = 'reverse'
		elif self.orientation == 'reverse' :
			self.orientation = 'forward'
		else :
			raise Exception( self.orientation )


	def generate_png( self, fn ) :
		'''
		generate png file of the pwm
		This function prints the PWM as transfac format into a temporary file
		then run weblogo3 python program to make the PNG file.

		Note that the X axis coordinates are printed as in the original PWM 
		before the extensions in the either end for the alignment purposes.
		'''
		fp = NamedTemporaryFile()
		tempfn = fp.name
		self.to_transfac( fp )
		fp.flush()

		xlabel = ','.join( [ w['i'] if 'i' in w else "" for w in self.weights ] )

		local( "weblogo -f %s -F png -o %s  --errorbars False --composition none --color red A 'Adenine' --color gold G 'Guanine' --color blue C 'Cytosine' --color green T 'Thymine' --annotate '%s'"%(tempfn,fn,xlabel) )

		
	def match( self, pwm, offset ) :
		'''
		match self (query PWM) to pwm (target PWM) by the offset
		and extends self or pwm according to the offset.
		The offset is as in the value given in the tomtom xml output.
		'''
		if offset < 0 :
			pwm.push( -offset )
		elif offset > 0 :
			self.push( offset )

		offset = len(pwm)-len(self)
		if offset < 0 :
			pwm.append( -offset )
		elif offset > 0 :
			self.append( offset )
		

#the tomtom result file should be available in the current working direcotry
tomtom_dir = 'top500.center.meme_tomtom_out'
if not exists( tomtom_dir ) :
	raise Exception( tomtom_dir + ' does not exists!' )
chdir( tomtom_dir )

tomtom_result_fn = 'tomtom.xml'

tomtom = et.parse( tomtom_result_fn ).getroot()
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
	qpwm.generate_png( '%s_f.png'%query_motif.attrib['id'] )
	qpwm.reverse()
	qpwm.generate_png( '%s_r.png'%query_motif.attrib['id'] )

	for i, match in enumerate( query.iter( 'match' ) ) : 

		print '*'*30
		print i,":", match.attrib
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

		qpwm.generate_png( '%s_m_%s_f.png' % (query_motif.attrib['id'],i) )
		tpwm.generate_png( '%s_m_%s_f_t.png' % (query_motif.attrib['id'],i) )

		#reversed
		qpwm.reverse()
		tpwm.reverse()
		
		qpwm.generate_png( '%s_m_%s_r.png' % (query_motif.attrib['id'],i) )
		tpwm.generate_png( '%s_m_%s_r_t.png' % (query_motif.attrib['id'],i) )
		print '*'*30
		print

		
