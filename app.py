from flask import Flask, render_template, request, redirect, session, send_file, flash
from pymongo import MongoClient
import bcrypt
from functools import wraps
from selenium import webdriver
import chromedriver_autoinstaller
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import copy
import pyperclip
from selenium.webdriver import ActionChains
import os
from io import BytesIO
import base64
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
import secrets
from datetime import datetime, timedelta
import pandas as pd
import openpyxl





app = Flask(__name__)
app.secret_key = "Lior_secret_12344321"

client = MongoClient('mongodb://127.0.0.1:27017')  # Replace with your MongoDB connection string
db = client['myDB']  # Replace with your database name
collection = db['users']  # Replace with your collection name

app.config['UPLOAD_FOLDER'] = '/home/lior/computer_science/whatsapp_bot/WhatsApp-Bot-Site/temp'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'webm', 'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'mpeg'}
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'delicious.final.project@gmail.com'
app.config['MAIL_PASSWORD'] = 'hmbgzxxozniqyzbr'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)



# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


# Function to send the password reset email
def send_password_reset_email(email, token):
    msg = Message('Password Reset',sender='delicious.final.project@gmail.com' , recipients=[email])
    msg.body = f"Click the following link to reset your password: {request.host_url}reset-password/{token}"
    mail.send(msg)

def generate_password_reset_token():
    token = secrets.token_hex(16)  # Generate a random hex token with 16 characters
    return token

def get_token_expiration_time():
    # Set the token expiration time to 1 hour from the current time
    expiration_time = datetime.now() + timedelta(hours=1)
    return expiration_time

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        # Retrieve the new password from the form
        new_password = request.form['password']

        # Find the user in the collection using the token
        user = collection.find_one({'reset_token': token})

        if user:
            # Check if the token has not expired
            expiration_time = user.get('expiration_time')
            if expiration_time and datetime.now() <= expiration_time:
                # Hash the new password
                hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

                # Update the user's password and remove the reset_token and expiration_time fields
                collection.update_one({'reset_token': token},
                                      {'$set': {'password': hashed_password},
                                       '$unset': {'reset_token': '', 'expiration_time': ''}})

                # flash('Password reset successfully. Please login with your new password.')
                return redirect('/login')
            else:
                # flash('Password reset token has expired. Please request a new password reset.')
                return redirect('/forgot-password')
        else:
            # flash('Invalid password reset token. Please request a new password reset.')
            return redirect('/forgot-password')

    return render_template('reset_password.html', token=token)


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():

    if request.method == 'POST':
        email = request.form['email']

        # Verify if the email exists in your database
        user = collection.find_one({'email': email})
        if user:
            # Generate a password reset token
            token = generate_password_reset_token()

            # Set the expiration time for the token
            expiration_time = get_token_expiration_time()

            # Store the token and expiration time in the user's document
            collection.update_one({'email': email},
                                  {'$set': {'reset_token': token, 'expiration_time': expiration_time}})

            # Send password reset email
            send_password_reset_email(email, token)

            flash('An email with password reset instructions has been sent to your email address.')
            sleep(6)
            return render_template('login.html', error="An email with password reset instructions has been sent to your email address.")
    if request.method == 'GET':
        return render_template('forgot_password.html', error="")

    return render_template('forgot_password.html', error="Email not found")

   


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Retrieve the form data
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Create a new document to insert into the collection
        user = {
            'username': username,
            'password': hashed_password,
            'email': email
        }

        # Insert the document into the collection
        collection.insert_one(user)

        return redirect('/login')  # or render_template with success message

    return render_template('signup.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Retrieve the form data
        username = request.form['username']
        password = request.form['password']

        # Find the user in the collection
        user = collection.find_one({'username': username})

        if user:
            # Verify the password
            if bcrypt.checkpw(password.encode('utf-8'), user['password']):
                # Store user session
                session['username'] = user['username']
                run = False
                error = ""
                return render_template('index.html', run=run, error=error, max_size=True, scan=False)
        
        return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')



# Open WhatsApp
@app.route('/open-whatsapp', methods=['POST','GET'])
def open_whatsapp():
    if request.method == 'GET':
        flash("hey how are you?")
        return render_template('index.html', max_size=True)
    
    global driver
    chromedriver_autoinstaller.install()
    try:
        driver = webdriver.Chrome()
        driver.get("https://web.whatsapp.com/")
        # Wait until the QR code is visible
        wait = WebDriverWait(driver, 30)  # Maximum wait time of 30 seconds
        qr_code_element = wait.until(EC.visibility_of_element_located((By.XPATH, "//canvas[@aria-label='Scan me!']")))

        
        screenshot = driver.get_screenshot_as_png()

        # driver.maximize_window()
        # Wait for the QR code to be scanned
        screenshot_base64 = base64.b64encode(screenshot).decode('utf-8')

        return render_template('index.html',scan=False, run=True, max_size=True, screenshot_base64=screenshot_base64)
        
    except WebDriverException:
        driver.quit()
        return render_template('index.html')


# scaned QR code?
@app.route('/scan-qr', methods=['POST','GET'])
def scan_qr():
    if request.method == 'GET':
        return render_template('index.html', max_size=True)
    
    try:
        wait = WebDriverWait(driver, 60)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#side .copyable-text')))
        profile_picture = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="app"]/div/div/div[4]/header/div[1]/div')))
        profile_picture.click()
        owner_name_container = wait.until(EC.visibility_of_element_located((By.XPATH,'//*[@id="app"]/div/div/div[3]/div[1]/span/div/span/div/div/div[2]/div[2]/div/div/span/span')))

        # Extract the text of the owner's name
        global owner_name
        owner_name = owner_name_container.text
        
        back_button = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="app"]/div/div/div[3]/div[1]/span/div/span/div/header/div/div[1]/div')))
        back_button.click()
        
        return render_template('index.html', run=True, max_size=True, scan=True, name=owner_name, screenshot_base64="")
    except WebDriverException:
        driver.quit()
        return render_template('index.html', max_size=True, message="Oops! Something went wrong with Open WhatsApp. Please try again.")
    

