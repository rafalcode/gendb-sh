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

1. Setup database using the provided SQL file.
2. Manually add the admin user in the database (password needs to be sha512 hash)
3. Enter the needed values in config.py
4. run 'python run'
5. Navigate to the URL of your server and login
