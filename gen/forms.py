from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, TextAreaField
from wtforms.validators import DataRequired

class AddGenotype(Form):
	individual_id = StringField('individual_id', validators=[DataRequired()])
	genotype			= StringField('genotype', validators=[DataRequired()])

class AddProject(Form):
	project_name				= StringField('project_name', validators=[DataRequired()])
	project_description	= TextAreaField('description', validators=[DataRequired()])