# Send message
@app.route('/send-message', methods=['POST', 'GET'])
def send_message():
    if request.method == 'GET':
        return render_template('index.html', max_size=True)
    
    try:
        # Get form data
        contact_name = request.form['contact']
        message = request.form['message']
        image_file = request.files['image']
        image_path = ''
        print(contact_name)
        print(message)
        if image_file and allowed_file(image_file.filename):
            max_size = 16 * 1024 * 1024
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            if (os.path.getsize(image_path) > max_size):
                driver.quit()
                return render_template('index.html', run=False, max_size=False, filename=filename)
            
            sleep(2)
           
            print("Image saved:", image_path)
        else:
            print("Invalid file format")
            image_file = ''

        

        names = contact_name.split('\n')
        print(names)
        act = ActionChains(driver)
        wait = WebDriverWait(driver, 3)
        # Find user contact
        not_found_names = []
        for name in names:
            name = name.rstrip('\r')
            if len(name) == 0 or name == '\r' or name == '':
                names.remove(name)
                continue
            find_user = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="side"]/div[1]/div/div/div[2]/div/div[1]')))
            find_user.click()
            act.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
            find_user.send_keys(name)
            
            # sleep(2)
            
            find_chat = None
            try:
                find_chat = wait.until(EC.visibility_of_element_located((By.XPATH, '//span[@title = "{}"]'.format(name))))
            except TimeoutException:
                not_found_names.append(name)
                
        # contact names not exist in client phone
        if len(not_found_names) != 0:
            driver.quit()
            return render_template('index.html', run=False, max_size=True, error=not_found_names)
        
        message = pyperclip.copy(str(message))
        # all contacts valid, start sending
        for name in names:
            name = name.rstrip('\r')
            find_user = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="side"]/div[1]/div/div/div[2]/div/div[1]')))
            find_user.click()
            act.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
            find_user.send_keys(name)
            # sleep(2)
            find_chat = wait.until(EC.visibility_of_element_located((By.XPATH, '//span[@title = "{}"]'.format(name))))
            find_chat.click()
            sleep(2)

            wait_for_v = WebDriverWait(driver, 10)  # Maximum wait time in seconds
            # send only message
            if image_file == '':

                # copy paste the message to send
                act = ActionChains(driver)
                act.key_down(Keys.CONTROL).send_keys("v").key_up(Keys.CONTROL).perform()

                # send the message
                act.key_down(Keys.ENTER).perform()
                sleep(4)
                

            else:
                attachment_box = driver.find_element(By.XPATH, '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[1]/div[2]/div/div')
                attachment_box.click()

                image_box = driver.find_element(By.XPATH, '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]')
                image_box.send_keys(image_path)
                sleep(3)

                # copy paste the message to send
                act = ActionChains(driver)
                act.key_down(Keys.CONTROL).send_keys("v").key_up(Keys.CONTROL).perform()

                # send the message + image
                act.key_down(Keys.ENTER).perform()
                sleep(5)

            
        
        # Check if the file exists
        if os.path.exists(image_path):
            # Delete the file
            os.remove(image_path)


        driver.quit()
        return render_template('index.html', run=False, max_size=True, error='', sent=names)    

    except WebDriverException:
        driver.quit()
        return render_template('index.html', max_size=True, message="Oops! Something went wrong with Open WhatsApp. Please try again.")

    except Exception as e:
            print("Error:", e)


@app.route('/contact-us', methods=['POST', 'GET'])
def contact_us():
    if request.method == 'POST':
        user_email = request.form['email']
        user_message = request.form['message']

        excel_file_path = "/home/lior/computer_science/whatsapp_bot/WhatsApp-Bot-Site/contact_us.xlsx"
        # Create a DataFrame to hold the data
        data = {'Email': [user_email], 'Message': [user_message]}
        df = pd.DataFrame(data)

        # Check if the Excel file already exists
        try:
            # Load the existing file
            existing_data = pd.read_excel(excel_file_path)
            # Append the new data to the existing data
            updated_data = pd.concat([existing_data, df], ignore_index=True)
        except FileNotFoundError:
            # If the file doesn't exist, create a new DataFrame with the data
            updated_data = df

        # Write the DataFrame to the Excel file
        updated_data.to_excel(excel_file_path, index=False)

        return render_template("index.html", contact_us=True, max_size=True)
    
    return redirect('/')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# Home page
@app.route('/')
def home():
    run = False
    error = ""
    return render_template('index.html', run=run, error=error, max_size=True, scan=False)

    

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
