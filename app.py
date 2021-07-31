from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL 
from wtforms import Form, StringField, TextAreaField , PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import numpy as np
from math import radians, cos, sin, asin, sqrt

app = Flask(__name__)

#Config MySql
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']=''
app.config['MYSQL_DB']='HOMETUTOR'
app.config['MYSQL_CURSORCLASS']='DictCursor'

# Init MySQL
mysql = MySQL(app)

#Index Page	
@app.route('/')
def index():
	return render_template('home.html')

#About
@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/whyus')
def whyus():
	return render_template('whyus.html')

@app.route('/contact')
def contact():
	return render_template('contact.html')


#Student Main Page
@app.route('/student')
def student():
	return render_template('student.html')

#Teacher Main Page
@app.route('/teacher')
def teacher():
	return render_template('teacher.html')

#Check if User is logged in
def login_required(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args,**kwargs)
		else:
			flash('Unauthorized, Please login', 'danger')
			return redirect(url_for('home'))
	return wrap

def haversine(lat1, lon1, lat2, lon2):

      R = 6372.8 
      lat1=float(lat1)
      lon1=float(lon1)
      lat2=float(lat2)
      lon2=float(lon2)

      dLat = radians(lat2 - lat1)
      dLon = radians(lon2 - lon1)
      lat1 = radians(lat1)
      lat2 = radians(lat2)

      a = sin(dLat/2)**2 + cos(lat1)*cos(lat2)*sin(dLon/2)**2
      c = 2*asin(sqrt(a))

      return R * c

# Recommendation
#Dataset - https://www.kaggle.com/hegdetapan/bangaloreareaspincodewithlatitudelongitude
@app.route('/recommendation')
@login_required
def recommendation():
	import pandas as pd
	# conn=MySQLdb.connect(host="127.0.0.1", port=3306,user="root", password="", db="movie")
	# import mysql.connector
	# from mysql.connector import Error
	# conn = mysql.connector.connect(host='localhost',
	#                                          database='HOMETUTOR',
	#                                          user='root',
	#                                          password='')
	conn = mysql.connection

	username = session.get('username')

	import warnings
	warnings.filterwarnings('ignore')
	#print("connected")
	#engine = sqlalchemy.create_engine('mysql+pymysql://root:localhost:3306/movie')
	cur = conn.cursor()
	cur.execute("Select * from student where username = %s", [username])
	data = cur.fetchone()
	stu_id = data['id']
	cur.execute("SELECT * from location_student where id= %s", [stu_id])
	data = cur.fetchone()
	s_latitude = data['latitude']
	s_longitude = data['longitude']
	cur.execute("SELECT * from teacher")
	data=cur.fetchall()
	totalTeachers=len(data)

	#Calculating distance
	distance = [0] * (totalTeachers+1)
	init_coord = [[0]*4]* (totalTeachers+1)
	cur.execute("SELECT * from location_teacher")
	i=1
	for row in cur:
		lati=row['latitude']
		longi=row['longitude']
		distance[i]=haversine(s_latitude,s_longitude,lati,longi)
		init_coord[i]=[s_latitude,s_longitude,lati,longi]
		i=i+1

	# Main Code of Recommender System
	columns_names=["student_id", "teacher_id", "rating"]
	df=pd.read_sql("select * from ratings", conn, columns=columns_names)
	columns_names=["teacher_id", "teacher_name"]
	df2=pd.read_sql("select id as teacher_id, name as teacher_name from teacher",conn,columns=columns_names)
	df= pd.merge(df, df2, on="teacher_id")
	df2=df.groupby('teacher_name').mean()['rating'].sort_values(ascending=False)
	#print(df2)
	df3=df.groupby('teacher_name').count()['rating'].sort_values(ascending=False)
	ratings=pd.DataFrame(df.groupby('teacher_name').mean()['rating'])
	# Add a column nums_of_ratings
	ratings['nums_of_ratings']=pd.DataFrame(df.groupby('teacher_name').count()['rating'])
	#print(ratings)
	ratings=ratings.sort_values(by='rating', ascending=False)
	teacher_matrix=df.pivot_table(index="student_id", columns="teacher_name", values="rating")
	ratings=ratings.sort_values('nums_of_ratings',ascending=False)

	#print(ratings)
	#print(teacher_matrix)

	def recommend(teach_name):
	    user_ratings=teacher_matrix[teach_name]
	    similar_to_it=teacher_matrix.corrwith(user_ratings)
	    corr_teacher = pd.DataFrame(similar_to_it, columns=['Correlation'])

	    
	    corr_teacher.dropna(inplace=True)
	    corr_teacher = corr_teacher.join(ratings['nums_of_ratings'])
	    #print(corr_teacher)
	    predictions=corr_teacher[corr_teacher['nums_of_ratings']>1].sort_values('Correlation', ascending=False)
	    tables=predictions.index.values
	    tables=list(tables)
	    tables=tables[:10]
	    return tables


	min_dis=100000;
	teacher_id=1;
	for i in range(1,len(distance)):
		if(min_dis>distance[i]):
			min_dis=distance[i]
			teacher_id=i
	print(teacher_id)
	result = cur.execute('SELECT name from teacher where id = %s', [teacher_id])
	data = cur.fetchone()
	name=data['name']
	tables=recommend(name)

	recommend_distance = []

	#Getting Distances of Recommended Teachers
	coord = []
	for i in range(len(tables)):
		cur.execute("SELECT id from teacher where name=%s", [tables[i]])
		data = cur.fetchone()
		recommend_distance.append(distance[data['id']])
		coord.append(init_coord[data['id']])

	merged_table = [(tables[i], recommend_distance[i], coord[i]) for i in range(0, len(tables))]
	merged_table.sort(key=lambda x:x[1])

	cur.close()

	return render_template('recommendation.html',len=len(tables),tables=merged_table)

