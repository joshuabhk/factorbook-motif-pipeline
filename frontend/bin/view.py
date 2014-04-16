import cherrypy
from json import JSONEncoder
from os.path import join, exists
from glob import glob
from xml.etree import ElementTree

#setting information from settings module
from settings import servername, hostaddress, admin_email, reference, hostparent
from settings import env, root_dir, user_dir, user_data_fn, jobserver, queuefile, job_dir, cmd_template
from settings import read_user_info, filter_cutoffs
from settings import read_logo_rc_file, motif_logo_dir, matched_motif_logo_dir
from settings import max_motif_id #maximum motif discovery value, currently set to 5.
from settings import tomtom_result_fn

#does not need anymore!
#from gviz_api import DataTable

def read_plot_data_file( fn ) :
	''' read linear array file'''
	fp = open( fn )
	a = []
	for l in fp :
		l = l.strip()
		try :
			a.append(float(l))
		except ValueError:
			a.append( None )
	return a


def read_score_data_file( fn ) :
	''' read linear array file'''
	fp = open( fn )
	a = []
	for l in fp :
		l = l.strip()
		if 'Inf' in l :
			l = '100.0'
		try :
			a.append(float(l))
		except ValueError:
			a.append( None )
	return a

def read_score_data_files( motifids, fns ) :
	'''read linear array score files'''
	score_data = {}
	for motifid, fn in zip( motifids, fns ) :
		data = read_score_data_file( fn )
		score_data[motifid] = data
	return score_data


class JobFailureError( Exception ) :
	pass

class View :
        exposed = True
        def __call__( self, jobid ) :
		info = read_user_info( jobid )
		try :
			if self.is_completed(jobid ) :
				tmpl = env.get_template( 'view.html' )
				motifids = range( 1, max_motif_id+1 )
				selection = self.select_tomtom_matches( jobid )
				motifscore = MotifScore( jobid )
				passed_motifids = motifscore.get_passed_motifids()

				return tmpl.render( servername=servername,
					hostaddress=hostaddress,
					hostparent=hostparent,
					jobid=jobid, 
					userInfo=info,
					motifids=motifids, 
					passed_motifids= passed_motifids,
					selection=selection,
					reference=reference, 
					admin_email=admin_email )
			else :
				tmpl = env.get_template( 'view_check.html' )
				check_result = '<b>Your job has not been finished yet. Check few minutes later.</b>'
				return tmpl.render( servername=servername,
					check_result= check_result,
					hostparent=hostparent,
					jobid=jobid, 
					userInfo=info,
					reference=reference, 
					admin_email=admin_email )

		except JobFailureError :
			tmpl = env.get_template( 'view_check.html' )
			check_result = '<strong>A problem occurred while processing your job. We are working on it and we will get back to you shortly.</strong>'
			return tmpl.render( servername=servername,
				check_result= check_result,
				hostparent=hostparent,
				jobid=jobid, 
				userInfo=info,
				reference=reference, 
				admin_email=admin_email )



	'''
	def read_plot_data( self, jobid, motifids ) :
		#returns list of JS codes of motif data as DataTable
		datatables = []
		for motifid in motifids :
			motifdata = MotifData()
			datatables.append( motifdata.getDataTable().ToJSCode('data'+motifid) )
		return datatables
	'''

	def is_completed( self, jobid ) :
		'''
		Check if the job is completed by the pipeline
		'''
		job_dir = join( user_dir, jobid )
		started_marker = join( job_dir, 'job_started' )
		finished_marker = join( job_dir, jobid+'.completed' )
		if exists( finished_marker ) :
			return True
		elif exists( started_marker ) :
			raise JobFailureError( 'job failed ' + jobid )
		else :
			return False


	def select_tomtom_matches( self, jobid ) :
		'''
		parse tomtom result xml file
		and select the most significant matches to each query motif
		and return the list of selected matches.
		'''

		tomtom = ElementTree.parse( join( user_dir, jobid, tomtom_result_fn ) ).getroot()

		#selection is dict of dict
		#selection[ query_index ][ target_file_index ]
		selection = {} 
		
		target_files = {}
		target_motifs = {} #need to be used for correcting the match name and find correct TF name
		for target_file in tomtom.getiterator('target_file') :
			target_files[ target_file.attrib['index'] ] = target_file
			for target_motif in target_file.getiterator('motif') :
				target_motifs[ target_motif.attrib['id'] ] = target_motif

		#assume that the max index is equal to the # of targets
		max_key_num = max( [ int(k) for k in target_files.keys() ] ) 

		for query in tomtom.getiterator( 'query' ) :
			query_id = query.find( 'motif' ).attrib['id']
			selected_matches = {}

			for i, match in enumerate( query.getiterator( 'match' ) ) :
				target_id = match.attrib['target']
				target_id_marker, target_file_index = target_id.split('_')[:2]

				target_motif = target_motifs[ target_id ]
				assert target_id_marker == 't'
		
				if not target_file_index in selected_matches : #newly found match in the database
					match.attrib['id'] = query_id + '_m_%d' %i 
					match.attrib['target_name'] = target_motif.attrib['name'] #motif name to be used
					match.attrib['target_altname'] = target_motif.attrib.get( 'alt' )

					selected_matches[ int(target_file_index) ] = match.attrib
				else :
					continue

			motif_id = int(query_id.split('_')[1])
			if selected_matches :
				selection[motif_id] = selected_matches
					
		return selection
				
