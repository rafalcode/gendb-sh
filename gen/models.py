from gen import db

class User(db.Model):
	user_id = db.Column(db.Integer, primary_key=True)
	user_name = db.Column(db.String(45), index=True, unique=True)

	def __repr__(self):
		return '<User %r>' % (self.user_name) 

class sample_table(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	family_id = db.Column(db.String(45))
	individual = db.Column(db.String(45))
	father = db.Column(db.String(45))
	mother = db.Column(db.String(45))
	gender = db.Column(db.String(45))
	genotype_1 = db.Column(db.String(45))
	genotype_2 = db.Column(db.String(45))
	genotype_3 = db.Column(db.String(45))
	genotype_4 = db.Column(db.String(45))
	phenotype_1 = db.Column(db.String(45))
	phenotype_2 = db.Column(db.String(45))
	phenotype_3 = db.Column(db.String(45))
	phenotype_4 = db.Column(db.String(45))

class Individual(db.Model):
	__tablename__ = 'individual'

	individual_id			= db.Column(db.String(45), primary_key=True)
	father_id					= db.Column(db.String(45))
	mother_id					= db.Column(db.String(45))
	gender						= db.Column(db.Integer)
	family_id					= db.Column(db.Integer)
	phenotype					= db.relationship('Phenotype', backref='pheno', lazy='dynamic')

class Phenotype(db.Model):
	phenotype_id			= db.Column(db.Integer, primary_key=True)
	individual_id 		= db.Column(db.String(45),
			db.ForeignKey('individual.individual_id'))
	phenotype					= db.Column(db.String(45))

class Genotype(db.Model):
	genotype_id				= db.Column(db.Integer, primary_key=True)
	individual_id			= db.Column(db.String(45),
			db.ForeignKey('individual.individual_id'))
	genotype					= db.Column(db.String(45))

class Family(db.Model):
	fmimly_id					= db.Column(db.String(45), primary_key=True)
	mother_id					= db.Column(db.String(45))
	father_id					= db.Column(db.String(45))
	child_1						= db.Column(db.String(45))
	child_2						= db.Column(db.String(45))
	child_3						= db.Column(db.String(45))

class Project(db.Model):
	project_id				= db.Column(db.Integer, primary_key=True)
	name							= db.Column(db.String(100))
	description				= db.Column(db.String(500))
	ped_file					= db.relationship('York_Ped',
			backref='Project',
			lazy='dynamic')

class York_Ped(db.Model):
	idyork_ped				= db.Column(db.Integer, primary_key=True)
	family_id					= db.Column(db.String(45))
	paternal_id				= db.Column(db.String(45))
	maternal_id				= db.Column(db.String(45))
	gender						= db.Column(db.String(45))
	phenotype					= db.Column(db.String(45))
	genotype_sec			= db.Column(db.Binary)
	project_id				= db.Column(db.Integer, db.ForeignKey('project.project_id'))
