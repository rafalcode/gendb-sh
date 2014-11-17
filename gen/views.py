from gen import gen_app,models, db, login_manager
from flask import render_template, flash, redirect, request, url_for, \
		send_from_directory, g
from .forms import AddGenotype, AddProject, LogInForm
from flask.ext.login import login_user, logout_user, current_user, login_required
from werkzeug import secure_filename
import os, csv, sys
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import exc

"""
==========================================
			Helper Functions
==========================================
"""
def allowed_file(filename):
	return '.' in filename and \
			filename.rsplit('.', 1)[1] in gen_app.config['ALLOWED_EXTENSIONS']

@gen_app.before_request
def before_reques():
	g.user=current_user

@login_manager.user_loader
def load_user(user_id):
	return models.User.query.get(user_id)

@gen_app.route('/')
@login_required
def index():
	"""Main page of the dashboard
	Displays overview information with content
	from the system
	"""
	return render_template('index.html', 
			title='Overview')

@gen_app.route('/login', methods=['GET', 'POST'])
def login():
	"""Checks the user credentials
	and logs him in
	"""
	form = LogInForm()
	if form.validate_on_submit():
		import hashlib
		user = models.User.query.get(request.form["username"])
		if user != None and \
				user.password == hashlib.sha512(request.form["password"]).hexdigest():
			login_user(user)
			log_entry = models.Log()
			import time
			log_entry.timestamp = int(time.time())
			log_entry.user_id = g.user.user_name
			log_entry.action = "Logged in"
			db.session.add(log_entry)
			db.session.commit()


			return redirect(url_for('index'))
		else:
			flash("Invalid login", "danger")
			return redirect(url_for('login'))
	return render_template('login.html', form=form)

@gen_app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('login'))
	
"""
========================================
	MENU VIEWS
========================================
"""
@gen_app.route('/reports')
@login_required
def reports():
	title = "Reports"

	rows = models.Individual.query.all()

	
	return render_template('reports.html',
			title=title,
			rows=rows)

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


@gen_app.route('/upload_individual', methods=['POST'])
def upload_individual():
	csv.field_size_limit(sys.maxsize)
	num_rows = 0

	if request.method == 'POST':
		ind_file = request.files['individuals']

		if ind_file and allowed_file(ind_file.filename):
			filename = secure_filename(ind_file.filename)
			ind_file.save(os.path.join(gen_app.config['UPLOAD_FOLDER'], filename))
			flash("Individuals file uploaded successfully", "success")

			try:
				with open(gen_app.config['UPLOAD_FOLDER'] + '/' + filename, 'rb') as csvfile:
					sr = csv.reader(csvfile, delimiter=' ')

					for row in sr:
						num_rows = num_rows+1
						if len(row) != 3:
							flash("Ivalid file format", "danger")
							return redirect(url_for('project_page', id=request.form['id']))
						ind = models.Individual()
						ind.individual_id = row[0]
						ind.old_id = row[1]
						ind.new_id = row[2]
						ind.project_id = request.form['id']
						db.session.add(ind)
					"""
					Create log entry
					"""
					log_entry = models.Log()
					import time
					log_entry.timestamp = int(time.time())
					log_entry.user_id = g.user.user_name
					log_entry.action = "Upload Individual file for project " + request.form['id']
					db.session.add(log_entry)
					"""
					Commit changes to DB
					"""
					db.session.commit()
			except exc.IntegrityError, e:
				try:
					os.remove(gen_app.config['UPLOAD_FOLDER'] + '/' +filename)
				except OSError,e :
					print str(e)
				flash(str(e), "danger")
				return redirect(url_for('project_page', id=request.form['id']))

			try:
				os.remove(gen_app.config['UPLOAD_FOLDER'] + '/' +filename)
			except OSError,e :
				print str(e)
			flash("File successfully parsed. "+ str(num_rows) + " lines added to database", "success")
			return redirect(url_for('project_page', id=request.form['id']))
	
	flash("Invalid file", "danger")
	return redirect(url_for('project_page', id=request.form['id']))

@gen_app.route('/single_geno', methods=['POST'])
def single_geno():
	csv.field_size_limit(sys.maxsize)
	num_rows = 0

	if request.method == 'POST':
		single_geno = request.files['single_geno']

		if single_geno and allowed_file(single_geno.filename):
			filename = secure_filename(single_geno.filename)
			single_geno.save(os.path.join(gen_app.config['UPLOAD_FOLDER'], filename))
			flash("Genotype file uploaded successfully", "success")

			try:
				with open(gen_app.config['UPLOAD_FOLDER'] + '/' + filename, 'rb') as csvfile:
					sr = csv.reader(csvfile, delimiter=' ')

					for row in sr:
						num_rows = num_rows+1
						if len(row) != 3:
							flash("Ivalid file format", "danger")
							return redirect(url_for('project_page', id=request.form['id']))
						gen = models.Genotype()
						gen.individual_id = row[0]
						gen.snp = row[1]
						if (row[2] != "Undetermined"):
							#TODO improve parsing
							gen.call = row[2][-3:]
						else:
							gen.call = "X"
						gen.project_id = request.form['id']
						db.session.add(gen)

					"""
					Create log entry
					"""
					log_entry = models.Log()
					import time
					log_entry.timestamp = int(time.time())
					log_entry.user_id = g.user.user_name
					log_entry.action = "Upload Genotype file for project " + request.form['id']
					db.session.add(log_entry)
					"""
					Commit changes to DB
					"""
					db.session.commit()
			except exc.IntegrityError, e:
				try:
					os.remove(gen_app.config['UPLOAD_FOLDER'] + '/' +filename)
				except OSError,e :
					print str(e)
				flash(str(e), "danger")
				return redirect(url_for('project_page', id=request.form['id']))

			try:
				os.remove(gen_app.config['UPLOAD_FOLDER'] + '/' +filename)
			except OSError,e :
				print str(e)
			flash("File successfully parsed. "+ str(num_rows) + " lines added to database", "success")
			return redirect(url_for('project_page', id=request.form['id']))
	
	flash("Invalid file", "danger")
	return redirect(url_for('project_page', id=request.form['id']))

@gen_app.route('/download_ped/<int:project_id>/<path:filename>', methods=['GET'])
def download_ped(project_id, filename):
	ped = models.Individual.query.join(models.Genotype).filter(models.Individual.new_id == models.Genotype.individual_id).order_by(models.Individual.new_id.asc()).all()
	
	with open(gen_app.config['UPLOAD_FOLDER'] + filename, 'wb') as f:
		writer = csv.writer(f, delimiter=',')
		
		for row in ped:
			row = [] + [str(row.individual_id)] + [str(row.new_id)] + [str(row.genotype[0].call)]
			writer.writerow(row)

	for row in ped:
		print row.new_id

	return send_from_directory(gen_app.config['UPLOAD_FOLDER'], filename=filename)
