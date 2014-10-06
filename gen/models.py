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
