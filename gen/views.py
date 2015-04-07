from gen import gen_app,models, db, login_manager
from flask import render_template, flash, redirect, request, url_for, \
		send_from_directory, g
from .forms import AddGenotype, AddProject, LogInForm, SearchProject, HardyButton
from flask.ext.login import login_user, logout_user, current_user, login_required
from werkzeug import secure_filename
import os, csv, sys
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import exc
from sqlalchemy import func, and_, or_, desc

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
	ind_count = models.Individual.query.count()
	project_count = models.Project.query.count()
	gen_entr = models.Genotype.query.group_by(models.Genotype.snp).count()
	phen_entr = models.Phenotype.query.group_by(models.Phenotype.name).count()
	latest_proj = models.Project.query.filter_by(owner=g.user.user_name).order_by(models.Project.project_id.desc()).limit(3)
	return render_template('index.html', 
			title='Welcome',
			ind_count=ind_count,
			project_count=project_count,
			gen_entr=gen_entr,
			phen_entr=phen_entr,
			latest=latest_proj)

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
@gen_app.route('/projects')
@login_required
def projects():
	"""Shows the projects that the curent
	logged in user is member of.
	"""
	project_list = []

	mem = models.Membership.query.filter_by(user_name=g.user.user_name).all()
	for row in mem:
		project_list.append(models.Project.query.filter_by(project_id=row.project)[0])

	return render_template('projects.html', title="Projects", rows=project_list)

@gen_app.route('/projects/<id>', methods=['GET', 'POST'])
@login_required
def project_page(id):
	"""Show a page for a specific project.
	Only members of the project can access this page.
	"""

	# Generate member table
	mems = models.Membership.query.filter_by(project=id).all()
	mem_list = []
	for row in mems:
		mem_list.append(row.user_name)

	# Check if current user has rights to view this page
	if g.user.user_name not in mem_list:
		flash("You should not be here", "danger")
		return redirect(url_for('index'))


	cnt = -1

	# Query the DB
	project = models.Project.query.filter_by(project_id=id).one()
	contribs = models.User.query.join(models.Membership).filter(and_(models.User.user_name == models.Membership.user_name, models.Membership.project==id)).all()
	indivs_proj = models.Individual.query.filter_by(project_id=id).count()
	genos_proj = models.Genotype.query.filter_by(project_id=id).group_by(models.Genotype.snp).count()
	phenos_proj = models.Phenotype.query.filter_by(project_id=id).group_by(models.Phenotype.name).count()
	groups = models.Group.query.filter_by(project_id=id).all()
	phen_list = models.Phenotype.query.filter_by(project_id=id).all()
	gen_list = models.Genotype.query.filter_by(project_id=id).all()


	# Generate phenotype dropdown menu
	phens = set()
	for row in phen_list:
		phens.add(row.name)
	
	gens = set()
	for row in gen_list:
		gens.add(row.snp)

	
	# run PLINK
	result = ""
	hardyBtn = HardyButton()
	if hardyBtn.validate_on_submit():
		print gen_ped(id)
		print gen_map(id)
		from subprocess import check_output, CalledProcessError
		try:
			# TODO: plink location variable
			result = check_output(["/cs/home/vt3/SHproject/plink", "--help"])  
			result = result.split('\n')
		except CalledProcessError, e:
			print e

	return render_template('single_project.html',
			title=project.name,
			rows=project,
			contribs=contribs,
			hardy=hardyBtn,
			cnt=cnt,
			indivs_proj=indivs_proj,
			genos_proj=genos_proj,
			phenos_proj=phenos_proj,
			hardy_data=result,
			groups=groups,
			phen_list=phens,
			gen_list=gens)

@gen_app.route('/add_member/<proj_id>', methods=['POST'])
@login_required
def add_member(proj_id):
	"""Add a user to a project.
	Error if user does not exist or is already a member.
	"""

	try:
		memship = models.Membership()
		memship.user_name = request.form['username']
		memship.project = proj_id

		db.session.add(memship)
		db.session.commit()
	except exc.IntegrityError:
		db.session.rollback()
		flash("User is already a member or does not exists.", "danger")
		return redirect(url_for("project_page", id=proj_id))

	flash("Member added", "success")
	return redirect(url_for('project_page', id=proj_id))

@gen_app.route('/add_project', methods=['GET','POST'])
@login_required
def add_project():
	"""Create a new project.
	No duplicate names are allowed.
	"""
	form = AddProject()
	project = models.Project() 
	memship = models.Membership()

	nm = models.Project.query.filter_by(name=form.project_name.data).all()
	if form.validate_on_submit():
		if nm:
			flash("A project with that name already exists", "danger")
			return redirect(url_for('projects'))
		project.name = form.project_name.data
		project.description = form.project_description.data
		project.owner = g.user.user_name

		"""
		Create log entry
		"""
		log_entry = models.Log()
		import time
		log_entry.timestamp = int(time.time())
		log_entry.user_id = g.user.user_name
		log_entry.action = "Created project " + form.project_name.data
		db.session.add(log_entry)
		db.session.add(project)
		db.session.commit()

		memship.user_name = g.user.user_name
		memship.project = project.project_id
		db.session.add(memship)
		db.session.commit()

		return redirect(url_for('projects'))

	return render_template('add_project.html', 
			title="New Project",
			ap=form)

