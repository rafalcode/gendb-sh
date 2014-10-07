from gen import gen_app, models, db
from flask import render_template, flash, redirect, request, url_for
from .forms import AddGenotype
from werkzeug import secure_filename
import os, csv

"""
			Helper Functions
"""

def allowed_file(filename):
	return '.' in filename and \
			filename.rsplit('.', 1)[1] in gen_app.config['ALLOWED_EXTENSIONS']

@gen_app.route('/')
def index():
	rows = models.Individual.query.all()
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

	rows = models.Individual.query.all()

	
	return render_template('reports.html',
			title=title,
			rows=rows)

@gen_app.route('/export')
def export_data():
	title = "Export"
	genos = db.engine.execute("SELECT * FROM genos;").fetchall()

	return render_template('export.html', title=title, rows=genos)

@gen_app.route('/import', methods=['GET', 'POST'])
def import_data():
	title = "Import"
	phenos = db.engine.execute("SELECT * FROM phenos;").fetchall()
	
	form = AddGenotype()

	new_gen = models.Genotype()
	
	if form.validate_on_submit():
		new_gen.individual_id = form.individual_id.data
		new_gen.genotype			= form.genotype.data
		db.session.add(new_gen)
		db.session.commit()
		flash("Genotype Added", "success")
		return redirect('/import')
	

	return render_template('import.html', title=title, rows=phenos, form=form)

@gen_app.route('/upload_template', methods=['GET', 'POST'])
def upload_template():
	if request.method == 'POST':

		file = request.files['template']
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(gen_app.config['UPLOAD_FOLDER'],filename))

			with open(gen_app.config['UPLOAD_FOLDER'] + '/' + filename, 'rb') as csvfile:
				sr = csv.reader(csvfile, delimiter=',')
				for row in sr:
					individual = models.Individual()

					individual.individual_id = row[1]
					individual.father_id = row[2]
					individual.mother_id = row[3]
					individual.gender = row[4]
					db.session.add(individual)
			db.session.commit()
			return redirect(url_for('index'))
		return "hello"

