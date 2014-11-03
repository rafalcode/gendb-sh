from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, TextAreaField, PasswordField
from wtforms.validators import Required

class AddGenotype(Form):
	individual_id = StringField('individual_id', validators=[Required()])
	genotype			= StringField('genotype', validators=[Required()])

class AddProject(Form):
	project_name				= StringField('project_name', validators=[Required()])
	project_description	= TextAreaField('description', validators=[Required()])

class LogInForm(Form):
	username = StringField('username', validators=[Required()])
	password = PasswordField('password', validators=[Required()])