@gen_app.route('/delete_project/<id>', methods=['GET'])
@login_required
def delete_project(id):
	"""Delete a project and
	all associated data.
	"""
	project = models.Project.query.filter_by(project_id=id).one()
	if project.owner == g.user.user_name:
		memship = models.Membership.query.filter_by(project=id).delete()
		db.session.commit()
		genotypes = models.Genotype.query.filter_by(project_id=id).delete()
		db.session.commit()
		phenotypes = models.Phenotype.query.filter_by(project_id=id).delete()
		db.session.commit()
		individuals = models.Individual.query.filter_by(project_id=id).delete()
		db.session.commit()
		groups = models.Group.query.filter_by(project_id=id).delete()
		db.session.commit()
		db.session.delete(project)
		db.session.commit()

		"""
		Create log entry
		"""
		log_entry = models.Log()
		import time
		log_entry.timestamp = int(time.time())
		log_entry.user_id = g.user.user_name
		log_entry.action = "Deleted project " + project.name
		db.session.add(log_entry)
		db.session.commit()

		flash('Project deleted successfuly.', 'success')
	else:
		flash('You do not have the premision to do that.', 'danger')
		
	return redirect(url_for('projects'))

@gen_app.route('/join_project/<id>', methods=['GET'])
@login_required
def join_project(id):
	"""Used when a user tries to join a project.
	Deprecated due to change in requirements.
	"""
	isMember = models.Membership.query.filter(and_(models.Membership.user_name == g.user.user_name, models.Membership.project == id)).count()
	if isMember > 0:
		flash('You are already a member', 'danger')
	else:
		memship = models.Membership()
		memship.user_name = g.user.user_name
		memship.project = id
		db.session.add(memship)
		db.session.commit()
		flash('Welcome to the project', 'success')
	return redirect(url_for('project_page', id=id))

@gen_app.route('/delete_member/<user_name>/<id>', methods=['GET'])
@login_required
def delete_member(user_name,id):
	"""Allows the project admin to
	delete project members
	"""
	project = models.Project.query.filter_by(project_id=id).one()
	if project.owner == g.user.user_name:
		if project.owner ==  user_name:
			flash("You cannot delete yourself", "info")
			return redirect(url_for('project_page', id=id))

		models.Membership.query.filter(and_(models.Membership.user_name==user_name, models.Membership.project==id)).delete()
		db.session.commit()
		flash('User removed from project successfuly', 'success')
	else:
		flash('There was an error while trying to remove this user', 'danger')

	return redirect(url_for('project_page', id=id))

@gen_app.route('/upload_group', methods=['POST'])
@login_required
def upload_group():
	"""Uploads a file that is used to create a group.
	The format of the fileis:

		ID -  column containing all the IDs that form up
					the group
	
	The file needs to have only one column.
	"""
	csv.field_size_limit(sys.maxsize)
	ind_list = []

	if request.method == 'POST':
		group_file = request.files['group']

		if group_file and allowed_file(group_file.filename):
			filename = secure_filename(group_file.filename)
			group_file.save(os.path.join(gen_app.config['UPLOAD_FOLDER'], filename))

			try:
				with open(gen_app.config['UPLOAD_FOLDER'] + '/' + filename, 'rb') as csvfile:
					sr = csv.reader(csvfile, delimiter=',')

					for row in sr:
						ind_list.append(row[0])
						if len(row) != 1:
							flash("Invalid file format", "danger")
							return redirect(url_for('project_page', id=request.form['id']))

				group_entry = models.Group()

				group_entry.name = request.form['name']
				group_entry.indiv_list =  ",".join(ind_list)
				group_entry.project_id = request.form['id']
				db.session.add(group_entry)
				db.session.commit()

			# clean up
			except exc.IntegrityError, e:
				try:
					os.remove(gen_app.config['UPLOAD_FOLDER'] + '/' + filename)
				except OSError, e:
					print str(e)
			# clean up
			try:
				os.remove(gen_app.config['UPLOAD_FOLDER'] + '/' +filename)
			except OSError,e :
				print str(e)

			flash("File successfully parsed.", "success")
			return redirect(url_for('project_page', id=request.form['id']))

	flash("Invalid file", "danger")
	return redirect(url_for('project_page', id=request.form['id']))


