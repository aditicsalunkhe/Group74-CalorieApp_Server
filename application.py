from datetime import datetime

import bcrypt
import smtplib
import uuid
import apps

# from apps import App
from flask import json
# from utilities import Utilities
from flask import render_template, session, url_for, flash, redirect, request, Flask
from flask_mail import Mail, Message
from flask_pymongo import PyMongo
from tabulate import tabulate
from forms import HistoryForm, RegistrationForm, LoginForm, CalorieForm, UserProfileForm, EnrollForm, ForgotForm, ResetPasswordForm

a = apps.App()
mongo = a.mongo

@a.app.route("/")
@a.app.route("/home")
def home():
    """
    home() function displays the homepage of our website.
    route "/home" will redirect to home() function.
    input: The function takes session as the input
    Output: Out function will redirect to the login page
    """
    if session.get('email'):
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))


@a.app.route("/login", methods=['GET', 'POST'])
def login():
    """"
    login() function displays the Login form (login.html) template
    route "/login" will redirect to login() function.
    LoginForm() called and if the form is submitted then various values are fetched and verified from the database entries
    Input: Email, Password, Login Type
    Output: Account Authentication and redirecting to Dashboard
    """
    
    form = LoginForm()
    if form.validate_on_submit():
        temp = mongo.db.user.find_one({'email': form.email.data}, {
            'email', 'pwd', 'name'})
        if temp is not None and temp['email'] == form.email.data and (
            bcrypt.checkpw(
                form.password.data.encode("utf-8"),
                temp['pwd'])):
            flash('You have been logged in!', 'success')
            session['email'] = temp['email']
            session['username'] = temp['name']
            #session['login_type'] = form.type.data
            return redirect(url_for('dashboard'))
        else:
            session.clear()
            flash(
                'Login Unsuccessful. Please check username and password',
                'danger')
            return redirect(url_for('login'))

    return render_template(
        'login.html',
        title='Login',
        form=form)


@a.app.route("/logout", methods=['GET', 'POST'])
def logout():
    """
    logout() function just clears out the session and returns success
    route "/logout" will redirect to logout() function.
    Output: session clear
    """
    session.clear()
    return "success"


@a.app.route("/register", methods=['GET', 'POST'])
def register():
    """
    register() function displays the Registration portal (register.html) template
    route "/register" will redirect to register() function.
    RegistrationForm() called and if the form is submitted then various values are fetched and updated into database
    Input: Username, Email, Password, Confirm Password
    Output: Value update in database and redirected to home login page
    """
    if not session.get('email'):
        form = RegistrationForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                username = request.form.get('username')
                email = request.form.get('email')
                password = request.form.get('password')
                mongo.db.user.insert({'name': username, 'email': email, 'pwd': bcrypt.hashpw(
                    password.encode("utf-8"), bcrypt.gensalt())})
            flash(f'Account created for {form.username.data}!', 'success')
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)


@a.app.route("/calories", methods=['GET', 'POST'])
def calories():
    """
    calorie() function displays the Calorieform (calories.html) template
    route "/calories" will redirect to calories() function.
    CalorieForm() called and if the form is submitted then various values are fetched and updated into the database entries
    Input: Email, date, food, burnout
    Output: Value update in database and redirected to home page
    """
    now = datetime.now()
    now = now.strftime('%Y-%m-%d')
    get_session = session.get('email')
    if get_session is not None:
        form = CalorieForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                selected_date = request.form.get('date')
                if selected_date <= now:
                    email = session.get('email')
                    food = request.form.get('food')

                    cals = food.split(" ")
                    cals = int(cals[-1][1:(len(cals[-1]) - 1)])
                    burn = request.form.get('burnout')

                    temp = mongo.db.calories.find_one({'email': email, 'date': selected_date}, {
                        'email', 'calories', 'burnout'})
                    if temp is not None:
                        mongo.db.calories.update({'email': email}, {'$set': {
                                                'calories': temp['calories'] + cals, 'burnout': temp['burnout'] + int(burn)}})
                    else:
                        mongo.db.calories.insert_one(
                            {'date': selected_date, 'email': email, 'calories': cals, 'burnout': int(burn)})
                    flash(f'Successfully updated the data', 'success')
                    return redirect(url_for('calories'))
                else:
                    flash(f'Select a current date or date in the past', 'warning')
    else:
        return redirect(url_for('home'))
    return render_template('calories.html', form=form, time=now)

