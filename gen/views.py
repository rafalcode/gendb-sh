from gen import gen_app,models, db, login_manager
from flask import render_template, flash, redirect, request, url_for, \
		send_from_directory, g
from .forms import AddGenotype, AddProject, LogInForm
from flask.ext.login import login_user, logout_user, current_user, login_required
from werkzeug import secure_filename
import os, csv, sys

"""
			Helper Functions
"""
def allowed_file(filename):
	return '.' in filename and \
			filename.rsplit('.', 1)[1] in gen_app.config['ALLOWED_EXTENSIONS']

@gen_app.before_request
def before_reques():
	g.user=current_user

@login_manager.user_loader
def load_user(user_id):
	return models.User.query.get(int(user_id))

@gen_app.route('/')
@login_required
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

@gen_app.route('/login', methods=['GET', 'POST'])
def login():
	form = LogInForm()
	if form.validate_on_submit():
		if request.form["username"] ==  "test" and request.form["password"] == "123":
			user = models.User.query.get(int(1))
			login_user(user)
			#g.user = user
			return redirect(url_for('index'))

	return render_template('login.html', form=form)

@gen_app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('index'))
	
"""
	MENU VIEWS
"""
@gen_app.route('/reports')
@login_required
def reports():
	title = "Reports"

	rows = models.Individual.query.all()

	
	return render_template('reports.html',
			title=title,
			rows=rows)

@gen_app.route('/export')
@login_required
def export_data():
	title = "Export"
	genos = db.engine.execute("SELECT * FROM genos;").fetchall()


	return render_template('export.html', title=title, rows=genos)

@gen_app.route('/import', methods=['GET', 'POST'])
@login_required
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
@login_required
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
@login_required
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
@login_required
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

"""
	CODE DUPLICATION WITH york_gen_map
	TODO: combine into one function
"""
@gen_app.route('/york_gen', methods=['POST'])
def york_gen():
	csv.field_size_limit(sys.maxsize)
	num_rows = 0

	if request.method == 'POST':
		ped = request.files['ped']

		if ped and allowed_file(ped.filename):
			filename = secure_filename(ped.filename)
			ped.save(os.path.join(gen_app.config['UPLOAD_FOLDER'], filename))
			flash(".PED file uploaded successfully", "success")
			with open(gen_app.config['UPLOAD_FOLDER'] + '/' + filename, 'rb') as csvfile:
				sr = csv.reader(csvfile, delimiter=' ')

				for row in sr:
					num_rows = num_rows + 1

					cols = len(row)
					ped = models.York_Ped()

					ped.family_id = row[0]
					ped.individual_id = row[1]
					ped.paternal_id = row[2]
					ped.maternal_id = row[3]
					ped.gender = row[4]
					ped.phenotype = row[5]
					gen_sec = ""
					for x in range(7,cols):
						gen_sec = gen_sec + row[x] 
					
					ped.genotype_sec = gen_sec					
					ped.project_id = request.form['id']
					
						
					db.session.add(ped)

			log_entry = models.Log()
			import time
			log_entry.timestamp = int(time.time())
			log_entry.user_id = g.user.user_id
			log_entry.action = "Upload ped file for project " + request.form['id']
			db.session.add(log_entry)
			db.session.commit()
			flash("File successfully parsed. "+ str(num_rows) + " lines added to database", "success")
			return redirect(url_for('project_page', id=request.form['id']))
	
	flash("Did not wrok", "danger")
	return redirect(url_for('projects'))

"""
	CODE DUPLICATION WITH york_gen
	TODO: combine into one function
"""
@gen_app.route('/york_gen_map', methods=['POST'])
def york_gen_map():
	if request.method == 'POST':
		mapf = request.files['map']

		if mapf and allowed_file(mapf.filename):
			filename = secure_filename(mapf.filename)
			mapf.save(os.path.join(gen_app.config['UPLOAD_FOLDER'], filename))
			flash(".MAP uploaded", "success")
			return redirect(url_for('project_page', id=request.form['id']))
	flash("Did not wrok", "danger")
	return redirect(url_for('projects'))

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

@gen_app.route('/projects/<id>')
def project_page(id):
	project = models.Project.query.filter_by(project_id=id).one()

	return render_template('single_project.html',
			title=project.name,
			rows=project)

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
