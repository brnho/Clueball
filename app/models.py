from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from datetime import datetime
from app.search import add_to_index, remove_from_index, query_index
import json

#whenever any changes are made to the models, you must run the commands:
#flask db migrate -m "description text"
#flask db upgrade
#these commands generate migration scripts and then apply those changes

#when adding/removing data from a database (not changing its schema), use:
#db.session.add(model object)
#db.session.commit()
#db.session.rollback() is used to abort the session and remove any changes stored in it

#UserMixin adds these items to the User model:
#is_authenticated, is_active, is_anonymous, get_id()

association_table = db.Table('association', db.Column('group_id', db.Integer, db.ForeignKey('group.id')), 
	db.Column('user_id', db.Integer, db.ForeignKey('user.id')))

class SearchableMixin(object):
	@classmethod #cls replaces self as the default first argument
	def search(cls, expression, page, per_page):
		ids, total = query_index(cls.__tablename__, expression, page, per_page)
		if total == 0:
			return cls.query.filter_by(id=0), 0
		when = []
		for i in range(len(ids)):
			when.append((ids[i], i)) #a tuple
		return cls.query.filter(cls.id.in_(ids)).order_by(db.case(when, value=cls.id)), total

	@classmethod
	def before_commit(cls, session):
		session._changes = {
		'add': list(session.new),
		'update': list(session.dirty),
		'delete': list(session.deleted)
		}

	@classmethod
	def after_commit(cls, session):
		for obj in session._changes['add']:
			if isinstance(obj, SearchableMixin):
				add_to_index(obj.__tablename__, obj)
		for obj in session._changes['update']:
			if isinstance(obj, SearchableMixin):
				add_to_index(obj.__tablename__, obj)
		for obj in session._changes['delete']:
			if isinstance(obj, SearchableMixin):
				remove_from_index(obj.__tablename__, obj)

		session._changes = None

	@classmethod
	def reindex(cls):
		for obj in cls.query:
			add_to_index(cls.__tablename__, obj)

db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)
#all session events will be intercepted, but after_commit's isInstance check will
#ensure that only classes which inherit SearchableMixin get added to the search index

class User(UserMixin, db.Model): #db.Model is a base class for all models from Flask-SQLAlchemy
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	password_hash = db.Column(db.String(128))
	#group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
	comments = db.relationship('Comment', backref='author', lazy='dynamic')
	posts = db.relationship('Post', backref='author', lazy='dynamic')
	messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
	messages_received = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy='dynamic')
	notifications = db.relationship('Notification', backref='user', lazy='dynamic')
	#high level abstraction of the relationship (one to many)

	last_message_read_time = db.Column(db.DateTime)

	def __repr__(self): #how to print objects of this class
		return '<User {}>'.format(self.username)

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

	def new_messages(self):
		last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
		return Message.query.filter_by(recipient=self).filter(Message.timestamp > last_read_time).count()

	def add_notification(self, name, data):
		self.notifications.filter_by(name=name).delete()
		#get rid of duplicate notifications
		n = Notification(name=name, payload_json=json.dumps(data), user=self)
		#json.dumps converts a python object into a json string
		db.session.add(n)
		db.session.commit()


class Post(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	text = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
	comments = db.relationship('Comment', backref='post', order_by="Comment.timestamp", lazy='dynamic')	

class Comment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	text = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	post_id = db.Column(db.Integer, db.ForeignKey('post.id')) 
	group_id = db.Column(db.Integer, db.ForeignKey('group.id'))

class Group(SearchableMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(120), unique=True)
	users = db.relationship('User', secondary=association_table, backref='groups', lazy='dynamic')
	posts = db.relationship('Post', backref='group', lazy='dynamic')
	comments = db.relationship('Comment', backref='group', lazy='dynamic')
	searchable=['name'] #indicates which fields need to be included in the search index

	def __repr__(self): #how to print objects of this class
		return '<Group {}>'.format(self.name)
	def hasMember(self, user):
		return self.users.filter(association_table.c.user_id == user.id).count() > 0

class Message(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	body = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

class Notification(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(128), index=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	payload_json = db.Column(db.Text)

	def get_data(self):
		return json.loads(str(self.payload_json))
		#json.loads() function from python standard library decodes JSON string into a Python object
		#json.dumps() does the opposite, turns an object into a JSON string 

#user loader function, called to load a user given the ID
@login.user_loader
def load_user(id):
	return User.query.get(int(id))