class MotifData:
        exposed = True
        def __call__( self, jobid, motifid=None ) :
                cherrypy.response.headers['Content-Type'] = 'application/json'
		self.datatable = self.getDataTable( jobid, motifid )
		#return datatable.ToJSon() 
		jsonencoder = JSONEncoder() 
		return jsonencoder.encode( self.datatable )

	def getDataTable( self, jobid, motifid ):
		'''
		returns a DataTable object for further processing
		'''
		job_dir = join( user_dir, jobid )
		binSizeFn = join( job_dir, jobid+'.binSize' )
		centerFractionFn = join( job_dir, jobid+'.centerPeakFraction.'+motifid )
		flankingFractionFn = join( job_dir, jobid+'.flankingPeakFraction.'+motifid )
		avgDistanceFn = join( job_dir, jobid+'.avgDistanceToSummit.'+motifid )

		binsize = int(open(binSizeFn).read().strip())
		center = read_plot_data_file( centerFractionFn )
		flanking = read_plot_data_file( flankingFractionFn )
		distance = read_plot_data_file( avgDistanceFn )

		#v: and f: would be a good thing to do!
		rcenter = [ '%.3e'%x if x is not None else x for x in center ]
		rflanking = [ '%.3e'%x if x is not None else x for x in flanking ]
		rdistance = [ '%.3e'%x if x is not None else x for x in distance ]

		data = [ {'c':[{'v':binsize*i,'f':binsize*i},{'v':c,'f':rc},{'v':f,'f':rf},{'v':d,'f':rd}]} for i, (c,rc,f,rf,d,rd) in enumerate( zip(center,rcenter,flanking,rflanking,distance,rdistance) ) ]
		#rows = {'rows': data}
		
		cols = [ {'type':'number', 'id':'Peak', 'label':'Peak'}, {'type':'number','id':'Peak Fraction','label':'Peak Fraction'},{'type':'number','id':'Flanking Fraction','label':'Flanking Fraction'},{'type':'number','id':'Distance to Summit','label':'Distance to Summit'} ]

		#data = [ (binsize*i,c,f,d) for i, (c,f,d) in enumerate( zip(center,flanking,distance) ) ]
		#datatable = DataTable( [('Peak','number'),('Peak Fraction','number'),('Flanking Fraction','number'), ('Distance to Summit','number')  ] )
		#datatable.AppendData( data )
		#return datatable
		
		return {'rows': data, 'cols':cols}

