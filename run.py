from flask import Flask, request, jsonify
from PIL import Image

import pymysql
import face_recognition
import json
import urllib.request

app = Flask(__name__)

class Database:
    def __init__(self):
        host = "localhost"
        user = "root"
        password = "password"
        db = "newdb"
        self.con = pymysql.connect(host=host, user=user, password=password, db=db, cursorclass=pymysql.cursors.
                                   DictCursor)
        self.cur = self.con.cursor()

    def add_user(self,name,email,phone,profile_image,status,encoding):
    	num = self.cur.execute("INSERT into face_table(name,email,phone,profile_image,status,encoding) VALUES(\""+name+"\",\""+email+"\",\""+phone+"\",\""+profile_image+"\",\""+status+"\",\""+encoding+"\")")
    	self.con.commit()
    	if num:
    		return "success"
    	else:
    		return "error"

    def find_user_encoding(self,email):
    	self.cur.execute("SELECT encoding FROM face_table WHERE email =\""+email+"\"")
    	result = self.cur.fetchall()
    	return result

    def get_all_users(self):
    	self.cur.execute("SELECT * FROM face_table")
    	result = self.cur.fetchall()
    	return result

    def get_status(self,email):
    	self.cur.execute("SELECT status FROM face_table WHERE email =\""+email+"\"")
    	result = self.cur.fetchall()
    	return result

    def deactivate_user(self,email):
    	number = self.cur.execute("UPDATE face_table SET status=\"unverified\" WHERE email=\""+email+"\"")
    	self.con.commit()
    	return number

    def user_exists(self,email):
      val = self.cur.execute("SELECT * FROM face_table WHERE email =\""+email+"\"")
      result = self.cur.fetchall()
      return result


@app.route("/api/v1/add_user_with_face",methods=['POST'])
def add_user_with_face():
	if request.method == 'POST':
		name = request.form['name']
		email = request.form['email']
		phone = request.form['phone']
		profile_image = request.form['profile_image']
		status = "unverified"
		if not name or not email or not phone or not profile_image:
			reply = {
              				"status": "error",
              				"message": "insufficient parameters",
              				"data": {}
            			}
			return reply

		image_name = "user_images/"+profile_image.split('/')[-1]
		urllib.request.urlretrieve(profile_image, image_name)

		try:
			new_image = face_recognition.load_image_file(image_name)
			image_encodings = face_recognition.face_encodings(new_image)[0]
		except IndexError:
			reply = {
   						"status": "error",
   						"message": "no face detected in image",
   						"data": {}
   					}
			return reply
		except:
			reply = {
   						"status": "error",
   						"message": "invalid image url",
   						"data": {}
   					}
			return reply

		db = Database()

		result = db.add_user(name,email,phone,profile_image,status,json.dumps(image_encodings.tolist()))
		
		if result is "success":
			reply = {
   						"status": "success",
   						"message": "successfully added new user",
   						"data": {}
   				}
		elif result is "error":
   			reply = {
   						"status": "error",
   						"message": "internal error in adding new user",
   						"data": {}
   				}
		return reply


@app.route("/api/v1/authorize_user",methods=['POST'])
def authorize_user():
	if request.method == 'POST':
		email = request.form['email']
		profile_image = request.form['profile_image']

		if not email or not profile_image:
			reply = {
              				"status": "error",
              				"message": "insufficient parameters",
              				"data": {}
            			}
			return reply

		image_name = "user_images/"+profile_image.split('/')[-1]
		urllib.request.urlretrieve(profile_image, image_name)

		try:
			new_image = face_recognition.load_image_file(image_name)
			image_encoding = face_recognition.face_encodings(new_image)[0]
		except IndexError:
			reply = {
   						"status": "error",
   						"message": "no face detected in image",
   						"data": {}
   					}
			return reply
		except:
			reply = {
   						"status": "error",
   						"message": "invalid image url",
   						"data": {}
   					}
			return reply


		db = Database()
		try:
			val = db.get_status(email)[0]["status"]
		except IndexError:
			reply = {
   						"status": "error",
   						"message": "email id not registered",
   						"data": {}
   					}
			return reply
		else:
			if val is "unverified":
				reply = {
   						"status": "error",
   						"message": "user unverified",
   						"data": {}
   					}
				return reply

		user_encoding = db.find_user_encoding(email)
		if len(user_encoding):
			user_encoding = json.loads(user_encoding[0]['encoding'])
			comparison_result = face_recognition.compare_faces([user_encoding],image_encoding)
			if comparison_result[0]:
				reply = {
   						"status": "success",
   						"message": "user authorized",
   						"data": {}
   					}
				return reply
			else:
				reply = {
   						"status": "error",
   						"message": "user not authorized",
   						"data": {}
   					}
				return reply
		else:
			reply = {
   						"status": "error",
   						"message": "email id not registered",
   						"data": {}
   					}
			return reply

@app.route("/api/v1/verify_user_face",methods=['POST'])
def verify_user_face():
	if request.method == 'POST':
		email = request.form['email']
		db = Database()
		
		if not email:
			reply = {
              				"status": "error",
              				"message": "insufficient parameters",
              				"data": {}
            			}
			return reply

		try:
			val = db.get_status(email)[0]["status"]
		except IndexError:
			reply = {
   						"status": "error",
   						"message": "email id not registered",
   						"data": {}
   					}
			return reply
		else:
			reply = {
   						"status": "success",
   						"message": val,
   						"data": {}
   					}
			return reply

@app.route("/api/v1/list_users_with_face",methods=['GET'])
def list_users_with_face():
	if request.method == 'GET':
		db = Database()
		result = db.get_all_users()
		reply = {
   						"status": "success",
   						"message": "list of all users",
   						"data": result
   					}
		return reply

@app.route("/api/v1/deactivate_user_face",methods=['POST'])
def deactivate_user_face():
	if request.method == 'POST':
		email = request.form['email']
		db = Database()

		if not email:
			reply = {
              				"status": "error",
              				"message": "insufficient parameters",
              				"data": {}
            			}
			return reply

		user = db.user_exists(email)
		number = db.deactivate_user(email)

		if number is 1:
			reply = {
   						"status": "success",
   						"message": "successfully deactivated",
   						"data": {}
   					}
			return reply
		elif number is 0 and user:
			reply = {
   						"status": "success",
   						"message": "already deactivated",
   						"data": {}
   					}
			return reply
		elif number is 0 and not user:
			reply = {
              					"status": "error",
              					"message": "email id not registered",
              					"data": {}
            			}
			return reply
		else:
			reply = {
   						"status": "error",
   						"message": "internal error try again",
   						"data": {}
   					}
			return reply


if __name__ == "__main__":
    app.run()
