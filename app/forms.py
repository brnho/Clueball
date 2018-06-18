from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from app.models import User
from flask import request


class LoginForm(FlaskForm): #inherits from FlaskForm class
	username = StringField('Username', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])
	remember_me = BooleanField('Remember Me')
	submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired()])
	email = StringField('Email', validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Register')

	#these custom validators are invoked in addition to the stock validators 
	def validate_username(self, username):
		user = User.query.filter_by(username=username.data).first()
		if user is not None:
			raise ValidationError('Sorry, that username is already taken.')

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user is not None:
			raise ValidationError('Sorry, that email address is already taken.')

class GroupForm(FlaskForm):
	name = StringField('Group Name', validators=[DataRequired()])
	submit = SubmitField('Create group')

class PostForm(FlaskForm):
	text = TextAreaField('What\'s on your mind?', validators=[DataRequired()])
	submit = SubmitField('Submit')

class CommentForm(FlaskForm):
	commentText = StringField('Write a comment', validators=[DataRequired()])	

class SearchForm(FlaskForm):
	q = StringField('Search for groups', validators=[DataRequired()])	

	def __init__(self, *args, **kwargs):
		kwargs['formdata'] = request.args
		#formdata determnies where Flask-WTF gets form submissions.
		#default = request.form for POST requests. Use request.args for GET requests since the field values
		#are in the query string.
		kwargs['csrf_enabled'] = False
		super(SearchForm, self).__init__(*args, **kwargs)

class MessageForm(FlaskForm):
	message = TextAreaField('Send a private message', validators=[DataRequired()])
	submit = SubmitField('Submit')