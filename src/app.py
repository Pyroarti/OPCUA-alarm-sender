from flask import Flask, request, render_template, redirect, flash, url_for, session
import json
import os

from sms_sender import send_sms
from data_encrypt import DataEncryptor


app = Flask(__name__, template_folder='../templates', static_folder="../static")
app.secret_key = os.urandom(24)

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
config_dir = os.path.join(parent_dir, "configs")

phone_book_file = os.path.join(config_dir, 'phone_book.json')
flask_server_config_file = os.path.join(config_dir, 'flask_server_config.json')

data_encrypt = DataEncryptor()
flask_config = data_encrypt.encrypt_credentials('flask_login_config.json', "flask_key")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = flask_config['users']

        user = next((u for u in users if u['username'] == username and u['password'] == password), None)

        if user:
            session['logged_in'] = True
            session['username'] = username
            session['user_type'] = user['type']  # Storing user type
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
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
        total_time_settings = int(request.form['totalTimeSettings'])

        time_settings = []

        for index in range(1, total_time_settings + 1):
            day_field = f'days{index}[]'
            if day_field not in request.form:
                continue

            start_time_field = f'startTime{index}'
            end_time_field = f'endTime{index}'
            lowest_severity_field = f'lowestSeverity{index}'
            highest_severity_field = f'highestSeverity{index}'
            word_filter_field = f'WordFilter{index}'

            time_setting = {
                "days": request.form.getlist(day_field),
                "startTime": request.form[start_time_field],
                "endTime": request.form[end_time_field],
                "lowestSeverity": request.form[lowest_severity_field],
                "highestSeverity": request.form[highest_severity_field],
                "wordFilter": request.form[word_filter_field]
            }
            time_settings.append(time_setting)

        if not name or not phone_number or not time_settings:
            flash('Fyll i alla fält.')
            return redirect(url_for('create_user'))

        with open(phone_book_file, 'r+', encoding='UTF-8') as f:
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

            with open(phone_book_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

        flash('Mottagare tillagd.')
        return redirect(url_for('index'))

    with open(phone_book_file, 'r', encoding='UTF-8') as f:
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

            with open(phone_book_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            flash('Mottagare raderad.')
            return redirect(url_for('index'))

        if request.method == 'POST':
            new_time_settings = []
            index = 1
            while True:
                delete_key = f'deleteTimeSetting{index}'
                days_key = f'days{index}[]'

                if delete_key in request.form:
                    index += 1
                    continue

                if days_key in request.form:
                    time_setting = {
                        "days": request.form.getlist(days_key),
                        "startTime": request.form[f'startTime{index}'],
                        "endTime": request.form[f'endTime{index}'],
                        "lowestSeverity": request.form[f'lowestSeverity{index}'],
                        "highestSeverity": request.form[f'highestSeverity{index}'],
                        "wordFilter": request.form[f'WordFilter{index}']
                    }
                    new_time_settings.append(time_setting)
                else:
                    break
                index += 1

            new_name = request.form['name']
            new_phone_number = request.form['phone_number']
            new_active = 'Yes' if 'active' in request.form else 'No'

            user_to_edit['Name'] = new_name
            user_to_edit['phone_number'] = new_phone_number
            user_to_edit['Active'] = new_active
            user_to_edit['timeSettings'] = new_time_settings


            with open(phone_book_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)


            flash('Mottagaren har uppdaterats.')
            return redirect(url_for('index'))

        return render_template('edit_user.html', user=user_to_edit, user_id=id)


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

    send_sms(phone_number, 'Test SMS från Elmo pannrum.')
    flash('Test SMS skickat.')

    return redirect(url_for('index'))


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    print(session['user_type'])
    

    return redirect(url_for('settings'))
    


def main():
    with open (flask_server_config_file, 'r', encoding='utf8') as server_data:
        data = json.load(server_data)
        host = data['ip_adress']
        port = data['port']

    app.run(host=host, port=port, debug=False)
