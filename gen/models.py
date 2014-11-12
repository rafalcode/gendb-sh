from gen import db

class User(db.Model):
	user_name				= db.Column(db.String(45), index=True, unique=True, primary_key=True)
	email						= db.Column(db.String(45))
	password				= db.Column(db.String(128))

	log_entry				= db.relationship('Log', backref='log', lazy='dynamic')

	def is_authenticated(self):
		return True
	
	def is_active(self):
		return True

	def is_anonymous(self):
		return False
	
	def get_id(self):
		return unicode(self.user_name)

	def __repr__(self):
		return '<User %r>' % (self.user_name) 





class Project(db.Model):
	project_id				= db.Column(db.Integer, primary_key=True)
	name							= db.Column(db.String(100))
	description				= db.Column(db.String(500))
	individual				= db.relationship('Individual', backref='individual', lazy='dynamic')
	

class Log(db.Model):
	idlog							= db.Column(db.Integer, primary_key=True)
	timestamp					= db.Column(db.Integer)
	user_id						= db.Column(db.String(64), db.ForeignKey('user.user_name'))
	action						= db.Column(db.String(400))

class Individual(db.Model):
	individual_id			= db.Column(db.Integer, primary_key=True)
	old_id						= db.Column(db.String(30))
	new_id						= db.Column(db.String(30))
	project_id				= db.Column(db.Integer, db.ForeignKey('project.project_id'))
