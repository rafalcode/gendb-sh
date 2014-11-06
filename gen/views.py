from gen import gen_app,models, db, login_manager
from flask import render_template, flash, redirect, request, url_for, \
		send_from_directory, g
from .forms import AddGenotype, AddProject, LogInForm
from flask.ext.login import login_user, logout_user, current_user, login_required
from werkzeug import secure_filename
import os, csv, sys
from sqlalchemy.orm.exc import NoResultFound

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
			log_entry.user_id = g.user.user_name
			log_entry.action = "Upload ped file for project " + request.form['id']
			db.session.add(log_entry)
			db.session.commit()
			flash("File successfully parsed. "+ str(num_rows) + " lines added to database", "success")
			return redirect(url_for('project_page', id=request.form['id']))
	
	flash("Invalid file", "danger")
	return redirect(url_for('project_page', id=request.form['id']))

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
	flash("Invalid file", "danger")
	return redirect(url_for('project_page', id=request.form['id']))




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
