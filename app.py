from flask import render_template, url_for, flash, redirect, request, Flask, jsonify
from forms import RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm
from models import app, db, bcrypt, User, mail, Heading, Education, ProfessionalExperience, Skills, Summary, Event, Blog, Review, Career, Support
from flask_mail import Message
from flask_login import login_user, current_user, logout_user, login_required
import secrets, threading
import datetime
from datetime import timedelta



def send_event_reminder(event):
    msg = Message('Event Reminder: ' + event.title,
                  sender='hr168074@gmail.com',
                  recipients=[event.user.email])
    msg.body = f'''Reminder for your event:
Title: {event.title}
Description: {event.description}
Start Time: {event.start_time}
End Time: {event.end_time}

Please do not reply to this email.
'''
    mail.send(msg)

def schedule_reminder(event):
    reminder_time = event.start_time - timedelta(minutes=30) 
    delay = (reminder_time - datetime.utcnow()).total_seconds()
    if delay > 0:
        threading.Timer(delay, send_event_reminder, args=[event]).start()

def send_reset_email(user):
    if user:
        token = secrets.token_hex(16)
        user.reset_token = token
        db.session.commit()
        msg = Message('Password Reset Request',
                      sender='hr168074@gmail.com',
                      recipients=[user.email])
        msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
        mail.send(msg)

@app.route("/")
def welcome():
    return "Welcome to the Application!"

@app.route("/home")
@login_required
def home():
    return render_template('home.html', title='Home')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(name=form.name.data, email=form.email.data, password=hashed_password, role='user')
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=True)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('welcome'))

