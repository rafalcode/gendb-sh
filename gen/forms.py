from flask.ext.wtf import Form
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired

class AddGenotype(Form):
	individual_id = StringField('individual_id', validators=[DataRequired()])
	genotype			= StringField('genotype', validators=[DataRequired()])