@a.app.route("/my_enrolled_workouts", methods=['GET', 'POST'])
def my_enrolled_workouts():
    email = session.get('email')
    try:
        workout_data = list(mongo.db.enrolled_workout.find({"Email" : email}, {"_id",'Email','Status'}))
        if workout_data is None:
            raise Exception("No data found for the given email")
        workout_data = list(workout_data)
    except Exception as e:
        return render_template('error.html', error_message=str(e))
    return render_template('enrolled_workouts.html', data=workout_data)


@a.app.route('/remove_status', methods=['POST'])
def remove_status():

    #Extract values from the form in the html
    status_id = request.form.get('status_id')
    email = request.form.get('email')
    status = request.form.get('status')
   
    mongo.db.enrolled_workout.delete_one({'Email': email, 'Status': status})
    return redirect(url_for('my_enrolled_workouts'))  # Redirect back to the data display page


@a.app.route("/profile", methods=['GET', 'POST'])
def profile():
    email = session.get('email')

    if email is not None:
        myProfile = mongo.db.profile.find_one({'email': email}, {'email', 'height', 'weight', 'target_weight', 'goal'})
        weight = myProfile['weight']
        height = myProfile['height']
        target_weight = myProfile['target_weight']
        goal = myProfile['goal']
        return render_template('display_profile.html', weight=weight, height=height, goal=goal, target_weight=target_weight)

    return redirect(url_for('login'))


@a.app.route("/edit_profile", methods=['GET', 'POST'])
def edit_profile():
    """
    edit_profile() function displays the UserProfileForm (user_profile.html) template
    route "/edit_profile" will redirect to edit_profile() function.
    edit_profile() called and if the form is submitted then various values are fetched and updated into the database entries
    Input: Email, height, weight, goal, Target weight
    Output: Value update in database and redirected to home login page
    """
    if session.get('email'):
        form = UserProfileForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                email = session.get('email')
                weight = request.form.get('weight')
                height = request.form.get('height')
                goal = request.form.get('goal')
                target_weight = request.form.get('target_weight')
                temp = mongo.db.profile.find_one({'email': email}, {'email', 'weight', 'height', 'target_weight', 'goal'})
                if temp is not None:
                    mongo.db.profile.update_one({'email': email},
                                            {'$set': {'weight': weight,
                                                      'height': height,
                                                      'goal': goal,
                                                      'target_weight': target_weight}})
                    print(mongo.db.profile.find_one({'email': email}, {'email', 'weight', 'height', 'target_weight', 'goal'}))
                else:
                    mongo.db.profile.insert_one({'email': email,
                                             'height': height,
                                             'weight': weight,
                                             'goal': goal,
                                             'target_weight': target_weight})
                flash(f'User Profile Updated', 'success')
            return render_template('display_profile.html', status=True, form=form, height=height, weight=weight, target_weight=target_weight)
    else:
        return redirect(url_for('login'))
    return render_template('user_profile.html', status=True, form=form)


@a.app.route("/history", methods=['GET'])
def history():
    # ############################
    # history() function displays the Historyform (history.html) template
    # route "/history" will redirect to history() function.
    # HistoryForm() called and if the form is submitted then various values are fetched and update into the database entries
    # Input: Email, date
    # Output: Value fetched and displayed
    # ##########################
    email = get_session = session.get('email')
    if get_session is not None:
        form = HistoryForm()
    else:
        return redirect(url_for('login'))
    return render_template('history.html', form=form)


