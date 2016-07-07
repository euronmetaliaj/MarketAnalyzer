from flask import render_template, redirect, request
from . import main
from core import cron
from .. import login_manager
from .. import mongo
import psutil
import json
import core.social.Objects.Location as Location
import core.social.Objects.Page as Page
import core.social.Objects.PageEval as PageEval
import core.social.Objects.User as User
import datetime
import re
import facebook
from collections import defaultdict
import time

@cron.interval_schedule(seconds = 2)
def job_function():
    # IF THERE ARE MONGODB QUERIES TO GET SOME LIKED PAGES
    # THAN WE INDEX THEM HERE IF CPU IS LESS THAN 10 % ,ELSE
    # WAIT
    pass


# Imports for mail sending
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

@main.route('/building')
def building():
    return render_template('building.html')


@main.route('/', endpoint='root')
def index():
    today = datetime.datetime.now().strftime("%H:%M")
    return render_template('agreement.html',today = today)


@main.route('/result', methods=["POST"])
def results():
    location = request.form.get('location') or None
    category_subcategory = request.form.get('category') or None
    keywords = request.form.getlist('keywords') or None
    results_type = request.form.get('results_type')

    if category_subcategory is not None:
        category, subcategory = category_subcategory.split(' - ')

    else:
        category = subcategory = None

    print (location)
    print category
    print subcategory
    print keywords
    print results_type

    users = PageEval.PageEval.get_filtered_evaluations(category, subcategory, keywords, location)
    print users
    addressPoints = []
    sorted_users = None

    if users is not None:
        for user, points in users:
            location = Location.Location.get_location_by_city(user.location['name'].split(',')[0])
            addressPoints.append([location.latitude, location.longitude, points])
        sorted_users = sorted(users, key=lambda x: x[1], reverse=True)


    if results_type == 'heatmap':
        return render_template('results_heatmap.html', users=users, addressPoints=addressPoints)

    elif results_type == 'list':
        return render_template('results_list.html', users=sorted_users)

#
# @main.route('/part')
# def part():
#
#     users = None
#     return render_template('token.html',users = users)


@main.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'GET':
        return render_template('feedback.html')

    # users = None
    msg = MIMEMultipart()
    msg['From'] = 'mhinfo.lab@gmail.com'
    msg['To'] = 'mhinfo.lab@gmail.com'
    msg['Subject'] = 'Feedback for Heatmap Service'

    sender_name = request.form.get('name')
    sender_email = request.form.get('email')
    sender_message = request.form.get('message')

    message = "Feedback from: " + sender_name + ", " + sender_email + "\n\nMessage: \n" + sender_message
    msg.attach(MIMEText(message))

    try:
        mailserver = smtplib.SMTP('smtp.gmail.com', 587)
        # identify ourselves to smtp gmail client
        mailserver.ehlo()
        # secure our email with tls encryption
        mailserver.starttls()
        # re-identify ourselves as an encrypted connection
        mailserver.ehlo()
        mailserver.login('mhinfo.lab@gmail.com', 'euronklajdi')

        # From, To, Content
        mailserver.sendmail('mhinfo.lab@gmail.com', 'mhinfo.lab@gmail.com', msg.as_string())

        mailserver.quit()
        return render_template('thankyou.html')

    except:
        return render_template('error.html', message="Something went wrong. Please try again later.")


@main.route('/filter')
def filtering():
    return render_template('filter.html')