@gen_app.route('/upload_individual', methods=['POST'])
@login_required
def upload_individual():
	"""Upload a file containing a list of individuals.
	The file format is the following:

			ID - a column containing all the individual IDs
			Gender - a column containing gender information
	
	No header is required.
	"""
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
					sr = csv.reader(csvfile, delimiter=',')

					for row in sr:
						num_rows = num_rows+1
						if len(row) != 2:
							flash("Ivalid file format. Only two column with \
									IDs and gender are required", "danger")
							return redirect(url_for('project_page', id=request.form['id']))
						ind = models.Individual()
						ind.new_id = row[0]
						ind.gender = row[1]
						ind.project_id = request.form['id']
						db.session.add(ind)
					"""
					Create log entry
					"""
					log_entry = models.Log()
					import time
					log_entry.timestamp = int(time.time())
					log_entry.user_id = g.user.user_name
					log_entry.action = "Upload Individual file for project " + request.form['proname']
					db.session.add(log_entry)

					"""
					Commit changes to DB
					"""
					db.session.commit()

			# clean up
			except exc.IntegrityError, e:
				try:
					os.remove(gen_app.config['UPLOAD_FOLDER'] + '/' +filename)
				except OSError,e :
					print str(e)
					flash("Error: missing or misspelled IDs", "danger")
					return redirect(url_for('project_page', id=request.form['id']))

			try:
				os.remove(gen_app.config['UPLOAD_FOLDER'] + '/' +filename)
			except OSError,e :
				print str(e)


			flash("File successfully parsed. "+ str(num_rows) + " lines added to database", "success")
			return redirect(url_for('project_page', id=request.form['id']))
	
	flash("Invalid file. Make sure you have the right file extension \
			and number of columns.", "danger")
	return redirect(url_for('project_page', id=request.form['id']))

@gen_app.route('/bulk_pheno', methods=['POST'])
@login_required
def bulk_pheno():
	"""Bulk upload of phenotype information
	The file format is the following:
			IDs - column containing all the IDs
			Phen1 - first phenotype
			Phen2 - second phenotype
			Phen3 - etc...
			PhenN - ...

	This file REQUIRES a header:
			ID - the first cell can be anything
			Phen Name 1 - coresponding phenotype name
			Pnen Name 2 - ...
			Phen Name 3 - ...
			Phen Name N - ...
	"""
	csv.field_size_limit(sys.maxsize)
	num_rows = 0

	if request.method == 'POST':
		bulk_pheno = request.files['bulk_pheno']

		if bulk_pheno and allowed_file(bulk_pheno.filename):
			filename = secure_filename(bulk_pheno.filename)
			bulk_pheno.save(os.path.join(gen_app.config['UPLOAD_FOLDER'], filename))
			flash("Phenotype file uploaded successfuly", "success")

			try:
				with open(gen_app.config['UPLOAD_FOLDER'] + filename, 'rb') as csvfile:
					
					sr = csv.reader(csvfile, delimiter=',')
					header = sr.next()
					
					# List of IDs for when it crashes
					future = []

					for row in sr:
						future.append(row[0])
						num_rows = num_rows+1
						num_cols = len(row)
						for i in range(1,num_cols):
							phen = models.Phenotype()
							phen.individual_id = row[0]
							phen.name = header[i]
							phen.value = row[i]
							phen.project_id = request.form['id']
							db.session.add(phen)
						
					"""
					Create log entry
					"""
					log_entry = models.Log()
					import time
					log_entry.timestamp = int(time.time())
					log_entry.user_id = g.user.user_name
					log_entry.action = "Upload Phenotype file for project " + request.form['proname']
					db.session.add(log_entry)

					"""
					Commit changes to DB
					"""
					db.session.commit()
			
			# clean up
			except exc.IntegrityError, e:
				print e
				db.session.rollback()
				try:
					os.remove(gen_app.config['UPLOAD_FOLDER'] + '/' +filename)
				except OSError,e :
					print str(e)

				# Generate a list of missing IDs
				inds = models.Individual.query.filter_by(project_id=request.form['id']).all()
				current = []
				missing = []
				for row in inds:
					current.append(row.new_id)
				for row in future:
					if row not in current:
						missing.append(row)

				flash("Error: missing or misspelled IDs.", "danger")
				flash(missing, "info")
				return redirect(url_for('project_page', id=request.form['id']))
			
			try:
				os.remove(gen_app.config['UPLOAD_FOLDER'] + '/' +filename)
			except OSError,e :
				print str(e)
			flash("File successfully parsed. "+ str(num_rows) + " lines added to database", "success")
			return redirect(url_for('project_page', id=request.form['id']))
	
	flash("Invalid file. Make sure you have the right file extension \
			and number of columns.", "danger")

	return redirect(url_for('project_page', id=request.form['id']))