@a.app.route("/ajaxhistory", methods=['POST'])
def ajaxhistory():
    # ############################
    # ajaxhistory() is a POST function displays the fetches the various information from database
    # route "/ajaxhistory" will redirect to ajaxhistory() function.
    # Details corresponding to given email address are fetched from the database entries
    # Input: Email, date
    # Output: date, email, calories, burnout
    # ##########################
    email = get_session = session.get('email')
    print(email)
    if get_session is not None:
        if request.method == "POST":
            date = request.form.get('date')
            res = mongo.db.calories.find_one({'email': email, 'date': date}, {
                                             'date', 'email', 'calories', 'burnout'})
            if res:
                return json.dumps({'date': res['date'], 'email': res['email'], 'burnout': res['burnout'], 'calories': res['calories']}), 200, {
                    'ContentType': 'application/json'}
            else:
                return json.dumps({'date': "", 'email': "", 'burnout': "", 'calories': ""}), 200, {
                    'ContentType': 'application/json'}


@a.app.route("/friends", methods=['GET'])
def friends():
    # ############################
    # friends() function displays the list of friends corrsponding to given email
    # route "/friends" will redirect to friends() function which redirects to friends.html page.
    # friends() function will show a list of "My friends", "Add Friends" functionality, "send Request" and Pending Approvals" functionality
    # Details corresponding to given email address are fetched from the database entries
    # Input: Email
    # Output: My friends, Pending Approvals, Sent Requests and Add new friends
    # ##########################
    email = session.get('email')

    if email is not None:
        myFriends = list(mongo.db.friends.find(
            {'sender': email, 'accept': True}, {'sender', 'receiver', 'accept'}))
        myFriendsList = list()

        for f in myFriends:
            myFriendsList.append(f['receiver'])

        print(myFriends)
        allUsers = list(mongo.db.user.find({}, {'name', 'email'}))

        pendingRequests = list(mongo.db.friends.find(
            {'sender': email, 'accept': False}, {'sender', 'receiver', 'accept'}))
        pendingReceivers = list()
        for p in pendingRequests:
            pendingReceivers.append(p['receiver'])

        pendingApproves = list()
        pendingApprovals = list(mongo.db.friends.find(
            {'receiver': email, 'accept': False}, {'sender', 'receiver', 'accept'}))
        for p in pendingApprovals:
            pendingApproves.append(p['sender'])

        print(pendingApproves)
    else:
        return redirect(url_for('login'))

    # print(pendingRequests)
    return render_template('friends.html', allUsers=allUsers, pendingRequests=pendingRequests, active=email,
                           pendingReceivers=pendingReceivers, pendingApproves=pendingApproves, myFriends=myFriends, myFriendsList=myFriendsList)


@a.app.route("/send_email", methods=['GET','POST'])
def send_email():
    # ############################
    # send_email() function shares Calorie History with friend's email
    # route "/send_email" will redirect to send_email() function which redirects to friends.html page.
    # Input: Email
    # Output: Calorie History Received on specified email
    # ##########################
    email = session.get('email')
    data = list(mongo.db.calories.find({'email': email}, {'date','email','calories','burnout'}))
    table = [['Date','Email ID','Calories','Burnout']]
    for a in data:
        tmp = [a['date'],a['email'],a['calories'],a['burnout']] 
        table.append(tmp) 
    
    friend_email = str(request.form.get('share')).strip()
    friend_email = str(friend_email).split(',')
    server = smtplib.SMTP_SSL("smtp.gmail.com",465)
    #Storing sender's email address and password
    sender_email = "burnoutapp74@gmail.com"
    sender_password = "fhjt vqpq slqr wdtr"
    
    #Logging in with sender details
    server.login(sender_email,sender_password)
    message = 'Subject: Calorie History\n\n Your Friend wants to share their calorie history with you!\n {}'.format(tabulate(table))
    for e in friend_email:
        print(e)
        server.sendmail(sender_email,e,message)
        
    server.quit()
    
    myFriends = list(mongo.db.friends.find(
        {'sender': email, 'accept': True}, {'sender', 'receiver', 'accept'}))
    myFriendsList = list()
    
    for f in myFriends:
        myFriendsList.append(f['receiver'])

    allUsers = list(mongo.db.user.find({}, {'name', 'email'}))
    
    pendingRequests = list(mongo.db.friends.find(
        {'sender': email, 'accept': False}, {'sender', 'receiver', 'accept'}))
    pendingReceivers = list()
    for p in pendingRequests:
        pendingReceivers.append(p['receiver'])

    pendingApproves = list()
    pendingApprovals = list(mongo.db.friends.find(
        {'receiver': email, 'accept': False}, {'sender', 'receiver', 'accept'}))
    for p in pendingApprovals:
        pendingApproves.append(p['sender'])
        
    return render_template('friends.html', allUsers=allUsers, pendingRequests=pendingRequests, active=email,
                           pendingReceivers=pendingReceivers, pendingApproves=pendingApproves, myFriends=myFriends, myFriendsList=myFriendsList)



