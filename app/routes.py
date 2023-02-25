from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, send_file
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
import sqlalchemy

from app.forms import LoginForm, RegistrationForm, SendMailForm, CreatePost, EditPost
from app import app, db
from app.models import User, Post
from sqlalchemy.exc import IntegrityError, DataError

import markdown
from markdown.extensions import fenced_code, codehilite
from io import BytesIO

@app.route("/", methods=['GET','POST'])
@app.route("/home", methods=['GET','POST'])
def index():
    page = request.args.get('page', type=int)
    pagination = db.session.query(Post).order_by(Post.timestamp.desc()).paginate(page=page, per_page=10)
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


@app.route("/contact", methods=['GET','POST'])
def contact():
    form = SendMailForm()
    if form.validate_on_submit():
        flash("Email sent")
        redirect(url_for('about'))
    return render_template('contact.html', form=form)


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
    return render_template('admin_panel.html')


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
        
        post.body = markdown.markdown(post.body, extensions=["fenced_code", "codehilite"])

    except IntegrityError or sqlalchemy.exc.DataError:
        flash("Post doesn't exist")
        return redirect(url_for("index"))
    
    return render_template("render_post.html", post=post)


@login_required
@app.route("/create", methods=['GET', 'POST'])
def create():
    form = CreatePost()
    if form.validate_on_submit():
        post = Post(title=form.title.data,
                    description=form.description.data,
                    body=form.body.data,
                    img=form.img.data.read())
        try:
            db.session.add(post)
            db.session.commit()
            flash('Post added successfully')
            return redirect(url_for('create'))
        except IntegrityError or sqlalchemy.exc.DataError:
            flash('Something went wrong, try again.')
    return render_template("create.html", form=form)


@login_required
@app.route("/<int:post_id>/edit", methods=['GET', 'POST'])
def edit(post_id: int):
    try:
        post = db.session.query(Post).where(Post.id == post_id).first()
    except IntegrityError or sqlalchemy.exc.DataError:
        flash("Post doesn't exist. Try again.")
        return redirect(url_for('admin'))

    form = EditPost(obj=post)

    if form.validate_on_submit():
        form.populate_obj(obj=post)
        db.session.commit()
        flash("Post edited successfully")
        return redirect(url_for('post', post_id=post_id))
    return render_template('edit.html', title="Edit post", form=form, id=post_id)


@login_required
@app.route("/admin/edit", methods=['GET', 'POST'])
def list_editable_posts():
    page = request.args.get('page', type=int)
    pagination = db.session.query(Post).order_by(Post.timestamp.desc()).paginate(page=page, per_page=10)
    posts = pagination.items
    return render_template('post_list_to_edit.html', pagination=pagination, posts=posts)


# @app.route("/robots.txt", methods=['GET'])
# def robots():
#     return render_template('robots.txt')


@app.route("/images/<int:post_id>.jpg", methods=['GET'])
def get_image(post_id: int):
    post = db.session.query(Post).where(Post.id == post_id).first()
    if post is None:
        flash("Photo doesn't exist")
        return redirect(url_for("create"))
    return send_file(BytesIO(post.img), mimetype='image/jpg')