@gen_app.route('/bulk_geno', methods=['POST'])
@login_required
def bulk_geno():
	"""Bulk upload of genotype information
	The file format is the following:
			IDs - column containing all the IDs
			Gen1 - first genotype
			Gen2 - second genotype
			Gen3 - etc...
			GenN - ...

	This file REQUIRES a header:
			ID - the first cell can be anything
			Gen Name 1 - coresponding genotype name
			Gen Name 2 - ...
			Gen Name 3 - ...
			Gen Name N - ...
	"""

	csv.field_size_limit(sys.maxsize)
	num_rows = 0

	if request.method == 'POST':
		bulk_geno = request.files['bulk_geno']

		if bulk_geno and allowed_file(bulk_geno.filename):
			filename = secure_filename(bulk_geno.filename)
			bulk_geno.save(os.path.join(gen_app.config['UPLOAD_FOLDER'], filename))
			flash("Genotype file uploaded successfuly", "success")

			try:
				with open(gen_app.config['UPLOAD_FOLDER'] + filename, 'rb') as csvfile:
					header=csvfile.readline()
					dell = ","
					if header.find(" ") !=- 1:
						dell = " "
					elif header.find("\t") != -1:
						dell = "\t"
					elif header.find(",") != -1:
						dell = ","
					# List of IDs for when it crashes
					csvfile.seek(0)
					future = []
					for row in sr:
						future.append(row[0])

					sr = csv.reader(csvfile, delimiter=dell)
					header = sr.next()
					print header

					csvfile.seek(0)
					for row in sr:
						num_rows = num_rows+1
						num_cols = len(row)
						for i in range(1,num_cols):
							gen = models.Genotype()
							gen.individual_id = row[0]
							gen.snp = header[i]
							gen.call = row[i]
							gen.project_id = request.form['id']
							db.session.add(gen)
						
					"""
					Create log entry
					"""
					log_entry = models.Log()
					import time
					log_entry.timestamp = int(time.time())
					log_entry.user_id = g.user.user_name
					log_entry.action = "Upload Genotype file for project " + request.form['proname']
					db.session.add(log_entry)
					"""
					Commit changes to DB
					"""
					db.session.commit()


			except exc.IntegrityError, e:
				db.session.rollback()
				try:
					os.remove(gen_app.config['UPLOAD_FOLDER'] + '/' +filename)
				except OSError,e :
					print str(e)
				# Generate a list of missing IDs
				inds = models.Individual.query.filter_by(project_id=request.form['id']).all()
				current = []
				missing = []
				for row in inds:
					current.append(row.new_id)
				for row in future:
					if row not in current:
						missing.append(row)

				flash("Error: missing or misspelled IDs", "danger")
				flash(missing, "info")
				return redirect(url_for('project_page', id=request.form['id']))
			
			try:
				os.remove(gen_app.config['UPLOAD_FOLDER'] + '/' +filename)
			except OSError,e :
				print str(e)
			flash("File successfully parsed. "+ str(num_rows) + " lines added to database", "success")
			return redirect(url_for('project_page', id=request.form['id']))
	
	flash("Invalid file. Make sure you have the right file extension \
			and number of columns.", "danger")
	return redirect(url_for('project_page', id=request.form['id']))

