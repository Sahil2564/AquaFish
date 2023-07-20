

# coding=utf-8
import sys
import os
import glob
import re
import numpy as np
import json
import src.labels as l

# Keras Import
from keras.applications.imagenet_utils import preprocess_input, decode_predictions
from keras.models import load_model
from keras.preprocessing import image

# Flask imports
from flask import Flask, redirect, session, url_for, request, render_template, flash
from werkzeug.utils import secure_filename
from gevent.pywsgi import WSGIServer
from flask_mail import Mail
from flask_mail import *
from random import randint
from flask import jsonify
import json

# imprt Pyodbc for database connection to SQL Server
import pyodbc
conn = pyodbc.connect(
    "Driver={SQL Server};"
    "Server=DESKTOP-MI4D74D\SQLEXPRESS;"
    "Database=AquaFish_db;"
    "Trusted_Connection=yes;"
    #DESKTOP-EPBB7BC\SQLEXPRESS
)

# Define a flask app
app = Flask(__name__)
app.secret_key = 'Flask Error'

#-----Model Import----
# Model saved with Keras model.save()
MODEL_PATH = 'models/AquariumFish.h5'
# MODEL_PATH = 'models/Trysave.h5'

# Load your trained model
model = load_model(MODEL_PATH)
# Print Now Model Ready to Serve
print('Model loaded. Start serving...')

# Read Aquarium Fish Species Description Function
def Read_Description(conn, Fish_Name):
    print("Retrieving Description")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT Description FROM FishDetails WHERE Fish_Name = '"+Fish_Name+"'")
    for row in cursor:
        return row
# Model Predict function
def model_predict(img_path, model):
    img = image.load_img(img_path, target_size=(224, 224))

    # Preprocessing the image
    x = image.img_to_array(img)
    #x = np.true_divide(x, 255)

    x = np.expand_dims(x, axis=0)
    #x = preprocess_input(x)/255
    x = preprocess_input(x)
    preds = model.predict(x)
    preds = np.argmax(preds[0])
    result = str(l.labels[preds])
    descp = Read_Description(conn, result) 
    descp = str(descp)
    return (result + '\n' + descp)
    #return result