@main.route('/analyzer', methods=['GET', 'POST'])
def analyzer():
    if request.method == 'GET':
        return render_template('analyzer.html')

    start_time = time.time()
    api_token = request.form.get('token')

    graph = facebook.GraphAPI(
        access_token=api_token,
        version='2.2')

    while True:
        # Load user
        try:
            fb_user = graph.get_object(id='me')
            break

        except facebook.GraphAPIError:
            message = "The provided token is not valid. Please try again."
            return render_template('error.html', message=message)

        except:
            continue
            # message = "Something went wrong. Please try again later."
            # return render_template('error.html', message=message)

    # If user is not already in database, save to database
    user = User.User.load_from_db(fb_user['id'])

    if user is None:
        user = User.User(**fb_user)
        user.save()

    # Get user posts
    users_likes = defaultdict(int)          # Stores the total likes of each user
    users_comments = defaultdict(int)       # Stores the total

    post_likes = defaultdict(int)
    post_comments = defaultdict(int)
    post_links = {}
    # graph_data = []

    posts = graph.get_connections(id='me', connection_name='posts', limit=1000)

    # Save number of posts analyzed
    number_of_posts = len(posts['data'])

    # Analyze each post
    for post in posts['data']:
        # Save the Facebook link of the posts, skip if no link
        if 'link' not in post:
            continue

        post_links[post['id']] = post['link']

        total_likes = 0
        total_comments = 0

        # Get likes
        if 'likes' in post:
            likes = post['likes']
            total_likes = len(likes['data'])
            # print "Post: " + post['id'] + " Likes: " + str(len(likes['data']))

            # Evaluate likes
            for like in likes['data']:
                users_likes[like['name']] += 1

            # Get other likes of the post
            while 'paging' in likes and 'next' in likes['paging']:
                likes = graph.get_connections(id=post['id'], connection_name='likes', limit=500,
                                              after=likes['paging']['cursors']['after'], summary=True)

                # Get total number of likes from the query
                total_likes = likes['summary']['total_count']
                # print "Post: " + post['id'] + " Likes: " + str(len(likes['data']))

                for like in likes['data']:
                    users_likes[like['name']] += 1

            # Save the total number of likes for this post
            post_likes[post['id']] = total_likes
            # graph_data.append({'date': str(post['created_time']), 'likes': total_likes})

        # Check if there are comments
        if 'comments' not in post:
            continue

        # Get comments
        comments = post['comments']
        total_comments = len(comments['data'])

        # Evaluate comments
        for comment in comments['data']:
            users_comments[comment['from']['name']] += 1

        # Get the other comments of the post (if there are)
        while 'paging' in comments and 'next' in comments['paging']:
            comments = graph.get_connections(id=post['id'], connection_name='comments', limit=500,
                                             after=comments['paging']['cursors']['after'], summary=True)

            # Get total number of likes from the query
            total_comments = comments['summary']['total_count']

            for comment in comments['data']:
                users_comments[comment['from']['name']] += 1

        # Save the total number of comments for this post
        post_comments[post['id']] = total_comments

    # while 'paging' in posts and 'next' in posts['paging']:
    #     posts = graph.get_connections(id='me', connection_name='posts', limit=1000,
    #                                   after=posts['paging']['cursors']['after'])
    #
    #     # Save number of posts analyzed
    #     number_of_posts += len(posts['data'])
    #
    #     # Analyze each post
    #     for post in posts['data']:
    #         # Save the Facebook link of the posts, skip if no link
    #         if 'link' not in post:
    #             continue
    #
    #         post_links[post['id']] = post['link']
    #
    #         total_likes = 0
    #         total_comments = 0
    #
    #         # Get likes
    #         if 'likes' in post:
    #             likes = post['likes']
    #             total_likes = len(likes['data'])
    #             # print "Post: " + post['id'] + " Likes: " + str(len(likes['data']))
    #
    #             # Evaluate likes
    #             for like in likes['data']:
    #                 users_likes[like['name']] += 1
    #
    #             # Get other likes of the post
    #             while 'paging' in likes and 'next' in likes['paging']:
    #                 likes = graph.get_connections(id=post['id'], connection_name='likes', limit=500,
    #                                               after=likes['paging']['cursors']['after'], summary=True)
    #
    #                 # Get total number of likes from the query
    #                 total_likes = likes['summary']['total_count']
    #                 # print "Post: " + post['id'] + " Likes: " + str(len(likes['data']))
    #
    #                 for like in likes['data']:
    #                     users_likes[like['name']] += 1
    #
    #             # Save the total number of likes for this post
    #             post_likes[post['id']] = total_likes
    #             # graph_data.append({'date': str(post['created_time']), 'likes': total_likes})
    #
    #         # Check if there are comments
    #         if 'comments' not in post:
    #             continue
    #
    #         # Get comments
    #         comments = post['comments']
    #         total_comments = len(comments['data'])
    #
    #         # Evaluate comments
    #         for comment in comments['data']:
    #             users_comments[comment['from']['name']] += 1
    #
    #         # Get the other comments of the post (if there are)
    #         while 'paging' in comments and 'next' in comments['paging']:
    #             comments = graph.get_connections(id=post['id'], connection_name='comments', limit=500,
    #                                              after=comments['paging']['cursors']['after'], summary=True)
    #
    #             # Get total number of likes from the query
    #             total_comments = comments['summary']['total_count']
    #
    #             for comment in comments['data']:
    #                 users_comments[comment['from']['name']] += 1
    #
    #         # Save the total number of comments for this post
    #         post_comments[post['id']] = total_comments

    top_likes = list(sorted(dict(users_likes).items(), key=lambda x: x[1], reverse=True))
    top_comments = list(sorted(dict(users_comments).items(), key=lambda x: x[1], reverse=True))
    most_liked_posts = list(sorted(dict(post_likes).items(), key=lambda x: x[1], reverse=True))
    most_commented_posts = list(sorted(dict(post_comments).items(), key=lambda x: x[1], reverse=True))

    print number_of_posts

    print top_likes
    print top_comments
    print most_liked_posts
    print most_commented_posts

    print "Total time: " + str(time.time() - start_time)

    return render_template('analyzer_results.html', user=user.name,
                           number_of_posts=number_of_posts, top_likes=top_likes,
                           top_comments=top_comments, most_liked_posts=most_liked_posts,
                           most_commented_posts=most_commented_posts, post_links=post_links)


@main.route('/location_ajax')
def location_ajax():
    user_input = request.args['user_input']
    response = Location.Location.get_all_locations()
    locations = [location for location in response if re.search(user_input, location, re.IGNORECASE)]
    return render_template('load_locations.html', locations=locations[:3])


@main.route('/category_ajax')
def category_ajax():
    user_input = request.args['user_input']
    response = Page.Page.get_categories_and_subcategories()
    categories = [category for category, _ in response.iteritems() if re.search(user_input, category, re.IGNORECASE)]
    return render_template('load_categories.html', categories=categories[:5])

@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@main.app_errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


@main.app_errorhandler(405)
def server_error(e):
    return render_template('405.html'), 405

