from flask import Flask, render_template, request, redirect, session
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


app = Flask(__name__)
app.secret_key = "Lior_secret_12344321"

client = MongoClient('mongodb://127.0.0.1:27017')  # Replace with your MongoDB connection string
db = client['myDB']  # Replace with your database name
collection = db['users']  # Replace with your collection name



# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Retrieve the form data
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

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
                return redirect('/')
        
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
        return redirect('/')
    
    global driver
    chromedriver_autoinstaller.install()
    try:
        driver = webdriver.Chrome()
        driver.get("https://web.whatsapp.com/")
        driver.maximize_window()

        # Wait for the QR code to be scanned
        wait = WebDriverWait(driver, 60)  # Adjust the timeout as needed
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#side .copyable-text')))

        return render_template('index_register.html', run=True)
    except WebDriverException:
        driver.quit()
        return redirect('/')

# Send message
@app.route('/send-message', methods=['POST', 'GET'])
def send_message():
    if request.method == 'GET':
        return redirect('/')
    
    try:
        # Get form data
        contact_name = request.form['contact']
        message = request.form['message']
        message = pyperclip.copy(str(message))

        names = contact_name.split('\n')
        act = ActionChains(driver)
        wait = WebDriverWait(driver, 3)
        # Find user contact
        not_found_names = []
        for name in names:
            name = name.rstrip('\r')
            find_user = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="side"]/div[1]/div/div/div[2]/div/div[1]')))
            find_user.click()
            act.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
            find_user.send_keys(name)
            
            sleep(2)
            
            find_chat = None
            try:
                find_chat = wait.until(EC.visibility_of_element_located((By.XPATH, '//span[@title = "{}"]'.format(name))))
            except TimeoutException:
                not_found_names.append(name)
                
        if len(not_found_names) != 0:
            driver.quit()
            return render_template('index_register.html', run=False, error=not_found_names)
        

        # all contacts valid
        for name in names:
            name = name.rstrip('\r')
            find_user = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="side"]/div[1]/div/div/div[2]/div/div[1]')))
            find_user.click()
            act.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
            find_user.send_keys(name)
            sleep(2)
            find_chat = wait.until(EC.visibility_of_element_located((By.XPATH, '//span[@title = "{}"]'.format(name))))
            find_chat.click()

            # Write and send message
            msg_box = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[1]')))

            act.key_down(Keys.CONTROL).send_keys("v").key_up(Keys.CONTROL).perform()

            msg_box.send_keys(Keys.ENTER)
            sleep(2)        
            
        driver.quit()
    except WebDriverException:
        driver.quit()
        return render_template('index_register.html', run=False, error=f"{contact_name} not found in your contacts")



    return redirect('/')





# Home page
@app.route('/')

def home():
    run = False
    error = ""
    return render_template('index_register.html', run=run, error=error)

    

if __name__ == '__main__':
    app.run()