@a.app.route("/ajaxsendrequest", methods=['POST'])
def ajaxsendrequest():
    # ############################
    # ajaxsendrequest() is a function that updates friend request information into database
    # route "/ajaxsendrequest" will redirect to ajaxsendrequest() function.
    # Details corresponding to given email address are fetched from the database entries and send request details updated
    # Input: Email, receiver
    # Output: DB entry of receiver info into database and return TRUE if success and FALSE otherwise
    # ##########################
    email = get_session = session.get('email')
    if get_session is not None:
        receiver = request.form.get('receiver')
        res = mongo.db.friends.insert_one(
            {'sender': email, 'receiver': receiver, 'accept': False})
        if res:
            return json.dumps({'status': True}), 200, {
                'ContentType': 'application/json'}
    return json.dumps({'status': False}), 500, {
        'ContentType:': 'application/json'}


@a.app.route("/ajaxcancelrequest", methods=['POST'])
def ajaxcancelrequest():
    # ############################
    # ajaxcancelrequest() is a function that updates friend request information into database
    # route "/ajaxcancelrequest" will redirect to ajaxcancelrequest() function.
    # Details corresponding to given email address are fetched from the database entries and cancel request details updated
    # Input: Email, receiver
    # Output: DB deletion of receiver info into database and return TRUE if success and FALSE otherwise
    # ##########################
    email = get_session = session.get('email')
    if get_session is not None:
        receiver = request.form.get('receiver')
        res = mongo.db.friends.delete_one(
            {'sender': email, 'receiver': receiver})
        if res:
            return json.dumps({'status': True}), 200, {
                'ContentType': 'application/json'}
    return json.dumps({'status': False}), 500, {
        'ContentType:': 'application/json'}


@a.app.route("/ajaxapproverequest", methods=['POST'])
def ajaxapproverequest():
    # ############################
    # ajaxapproverequest() is a function that updates friend request information into database
    # route "/ajaxapproverequest" will redirect to ajaxapproverequest() function.
    # Details corresponding to given email address are fetched from the database entries and approve request details updated
    # Input: Email, receiver
    # Output: DB updation of accept as TRUE info into database and return TRUE if success and FALSE otherwise
    # ##########################
    email = get_session = session.get('email')
    if get_session is not None:
        receiver = request.form.get('receiver')
        print(email, receiver)
        res = mongo.db.friends.update_one({'sender': receiver, 'receiver': email}, {
                                          "$set": {'sender': receiver, 'receiver': email, 'accept': True}})
        mongo.db.friends.insert_one(
            {'sender': email, 'receiver': receiver, 'accept': True})
        if res:
            return json.dumps({'status': True}), 200, {
                'ContentType': 'application/json'}
    return json.dumps({'status': False}), 500, {
        'ContentType:': 'application/json'}


@a.app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    # ############################
    # dashboard() function displays the dashboard.html template
    # route "/dashboard" will redirect to dashboard() function.
    # dashboard() called and displays the list of activities
    # Output: redirected to dashboard.html
    # ##########################
    return render_template('dashboard.html', title='Dashboard')


