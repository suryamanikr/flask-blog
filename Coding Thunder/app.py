from flask import Flask, render_template, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import json, os
from werkzeug.utils import redirect
from markupsafe import escape

# from flask_mail import Mail

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True


app = Flask(__name__)
app.secret_key = "SECRETKEY"
app.config['UPLOAD_FOLDER'] = params['upload_folder']
# app.config.update(
#     MAIL_SERVER = 'smtp.gmail.com',
#     MAIL_PORT = '465',
#     MAIL_USE_SSL = True,
#     MAIL_USERNAME = params['gmail-user'],
#     MAIL_PASSWORD=  params['gmail-password']
# )
# mail = Mail(app)

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/codingthunder'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.Text(), nullable=False)
    date = db.Column(db.String(), nullable=True)
    email = db.Column(db.String(50), nullable=False)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    content = db.Column(db.Text(), nullable=False)
    date = db.Column(db.String(), nullable=True)
    img_file = db.Column(db.String(10), nullable=True)


# db.create_all()
# db.session.commit()


@app.route("/")
@app.route('/home')
def home():
    # Pagination Logic
    posts = Posts.query.filter_by().all()[0:params["no_of_posts_on_homepage"]]
    return render_template('index.html', params=params, posts=posts)


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin_username']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)

    if request.method == "POST":
        login_error=""
        username = request.form.get('username')
        password = request.form.get('password')
        if (username == params['admin_username'] and password == params['admin_password']):
            # set the session
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts=posts)
        else:
            flash("Invalid Username or Password", "login-error")
            return render_template("login.html", params=params)

    return render_template("login.html", params=params)


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route('/delete/<string:sno>', methods=['GET', 'POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_username']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()

    return redirect("/dashboard")


@app.route('/edit/<string:sno>', methods=['GET', 'POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_username']):
        if request.method == "POST":
            box_title = request.form.get('title')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if sno == '0':
                new_post = Posts(title=box_title, slug=slug,
                                 content=content, img_file=img_file, date=date)
                db.session.add(new_post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.add(post)
                db.session.commit()
                return redirect('/edit/'+sno)

        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, post=post, sno=sno)


@app.route('/uploadfile', methods=['POST'])
def upload_file():
    if ('user' in session and session['user'] == params['admin_username']):
        if request.method == 'POST':
            f = request.files['file']
            f.save(os.path.join(
                app.config['UPLOAD_FOLDER'] + secure_filename(f.filename)))
            return redirect('/dashboard')


@ app.route('/about')
def about():
    return render_template('about.html', params=params)


@ app.route("/post/<string:post_slug>/", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    # fname = "assets/img" + post.img_file
    post_content=escape(post.content)
    return render_template('post.html', params=params, post=post, post_content=post_content )


@ app.route("/contact", methods=['GET', 'POST'])
def contact():
    if(request.method == 'POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone_num = request.form.get('phone_num')
        msg = request.form.get('msg')
        entry = Contacts(name=name, email=email, phone_num=phone_num,
                         msg=msg, date=datetime.now(),)
        db.session.add(entry)
        db.session.commit()
        # mail.send_message('New message from ' + name,
        #                   sender=email,
        #                   recipients = [params['gmail-user']],
        #                   body = message + "\n" + phone
        #                   )

    return render_template('contact.html', params=params)


@app.route('/messages')
def messages():
    if ('user' in session and session['user'] == params["admin_username"]):
        contacts = Contacts.query.all()
        return render_template("messages.html", contacts=contacts, params=params)

# @app.errorhandler(404)
# def errorhandle(error):
#     return render_template('error.html', params=params, error=404), 404


# @app.errorhandler(405)
# def errorhandle(error):
#     return render_template('error.html', params=params, error=405), 405


if __name__ == '__main__':
    app.run(debug=True)