@app.route("/forgot_password", methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('forgot_password.html', title='Forgot Password', form=form)

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('forgot_password'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        user.reset_token = None
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', title='Reset Password', form=form)

@app.route("/account")
@login_required
def account():
    user_info = {
        'name': current_user.name,
        'email': current_user.email,
        'role': current_user.role,
        'logout_link': url_for('logout', _external=True),
        'account_details_link': url_for('account_details', _external=True)
    }
    return jsonify(user_info)

@app.route("/account_details")
@login_required
def account_details():
    detailed_info = {
        'name': current_user.name,
        'email': current_user.email,
        'role': current_user.role,
        'heading_link': url_for('heading', _external=True),
        'education_link': url_for('education', _external=True),
        'professional_experience_link': url_for('professional_experience', _external=True),
        'skills_link': url_for('skills', _external=True),
        'summary_link': url_for('summary', _external=True)
    }
    return jsonify(detailed_info)



@app.route("/heading", methods=['GET', 'POST'])
@login_required
def manage_heading():
    if request.method == 'POST':
        data = request.get_json()
        new_heading = Heading(
            first_name=data['first_name'],
            last_name=data['last_name'],
            profession=data['profession'],
            city=data['city'],
            country=data['country'],
            phone_number=data['phone_number'],
            email=data['email'],
            user_id=current_user.id
        )
        db.session.add(new_heading)
        db.session.commit()
        return jsonify({"message": "Heading created successfully"}), 201

    elif request.method == 'GET':
        heading = Heading.query.filter_by(user_id=current_user.id).first()
        if heading:
            heading_info = {
                'first_name': heading.first_name,
                'last_name': heading.last_name,
                'profession': heading.profession,
                'city': heading.city,
                'country': heading.country,
                'phone_number': heading.phone_number,
                'email': heading.email
            }
            return jsonify(heading_info), 200
        else:
            return jsonify({"message": "No heading found"}), 404

@app.route("/heading/<int:heading_id>", methods=['PUT', 'DELETE'])
@login_required
def modify_heading(heading_id):
    if request.method == 'PUT':
        data = request.get_json()
        heading = Heading.query.filter_by(user_id=current_user.id, id=heading_id).first()
        if heading:
            heading.first_name = data['first_name']
            heading.last_name = data['last_name']
            heading.profession = data['profession']
            heading.city = data['city']
            heading.country = data['country']
            heading.phone_number = data['phone_number']
            heading.email = data['email']
            heading.date_updated = datetime.datetime.utcnow()
            db.session.commit()
            return jsonify({"message": "Heading updated successfully"}), 200
        else:
            return jsonify({"message": "No heading found"}), 404

    elif request.method == 'DELETE':
        heading = Heading.query.filter_by(user_id=current_user.id, id=heading_id).first()
        if heading:
            db.session.delete(heading)
            db.session.commit()
            return jsonify({"message": "Heading deleted successfully"}), 200
        else:
            return jsonify({"message": "No heading found"}), 404



@app.route("/education", methods=['GET', 'POST'])
@login_required
def manage_education():
    if request.method == 'POST':
        data = request.get_json()
        new_education = Education(
            college_name=data['college_name'],
            college_location=data['college_location'],
            degree=data['degree'],
            field_of_study=data['field_of_study'],
            grade=data['grade'],
            graduation_year=data['graduation_year'],
            user_id=current_user.id
        )
        db.session.add(new_education)
        db.session.commit()
        return jsonify({"message": "Education created successfully"}), 201

    elif request.method == 'GET':
        educations = Education.query.filter_by(user_id=current_user.id).all()
        if educations:
            education_list = [{
                'id': education.id,
                'college_name': education.college_name,
                'college_location': education.college_location,
                'degree': education.degree,
                'field_of_study': education.field_of_study,
                'grade': education.grade,
                'graduation_year': education.graduation_year
            } for education in educations]
            return jsonify(education_list), 200
        else:
            return jsonify({"message": "No education records found"}), 404

@app.route("/education/<int:education_id>", methods=['PUT', 'DELETE'])
@login_required
def modify_education(education_id):
    if request.method == 'PUT':
        data = request.get_json()
        education = Education.query.filter_by(user_id=current_user.id, id=education_id).first()
        if education:
            education.college_name = data['college_name']
            education.college_location = data['college_location']
            education.degree = data['degree']
            education.field_of_study = data['field_of_study']
            education.grade = data['grade']
            education.graduation_year = data['graduation_year']
            education.date_updated = datetime.datetime.utcnow()
            db.session.commit()
            return jsonify({"message": "Education updated successfully"}), 200
        else:
            return jsonify({"message": "No education record found"}), 404

    elif request.method == 'DELETE':
        education = Education.query.filter_by(user_id=current_user.id, id=education_id).first()
        if education:
            db.session.delete(education)
            db.session.commit()
            return jsonify({"message": "Education deleted successfully"}), 200
        else:
            return jsonify({"message": "No education record found"}), 404



@app.route("/professional_experience", methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def professional_experience():
    if request.method == 'POST':
        data = request.get_json()
        new_experience = ProfessionalExperience(
            experience_type=data['experience_type'],
            company_name=data['company_name'],
            company_location=data['company_location'],
            title=data['title'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            currently_work=data['currently_work'],
            user_id=current_user.id
        )
        db.session.add(new_experience)
        db.session.commit()
        return jsonify({"message": "Professional experience created successfully"}), 201

    elif request.method == 'GET':
        experiences = ProfessionalExperience.query.filter_by(user_id=current_user.id).all()
        if experiences:
            experience_list = []
            for experience in experiences:
                experience_info = {
                    'id': experience.id,
                    'experience_type': experience.experience_type,
                    'company_name': experience.company_name,
                    'company_location': experience.company_location,
                    'title': experience.title,
                    'start_date': experience.start_date,
                    'end_date': experience.end_date,
                    'currently_work': experience.currently_work
                }
                experience_list.append(experience_info)
            return jsonify(experience_list)
        else:
            return jsonify({"message": "No professional experience records found"}), 404

    elif request.method == 'PUT':
        data = request.get_json()
        experience = ProfessionalExperience.query.filter_by(user_id=current_user.id, id=data['id']).first()
        if experience:
            experience.experience_type = data['experience_type']
            experience.company_name = data['company_name']
            experience.company_location = data['company_location']
            experience.title = data['title']
            experience.start_date = data['start_date']
            experience.end_date = data['end_date']
            experience.currently_work = data['currently_work']
            experience.date_updated = datetime.datetime.utcnow()
            db.session.commit()
            return jsonify({"message": "Professional experience updated successfully"}), 200
        else:
            return jsonify({"message": "No professional experience record found"}), 404

    elif request.method == 'DELETE':
        data = request.get_json()
        experience = ProfessionalExperience.query.filter_by(user_id=current_user.id, id=data['id']).first()
        if experience:
            db.session.delete(experience)
            db.session.commit()
            return jsonify({"message": "Professional experience deleted successfully"}), 200
        else:
            return jsonify({"message": "No professional experience record found"}), 404




@app.route("/skills", methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def skills():
    if request.method == 'POST':
        data = request.get_json()
        new_skill = Skills(
            skill_name=data['skill_name'],
            skill_rating=data['skill_rating'],
            user_id=current_user.id
        )
        db.session.add(new_skill)
        db.session.commit()
        return jsonify({"message": "Skill created successfully"}), 201

    elif request.method == 'GET':
        skills = Skills.query.filter_by(user_id=current_user.id).all()
        if skills:
            skill_list = []
            for skill in skills:
                skill_info = {
                    'id': skill.id,
                    'skill_name': skill.skill_name,
                    'skill_rating': skill.skill_rating
                }
                skill_list.append(skill_info)
            return jsonify(skill_list)
        else:
            return jsonify({"message": "No skills found"}), 404

    elif request.method == 'PUT':
        data = request.get_json()
        skill = Skills.query.filter_by(user_id=current_user.id, id=data['id']).first()
        if skill:
            skill.skill_name = data['skill_name']
            skill.skill_rating = data['skill_rating']
            skill.date_updated = datetime.utcnow()
            db.session.commit()
            return jsonify({"message": "Skill updated successfully"}), 200
        else:
            return jsonify({"message": "Skill not found"}), 404

    elif request.method == 'DELETE':
        data = request.get_json()
        skill = Skills.query.filter_by(user_id=current_user.id, id=data['id']).first()
        if skill:
            db.session.delete(skill)
            db.session.commit()
            return jsonify({"message": "Skill deleted successfully"}), 200
        else:
            return jsonify({"message": "Skill not found"}), 404





@app.route("/summary", methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def summary():
    if request.method == 'POST':
        data = request.get_json()
        new_summary = Summary(
            content=data['content'],
            user_id=current_user.id
        )
        db.session.add(new_summary)
        db.session.commit()
        return jsonify({"message": "Summary created successfully"}), 201

    elif request.method == 'GET':
        summary = Summary.query.filter_by(user_id=current_user.id).first()
        if summary:
            summary_info = {
                'id': summary.id,
                'content': summary.content,
                'date_created': summary.date_created.strftime('%Y-%m-%d %H:%M:%S'),
                'date_updated': summary.date_updated.strftime('%Y-%m-%d %H:%M:%S')
            }
            return jsonify(summary_info)
        else:
            return jsonify({"message": "No summary found"}), 404

    elif request.method == 'PUT':
        data = request.get_json()
        summary = Summary.query.filter_by(user_id=current_user.id).first()
        if summary:
            summary.content = data['content']
            summary.date_updated = datetime.datetime.utcnow()
            db.session.commit()
            return jsonify({"message": "Summary updated successfully"}), 200
        else:
            return jsonify({"message": "No summary found"}), 404

    elif request.method == 'DELETE':
        summary = Summary.query.filter_by(user_id=current_user.id).first()
        if summary:
            db.session.delete(summary)
            db.session.commit()
            return jsonify({"message": "Summary deleted successfully"}), 200
        else:
            return jsonify({"message": "No summary found"}), 404



@app.route("/events", methods=['POST'])
@login_required
def create_event():
    data = request.get_json()
    new_event = Event(
        title=data['title'],
        description=data.get('description', ''),
        start_time=datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S'),
        end_time=datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M:%S'),
        user_id=current_user.id
    )
    db.session.add(new_event)
    db.session.commit()
    schedule_reminder(new_event)
    return jsonify({"message": "Event created successfully"}), 201

@app.route("/events", methods=['GET'])
@login_required
def get_events():
    date_str = request.args.get('date')
    if date_str:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        start_of_day = datetime(date.year, date.month, date.day)
        end_of_day = start_of_day + timedelta(days=1)
        events = Event.query.filter(Event.user_id == current_user.id,
                                    Event.start_time >= start_of_day,
                                    Event.start_time < end_of_day).all()
    else:
        events = Event.query.filter_by(user_id=current_user.id).all()
    
    events_list = [{
        'id': event.id,
        'title': event.title,
        'description': event.description,
        'start_time': event.start_time.strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': event.end_time.strftime('%Y-%m-%d %H:%M:%S')
    } for event in events]
    return jsonify(events_list), 200

@app.route("/events/<int:event_id>", methods=['PUT'])
@login_required
def update_event(event_id):
    data = request.get_json()
    event = Event.query.get_or_404(event_id)
    if event.user_id != current_user.id:
        return jsonify({"message": "Permission denied"}), 403
    event.title = data['title']
    event.description = data.get('description', '')
    event.start_time = datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S')
    event.end_time = datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M:%S')
    db.session.commit()
    return jsonify({"message": "Event updated successfully"}), 200

@app.route("/events/<int:event_id>", methods=['DELETE'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.user_id != current_user.id:
        return jsonify({"message": "Permission denied"}), 403
    db.session.delete(event)
    db.session.commit()
    return jsonify({"message": "Event deleted successfully"}), 200



@app.route("/blogs", methods=['POST'])
@login_required
def create_blog():
    data = request.get_json()
    new_blog = Blog(
        title=data['title'],
        content=data['content'],
        user_id=current_user.id
    )
    db.session.add(new_blog)
    db.session.commit()
    return jsonify({"message": "Blog created successfully"}), 201

@app.route("/blogs", methods=['GET'])
@login_required
def get_blogs():
    blogs = Blog.query.filter_by(user_id=current_user.id).all()
    blogs_list = [{
        'id': blog.id,
        'title': blog.title,
        'content': blog.content,
        'date_posted': blog.date_posted.strftime('%Y-%m-%d %H:%M:%S')
    } for blog in blogs]
    return jsonify(blogs_list), 200

@app.route("/blogs/<int:blog_id>", methods=['GET'])
@login_required
def get_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if blog.user_id != current_user.id:
        return jsonify({"message": "Permission denied"}), 403
    blog_data = {
        'id': blog.id,
        'title': blog.title,
        'content': blog.content,
        'date_posted': blog.date_posted.strftime('%Y-%m-%d %H:%M:%S')
    }
    return jsonify(blog_data), 200

@app.route("/blogs/<int:blog_id>", methods=['PUT'])
@login_required
def update_blog(blog_id):
    data = request.get_json()
    blog = Blog.query.get_or_404(blog_id)
    if blog.user_id != current_user.id:
        return jsonify({"message": "Permission denied"}), 403
    blog.title = data['title']
    blog.content = data['content']
    db.session.commit()
    return jsonify({"message": "Blog updated successfully"}), 200

@app.route("/blogs/<int:blog_id>", methods=['DELETE'])
@login_required
def delete_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if blog.user_id != current_user.id:
        return jsonify({"message": "Permission denied"}), 403
    db.session.delete(blog)
    db.session.commit()
    return jsonify({"message": "Blog deleted successfully"}), 200



@app.route("/reviews", methods=['POST'])
@login_required
def create_review():
    data = request.get_json()
    new_review = Review(
        title=data['title'],
        content=data['content'],
        rating=data['rating'],
        user_id=current_user.id
    )
    db.session.add(new_review)
    db.session.commit()
    return jsonify({"message": "Review created successfully"}), 201

@app.route("/reviews", methods=['GET'])
@login_required
def get_reviews():
    reviews = Review.query.filter_by(user_id=current_user.id).all()
    reviews_list = [{
        'id': review.id,
        'title': review.title,
        'content': review.content,
        'rating': review.rating,
        'date_posted': review.date_posted.strftime('%Y-%m-%d %H:%M:%S')
    } for review in reviews]
    return jsonify(reviews_list), 200

@app.route("/reviews/<int:review_id>", methods=['GET'])
@login_required
def get_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id != current_user.id:
        return jsonify({"message": "Permission denied"}), 403
    review_data = {
        'id': review.id,
        'title': review.title,
        'content': review.content,
        'rating': review.rating,
        'date_posted': review.date_posted.strftime('%Y-%m-%d %H:%M:%S')
    }
    return jsonify(review_data), 200

@app.route("/reviews/<int:review_id>", methods=['PUT'])
@login_required
def update_review(review_id):
    data = request.get_json()
    review = Review.query.get_or_404(review_id)
    if review.user_id != current_user.id:
        return jsonify({"message": "Permission denied"}), 403
    review.title = data['title']
    review.content = data['content']
    review.rating = data['rating']
    db.session.commit()
    return jsonify({"message": "Review updated successfully"}), 200

@app.route("/reviews/<int:review_id>", methods=['DELETE'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id != current_user.id:
        return jsonify({"message": "Permission denied"}), 403
    db.session.delete(review)
    db.session.commit()
    return jsonify({"message": "Review deleted successfully"}), 200



@app.route("/career", methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def career():
    if request.method == 'POST':
        data = request.get_json()
        new_career = Career(
            title=data['title'],
            description=data['description'],
            requirements=data['requirements'],
            location=data['location']
        )
        db.session.add(new_career)
        db.session.commit()
        return jsonify({"message": "Career created successfully"}), 201

    elif request.method == 'GET':
        careers = Career.query.all()
        if careers:
            career_list = []
            for career in careers:
                career_info = {
                    'id': career.id,
                    'title': career.title,
                    'description': career.description,
                    'requirements': career.requirements,
                    'location': career.location,
                    'date_created': career.date_created.strftime('%Y-%m-%d %H:%M:%S'),
                    'date_updated': career.date_updated.strftime('%Y-%m-%d %H:%M:%S')
                }
                career_list.append(career_info)
            return jsonify(career_list)
        else:
            return jsonify({"message": "No careers found"}), 404

    elif request.method == 'PUT':
        data = request.get_json()
        career = Career.query.filter_by(id=data['id']).first()
        if career:
            career.title = data['title']
            career.description = data['description']
            career.requirements = data['requirements']
            career.location = data['location']
            career.date_updated = datetime.utcnow()
            db.session.commit()
            return jsonify({"message": "Career updated successfully"}), 200
        else:
            return jsonify({"message": "Career not found"}), 404

    elif request.method == 'DELETE':
        data = request.get_json()
        career = Career.query.filter_by(id=data['id']).first()
        if career:
            db.session.delete(career)
            db.session.commit()
            return jsonify({"message": "Career deleted successfully"}), 200
        else:
            return jsonify({"message": "Career not found"}), 404



@app.route("/support", methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def support():
    if request.method == 'POST':
        data = request.get_json()
        new_support = Support(
            user_id=current_user.id,
            issue=data['issue'],
            description=data['description'],
            status=data['status']
        )
        db.session.add(new_support)
        db.session.commit()
        return jsonify({"message": "Support ticket created successfully"}), 201

    elif request.method == 'GET':
        supports = Support.query.filter_by(user_id=current_user.id).all()
        if supports:
            support_list = []
            for support in supports:
                support_info = {
                    'id': support.id,
                    'issue': support.issue,
                    'description': support.description,
                    'status': support.status,
                    'date_created': support.date_created.strftime('%Y-%m-%d %H:%M:%S'),
                    'date_updated': support.date_updated.strftime('%Y-%m-%d %H:%M:%S')
                }
                support_list.append(support_info)
            return jsonify(support_list)
        else:
            return jsonify({"message": "No support tickets found"}), 404

    elif request.method == 'PUT':
        data = request.get_json()
        support = Support.query.filter_by(user_id=current_user.id, id=data['id']).first()
        if support:
            support.issue = data['issue']
            support.description = data['description']
            support.status = data['status']
            support.date_updated = datetime.utcnow()
            db.session.commit()
            return jsonify({"message": "Support ticket updated successfully"}), 200
        else:
            return jsonify({"message": "Support ticket not found"}), 404

    elif request.method == 'DELETE':
        data = request.get_json()
        support = Support.query.filter_by(user_id=current_user.id, id=data['id']).first()
        if support:
            db.session.delete(support)
            db.session.commit()
            return jsonify({"message": "Support ticket deleted successfully"}), 200
        else:
            return jsonify({"message": "Support ticket not found"}), 404



if __name__ == '__main__':
    app.run(debug=True)