@gen_app.route('/single_geno', methods=['POST'])
@login_required
def single_geno():
	"""Upload a file containing information
	for a single genotype.
	The file format is the following:
			ID - column with genotype IDs
			SNP - SNP name column
			Call - call column
	
	No header is required.
	"""
	abort_commit = False
	csv.field_size_limit(sys.maxsize)
	num_rows = 0
	current_geno_q = models.Genotype.query.filter_by(project_id=request.form['id']).all()
	current_geno = set()
	duplicate = set()
	for row in current_geno_q:
		current_geno.add(row.snp)
	print current_geno

	if request.method == 'POST':

		single_geno = request.files['single_geno']

		if single_geno and allowed_file(single_geno.filename):
			filename = secure_filename(single_geno.filename)
			single_geno.save(os.path.join(gen_app.config['UPLOAD_FOLDER'], filename))
			flash("Genotype file uploaded successfully", "success")

			try:
				with open(gen_app.config['UPLOAD_FOLDER'] + filename, 'rb') as csvfile:
					header=csvfile.readline()
					dell = ","
					if header.find(" ") !=- 1:
						dell = " "
					elif header.find("\t") != -1:
						dell = "\t"
					elif header.find(",") != -1:
						dell = ","
					sr = csv.reader(csvfile, delimiter=dell)
					
					csvfile.seek(0)
					# List of IDs for when it crashes
					future = []
					for row in sr:
						future.append(row[0])

					
					csvfile.seek(0)
					for row in sr:
						num_rows = num_rows+1
						if len(row) > 4:
							flash("Ivalid file format", "danger")
							return redirect(url_for('project_page', id=request.form['id']))
						gen = models.Genotype()
						gen.individual_id = row[0]
						if row[1] in current_geno:
							duplicate.add(row[1])
							abort_commit = True
						gen.snp = row[1]

						if len(row) == 4:
							gen.call = row[2] + "/" + row[3]
						else:
							gen.call = row[2]

						gen.project_id = request.form['id']
						db.session.add(gen)

					if abort_commit:
						flash("Duplicate genotypes detected", "danger")
						flash(list(duplicate), "info")
						return redirect(url_for('project_page', id=request.form['id']))

					"""
					Create log entry
					"""
					log_entry = models.Log()
					import time
					log_entry.timestamp = int(time.time())
					log_entry.user_id = g.user.user_name
					log_entry.action = "Upload Genotype file for project " + request.form['proname']
					db.session.add(log_entry)
					"""
					Commit changes to DB
					"""
					db.session.commit()
			except exc.IntegrityError, e:
				db.session.rollback()
				try:
					os.remove(gen_app.config['UPLOAD_FOLDER'] + '/' +filename)
				except OSError,e :
					print str(e)
				
				# Generate a list of missing IDs
				inds = models.Individual.query.filter_by(project_id=request.form['id']).all()
				current = []
				missing = []
				for row in inds:
					current.append(row.new_id)
				for row in future:
					if row not in current:
						missing.append(row)


				flash("Error: missing or misspelled IDs.", "danger")
				flash(missing, "info")
				return redirect(url_for('project_page', id=request.form['id']))

			try:
				os.remove(gen_app.config['UPLOAD_FOLDER'] + '/' +filename)
			except OSError,e :
				print str(e)
			flash("File successfully parsed. "+ str(num_rows) + " lines added to database", "success")
			return redirect(url_for('project_page', id=request.form['id']))
	
	flash("Invalid file. Make sure you have the right file extension \
			and number of columns.", "danger")
	return redirect(url_for('project_page', id=request.form['id']))