class MotifScore( MotifData ):
	def getDataTable( self, jobid, motifid=None ):
		'''
		returns a DataTable object for further processing
		'''
		job_dir = join( user_dir, jobid )
		if motifid != None :
			motifids = [ int(motifid) ]
			score_fns = [join( job_dir, jobid+'.score.'+motifid )]
		else :
			score_fns = glob( join(job_dir, jobid+'.score.*') )
			motifids = [ int( fn.split('.score.')[-1] ) for fn in score_fns ]
		
		motifscores = read_score_data_files( motifids, score_fns )
		c0, c1, c2 = filter_cutoffs['T1'], filter_cutoffs['T2'], filter_cutoffs['T2/C2']

		#data = [ (k,v[0],v[1],v[2],True) if v[0]<=c0 and v[1]>c1 and v[2]>c2 else (k,v[0],v[1],v[2],False) for k, v in sorted( motifscores.iteritems() ) ]
		#datatable = DataTable( [('Motif ID','number'),('T1','number'),('T2','number'), ('T2/C2','number'), ('Filtered','boolean') ] )
		#datatable.AppendData( data )
		data = [ {'c':(
			{'v':k,'f':k},
			{'v':v[0],'f':'%.2e'%v[0]},
			{'v':v[1],'f':'%d'%(v[1]*100)},
			{'v':v[2],'f':'%.1f'%v[2]},
			{'v':True,'f':'True'}) } 
		if v[0]<=c0 and v[1]>c1 and v[2]>c2 else {'c':(
			{'v':k,'f':k},
			{'v':v[0],'f':'%.2e'%v[0]},
			{'v':v[1],'f':'%d'%(v[1]*100)},
			{'v':v[2],'f':'%.1f'%v[2]},
			{'v':False,'f':'False'})} 
		for k, v in sorted( motifscores.iteritems() ) ]

		description = [
			{'type':'number','id':'Motif ID', 'label':'Motif ID'},
			{'type':'number', 'id':'T1','label':'GC content p-value'},
			{'type':'number','id':'T2','label':'Percent of motif instances in peak regions'},
			{'type':'number', 'id':'T2/C2','label':'(Percent of motif instances in peaks) / (Percent of motif instances in flanking regions)'},
			{'type':'boolean','id':'Filtered', 'label':'Filtered'}
		]

		datatable = {'rows':data, 'cols':description}
		return datatable


	def __init__( self, jobid=None ) :
		if jobid :
			self.datatable = self.getDataTable( jobid )
			

	def get_passed_motifids( self ) :
		passed= []
		for row in self.datatable['rows'] :
			motifid = row['c'][0]['v']
			test_result = row['c'][4]['v']
			if test_result :
				passed.append( motifid )
		return passed


class MotifLogoPNG :
	def _get_png_data(self, jobid, motifid):
		"""This method should return the png data"""
		''' motif id need to be processed!'''

		#query motif id: < query motif number >
		# e.g. 1, 2, ... 5

		#query motif id matched to the target
		# q<query motif id>_m<match number>_<f|r forward or backward>[_t optional postfix for target motif]

		#match motif
		if '_' in motifid :
			png_fn = join( user_dir, jobid, matched_motif_logo_dir, motifid+'.png' )
		#query only motif
		else :
			logo_rc = read_logo_rc_file( jobid )
			motifid = int( motifid )
			logo = logo_rc[ motifid-1 ] #need to convert to 0 based index
			#old way by getting png file from meme_output
			#png_fn = join( user_dir, jobid, motif_logo_dir, logo )

			#new way by getting png file from tomtom generated by weblogo
			if 'rc' in logo :
				png_fn = join( user_dir, jobid, matched_motif_logo_dir, 'q_%d_r.png'%motifid )
			else :
				png_fn = join( user_dir, jobid, matched_motif_logo_dir, 'q_%d_f.png'%motifid )
		return open(png_fn).read()

	exposed = True
	def __call__(self, jobid, motifid):
		cherrypy.response.headers['Content-Type'] = 'image/png'
		return self._get_png_data( jobid, motifid )


class MotifPDF :
	def _get_pdf_data(self, jobid):
		"""This method should return pdf data"""
		#new way by getting png file from tomtom generated by weblogo
		pdf_files = glob( join( user_dir, jobid, '*.pdf' ) )
		if pdf_files :
			return open(pdf_files[0]).read()
		else :
			raise Exception( "No PDF file found!", jobid )

	exposed = True
	def __call__(self, jobid):
		cherrypy.response.headers['Content-Type'] = 'application/pdf'
		return self._get_pdf_data( jobid )


