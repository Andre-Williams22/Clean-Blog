import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from flaskapp import app, db, bcrypt
from flaskapp.forms import RegistrationForm, LoginForm, QuizForm, UpdateAccountForm, PostForm 
from flaskapp.models import User, Posts, Mealplan, Meal
from flask_login import login_user, current_user, logout_user, login_required
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
import numpy as np 
import pandas as pd
import pickle
import csv

# loads decision tree model 
model = pickle.load(open('decisiontree2.pkl', 'rb'))
rfc = pickle.load(open('random_forest.pkl', 'rb'))

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    posts = Posts.query.order_by(Posts.date_posted.desc()).paginate(page=page, per_page=10)

    return render_template('home.html', posts=posts)

@app.route('/home')
def home():
    page = request.args.get('page', 1, type=int)
    posts = Posts.query.order_by(Posts.date_posted.desc()).paginate(page=page, per_page=10)

    return render_template('home.html', posts=posts)

@app.route("/about")
def about():
    return render_template('about.html', title='About')
@app.route("/contact")
def contact():
    return render_template('contact.html', title='Contact')

# registration 
@app.route("/registration", methods=['GET', 'POST'])
def registration():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('registration.html', title='Registration', form=form)

@app.route("/quiz", methods=['GET', 'POST'])
def quiz():
    form = QuizForm()
    if form.validate_on_submit():
        #label = LabelEncoder()
        # grab data from form
        age = float(request.form['age'])
        gender = request.form['gender']
        allergies = request.form['allergies']
        exercise = request.form['exercise']
        bp = request.form['high_bp']
        diabetes = request.form['diabetes']
        muscle = request.form['muscle_building']
        weight = request.form['weight_loss']
        hungry = request.form['hungry_often']
        eat_snacks = request.form['eat_snacks']
        # put values into a list 
        values = [eat_snacks,exercise, allergies,gender, bp, diabetes, muscle, weight, hungry]
        # new values converted to numbers for ml model 
        new_values = []
        # converts strings to numbers like label encoder 
        for item in values:
            if item == 'Male' or 'male':
                item = 1
                item = float(item)
                new_values.append(item)
            elif item == 'Female' or item == 'female':
                item = 0
                item = float(item)
                new_values.append(item)
            elif item == 'Yes' or item == 'yes':
                item = 1
                item = float(item)
                new_values.append(item)
            else:
                item = 0
                item = float(item)
                new_values.append(item)
        #print(new_values)
        
        # add age list 
        new_values.insert(0,age)
        # put values into an array
        pred_args = np.array(new_values)
        # reshape the array for model
        new_args = pred_args.reshape(1,-1)
        # final = [np.array(int_features)]
        #print(new_args)
        # make predictions on model
        prediction = rfc.predict(new_args)
        print(prediction)

        if prediction == 0:
            print('Male Maintain')
            # df = pd.read_csv(request.file.get('High-Cal.csv'))
            with open(os.path.join(os.path.dirname(__file__),'Maintain.csv')) as readfile:
                df = pd.read_csv(readfile)

                df = df.iloc[1:6]
                week = df['Maintain Calorie Plan'].iloc[0]
                breakfast = df['Unnamed: 1'].iloc[0]
                lunch = df['Unnamed: 2'].iloc[0]
                dinner = df['Unnamed: 3'].iloc[0]
                snack = df['Unnamed: 4'].iloc[0]
                calories = df['Unnamed: 5'].iloc[1]
                measurement = df['Unnamed: 6'].iloc[1]
                
                week_1 = Meal(week=week, breakfast=breakfast, lunch=lunch, dinner=dinner, snack=snack, total=calories, measurement=measurement, user_id=current_user.id)
                db.session.add(week_1)
                db.session.commit()
                flash(f"You're meal plan is ready {form.first.data} " + f"{form.last.data}! Please enjoy your meal plan", 'success')
                return redirect(url_for('mealplan'))     

        elif prediction == 1:
            print('Male Low Cal')
            with open(os.path.join(os.path.dirname(__file__),'Low-Cal.csv')) as readfile:
                data = pd.read_csv(readfile)
            # data = pd.read_csv('Low-Cal.csv')
            data = data.iloc[1:6]
            #data['Low Calorie Plan'].iloc[0]
            week = data['Low Calorie Plan'].iloc[0]
            breakfast = data['Breakfast'].iloc[0]
            lunch = data['Lunch'].iloc[0]
            dinner = data['Dinner'].iloc[0]
            snack = data['Snack'].iloc[0]
            total = data['Total'].iloc[1]
            week = data['Low Calorie Plan'].iloc[0]
            measurement = data['Measurement'].iloc[0]
            print(breakfast)
            print(lunch)

            week_1 = Meal(week=week, breakfast=breakfast, lunch=lunch, dinner=dinner, snack=snack, total=total, measurement=measurement, user_id=current_user.id)
            # save prediction in database 
            db.session.add(week_1)
            db.session.commit()
            flash(f"You're meal plan is ready {form.first.data} " + f"{form.last.data}! Please view your meal plan: " + f"{week_1}", 'success')
            return redirect(url_for('mealplan'))   

        elif prediction == 2:
            print('Male High Calorie')
            with open(os.path.join(os.path.dirname(__file__), 'High-Cal.csv')) as readfile:
                df = pd.read_csv(readfile)
            df = df.iloc[1:6]
            week = df['High Calorie Plan'].iloc[0]
            breakfast = df['Breakfast'].iloc[0]
            lunch = df['Lunch'].iloc[0]
            dinner = df['Dinner'].iloc[0]
            snack = df['Snack'].iloc[0]
            total = df['Total'].iloc[1]
            measurement = df['Measurement'].iloc[0]

            week_1 = Meal(week=week, breakfast=breakfast, lunch=lunch, dinner=dinner, snack=snack, total=total, measurement=measurement, user_id=current_user.id)
            # save prediction in database 
            db.session.add(week_1)
            db.session.commit()
            flash(f"You're meal plan is ready {form.first.data} " + f"{form.last.data}! Please view your meal plan: " + f"{week_1}", 'success')
            return redirect(url_for('mealplan'))   

        elif prediction == 3:
            print('Female Maintain')
            with open(os.path.join(os.path.dirname(__file__), 'F-Maintain.csv')) as readfile:
                df = pd.read_csv(readfile)
            df = df.iloc[1:6]
            week = df['Maintain Calorie Plan'].iloc[0]
            breakfast = df['Unnamed: 1'].iloc[0]
            lunch = df['Unnamed: 2'].iloc[0]
            dinner = df['Unnamed: 3'].iloc[0]
            snack = df['Unnamed: 4'].iloc[0]
            calories = df['Unnamed: 5'].iloc[1]
            measurement = df['Unnamed: 6'].iloc[1]

            week_1 = Meal(week=week, breakfast=breakfast, lunch=lunch, dinner=dinner, snack=snack, total=calories, measurement=measurement, user_id=current_user.id)
            # save prediction in database 
            db.session.add(week_1)
            db.session.commit()
            flash(f"You're meal plan is ready {form.first.data} " + f"{form.last.data}! Please view your meal plan: " + f"{week_1}", 'success')
            return redirect(url_for('mealplan')) 

        elif prediction == 4:
            print('Female Low Cal')
            with open(os.path.join(os.path.dirname(__file__), 'F-Low-Cal.csv')) as readfile:
                df = pd.read_csv(readfile)
            df = df.iloc[1:6]
            week = df['Low Calorie Plan'].iloc[0]
            breakfast = df['Breakfast'].iloc[0]
            lunch = df['Lunch'].iloc[0]
            dinner = df['Dinner'].iloc[0]
            snack = df['Snack'].iloc[0]
            total = df['Total'].iloc[1]
            measurement = df['Measurement'].iloc[0]

            week_1 = Meal(week=week, breakfast=breakfast, lunch=lunch, dinner=dinner, snack=snack, total=total, measurement=measurement, user_id=current_user.id)
            # save prediction in database 
            db.session.add(week_1)
            db.session.commit()
            flash(f"You're meal plan is ready {form.first.data} " + f"{form.last.data}! Please view your meal plan: " + f"{week_1}", 'success')
            return redirect(url_for('mealplan')) 

        else:
            print('Female High Cal')
            with open(os.path.join(os.path.dirname(__file__), 'F-High-Cal.csv')) as readfile:
                df = pd.read_csv(readfile)
            df = df.iloc[1:6]
            week = df['Maintain Calorie Plan'].iloc[0]
            breakfast = df['Breakfast'].iloc[0]
            lunch = df['Lunch'].iloc[0]
            dinner = df['Dinner'].iloc[0]
            snack = df['Snack'].iloc[0]
            total = df['Total'].iloc[1]
            measurement = df['Measurement'].iloc[0]
            
            week_1 = Meal(week=week, breakfast=breakfast, lunch=lunch, dinner=dinner, snack=snack, total=total, measurement=measurement, user_id=current_user.id)
            # save prediction in database 
            db.session.add(week_1)
            db.session.commit()
            flash(f"You're meal plan is ready {form.first.data} " + f"{form.last.data}! Please view your meal plan: " + f"{week_1}", 'success')
            return redirect(url_for('mealplan')) 
          
    return render_template('quiz.html', title='Quiz', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    quiz_data = QuizForm()
    if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('quiz')) # a ternary conditional like a list comprehension
            else:
                flash('Login Unsucessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form, quiz=quiz_data)
@app.route("/normlogin", methods=['GET', 'POST'])
def normlogin():
    if current_user.is_authenticated:
        return redirect(url_for('mealplan'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('normlogin.html', title='Login', form=form)

@app.route("/mealplan", methods=['GET', 'POST'])
@login_required
def mealplan():
    #form = Meal()
    #print(form)
    user = current_user
    print(user)
    meal = user.meal
    print(meal)
    #return redirect(url_for('account'))
    # breakfast = form.query.first()
    # breakfast = form.query.all()
    # form = form.query.first()
    # print(form)
        
    mp = Mealplan()
    b1 = mp.query.first()

    return render_template('mealplan.html', title='Mealplan', form=meal)

@app.route("/logout", methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('index'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    # returns filename with and without extension
    f_name, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext 
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    
    # resize the image
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)

    i.save(picture_path)

    return picture_fn

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    # meal = Meal()
    # meal = meal.query.all()
    account_form = UpdateAccountForm()
    if account_form.validate_on_submit():
        if account_form.picture.data:
            picture_file = save_picture(account_form.picture.data)
            current_user.image_file = picture_file 

        current_user.username = account_form.username.data 
        current_user.email = account_form.email.data
        db.session.commit()
        flash('your account has been updates!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        account_form.username.data = current_user.username
        account_form.email.data = current_user.email

    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)

    user = current_user 
    meal = user.meal[1]
    
    
    return render_template('account.html', title='Account', meal=meal, image_file=image_file, form=account_form)



@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Posts(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))

    
    return render_template('create_post.html', form=form, title='New Post', legend='New Post')


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Posts.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)

@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Posts.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content

    return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')

# route for deleting only if it's the user's post
@app.route("/post/<int:post_id>/delete", methods=['POST']) # only accept when they submit the modal
@login_required
def delete_post(post_id):
    post = Posts.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    # deletes post from database 
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))

@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    # this says to get the first user with this username 
    user = User.query.filter_by(username=username).first_or_404()
    posts = Posts.query.filter_by(author=user)\
        .order_by(Posts.date_posted.desc())\
        .paginate(page=page, per_page=10)

    return render_template('user_posts.html', posts=posts, user=user)