@gen_app.route('/download_ped/<int:project_id>/<path:filename>', methods=['POST'])
@login_required
def download_ped(project_id, filename):
	"""Generate and serve a PED file upon request.
	Magic pretty much...
	"""
	selected_phens = request.form.getlist('phen')
	selected_gens = request.form.getlist('gen')

	if "NONE" in selected_gens:
		selected_gens = ["NONE"]
	if len(selected_gens) == 0:
		selected_gens = ["ALL"]

	if "NONE" in selected_phens:
		selected_phens = ["NONE"]
	if len(selected_phens) == 0:
		selected_phens = ["ALL"]



	

	if models.Individual.query.filter_by(project_id=project_id).order_by(models.Individual.new_id.asc()).count() ==0:
		print "LEL"
		flash("No individuals", "danger")
		return redirect(url_for('project_page', id=project_id))
	
	final_out = {}
	gens_list = {}
	phen_list = {}
	ordered_ind = []
	group_list = []
	genders = {}


	grp = request.form['group']

	if grp != "ALL":
		group = models.Group.query.filter_by(group_id=grp).all()
		group_list = group[0].indiv_list.split(",")
	#print group_list

	phens = db.engine.execute('SELECT * FROM phenotype where project_id='+ str(project_id) +' group by name;')
	for p in phens:
		temp= models.Phenotype.query.filter(and_(models.Phenotype.project_id==project_id,models.Phenotype.name==p.name)).all()
		for row in temp:
			if 'ALL' in selected_phens:
				try:
					phen_list[row.individual_id].append(row.value)
				except KeyError:
					phen_list[row.individual_id] = [row.value]
			elif row.name in selected_phens:
				try:
					phen_list[row.individual_id].append(row.value)
				except KeyError:
					phen_list[row.individual_id] = [row.value]

	ind = models.Individual.query.filter_by(project_id=project_id).order_by(models.Individual.new_id.asc()).all()
		
	for row in ind:
		ordered_ind.append(row.new_id)
		final_out[row.new_id] = []
		genders[row.new_id] = row.gender
	
	gens = models.Genotype.query.filter_by(project_id=project_id).all()
	for row in gens:
		if 'ALL' in selected_gens:
			gens_list[row.snp] = [row.snp]
		elif row.snp in selected_gens:
			gens_list[row.snp] = [row.snp]

	for i in gens_list:
		current_gen = models.Genotype.query.filter_by(project_id=project_id).order_by().filter(models.Genotype.snp == i).all()
		for row in current_gen:
			final_out[row.individual_id] += [row.call]
	
	new_final_out = {}
	for row in final_out:
		if final_out[row] != []:
			new_final_out[row] = final_out[row]
	

	with open(gen_app.config['UPLOAD_FOLDER'] + filename, 'w+') as f:
		writer = csv.writer(f, delimiter=' ')
		final_line = []
		for i in ind:
			final_line.append([i.new_id])
	
		for column in range(0,len(gens_list)):
			print "LOLE"
			A = False
			C = False
			G = False
			T = False
			X = False

			for row in new_final_out:
				try:
					if new_final_out[row] != []:
						spl = new_final_out[row][column].split("/")
						if spl[0] == "A" or spl[1] == "A":
							A = True
						if spl[0] == "C" or spl[1] == "C":
							C = True
						if spl[0] == "G" or spl[1] == "G":
							G = True
						if spl[0] == "T" or spl[1] == "T":
							T = True
						if spl[0] == "X" or spl[1] == "X":
							X = True
				except IndexError:
					flash("Possible difference in genotype/phenotype count.", "danger")
					return redirect(url_for('project_page', id=project_id))

			lol = 0
			for row in new_final_out:
				if new_final_out[row] != []:
					fr = ""
					sn = ""
					if A and G:
						if new_final_out[row][column] == "A/G":
							fr = "1"
							sn = "2"
						elif new_final_out[row][column] == "A/A":
							fr = sn = "1"
						elif new_final_out[row][column] == "G/G":
							fr = sn = "2"
					elif A and C:
						if new_final_out[row][column] == "A/C":
							fr = "1"
							sn = "2"
						elif new_final_out[row][column] == "A/A":
							fr = sn = "1"
						elif new_final_out[row][column] == "C/C":
							fr = sn = "2"
					elif A and T:
						if new_final_out[row][column] == "A/T":
							fr = "1"
							sn = "2"
						elif new_final_out[row][column] == "A/A":
							fr = sn = "1"
						elif new_final_out[row][column] == "T/T":
							fr = n = "2"
					elif C and G:
						if new_final_out[row][column] == "C/G":
							fr = "1"
							sn = "2"
						elif new_final_out[row][column] == "C/C":
							fr = sn = "1"
						elif new_final_out[row][column] == "G/G":
							fr = sn = "2"
					elif C and T:
						if new_final_out[row][column] == "C/T":
							fr = "1"
							sn = "2"
						elif new_final_out[row][column] == "C/C":
							fr = sn = "1"
						elif new_final_out[row][column] == "T/T":
							fr = sn = "2"
					elif G and T:
						if new_final_out[row][column] == "G/T":
							fr = "1"
							sn = "2"
						elif new_final_out[row][column] == "G/G":
							fr = sn = "1"
						elif new_final_out[row][column] == "T/T":
							fr = sn = "2"
					if new_final_out[row][column] == "X/X":
						fr = sn = "X"
					new_final_out[row][column] = fr+','+sn
					lol += 1


		# a stack used to keep track of previously encountered IDs
		tiny_stack = ['0','0','0']

		for row in ordered_ind:
			#TODO That's dirty: you are expecting to catch
			# an exception in the if in order to skip a missing entry. FIX IT!1!!!11	
			try:
				if new_final_out[row] != []:

					# shift down the stack
					tiny_stack[0] = tiny_stack[1]
					tiny_stack[1] = tiny_stack[2]
					tiny_stack[2] = row

					# base of the ID
					base_str = row[:-1]

					zeros = []

					# check if child or parent

					if row[-1] == '3':
						if tiny_stack[1] == base_str+'1':
							if phen_list != {}:
								for x in range(0,len(gens_list)+len(phen_list.values()[0])+2):
									zeros.append('0')
							else:
								for x in range(0,len(gens_list)+2):
									zeros.append('0')

							if group_list == []:
								writer.writerow([int(row.split('_')[-2])]+ [base_str+'2']+['0']+['0'] +['0'] + zeros)
							else:
								if row in group_list:
									writer.writerow([int(row.split('_')[-2])]+ [base_str+'2']+['0']+['0'] +['0'] + zeros)
						elif tiny_stack[1] == base_str+'2':
							print "do nothing"
						else:
							if phen_list != {}:
								for x in range(0,len(gens_list)+len(phen_list.values()[0])+2):
									zeros.append('0')
							else:
								for x in range(0,len(gens_list)+2):
									zeros.append('0')

							if group_list == []:
								writer.writerow([int(row.split('_')[-2])]+ [base_str+'1']+['0']+['0'] +['0']+ zeros)
								writer.writerow([int(row.split('_')[-2])]+ [base_str+'2']+['0']+['0'] +['0']+ zeros)
							else:
								if row in group_list:
									writer.writerow([int(row.split('_')[-2])]+ [base_str+'1']+['0']+['0'] +['0']+ zeros)
									writer.writerow([int(row.split('_')[-2])]+ [base_str+'2']+['0']+['0'] +['0']+ zeros)

					elif row[-1] == '2' and tiny_stack[1] != base_str+'1':
							if phen_list != {}:
								for x in range(0,len(gens_list)+len(phen_list.values()[0])+2):
									zeros.append('0')
							else:
								for x in range(0,len(gens_list)+2):
									zeros.append('0')
							if group_list == []:
								writer.writerow([int(row.split('_')[-2])]+[base_str+'1']+['0']+['0'] +['0']+ zeros)
							else:
								if row in group_list:
									writer.writerow([int(row.split('_')[-2])]+[base_str+'1']+['0']+['0'] +['0']+ zeros)

				
					c = []

					for column in range(len(gens_list)):

						c += new_final_out[row][column].split(',')

					par_1 = 0
					par_2 = 0
					if int(row[-1]) > 2:
						par_1 = base_str+'1'
						par_2 = base_str+'2'

					if phen_list != {}:
						try:
							z = [] + [int(row.split('_')[-2])] + [row] + [par_1] + [par_2] + [genders[row]] + c + phen_list[row]
						except KeyError, e:
							z = [] + [int(row.split('_')[-2])] + [row] + [par_1] + [par_2] + [genders[row]]  + c
					else:
						z = [] + [int(row.split('_')[-2])] + [row] + [par_1] + [par_2] + [genders[row]]  + c


					if group_list == []:
						writer.writerow(z)
					else:
						if row in group_list:
							writer.writerow(z)

			except KeyError, e:

				tmeptemptemp = 1+1
		#print final_out
		#row = [] + [str(row.individual_id)] + [str(row.new_id)] + [fr] + [sn]
		#writer.writerow(row)
	return send_from_directory(gen_app.config['UPLOAD_FOLDER'], filename=filename)