@a.app.route("/yoga", methods=['GET', 'POST'])
def yoga():
    # ############################
    # yoga() function displays the yoga.html template
    # route "/yoga" will redirect to yoga() function.
    # A page showing details about yoga is shown and if clicked on enroll then DB updation done and redirected to new_dashboard
    # Input: Email
    # Output: DB entry about enrollment and redirected to new dashboard
    # ##########################
    email = session.get('email')
    if email is not None:
        form = EnrollForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                enroll = "yoga"
                temp = mongo.db.enrolled_workout.find_one({'Email': email, 'Status': enroll})
                if temp is None:
                    mongo.db.enrolled_workout.insert({'Email': email, 'Status': enroll})
                    flash(f' You have succesfully enrolled in our {enroll} plan!', 'success')
                else:
                    flash(f'You have already enrolled in this plan!', 'warning')
            return render_template('dashboard.html', form=form)
    else:
        return redirect(url_for('dashboard'))
    return render_template('yoga.html', title='Yoga', form=form)


@a.app.route("/swim", methods=['GET', 'POST'])
def swim():
    # ############################
    # swim() function displays the swim.html template
    # route "/swim" will redirect to swim() function.
    # A page showing details about swimming is shown and if clicked on enroll then DB updation done and redirected to new_dashboard
    # Input: Email
    # Output: DB entry about enrollment and redirected to new dashboard
    # ##########################
    email = session.get('email')
    if email is not None:
        form = EnrollForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                enroll = "swim"
                temp = mongo.db.enrolled_workout.find_one({'Email': email, 'Status': enroll})
                if temp is None:
                    mongo.db.enrolled_workout.insert({'Email': email, 'Status': enroll})
                    flash(f' You have succesfully enrolled in our {enroll} plan!', 'success')
                else:
                    flash(f'You have already enrolled in this plan!', 'warning')
            return render_template('dashboard.html', form=form)
    else:
        return redirect(url_for('dashboard'))
    return render_template('swim.html', title='Swim', form=form)


@a.app.route("/abbs", methods=['GET', 'POST'])
def abbs():
    # ############################
    # abbs() function displays the abbs.html template
    # route "/abbs" will redirect to abbs() function.
    # A page showing details about abbs workout is shown and if clicked on enroll then DB updation done and redirected to new_dashboard
    # Input: Email
    # Output: DB entry about enrollment and redirected to new dashboard
    # ##########################
    email = session.get('email')
    if email is not None:
        form = EnrollForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                enroll = "abbs"
                temp = mongo.db.enrolled_workout.find_one({'Email': email, 'Status': enroll})
                if temp is None:
                    mongo.db.enrolled_workout.insert({'Email': email, 'Status': enroll})
                    flash(f' You have succesfully enrolled in our {enroll} plan!', 'success')
                else:
                    flash(f'You have already enrolled in this plan!', 'warning')
            return render_template('dashboard.html', form=form)
    else:
        return redirect(url_for('dashboard'))
    return render_template('abbs.html', title='Abbs Smash!', form=form)


@a.app.route("/belly", methods=['GET', 'POST'])
def belly():
    # ############################
    # belly() function displays the belly.html template
    # route "/belly" will redirect to belly() function.
    # A page showing details about belly workout is shown and if clicked on enroll then DB updation done and redirected to dashboard
    # Input: Email
    # Output: DB entry about enrollment and redirected to new dashboard
    # ##########################
    email = session.get('email')
    if email is not None:
        form = EnrollForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                enroll = "belly"
                temp = mongo.db.enrolled_workout.find_one({'Email': email, 'Status': enroll})
                if temp is None:
                    mongo.db.enrolled_workout.insert({'Email': email, 'Status': enroll})
                    flash(f' You have succesfully enrolled in our {enroll} plan!', 'success')
                else:
                    flash(f'You have already enrolled in this plan!', 'warning')
            return render_template('dashboard.html', form=form)
    else:
        return redirect(url_for('dashboard'))
    return render_template('belly.html', title='Belly Burner!', form=form)


