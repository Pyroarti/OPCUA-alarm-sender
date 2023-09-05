from flask import Flask, request, render_template, redirect, flash, url_for
import json
import os

app = Flask(__name__, template_folder='../templates', static_folder="../static")
app.secret_key = "supersecretkey"


current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
config_dir = os.path.join(parent_dir, "configs")
phone_book_file = os.path.join(config_dir, 'phone_book.json')

@app.route("/", methods=["GET", "POST"])
def index():
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
        return redirect(url_for('index'))

    with open(phone_book_file, 'r', encoding='utf8') as f:
        users = json.load(f)

    return render_template('index.html', users=users)


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_user(id):
    action = request.args.get('action', '')  # Check for an 'action' query parameter

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


if __name__ == "__main__":
    app.run(debug=True)