def gen_ped(project_id):
	filename = "random"

	final_out = {}
	gens_list = {}
	ordered_ind = []

	ind = models.Individual.query.filter_by(project_id=project_id).order_by(models.Individual.new_id.asc()).all()
	for row in ind:
		ordered_ind.append(row.new_id)
		final_out[row.new_id] = []
	
	gens = models.Genotype.query.all()
	for row in gens:
		gens_list[row.snp] = [row.snp]

	for i in gens_list:
		current_gen = models.Genotype.query.filter_by(project_id=project_id).order_by().filter(models.Genotype.snp == i).all()
		for row in current_gen:
			final_out[row.individual_id] += [row.call]
	
	new_final_out = {}
	for row in final_out:
		if final_out[row] != []:
			new_final_out[row] = final_out[row]
	

	with open(gen_app.config['UPLOAD_FOLDER'] + filename, 'w+') as f:
		writer = csv.writer(f, delimiter=',')
		final_line = []
		for i in ind:
			final_line.append([i.new_id])

		for column in range(len(gens_list)):
			A = False
			C = False
			G = False
			T = False
			X = False

			for row in new_final_out:
				if new_final_out[row] != []:
					spl = new_final_out[row][column].split("/")
					if spl[0] == "A" or spl[1] == "A":
						A = True
					if spl[0] == "C" or spl[1] == "C":
						C = True
					if spl[0] == "G" or spl[1] == "G":
						G = True
					if spl[0] == "T" or spl[1] == "T":
						T = True
					#elif spl[0] == "X" or spl[2] == "X":
					#	X = True

			lol = 0
			for row in new_final_out:
				if new_final_out[row] != []:
					fr = ""
					sn = ""
					if A and G:
						if new_final_out[row][column] == "A/G":
							fr = "1"
							sn = "2"
						elif new_final_out[row][column] == "A/A":
							fr = sn = "1"
						elif new_final_out[row][column] == "G/G":
							fr = sn = "2"
					elif A and C:
						if new_final_out[row][column] == "A/C":
							fr = "1"
							sn = "2"
						elif new_final_out[row][column] == "A/A":
							fr = sn = "1"
						elif new_final_out[row][column] == "C/C":
							fr = sn = "2"
					elif A and T:
						if new_final_out[row][column] == "A/T":
							fr = "1"
							sn = "2"
						elif new_final_out[row][column] == "A/A":
							fr = sn = "1"
						elif new_final_out[row][column] == "T/T":
							fr = n = "2"
					elif C and G:
						if new_final_out[row][column] == "C/G":
							fr = "1"
							sn = "2"
						elif new_final_out[row][column] == "C/C":
							fr = sn = "1"
						elif new_final_out[row][column] == "G/G":
							fr = sn = "2"
					elif C and T:
						if new_final_out[row][column] == "C/T":
							fr = "1"
							sn = "2"
						elif new_final_out[row][column] == "C/C":
							fr = sn = "1"
						elif new_final_out[row][column] == "T/T":
							fr = sn = "2"
					elif G and T:
						if new_final_out[row][column] == "G/T":
							fr = "1"
							sn = "2"
						elif new_final_out[row][column] == "G/G":
							fr = sn = "1"
						elif new_final_out[row][column] == "T/T":
							fr = sn = "2"
					elif X:
						fr = sn = "X"
					new_final_out[row][column] = fr+','+sn
					lol += 1


		# a stack used to keep track of previously encountered IDs
		tiny_stack = ['0','0','0']

		for row in ordered_ind:
			#TODO That's dirty: you are expecting to catch
			# an exception in the if in order to skip a missing entry. FIX IT!1!!!11	
			try:
				if new_final_out[row] != []:

					# shift down the stack
					tiny_stack[0] = tiny_stack[1]
					tiny_stack[1] = tiny_stack[2]
					tiny_stack[2] = row

					# base of the ID
					base_str = row[:-1]

					# check if child or parent
					if row[-1] == '3':
						if tiny_stack[1] == base_str+'1':
							writer.writerow([int(row.split('_')[2])]+ [base_str+'2']+['0']+['0'])
						elif tiny_stack[1] == base_str+'2':
							print "do nothing"
						else:
							writer.writerow([int(row.split('_')[2])]+ [base_str+'1']+['0']+['0'])
							writer.writerow([int(row.split('_')[2])]+ [base_str+'2']+['0']+['0'])
					elif row[-1] == '2' and tiny_stack[1] != base_str+'1':
							writer.writerow([int(row.split('_')[2])]+[base_str+'1']+['0']+['0'])
				
					c = []

					for column in range(len(gens_list)):
						c += new_final_out[row][column].split(',')

					par_1 = 0
					par_2 = 0
					if int(row[-1]) > 2:
						par_1 = base_str+'1'
						par_2 = base_str+'2'

					z = [] + [int(row.split('_')[2])] + [row] + [par_1] + [par_2] + c
					writer.writerow(z)

			except KeyError, e:
				tmeptemptemp = 1+1
		#print final_out
		#row = [] + [str(row.individual_id)] + [str(row.new_id)] + [fr] + [sn]
		#writer.writerow(row)
	return filename

