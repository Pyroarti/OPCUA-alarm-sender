from flask import Flask, request, render_template, redirect, flash, url_for, session
import json
import os

app = Flask(__name__, template_folder='../templates', static_folder="../static")
secret_key = os.urandom(24)

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
config_dir = os.path.join(parent_dir, "configs")
phone_book_file = os.path.join(config_dir, 'phone_book.json')
flask_login_config_file = os.path.join(config_dir, 'flask_login_config.json')
flask_server_config_file = os.path.join(config_dir, 'flask_server_config.json')


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with open (flask_login_config_file, 'r', encoding='utf8') as f:
            data = json.load(f)
            if username == data['username'] and password == data['password']:
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


@app.route("/", methods=["GET", "POST"])
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        phone_number = request.form['phone_number']

        if not name or not phone_number:
            flash('Please fill out all the fields.')
            return redirect(url_for('index'))

        with open(phone_book_file, 'r+', encoding='utf8') as f:
            data = json.load(f)
            for user in data:
                if user['phone_number'] == phone_number:
                    flash('Det här nummret används redan')
                    return redirect(url_for('index'))

            data.append({
                'Name': name,
                'phone_number': phone_number,
                'Active': 'Yes'
            })

            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

        flash('Mottagare tillagd.')

    with open(phone_book_file, 'r', encoding='utf8') as f:
        users = json.load(f)

    return render_template('index.html', users=users)


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
            del data[id]  # Delete the user from the list

            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

            flash('Mottagare raderad.')
            return redirect(url_for('index'))

        if request.method == 'POST':
            new_name = request.form['name']
            new_phone_number = request.form['phone_number']
            new_active = 'Yes' if 'active' in request.form else 'No'

            user_to_edit['Name'] = new_name
            user_to_edit['phone_number'] = new_phone_number
            user_to_edit['Active'] = new_active

            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

            flash('Mottagaren har uppdaterats.')
            return redirect(url_for('index'))

        return render_template('edit_user.html', user=user_to_edit, id=id)


def main():
    with open (flask_server_config_file, 'r', encoding='utf8') as server_data:
        data = json.load(server_data)
        host = data['ip_adress']
        port = data['port']

    app.run(host=host, port=port, debug=False)