#Nearby Teacher
@app.route('/nearby_loc')
def nearby_loc():
	conn = mysql.connection
	username=session.get('username')
	cur = conn.cursor()
	cur.execute("Select * from student where username = %s", [username])
	data = cur.fetchone()
	stu_id = data['id']
	cur.execute("SELECT * from location_student where id= %s", [stu_id])
	data = cur.fetchone()
	s_latitude = data['latitude']
	s_longitude = data['longitude']
	cur.execute("SELECT * from teacher")
	data=cur.fetchall()
	totalTeachers=len(data)

	#Calculating distance
	distance = [0] * (totalTeachers+1)
	coord = [[0]*4]* (totalTeachers+1)
	cur.execute("SELECT * from location_teacher")
	i=1
	for row in cur:
		lati=row['latitude']
		longi=row['longitude']
		distance[i]=haversine(s_latitude,s_longitude,lati,longi)
		coord[i]=[s_latitude,s_longitude,lati,longi]
		i=i+1
	i=1;
	cur.execute("SELECT * from teacher")
	teacher=[0] * (totalTeachers+1)
	for row in cur:
		teacher[i]=row['name']
		i=i+1

	tables = [(teacher[i],distance[i],coord[i]) for i in range(1,len(distance))]
	tables.sort(key=lambda x:x[1])
	tables=tables[:10]

	cur.close()

	# merged_table = [(tables[i], recommend_distance[i], coord[i]) for i in range(0, len(tables))]
	# merged_table.sort(key=lambda x:x[1])


	return render_template('recommendation.html',len=len(tables),tables=tables)


#Register Form Class
class RegisterForm(Form):
	name = StringField('Name', [validators.Length(min=1, max=50)])
	username = StringField('Username', [validators.Length(min=4, max=25)])
	email = StringField('Email', [validators.Length(min=6,max=50)])
	password = PasswordField('Password',[
			validators.DataRequired(),
			validators.EqualTo('confirm', message="Passwords do not match")
		])
	confirm = PasswordField('Confirm Password')
	phone = StringField('Phone', [validators.Length(min=10,max=10)])

