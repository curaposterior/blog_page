from datetime import datetime
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
import sqlalchemy

from app.forms import LoginForm, RegistrationForm, SendMailForm
from app import app, db
from app.models import User, Post
from sqlalchemy.exc import IntegrityError, DataError

import markdown

# ENDPOINTS aren't working yet
@app.route("/", methods=['GET','POST'])
@app.route("/home", methods=['GET','POST'])
def index():
    page = request.args.get('page', type=int)
    pagination = db.session.query(Post).paginate(page=page, per_page=10)
    posts = pagination.items
    return render_template("index.html", title='Home page', pagination=pagination, posts=posts)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            flash('Try different username')
            return redirect(url_for('register'))
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))



@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    return render_template('admin.html')


@app.route("/about", methods=['GET'])
def about():
    form = SendMailForm()
    if form.validate_on_submit():
        flash("Email sent")
        redirect(url_for('about'))
    return render_template("about.html", form=form)

@app.route("/post/<int:post_id>", methods=['GET'])
def post(post_id: int):
    if post_id is str or post_id is None:
        flash("Wrong post id")
        redirect(url_for('index'))
    
    try:
        post = db.session.query(Post).where(Post.id == post_id).first()
        if post is None:
            flash("Post doesn't exist")
            return redirect(url_for("index"))
        post.body = markdown.markdown(post.body)
    except IntegrityError or sqlalchemy.exc.DataError:
        flash("Post doesn't exist")
        return redirect(url_for("index"))
    
    
    return render_template("render_post.html", post=post)

@login_required
@app.route("/test", methods=['GET', 'POST'])
def test():
    return render_template('test_bootstrap.html')