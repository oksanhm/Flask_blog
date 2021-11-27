from datetime import datetime
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, \
    EmptyForm, PostForm, EditPostForm, EditCommentForm, Contact
from app.models import User, Post
from app.forms import AddCommentForm, Search_user_Form
from app.models import Comment
from flask import g
from app.forms import SearchForm
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required
from app import db
from app.forms import EditProfileForm, EmptyForm, PostForm, SearchForm
from app.models import User, Post


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()
    #g.locale = str(get_locale())


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Home', form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Explore', posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/post/<id>', methods=['GET', 'POST'])
def post(id):
    page = request.args.get('page', 1, type=int)
    form = AddCommentForm()
    post = Post.query.filter_by(id=id).first_or_404()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, author=current_user, article=post)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment is now live!')
        return redirect(url_for('post', id=id))
    comments = post.comments.order_by(Comment.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('post', id=id, page=comments.next_num) \
        if comments.has_next else None
    prev_url = url_for('post', id=id, page=comments.prev_num) \
        if comments.has_prev else None
    return render_template('post.html', post=post, comments=comments.items, form=form,
                           next_url=next_url, prev_url=prev_url)


@app.route('/login', methods=['GET', 'POST'])
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


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@app.route('/edit_post/<id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Post.query.filter_by(id=id).first_or_404()
    if not post.author == current_user:
        return render_template('404.html')
    form = EditPostForm(current_user.username)
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_post', id=id))
    elif request.method == 'GET':
        form.body.data = post.body
    return render_template('edit_post.html',
                           form=form)


@app.route('/edit_comment/<id>', methods=['GET', 'POST'])
@login_required
def edit_comment(id):
    comment = Comment.query.filter_by(id=id).first_or_404()
    if not comment.author == current_user:
        return render_template('404.html')
    form = EditCommentForm(current_user.username)
    if form.validate_on_submit():
        comment.body = form.body.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_comment', id=id))
    elif request.method == 'GET':
        form.body.data = comment.body
    return render_template('edit_comment.html',
                           form=form)


@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


from app.forms import ResetPasswordRequestForm
from app.email import send_password_reset_email
from app.email import send_email_2


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = Contact()
    if form.validate_on_submit():
        text = form.body.data
        send_email_2(text)
        flash('Your message has been sent')
        return redirect(url_for('contact'))
    return render_template('contacts.html', form=form)


from app.forms import ResetPasswordForm


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/following/<username>')
def following(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first()
    users = user.followed.paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('following', users=users, page=users.next_num) \
        if users.has_next else None
    prev_url = url_for('following', users=users, page=users.prev_num) \
        if users.has_prev else None
    return render_template('following.html', users=users.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/followers/<username>')
def followers(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first()
    users = user.followers.paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('followers', users=users, page=posts.next_num) \
        if users.has_next else None
    prev_url = url_for('followers', users=users, page=posts.prev_num) \
        if users.has_prev else None
    return render_template('followers.html', users=users.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('search', q=g.search_form.q.data, page=page + 1) \
        if total['value'] > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title='Search', posts=posts,
                           next_url=next_url, prev_url=prev_url)


@app.route('/search_user', methods=['GET', 'POST'])
def search_user():
    m=1
    page = request.args.get('page', 1, type=int)
    form = Search_user_Form()
    if form.validate_on_submit():
        username = form.q.data
        flash('Your results')
        return redirect(url_for('user_results', username=username))
    users = User.query.paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('following', users=users, page=users.next_num) \
        if users.has_next else None
    prev_url = url_for('following', users=users, page=users.prev_num) \
        if users.has_prev else None
    return render_template('search_user.html', users=users.items, m=m, form = form,
                           next_url=next_url, prev_url=prev_url)


@app.route('/user_results/<username>', methods=['GET', 'POST'])
def user_results(username):
    m=0
    form = Search_user_Form()
    if form.validate_on_submit():
        username = form.q.data
        flash('Your results')
        return redirect(url_for('user_results', username=username))
    users = User.query.filter_by(username=username)
    return render_template('search_user.html', users=users, m=m, form = form)


@app.route("/post_delete/<id>", methods=['GET'])
@login_required
def post_delete(id):
    post = Post.query.filter_by(id=id, user_id=current_user.id).first()
    comment = post.comments
    if not post.author == current_user:
        return render_template('404.html')
    for i in comment:
        db.session.delete(i)
    db.session.delete(post)
    db.session.commit()
    flash("Post is deleted", 'success')
    return redirect(url_for('explore'))


@app.route("/comment_delete/<id>", methods=['GET'])
@login_required
def comment_delete(id):
    comment = Comment.query.filter_by(id=id, user_id=current_user.id).first()
    i=comment.post_id
    if not comment.author == current_user:
        return render_template('404.html')
    db.session.delete(comment)
    db.session.commit()
    flash("Comment is deleted", 'success')
    return redirect(url_for('post', id=i))
