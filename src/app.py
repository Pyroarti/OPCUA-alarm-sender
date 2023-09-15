from flask import Flask, request, render_template, redirect, flash, url_for, session
import json
import os
import re

from sms_sender import send_sms
from data_encrypt import DataEncrypt


app = Flask(__name__, template_folder='../templates', static_folder="../static")
app.secret_key = os.urandom(24)

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
config_dir = os.path.join(parent_dir, "configs")

phone_book_file = os.path.join(config_dir, 'phone_book.json')
flask_server_config_file = os.path.join(config_dir, 'flask_server_config.json')

data_encrypt = DataEncrypt()
flask_config = data_encrypt.encrypt_credentials('flask_login_config.json', "flask_key")


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Login page.
    Username and password are stored crypted in a JSON file.
    Not the best security, but good enough for this project.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        encrypted_username = flask_config["username"]
        encrypted_password = flask_config["password"]

        if username == encrypted_username and password == encrypted_password:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash('Fel inloggnings information!')
    return render_template("login.html")


@app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect(url_for('index'))

@app.route("/")
def index():
    """
    Index page.
    """
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    with open(phone_book_file, 'r', encoding='utf8') as f:
        users = json.load(f)

    return render_template('index.html', users=users)


@app.route("/create_user", methods=["GET", "POST"])
def create_user():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        phone_number = request.form['phone_number']

        time_settings = [
            {
                "days": request.form.getlist('days1'),
                "startTime": request.form['startTime1'],
                "endTime": request.form['endTime1'],
                "lowestSeverity": request.form['lowestSeverity1'],
                "highestSeverity": request.form['highestSeverity1']
            },
            {
                "days": request.form.getlist('days2'),
                "startTime": request.form['startTime2'],
                "endTime": request.form['endTime2'],
                "lowestSeverity": request.form['lowestSeverity2'],
                "highestSeverity": request.form['highestSeverity2']
            }
            ]

        if not name or not phone_number or not time_settings:
            flash('Fyll i alla fält.')
            return redirect(url_for('create_user'))

        with open(phone_book_file, 'r+', encoding='utf8') as f:
            data = json.load(f)
            for user in data:
                if user['phone_number'] == phone_number:
                    flash('Det här nummret används redan')
                    return redirect(url_for('create_user'))

            data.append({
            'Name': name,
            'phone_number': phone_number,
            'Active': 'Yes',
            'timeSettings': time_settings
            })


            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

        flash('Mottagare tillagd.')
        return redirect(url_for('index'))

    with open(phone_book_file, 'r', encoding='utf8') as f:
        users = json.load(f)

    return render_template('create_user.html', users=users)


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_user(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    action = request.args.get('action', '')

    with open(phone_book_file, 'r+', encoding='utf8') as f:
        data = json.load(f)

        if id < 0 or id >= len(data):
            flash('Invalid user ID.')
            return redirect(url_for('index'))

        user_to_edit = data[id]

        if action == 'delete':
            del data[id]

            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

            flash('Mottagare raderad.')
            return redirect(url_for('index'))

        if request.method == 'POST':
            time_settings = [
            {
                "days": request.form.getlist('days1'),
                "startTime": request.form['startTime1'],
                "endTime": request.form['endTime1'],
                "lowestSeverity": request.form['lowestSeverity1'],
                "highestSeverity": request.form['highestSeverity1']
            },
            {
                "days": request.form.getlist('days2'),
                "startTime": request.form['startTime2'],
                "endTime": request.form['endTime2'],
                "lowestSeverity": request.form['lowestSeverity2'],
                "highestSeverity": request.form['highestSeverity2']
            }
            ]
            new_name = request.form['name']
            new_phone_number = request.form['phone_number']
            new_active = 'Yes' if 'active' in request.form else 'No'
            new_time_settings = time_settings


            user_to_edit['Name'] = new_name
            user_to_edit['phone_number'] = new_phone_number
            user_to_edit['Active'] = new_active
            user_to_edit['timeSettings'] = new_time_settings


            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

            flash('Mottagaren har uppdaterats.')
            return redirect(url_for('index'))

        return render_template('edit_user.html', user=user_to_edit, id=id)


@app.route("/test_sms/<int:id>", methods=["GET"])
def test_sms(id):
    """
    Send a test SMS to the user with the given ID.
    :param id: User ID
    """

    if not session.get('logged_in'):
        return redirect(url_for('login'))

    with open(phone_book_file, 'r', encoding='utf8') as f:
        data = json.load(f)

    if id < 0 or id >= len(data):
        flash('Invalid user ID.')
        return redirect(url_for('index'))

    user = data[id]
    phone_number = user['phone_number']

    send_sms(phone_number, 'Test SMS från Elmo pumpstation.')
    flash('Test SMS skickat.')

    return redirect(url_for('index'))

def main():
    with open (flask_server_config_file, 'r', encoding='utf8') as server_data:
        data = json.load(server_data)
        host = data['ip_adress']
        port = data['port']

    app.run(host=host, port=port, debug=True)