@a.app.route("/easy_enroll", methods=['GET', 'POST'])
def easy_enroll():
    # ############################
    # easy_enroll() function quickly enrolls a user in the given workout without having to go through all the details of the workout.
    # route "/easy_enroll" will redirect to easy_enroll() function.
    # Input: Email
    # Output: DB entry about enrollment and redirected to dashboard
    # ##########################
    email = session.get('email')
    enroll = request.args.get('enroll')
    workout = request.args.get('workout')

    if email is not None and enroll == 'yes':
        # Check if the user is already enrolled
        temp = mongo.db.enrolled_workout.find_one({'Email': email, 'Status': workout})
        if temp is None:
            mongo.db.enrolled_workout.insert_one({'Email': email, 'Status': workout})
            flash(f' You have succesfully enrolled in our {workout} plan!', 'success')
        else: 
            flash(f'You have already enrolled in this plan!', 'warning')
            redirect(url_for(workout))
    return redirect(url_for('dashboard'))


@a.app.route("/core", methods=['GET', 'POST'])
def core():
    # ############################
    # core() function displays the belly.html template
    # route "/core" will redirect to core() function.
    # A page showing details about core workout is shown and if clicked on enroll then DB updation done and redirected to new_dashboard
    # Input: Email
    # Output: DB entry about enrollment and redirected to new dashboard
    # ##########################
    email = session.get('email')
    if email is not None:
        form = EnrollForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                enroll = "core"
                temp = mongo.db.enrolled_workout.find_one({'Email': email, 'Status': enroll})
                if temp is None:
                    mongo.db.enrolled_workout.insert({'Email': email, 'Status': enroll})
                    flash(f' You have succesfully enrolled in our {enroll} plan!', 'success')
                else:
                    flash(f'You have already enrolled in this plan!', 'warning')
            return render_template('dashboard.html', form=form)
    else:
        return redirect(url_for('dashboard'))
    return render_template('core.html', title='Core Conditioning', form=form)


@a.app.route("/gym", methods=['GET', 'POST'])
def gym():
    # ############################
    # gym() function displays the gym.html template
    # route "/gym" will redirect to gym() function.
    # A page showing details about gym plan is shown and if clicked on enroll then DB updation done and redirected to new_dashboard
    # Input: Email
    # Output: DB entry about enrollment and redirected to new dashboard
    # ##########################
    email = session.get('email')
    if email is not None:
        form = EnrollForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                enroll = "gym"
                temp = mongo.db.enrolled_workout.find_one({'Email': email, 'Status': enroll})
                if temp is None:
                    mongo.db.enrolled_workout.insert({'Email': email, 'Status': enroll})
                    flash(f' You have succesfully enrolled in our {enroll} plan!', 'success')
                else:
                    flash(f'You have already enrolled in this plan!', 'warning')
            return render_template('dashboard.html', form=form)
    else:
        return redirect(url_for('dashboard'))
    return render_template('gym.html', title='Gym', form=form)


@a.app.route("/walk", methods=['GET', 'POST'])
def walk():
    # ############################
    # walk() function displays the walk.html template
    # route "/walk" will redirect to walk() function.
    # A page showing details about walk plan is shown and if clicked on enroll then DB updation done and redirected to new_dashboard
    # Input: Email
    # Output: DB entry about enrollment and redirected to new dashboard
    # ##########################
    email = session.get('email')
    if email is not None:
        form = EnrollForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                enroll = "walk"
                temp = mongo.db.enrolled_workout.find_one({'Email': email, 'Status': enroll})
                if temp is None:
                    mongo.db.enrolled_workout.insert({'Email': email, 'Status': enroll})
                    flash(f' You have succesfully enrolled in our {enroll} plan!', 'success')
                else:
                    flash(f'You have already enrolled in this plan!', 'warning')
            return render_template('dashboard.html', form=form)
    else:
        return redirect(url_for('dashboard'))
    return render_template('walk.html', title='Walk', form=form)


