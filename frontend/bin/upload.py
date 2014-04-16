import cherrypy
from os.path import join, basename
from jinja2 import FileSystemLoader
from os import system
from tempfile import mkdtemp

from settings import env, root_dir, user_dir, user_data_fn, jobserver, queuefile, job_dir, cmd_template


class Upload :
        exposed = True
        def __call__( self, myFile, email, db, fileformat, normtype, jobname, cell, treatment, lab, summitcol='' ) :
        # dealing uploaded file.
        # myFile contains file handle for the uploaded peak file
        # email should be given all the time!
        # fileformat value can be either 'narrowpeak' or 'bed'
        # db can be 'hg19' or 'mm9' depending on which genome the experiment were performed.
        # normtype can be 'summit' or 'center'
        # summitcol should be either None or 'col<column number>' where the column number should be
        # in 1 based ordering
        # jobname can be either None or name of the job or TF depending on the user input.

        ## This is very useful trick to check the internal structure of submitted and parsed values.
        #def __call__( self, **kwargs ) :
                #print kwargs
                #return

                tmpl = env.get_template( 'uploaded.html' )

                #1. make the save_dir
                save_dir = mkdtemp( dir=user_dir, prefix='fmp' )
                jobid = basename( save_dir )

                #2. save  uploaded file into the save_dir
                save_fn = join( save_dir, jobid )
                save_fp = open( save_fn, 'w' )
                size = 0
                while True:
                    data = myFile.file.read(8192)
                    if not data:
                        break
                    size += len(data)
                    save_fp.write( data )
                save_fp.close()

                #3. save user information
                data_fp = open( join( save_dir, user_data_fn ), "w" )
                print >>data_fp, "jobname:", jobname
                print >>data_fp, "cell:", cell
                print >>data_fp, "treatment:", treatment
                print >>data_fp, "lab:", lab
                print >>data_fp, "email:", email
                print >>data_fp, "filename:", myFile.filename
                print >>data_fp, "mime-type:", myFile.content_type
                print >>data_fp, 'db:', db
                print >>data_fp, 'normtype:', normtype
                print >>data_fp, 'fileformat:', fileformat
                print >>data_fp, 'summitcol:', summitcol
                data_fp.close()

                #4. submit the jobscript
                self.submit(jobid)

                return tmpl.render( filename=myFile.filename, jobname=jobname, email=email, jobid=jobid, size=size, mimetype=myFile.content_type )

        def submit( self, jobid ) :
                data_dir = join( user_dir, jobid )
                #submission code will be here!
                copy = system( "rsync -r %s %s:%s" % (data_dir,jobserver,job_dir) )
                if copy != 0 :
                        raise Exception( "Copying Failed.", jobid, email, jobname, myFile.filename )

                #cmd = cmd_template % {"jobid":jobid}
                #queue = system( 'echo %s | ssh %s "cat >> %s"' % (cmd, jobserver, queuefile) )
                return