def gen_map(project_id):
	filename = "random2"
	from sqlalchemy import distinct
	geno = models.Genotype.query.filter_by(project_id=project_id).all()
	darn = {}

	for row in geno:
		darn[row.snp] = row.snp


	with open(gen_app.config['UPLOAD_FOLDER'] + filename, 'w+') as f:
		writer = csv.writer(f, delimiter=',')

		for row in darn:
			r = [] + ["M"] + [darn[row]]
			writer.writerow(r)
	
	return filename




@gen_app.route('/download_dat/<int:project_id>/<path:filename>', methods=['GET'])
@login_required
def download_dat(filename,project_id):
	geno = models.Genotype.query.filter_by(project_id=project_id).all()
	pheno = db.engine.execute('SELECT name FROM phenotype where project_id='+ str(project_id) +' group by name;')
	gen_list = {}
	phn_list = {}

	for row in geno:
		gen_list[row.snp] = row.snp
	for row in pheno:
		phn_list[row.name] = row.name

	with open(gen_app.config['UPLOAD_FOLDER'] + filename, 'w+') as f:
		writer = csv.writer(f, delimiter=',')

		for row in gen_list:
			r = [] + ["M"] + [gen_list[row]]
			writer.writerow(r)
		for row in phn_list:
			r = [] + ["T"] + [phn_list[row]]
			writer.writerow(r)

	return send_from_directory(gen_app.config['UPLOAD_FOLDER'], filename=filename)



@gen_app.route('/log')
@gen_app.route('/log/page/<int:page>')
@login_required
def log_page(page=1):
	try:
		log = models.Log.query.order_by(models.Log.timestamp.desc()).paginate(page, per_page=15)
	except exc.OperationalError:
		flash("No logs found", "info")
		log = None
	import datetime
	for row in log.items:
		row.timestamp = datetime.datetime.fromtimestamp(int(row.timestamp)).strftime('%Y-%m-%d %H:%M:%S')
	return render_template('log.html', title="Logs",rows=log)

@gen_app.route('/help')
@login_required
def help():

	return render_template('help.html', title="Help")

@gen_app.route('/users')
@login_required
def users():
	if g.user.user_name != gen_app.config['ADMIN_USER']:
		flash("You should not be here", "danger")
		return redirect(url_for('index'))

	
	usrs = models.User.query.all()


	return render_template('users.html', title="Users", rows=usrs)



@gen_app.route('/add_user', methods=['POST'])
@login_required
def add_user():
	if g.user.user_name != gen_app.config['ADMIN_USER']:
		flash("You should not be here", "danger")
		return redirect(url_for('index'))

	user = models.User()
	if request.method == 'POST':
		import hashlib
		user.password = hashlib.sha512(request.form["password"]).hexdigest()
		user.user_name = request.form['username']
		user.email = request.form['email']
		db.session.add(user)
		db.session.commit()

	return redirect(url_for('users'))


