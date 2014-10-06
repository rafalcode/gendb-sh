from gen import gen_app, models, db
from flask import render_template

@gen_app.route('/')
def index():
	rows = models.sample_table.query.all()
	return render_template('index.html', 
			title='Overview',
			rows=rows)

@gen_app.route('/user/<name>')
def new_user(name):
	u = models.User(user_name=name)
	db.session.add(u)
	db.session.commit()
	
	return "user added"

@gen_app.route('/reports')
def reports():
	title = "Reports"
	
	return render_template('reports.html', title=title)

@gen_app.route('/export')
def export_data():
	title = "Export"

	return render_template('export.html', title=title)

@gen_app.route('/import')
def import_data():
	title = "Import"

	return render_template('import.html', title=title)