#Student Register
@app.route('/register_student', methods=['GET', 'POST'])
def register_student():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		username = form.username.data
		# password = sha256_crypt.hash(str(form.password.data))  
		password=form.password
		phone = form.phone.data

		#Create Cursor
		cur = mysql.connection.cursor()

		#Execute Query
		cur.execute("INSERT INTO student(name,email,username,password,phone) VALUES(%s, %s, %s, %s, %s)", (name,email,username,password,phone))

		# Commit to DB
		mysql.connection.commit()

		#Close conn
		cur.close()

		flash('You are now registered and can login', 'success')  

		return redirect(url_for('login_student'))

	return render_template('register_student.html', form=form)

#Teacher  Register
@app.route('/register_teacher', methods=['GET', 'POST'])
def register_teacher():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		username = form.username.data
		# password = sha256_crypt.hash(str(form.password.data))  
		password=form.password
		phone = form.phone.data

		#Create Cursor
		cur = mysql.connection.cursor()

		#Execute Query
		cur.execute("INSERT INTO teacher(name,email,username,password,phone) VALUES(%s, %s, %s, %s, %s)", (name,email,username,password,phone))

		# Commit to DB
		mysql.connection.commit()

		#Close conn
		cur.close()

		flash('You are now registered and can login', 'success')  

		return redirect(url_for('login_teacher'))

	return render_template('register_teacher.html', form=form)

#Student Login
@app.route('/login_student', methods=['POST','GET']) 
def login_student():
	if request.method == 'POST':
		#Get Form Fields
		username = request.form['username']
		password_candidate = request.form['password']


		#Create cursor
		cur = mysql.connection.cursor()

		#Get user by username
		result = cur.execute("SELECT * FROM student WHERE username = %s" , [username])

		if result>0:
			#Get stored hash
			data = cur.fetchone() 
			password = data['password']

			#Compare the passwords
			# if sha256_crypt.verify(password_candidate,password):
			if(password_candidate==password):
				#Passed
				session['logged_in'] = True
				session['username'] = username

				flash("You are now logged in", 'success')
				return redirect(url_for('dashboard_student'))

			else:
				error = "Invalid Login"
				return render_template('login_student.html',error=error)

			cur.close()
		else:
			error = "User Not Found"
			return render_template('login_student.html',error=error)


	return render_template('login_student.html')


#Teacher Login
@app.route('/login_teacher', methods=['POST','GET']) 
def login_teacher():
	if request.method == 'POST':
		#Get Form Fields
		username = request.form['username']
		password_candidate = request.form['password']


		#Create cursor
		cur = mysql.connection.cursor()

		#Get user by username
		result = cur.execute("SELECT * FROM teacher WHERE username = %s" , [username])

		if result>0:
			#Get stored hash
			data = cur.fetchone() 
			password = data['password']

			#Compare the passwords
			# if sha256_crypt.verify(password_candidate,password):
			if(password_candidate==password):

				#Passed
				session['logged_in'] = True
				session['username'] = username

				flash("You are now logged in", 'success')
				return redirect(url_for('dashboard_teacher'))

			else:
				error = "Invalid Login"
				return render_template('login_teacher.html',error=error)

			cur.close()
		else:
			error = "User Not Found"
			return render_template('login_teacher.html',error=error)


	return render_template('login_teacher.html')

#Logout
@app.route('/logout')
def logout():
	session.clear()
	flash("You are now logged out", 'success')
	return redirect(url_for('home'))  


#Home Route
@app.route('/home')
def home():
	return render_template('home.html')

# @app.route('/addLocation/<whichTable>',methods=['POST'])
# def addLocation(whichTable):
# 	if request.method=='POST':
# 		username = session.get('username')
# 		latitude = request.form['Latitude']
# 		longitude = request.form['Longitude']

# 		#Create cursor
# 		cur = mysql.connection.cursor()

# 		#Execute Query
# 		results = cur.execute("SELECT * FROM whichTable where username = %s", ['username'])

# 		if(results==0):
# 			cur.execute("INSERT INTO whichTable(username,latitude,longitude) VALUES(%s, %s, %s)", (username,latitude,longitude))

# 		# Commit to DB
# 		mysql.connection.commit()

# 		#Close conn
# 		cur.close()