#Image Upload and Predict Image
@app.route('/predict', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Get the file from post request
        f = request.files['file']
        # Save the file to ./uploads
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(
            basepath, 'uploads', secure_filename(f.filename))
        f.save(file_path)
        # Make prediction
        preds = model_predict(file_path, model)
        #print(preds)
        result= preds
        return result
    return None
    #descp = Read_Description(conn,result)
    #descp = str(descp)
    # return (result + "\n" + descp)


#-----Users Endpoint----
#Homepage Redirects
@app.route("/")
def home():
    return render_template('index.html')

# For Gmail Verification
with open('config.json', 'r') as f:
    params = json.load(f)['param']

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = params['gmail-user']
app.config['MAIL_PASSWORD'] = params['gmail-password']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

# Generating random number
otp = randint(000000, 999999)

# Login Endpoint
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    susmsg = ''
    userexists = ''
    pwderror = ""
    erroruser = ""
    nameunvalid = ""
    emailunvalid = ""

    if request.method == "POST":

        # Register or SignUP Form Backend
        if request.form['action'] == 'Signup':

            gmail = request.form['email']
            if not gmail:
                return 'Please Enter gmail to verify!'
            msg = Message('OTP', sender='sahilfyp2022@gmail.com',
                          recipients=[gmail])
            msg.body = str(otp)
            mail.send(msg)

            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            cpassword = request.form.get('cpassword')
            print(name, email, password, cpassword)

            if(request.form.get('name') != "" and request.form.get('email') != "" and request.form.get('password') != "" and request.form.get('cpassword') != ""):
                print("empty check")
                # Name Validation
                if(is_name_valid(name)):
                    # Email Validation
                    if(is_email_address_valid(email)):
                        if (password == cpassword):
                            print("password checked")
                            cursor = conn.cursor()
                            cursor.execute(
                                "SELECT * FROM Users WHERE email = ?", (email))
                            if cursor.fetchone() is not None:
                                userexists = " " + email + " Already Exists. Please try different gmail."
                                cursor.close()
                            else:
                                cursor.execute("insert into Users(name, email, password,status) values('"+str(
                                    name)+"','"+str(email)+"','"+str(password)+"', 'unverified');")
                                conn.commit()
                                print("Success")
                                susmsg = name + " user Account has been created"
                                return render_template("verify.html")
                        else:
                            pwderror = "Password and Confirm password Doesnot Match "
                    else:
                        emailunvalid = "Gmail is Not Valid"
                else:
                    nameunvalid = "Name is not Valid"
            else:
                msg = "Required Field"
        # SignIN Form Backend

        elif request.form['action'] == 'Login':
            if(request.method == 'POST'):
                email = request.form.get('email')
                password = request.form.get('password')
                if(email == "admin@gmail.com" and password == "admin"):
                    session['name']=request.form['email'] 
                    return redirect(url_for('homepage'))
                else:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT email,password from Users WHERE email = '"+email+"' AND password = '"+password+"' AND status ='Verifed'")
                    # Fetch one record and return result
                    for row in cursor:
                        if (email == row[0] and password == row[1]):
                            # session['logged_in'] = True
                            # flash('You were successfully logged in')
                            session['email']=request.form['email'] 
                            return redirect(url_for('fishdetection'))
                            # render_template('verify.html')

                    else:
                        # Account doesnt exist or Email/password incorrect
                        erroruser = ' Gmail and Password Doesnot Match !!!! Or  Verify your account'
            print("for login")

    return render_template('login.html',  susmsg=susmsg, userexists=userexists, pwderror=pwderror, erroruser=erroruser)


def is_email_address_valid(email):
    # Email Validation using regex
    if not re.match("^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$", email):
        return False
    return True


def is_name_valid(name):
    # Name Validation using regex
    if not re.match("^[a-zA-Z]*$", name):
        return False
    return True

# for FishDetection of email
@app.route('/fishdetection', methods=['GET', 'POST'])
def fishdetection():
    if 'email' in session:  
        email = session['email']  
        return render_template('fishdetection.html')
    else:  
        return redirect(url_for('login'))
  

# For Gmail validation
@app.route('/validate', methods=['GET', 'POST'])
def validate():
    useropt = request.form['otp']
    success = ""
    error = ""
    if otp == int(useropt):
        email = request.form.get('email')
        cursor = conn.cursor()
        cursor.execute(
            "update Users set status = 'Verifed' where email ='"+email+"' ;")
        cursor.commit()
        cursor.close()
        success = 'Email Verified Successfully....'
        return render_template('verify.html', success=success)
        
    else:
        error = 'Email not verified, Try Again!!!'
        return render_template('verify.html', error=error)

# Forget Password Endpoint
@app.route('/password_forget', methods=['GET', 'POST'])
def password_forget():
    psw = ""
    erroruser = ""
    if(request.method == 'POST'):
        email = request.form.get('email')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT email, password from Users WHERE email = '"+email+"'")
        for row in cursor:
            print(row)
            if(email == row[0]):
                psw = row[1]
            else:
                erroruser = "Invalid Gmail"
    return render_template('password_forget.html', psw=psw, erroruser=erroruser)

# contact Endpoint
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    success = ""
    error = ""
    empty = ""
    emailerror = ""
    nameerror = ""
    if(request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        # empty Validation
        if(request.form.get('name') != "" and request.form.get('email') != "" and request.form.get('message') != ""):
            # Name Validation
            if(is_name_valid(name)):
                # Email Validation
                if(is_email_address_valid(email)):
                    if True:
                        cursor = conn.cursor()
                        cursor.execute("insert into Contacts(name, email, message) values('"+str(
                            name)+"','"+str(email)+"','"+str(message)+"');")
                        cursor.commit()
                        success = "Message Send Successfully..."
                    else:
                        error = "Inserting Error in a Database"
                else:
                    emailerror = "Email is Not Valid"
            else:
                nameerror = "Name is Not Valid"
        else:
            empty = "Field are Required..."
    return render_template('contact.html', success=success, error=error, empty=empty, emailerror=emailerror, nameerror=nameerror)

# About Us Endpoint
@app.route("/about")
def about():
    return render_template('about.html')

#-----Admin Endpoint----

# AddFishData
@app.route('/addfishdata', methods=['GET', 'POST'])
def addfishdata():
    if 'name' in session:  
        email = session['name']  
        msg = ""
        if request.method == "POST":
            #SN = request.form.get('SN')
            Fish_Name = request.form.get('Fish_Name')
            Description = request.form.get('Description')

            #Plant_Avaliability = request.form.get('Plant_Avaliability')
            print(Fish_Name, Description)
            cursor = conn.cursor()
            cursor.execute("insert into FishDetails(Fish_Name, Description) values ('" +str(Fish_Name)+"','" + str(Description)+"');")
            cursor.commit()
            msg = "Successfully Added....."
            cursor.close()
            #cursor = conn.cursor()
            #cursor.execute("select * from FishDetails")
            # data = cursor.fetchall()  # data from database
            # cursor.close()
        return render_template('adminlayout/addfishdata.html', msg=msg)
    else:  
        return redirect(url_for('login'))

# fishdetail code
@app.route('/viewfishdata', methods=['GET', 'POST'])
def viewfishdata():
    if 'name' in session:  
        email = session['name']  
        try:
            cursor = conn.cursor()
            cursor.execute("select * from FishDetails")
            data = cursor.fetchall()  # data from database
            cursor.close()
        except:
            print("Something Wrong in View_reports Function")
        return render_template('adminlayout/viewfishdata.html', value=data)
    else:  
        return redirect(url_for('login'))

# manageruser code
@app.route('/manageuser', methods=['GET', 'POST'])
def manageuser():
    if 'name' in session:  
        email = session['name']  
        try:
            cursor = conn.cursor()
            cursor.execute("select * from Users")
            data = cursor.fetchall()  # data from database
            cursor.close()
        except:
            print("Something Wrong. Check Function")
        return render_template('adminlayout/manageuser.html', value=data)
    else:  
        return redirect(url_for('login'))
   


@app.route("/homepage")
def homepage():
    if 'name' in session:  
        email = session['name']  
        return render_template('adminlayout/homepage.html')
    else:  
        return redirect(url_for('login'))
   

#logout
@app.route("/logout")
def logout():
    if 'email' in session:  
        session.pop('email',None)  
    return redirect(url_for('login'))
    # return render_template('login.html')

# admin logout
@app.route("/log")
def log():
    if 'name' in session:  
        session.pop('name',None)  
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)
