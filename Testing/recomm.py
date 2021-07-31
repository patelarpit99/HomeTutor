import sqlalchemy
import MySQLdb
import pandas as pd
# conn=MySQLdb.connect(host="127.0.0.1", port=3306,user="root", password="", db="movie")
import mysql.connector
from mysql.connector import Error
conn = mysql.connector.connect(host='localhost',
                                         database='HOMETUTOR',
                                         user='root',
                                         password='')
if conn.is_connected():

	import warnings
	warnings.filterwarnings('ignore')
	#print("connected")
	#engine = sqlalchemy.create_engine('mysql+pymysql://root:localhost:3306/movie')
	columns_names=["student_id", "student_id", "rating"]
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
        # tables=list(tables)
        # tables=tables[:10]
        # return tables
    # return render_template('recommendation.html',tables=tables)
item=recommend('Ray Dillard')
print(item)