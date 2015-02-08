from gen import db

class User(db.Model):
	user_name				= db.Column(db.String(45), index=True, unique=True, primary_key=True)
	email						= db.Column(db.String(45))
	password				= db.Column(db.String(128))

	log_entry				= db.relationship('Log', backref='log', lazy='dynamic')
	project_owner		= db.relationship('Project', backref='project', lazy='dynamic')
	memship					= db.relationship('Membership', backref='membership', lazy='dynamic')

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
	genotype					= db.relationship('Genotype', backref='genotype_project', lazy='dynamic')
	phenotype					= db.relationship('Phenotype', backref='phenotype_project', lazy='dynamic')
	owner							= db.Column(db.String(45), db.ForeignKey('user.user_name'))
	

class Log(db.Model):
	idlog							= db.Column(db.Integer, primary_key=True)
	timestamp					= db.Column(db.Integer)
	user_id						= db.Column(db.String(64), db.ForeignKey('user.user_name'))
	action						= db.Column(db.String(400))

class Individual(db.Model):
	individual_id			= db.Column(db.Integer, primary_key=True)
	old_id						= db.Column(db.String(30))
	new_id						= db.Column(db.String(30), primary_key=True)
	project_id				= db.Column(db.Integer, db.ForeignKey('project.project_id'))
	genotype					= db.relationship('Genotype', backref='genotype_individual', lazy='dynamic')

class Genotype(db.Model):
	#TODO Change from int ID to composite keys
	genotype_id				= db.Column(db.Integer, primary_key=True)
	individual_id			= db.Column(db.String(45), db.ForeignKey('individual.new_id'))
	snp								= db.Column(db.String(45))
	call							= db.Column(db.String(3))
	project_id				= db.Column(db.Integer, db.ForeignKey('project.project_id'))

class Phenotype(db.Model):
	phenotype_id			= db.Column(db.Integer, primary_key=True)
	individual_id			= db.Column(db.String(45), db.ForeignKey('individual.new_id'))
	name							= db.Column(db.String(45))
	value							= db.Column(db.String(45))
	project_id				= db.Column(db.Integer, db.ForeignKey('project.project_id'))

class Membership(db.Model):
	user_name					= db.Column(db.String(45), db.ForeignKey('user.user_name'),primary_key=True)
	project						= db.Column(db.Integer, primary_key=True)
