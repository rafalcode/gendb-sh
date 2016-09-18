### Forked from Valentin Tunev's git hub repo

### SETUP

####Requirements:
```
pip install sqlalchemy==0.9.7
pip install flask==0.10.1
pip install flask-login==0.2.11
pip install flask-sqlalchemy==2.0
pip install flask-uploads==0.1.3
pip install flask-wtf==0.10.2
pip install pymysql==0.6.2
pip install wtforms==2.0.1
```
Original instructions:
1. Setup (the MySQL) database using the provided SQL file.
2. Manually add the admin user in the database (password needs to be sha512 hash)
3. Enter the needed values in config.py
4. run 'python run'
5. Navigate to the URL of your server and login

Ref. No. 3, such a file doesn't exist.

### arch.tar.gz
This is an awkwardly packaged (mistakenly - one presumes - recursived compressed) set of flask,celery and sqlalchemy
core libraries which are not part of the gendb package. These can be installed with the usual virtualenv procedure.
So, therefore, this fork will leave them out. There is also flask subdirectory which pretty much has nothings
and that vitualenv should take of.

### Relevant links
config's:
http://stackoverflow.com/questions/5025720/how-do-you-set-up-a-flask-application-with-sqlalchemy-for-testing
the config-py approach seems to be described here:
http://exploreflask.com/en/latest/configuration.html
