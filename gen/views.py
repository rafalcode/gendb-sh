from gen import gen_app, models, db
from flask import render_template, flash, redirect, request, url_for, \
		send_from_directory
from .forms import AddGenotype, AddProject
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
					if len(row) != 9:
						flash("Invalid file format", "danger")
						return redirect(url_for('import_data'))

					individual = models.Individual()
					phenotype1 = models.Phenotype()
					phenotype2 = models.Phenotype()
					phenotype3 = models.Phenotype()
					phenotype4 = models.Phenotype()

					individual.family_id = row[0]
					individual.individual_id = row[1]
					individual.father_id = row[2]
					individual.mother_id = row[3]
					individual.gender = row[4]
					phenotype1.individual_id = row[1]
					phenotype1.phenotype = row[5]
					phenotype2.individual_id = row[1]
					phenotype2.phenotype = row[6]
					phenotype3.individual_id = row[1]
					phenotype3.phenotype = row[7]
					phenotype4.individual_id = row[1]
					phenotype4.phenotype = row[8]



					db.session.add(individual)
					db.session.add(phenotype1)
					db.session.add(phenotype2)
					db.session.add(phenotype3)
					db.session.add(phenotype4)



			db.session.commit()
			flash("File uploaded and parsed", "success")
			return redirect(url_for('import_data'))

		flash("Invalid file, please try again", "danger")
		return redirect(url_for('import_data'))



@gen_app.route('/upload_phenotypes', methods=['GET', 'POST'])
def upload_phenotypes():
	if request.method == 'POST':

		file = request.files['phenotypes']
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(gen_app.config['UPLOAD_FOLDER'],filename))

			with open(gen_app.config['UPLOAD_FOLDER'] + '/' + filename, 'rb') as csvfile:
				sr = csv.reader(csvfile, delimiter=',')

				


				for row in sr:
					cols = len(row)
					for x in range(1,cols):
						print "11"
						phenotype = models.Phenotype()
						phenotype.individual_id = row[0]
						phenotype.phenotype = row[x]
						db.session.add(phenotype)


			db.session.commit()
			flash("File uploaded and parsed", "success")
			return redirect(url_for('import_data'))

		flash("Invalid file, please try again", "danger")
		return redirect(url_for('import_data'))

@gen_app.route('/upload_genotypes', methods=['GET', 'POST'])
def upload_genotypes():
	if request.method == 'POST':

		file = request.files['genotypes']
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(gen_app.config['UPLOAD_FOLDER'],filename))

			with open(gen_app.config['UPLOAD_FOLDER'] + '/' + filename, 'rb') as csvfile:
				sr = csv.reader(csvfile, delimiter=',')

				for row in sr:
					cols = len(row)
					for x in range(1,cols):
						print "11"
						genotype = models.Genotype()
						genotype.individual_id = row[0]
						genotype.genotype = row[x]
						db.session.add(genotype)


			db.session.commit()
			flash("File uploaded and parsed", "success")
			return redirect(url_for('import_data'))

		flash("Invalid file, please try again", "danger")
		return redirect(url_for('import_data'))

@gen_app.route('/uploads/<filename>')
def uploaded_file(filename):
	return send_from_directory(gen_app.config['UPLOAD_FOLDER'], filename)


@gen_app.route('/download_gens/<filename>')
def download_gens(filename):
	genos = db.engine.execute("SELECT * FROM genos;").fetchall()
	with open(gen_app.config['UPLOAD_FOLDER'] + '/temp.csv', 'wb') as fl:
		sr = csv.writer(fl, delimiter=',')
		
		for row in genos:
			data = [str(row[0]),str(row[1]),str(row[2]),str(row[3]),str(row[4])] + [str(x.strip()) for x in row[5].split(',')] + [str(x.strip()) for x in row[6].split(',')]
			sr.writerow(data)
	return send_from_directory(gen_app.config['UPLOAD_FOLDER'], 'temp.csv')


@gen_app.route('/download_indiv/<filename>')
def download_indiv(filename):
	genos = db.engine.execute("SELECT * FROM individual;").fetchall()
	with open(gen_app.config['UPLOAD_FOLDER'] + '/temp.csv', 'wb') as fl:
		sr = csv.writer(fl, delimiter=',')
		
		for row in genos:
			sr.writerow([row[0],row[1],row[2],row[3],row[4]])
	return send_from_directory(gen_app.config['UPLOAD_FOLDER'], 'temp.csv')


@gen_app.route('/download_single_gen/<filename>')
def download_single_gen(filename):
	genos = db.engine.execute("SELECT * FROM genotype;").fetchall()
	with open(gen_app.config['UPLOAD_FOLDER'] + '/temp.csv', 'wb') as fl:
		sr = csv.writer(fl, delimiter=',')
		
		for row in genos:
			sr.writerow([row[0],row[1],row[2]])
	return send_from_directory(gen_app.config['UPLOAD_FOLDER'], 'temp.csv')


@gen_app.route('/download_single_phen/<filename>')
def download_single_phen(filename):
	genos = db.engine.execute("SELECT * FROM phenotype;").fetchall()
	with open(gen_app.config['UPLOAD_FOLDER'] + '/temp.csv', 'wb') as fl:
		sr = csv.writer(fl, delimiter=',')
		
		for row in genos:
			sr.writerow([row[0],row[1],row[2]])
	return send_from_directory(gen_app.config['UPLOAD_FOLDER'], 'temp.csv')

@gen_app.route('/projects')
def projects():
	project_list = models.Project.query.all()

	return render_template('projects.html', title="Projects", rows=project_list)

@gen_app.route('/projects/<int:id>')
def project_page(id):
	project = models.Project.query.filter_by(id=id).one()

@gen_app.route('/add_project', methods=['GET','POST'])
def add_project():
	form = AddProject()
	project = models.Project() 

	if form.validate_on_submit():
		project.name = form.project_name.data
		project.description = form.project_description.data
		db.session.add(project)
		db.session.commit()

		return redirect(url_for('projects'))

	return render_template('add_project.html', 
			title="New Project",
			ap=form)