@a.app.route("/dance", methods=['GET', 'POST'])
def dance():
    # ############################
    # dance() function displays the dance.html template
    # route "/dance" will redirect to dance() function.
    # A page showing details about dance plan is shown and if clicked on enroll then DB updation done and redirected to new_dashboard
    # Input: Email
    # Output: DB entry about enrollment and redirected to new dashboard
    # ##########################
    email = session.get('email')
    if email is not None:
        form = EnrollForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                enroll = "dance"
                temp = mongo.db.enrolled_workout.find_one({'Email': email, 'Status': enroll})
                if temp is None:
                    mongo.db.enrolled_workout.insert({'Email': email, 'Status': enroll})
                    flash(f' You have succesfully enrolled in our {enroll} plan!', 'success')
                else:
                    flash(f'You have already enrolled in this plan!', 'warning')
            return render_template('dashboard.html', form=form)
    else:
        return redirect(url_for('dashboard'))
    return render_template('dance.html', title='Dance', form=form)


@a.app.route("/hrx", methods=['GET', 'POST'])
def hrx():
    # ############################
    # hrx() function displays the hrx.html template
    # route "/hrx" will redirect to hrx() function.
    # A page showing details about hrx plan is shown and if clicked on enroll then DB updation done and redirected to new_dashboard
    # Input: Email
    # Output: DB entry about enrollment and redirected to new dashboard
    # ##########################
    email = session.get('email')
    if email is not None:
        form = EnrollForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                enroll = "hrx"
                temp = mongo.db.enrolled_workout.find_one({'Email': email, 'Status': enroll})
                if temp is None:
                    mongo.db.enrolled_workout.insert({'Email': email, 'Status': enroll})
                    flash(f' You have succesfully enrolled in our {enroll} plan!', 'success')
                else:
                    flash(f'You have already enrolled in this plan!', 'warning')
            return render_template('dashboard.html', form=form)
    else:
        return redirect(url_for('dashboard'))
    return render_template('hrx.html', title='HRX', form=form)


@a.app.route("/forgot", methods=['GET', 'POST'])
def forgot():
    error = None
    message = None
    form = ForgotForm()
    if form.validate_on_submit():
        email=form.email.data.lower()
        temp = mongo.db.user.find_one({'email': email}, {'email'})
        if temp: 
            # Generate a password reset code
            code = str(uuid.uuid4())
            
            # Store the code in the database (you may need to modify your schema)
            mongo.db.user.update_one({'email': email}, {'$set': {'password_reset_code': code}})

            # Send the password reset email
            reset_link = url_for('reset_password', token=code, _external=True)
            email_content = render_template('password_reset.html', reset_link=reset_link)

            # Create the email message
            msg = Message('Password Reset Request', sender='burnoutapp74@gmail.com', recipients=[email])
            msg.html = email_content

            # Send the email
            try:
                a.mail.send(msg)
            except smtplib.SMTPAuthenticationError as e:
                print(f"SMTP Authentication Error: {str(e)}")
            
            message = "You will receive an email with instructions to reset your password if your email is registered with us."
        else:
            error = "Email not found in our database."
    
    return render_template('forgot.html', form=form, error=error, message=message)


@a.app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_password(token):
    error = None
    form = ResetPasswordForm()  # Create a form for resetting the password
    
    # Verify the token and get the associated email address from the database
    reset_data = mongo.db.user.find_one({'password_reset_code': token}, {'email'})
    if not reset_data:
        flash('Invalid or expired token. Please request a new password reset.', 'danger')
        return redirect(url_for('forgot'))
    
    email = reset_data['email']
    
    if form.validate_on_submit():
        # Reset the user's password and update the database
        new_password = form.new_password.data
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        # Update the user's password in the database
        mongo.db.user.update_one({'email': email}, {'$set': {'pwd': hashed_password}})
        
        # Remove the password reset code from the database (optional)
        mongo.db.user.update_one({'email': email}, {'$unset': {'password_reset_code': 1}})
        
        flash('Password reset successful. You can now log in with your new password.', 'success')
        return redirect(url_for('login'))  # Redirect to the login page
    
    return render_template('reset_password.html', form=form, token=token, error=error)

if __name__ == '__main__':
    a.app.run(debug=True)
