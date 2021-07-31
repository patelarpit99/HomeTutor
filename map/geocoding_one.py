import requests
from flask import Flask,render_template

URL = "https://geocode.search.hereapi.com/v1/geocode"
location = input("Enter the location here: ") #taking user input
api_key = '_JKSO1-A3gwB5jgeg_dBNaucxr-IPNyvBxorkDPYQ20' # Acquire from developer.here.com
PARAMS = {'apikey':api_key,'q':location} 

# sending get request and saving the response as response object 
r = requests.get(url = URL, params = PARAMS) 
data = r.json()
#print(data)

#Acquiring the latitude and longitude from JSON 
latitude = data['items'][0]['position']['lat']
#print(latitude)
longitude = data['items'][0]['position']['lng']
#print(longitude)

#Flask code 
app = Flask(__name__)
@app.route('/')

def map_func():
	return render_template('map.html',apikey=api_key,latitude=latitude,longitude=longitude)#map.html is my HTML file name

if __name__ == '__main__':
    app.run(debug = True)