from flask import render_template, flash, redirect, url_for, request, g, ctx, jsonify
from app import app, db #import the app instance from the app package
from app.forms import LoginForm, RegistrationForm, GroupForm, PostForm, SearchForm,CommentForm, MessageForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Group, Post, Comment, Message, Notification
from datetime import datetime

@app.before_request
def before_request():
	ctx._AppCtxGlobals.searchForm = SearchForm()

@app.route('/add')
def add():
	return render_template('add.html')

@app.route('/calculate')
def calculate():
	a = request.args.get('a', 0, type=int)
	b = request.args.get('b', 0, type=int)
	return jsonify(result=a+b)

@app.route('/')
@app.route('/index')
@login_required
def index():	
	#ctx._AppCtxGlobals.searchForm = SearchForm() #this is really weird...	
	return render_template('index.html')

@app.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
	user = User.query.filter_by(username=recipient).first()
	messageForm = MessageForm()

	if messageForm.validate_on_submit():
		message = Message(sender=current_user, recipient=user, body=messageForm.message.data)
		db.session.add(message)		
		db.session.commit()
		user.add_notification('unread_message_count', user.new_messages())		
		flash('Your message has been sent.')		

	return render_template('send_message.html', messageForm=messageForm)

@app.route('/messages')
@login_required
def messages():
	current_user.last_message_read_time = datetime.utcnow()
	db.session.commit()
	current_user.add_notification('unread_message_count', 0)
	messages = current_user.messages_received.order_by(Message.timestamp.desc())
	return render_template('message.html', messages=messages)

@app.route('/explore')
@login_required
def explore():
	groups = Group.query.all()
	return render_template('explore.html', groups=groups)

@app.route('/my_groups')
@login_required
def my_groups():
	groups = current_user.groups
	return render_template('my_groups.html', groups=groups)


@app.route('/group/<groupname>', methods=['GET', 'POST'])
@login_required
def group(groupname):
	group = Group.query.filter_by(name=groupname).first()

	if not group.hasMember(current_user):
		flash('Sorry, you are not a member of that group')		
		return redirect(url_for('index'))

	posts = Post.query.filter_by(group=group).order_by(Post.timestamp.desc())
	comments = Comment.query.filter_by(group=group).order_by(Comment.timestamp.asc())
	postId = request.args.get('postId', type=int)
	users = User.query.all()

	
	commentForm = CommentForm()
	postForm = PostForm()

	#validate_on_submit inspects the contents of request.form for validation
	#I inspect the comments of request.form to determine whether the postForm or commentForm was submitted
	if request.form.get('commentText') and commentForm.validate_on_submit(): 
		comment = Comment(text=commentForm.commentText.data, post=Post.query.filter_by(id=postId).first(), author=current_user, group=group)
		db.session.add(comment)
		db.session.commit()		
		return redirect(url_for('group', groupname=group.name))
	
	if request.form.get('text') and postForm.validate_on_submit():
		post = Post(text=postForm.text.data, group=group, author=current_user)
		db.session.add(post)
		db.session.commit()		
		return redirect(url_for('group', groupname=group.name))

	return render_template('group.html', users=users, group=group, postForm=postForm, commentForm=commentForm, posts=posts, Comment=Comment, comments=comments)

@app.route('/add_member')
@login_required
def add_member():
	userId = request.args.get('userId', type=int)
	groupId = request.args.get('groupId', type=int)
	user = User.query.filter_by(id=userId).first()
	group = Group.query.filter_by(id=groupId).first()
	if not group.hasMember(user):
		group.users.append(user)
		db.session.commit()
	return redirect(url_for('group', groupname=group.name))	


@app.route('/delete', methods=['POST'])
@login_required
def delete():
	postId = request.args.get('postId', type=int)	
	groupname = request.args.get('groupname')	
	post = Post.query.filter_by(id=postId).first()
	comments = Comment.query.filter_by(post_id=postId)
	if post:	
		db.session.delete(post)	
	for comment in comments:
		db.session.delete(comment)
	db.session.commit()
	return redirect(url_for('group', groupname=groupname))

@app.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('index'))

	form = LoginForm()

	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user is None or not user.check_password(form.password.data):
			flash('Invalid username or password')
			return redirect(url_for('login'))
		login_user(user, remember=form.remember_me.data)
		return redirect(url_for('index'))
				 

	return render_template('login.html', form=form)

@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('index'))

	form = RegistrationForm()

	if form.validate_on_submit():
		user = User(username=form.username.data, email=form.email.data)
		user.set_password(form.password.data)
		db.session.add(user)
		db.session.commit()
		flash('Congratulations, you are now a registered user!')
		return redirect(url_for('login'))


	return render_template('register.html', form=form)

@app.route('/create_group', methods=['GET', 'POST'])
@login_required
def createGroup():
	form = GroupForm()

	if form.validate_on_submit():
		group = Group(name=form.name.data)
		current_user.groups.append(group)
		db.session.add(group)
		db.session.commit()
		flash('Congratulations, you have now created a new group!')
		return redirect(url_for('index'))

	return render_template('create_group.html', form=form)

@app.route('/search')
@login_required
def search():
	#Something seems to be wrong with g.searchForm
	searchData = request.args.get('q')
	if not searchData:
		return redirect(url_for(index))

	'''if not g.searchForm.validate():
		return "tf"
		return redirect(url_for('index'))'''
	page = request.args.get('page', 1, type=int)
	
	groups, total = Group.search(searchData, page, app.config['POSTS_PER_PAGE'])
	next_url = url_for('search', page=page+1) if total > page * app.config['POSTS_PER_PAGE'] else None
	prev_url = url_for('search', page=page-1) if page > 1 else None
	return render_template('search.html', groups=groups, next_url=next_url, prev_url=prev_url, data=searchData, total=total)
	
@app.route('/notifications')
@login_required
def notifications():
	since = request.args.get('since', 0.0, type=float)		
	#only retrieve notficiations that have occurred since the last notification you've seen
	notifications = current_user.notifications.filter(Notification.timestamp > since).order_by(Notification.timestamp.asc())
	return jsonify([{'name': n.name, 'data': n.get_data(), 'timestamp': n.timestamp} for n in notifications])
	#i think you have to return a json object for the ajax request
