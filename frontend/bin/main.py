import cherrypy
from os.path import join, exists, basename, getmtime
from os import makedirs
from time import ctime

#setting information is in settings module
from settings import servername, hostaddress, hostparent
from settings import env, root_dir, user_dir, user_data_fn, jobserver, queuefile, job_dir, cmd_template, admin_email, reference, exampleid

last_updated_time = ctime(getmtime(__file__))

class CleanUp :
	#cleanup function!
	exposed = True
	def __call__( self, ID=None, PW=None, initialize=False ) :
		pass

from view import View, MotifData, MotifScore, MotifLogoPNG, MotifPDF
from upload import Upload
class Root:
    def __init__( self ) :
	self.upload = Upload()
	self.view = View()
	self.motifdata = MotifData()
	self.motifscore = MotifScore()
	self.motiflogo = MotifLogoPNG()
	self.pdf=MotifPDF()

    @cherrypy.expose
    def index(self):
        tmpl = env.get_template('index.html')
        return tmpl.render( hostaddress=hostaddress, 
		admin_email=admin_email,
		reference=reference,
		servername=servername, 
		hostparent=hostparent,
		exampleid=exampleid, 
		last_updated_time=last_updated_time )

cherrypy.config.update({'server.socket_host': '127.0.0.1',
                         'server.socket_port': 13246,
                        })
config = { 
	'/': {'tools.staticdir.root': "/home/kimb/factorbook_motif_pipeline/frontend" }, 
	'/css':
		{ 'tools.staticdir.on': True,
                  'tools.staticdir.dir': "css"
		},
	'/doc':
		{ 'tools.staticdir.on': True,
                  'tools.staticdir.dir': "doc"
		}
	}

cherrypy.quickstart(Root(), '/', config=config)
