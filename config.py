import os
basedir = os.path.abspath(os.path.dirname(__file__))
#basedir stores the name of the main directory of the application

class Config(object):
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'very-excellent-password'
	#SECRET_KEY used by FLASK_WTF to protect against CSRF attacks
	SQLALCHEMY_DATABASE_URI = 'mysql://sql9242034:3rAqU4iMrU@sql9.freemysqlhosting.net:3306/sql9242034'
	#Using a MySQL database
	#mysql://username:password.databasehost:port_number/database_name
	#Flask-SQLAlchemy take the location of the application's database from this variable
	#configures a database named app.db located in the main directory of the application
	SQLALCHEMY_TRACK_MODIFICATIONS = False

	ELASTICSEARCH_URL = 'http://localhost:9200' #os.environ.get('ELASTICSEARCH_URL')
	#I defined the ELASTICSEARCH_URL environment variable in command prompt with 'set'
	#that doesn't seem to be working, so im just setting it directly here 

	POSTS_PER_PAGE = 5