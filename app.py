from flask import Flask, render_template, request, redirect, session, send_file
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




application = Flask(__name__)
application.secret_key = "Lior_secret_12344321"

client = MongoClient('mongodb://127.0.0.1:27017')  # Replace with your MongoDB connection string
db = client['myDB']  # Replace with your database name
collection = db['users']  # Replace with your collection name

application.config['UPLOAD_FOLDER'] = '/home/lior/computer_science/whatsapp_bot/WhatsApp-Bot-Site/temp'
application.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'webm', 'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'mpeg'}


# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


@application.route('/signup', methods=['GET', 'POST'])
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



@application.route('/login', methods=['GET', 'POST'])
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
                return render_template('index.html', run=run, error=error)
        
        return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')


@application.route('/logout')
def logout():
    session.clear()
    return redirect('/')



# Open WhatsApp
@application.route('/open-whatsapp', methods=['POST','GET'])
def open_whatsapp():
    if request.method == 'GET':
        return render_template('index.html')
    
    global driver
    chromedriver_autoinstaller.install()
    try:
        driver = webdriver.Chrome()
        driver.get("https://web.whatsapp.com/")
        sleep(3)
        screenshot = driver.get_screenshot_as_png()
        
        # driver.maximize_window()
        # Wait for the QR code to be scanned
        screenshot_base64 = base64.b64encode(screenshot).decode('utf-8')

        return render_template('index.html', run=True,  screenshot_base64=screenshot_base64)
        

        
    except WebDriverException:
        driver.quit()
        return render_template('index.html')

# Send message
@application.route('/send-message', methods=['POST', 'GET'])
def send_message():
    if request.method == 'GET':
        return render_template('index.html')
    
    try:
        wait = WebDriverWait(driver, 60)  # Adjust the timeout as needed
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#side .copyable-text')))
        print("lior")
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
            image_path = os.path.join(application.config['UPLOAD_FOLDER'], filename)
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
            return render_template('index.html', run=False, error=not_found_names)
        
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

           
            # send only message
            if image_file == '':

                # copy paste the message to send
                act = ActionChains(driver)
                act.key_down(Keys.CONTROL).send_keys("v").key_up(Keys.CONTROL).perform()

                # send the message
                act.key_down(Keys.ENTER).perform()
                sleep(3)
                

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
                sleep(4)

            
        
        # Check if the file exists
        if os.path.exists(image_path):
            # Delete the file
            os.remove(image_path)


        driver.quit()
        return render_template('index.html', run=False, error='', sent=names)    

    except WebDriverException:
        driver.quit()
        return render_template('index.html', max_size=False, message="Scan QR code before sending the message.")

    except Exception as e:
            print("Error:", e)
            


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in application.config['ALLOWED_EXTENSIONS']


# Home page
@application.route('/')
def home():
    run = False
    error = ""
    return render_template('index.html', run=run, error=error, max_size=True)

    

if __name__ == '__main__':
    application.run(host='0.0.0.0', debug=False)