#Dashboard Student
@app.route('/dashboard_student')
@login_required 
def dashboard_student():
	# addLocation("location_student")
	if request.method=='POST':
		username = session.get('username')
		latitude = request.form['Latitude']
		longitude = request.form['Longitude']

		#Create cursor
		cur = mysql.connection.cursor()

		#Execute Query
		results = cur.execute("SELECT * FROM location_student where username = %s", ['username'])

		if(results==0):
			cur.execute("INSERT INTO location_student(username,latitude,longitude) VALUES(%s, %s, %s)", (username,latitude,longitude))

		# Commit to DB
		mysql.connection.commit()

		#Close conn
		cur.close()

	return render_template('dashboard_student.html')

#Dashboard Teacher
@app.route('/dashboard_teacher',methods=['POST','GET'])
@login_required 
def dashboard_teacher():
	# addLocation("location_teacher")
	if request.method=='POST':
		username = session.get('username')
		latitude = request.form['Latitude']
		longitude = request.form['Longitude']

		#Create cursor
		cur = mysql.connection.cursor()

		#Execute Query
		results = cur.execute("SELECT * FROM location_teacher where username = %s", ['username'])

		if(results==0):
			cur.execute("INSERT INTO location_teacher(username,latitude,longitude) VALUES(%s, %s, %s)", (username,latitude,longitude))

		# Commit to DB
		mysql.connection.commit()

		#Close conn
		cur.close()

	return render_template('dashboard_teacher.html')



#Profile Teacher
@app.route('/profile_teacher')
@login_required
def profile_teacher():
	cur = mysql.connection.cursor()
	#Get user by username
	result = cur.execute("SELECT * FROM teacher WHERE username = %s" , [session['username']])
	data = cur.fetchone() 
	return render_template('profile_teacher.html',data=data)

#Edit
@app.route('/edit',methods=['POST','GET'])
@login_required
def edit():
	# if request.method=='POST':

	cur = mysql.connection.cursor()
	#Get user by username
	result = cur.execute("SELECT * FROM teacher WHERE username = %s" , [session['username']])
	data = cur.fetchone() 
	return render_template('edit.html',data=data)

# def haversine(lat1, lon1, lat2, lon2):

#       R = 6372.8 

#       dLat = radians(lat2 - lat1)
#       dLon = radians(lon2 - lon1)
#       lat1 = radians(lat1)
#       lat2 = radians(lat2)

#       a = sin(dLat/2)**2 + cos(lat1)*cos(lat2)*sin(dLon/2)**2
#       c = 2*asin(sqrt(a))

#       return R * c

# # Usage
# lon1 = -103.548851
# lat1 = 32.0004311
# lon2 = -103.6041946
# lat2 = 33.374939

# print(haversine(lat1, lon1, lat2, lon2))

#Teacher Rating
@app.route('/ratings')
def ratings():

	cur = mysql.connection.cursor()
	#Get user by username
	totalTeachers = 0
	teacher_name = [0] * 1000 
	result = cur.execute("SELECT * FROM teacher")
	for row in cur:
		totalTeachers = totalTeachers+1
		teacher_name[totalTeachers] = row['name']

	distance = [0] * (totalTeachers+1)
	cur.execute("SELECT * from location_teacher")
	i=1
	for row in cur:
		lati=row['latitude']
		longi=row['longitude']
		distance[i]=haversine(s_latitude,s_longitude,lati,longi)
		coord[i]=[s_latitude,s_longitude,lati,longi]
		i=i+1

	username=session.get('username')
	cur.execute("SELECT * from student where username = %s", [username])
	data = cur.fetchone()
	stu_id = data['id']

	cur.execute("SELECT * from ratings where id= %s",[stu_id])
	teacher_rating = [0] * (totalTeachers+1)
	for row in cur:
		t_id = row['teacher_id']
		teacher_rating[t_id] = row['rating']

	tables = [(distance[i],teacher_name[i],teacher_rating[i]) for i in range(1,totalTeachers)]

	return render_template('ratings.html',tables=tables)


if __name__ == '__main__':
	app.secret_key='secret123'
	app.run(debug=True)