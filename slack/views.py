from flask import Flask, render_template, request, url_for, send_from_directory, redirect, send_file, jsonify
from models import parse_text_into_params, save_team_token, get_team_token, save_team_bot, get_team_bot, generate_image
from slacker import *
import shutil, urllib, os, sys, datetime, requests, json, random, datetime
from slack import app

@app.route('/authorize')
def authorize():
    try:
        if 'error' in request.args:
            return redirect('http://dev.to/rlyslack', code=302)
        code = request.args['code']

        SLASH_CLIENT_ID = os.environ.get("SLACK_CLIENT_ID").strip()
        SLASH_CLIENT_SECRET = os.environ.get("SLACK_CLIENT_SECRET").strip()
        oauthDict = {
            'client_id': SLASH_CLIENT_ID,
            'client_secret': SLASH_CLIENT_SECRET,
            'code': code
        }
        res = requests.post('https://slack.com/api/oauth.access', data=oauthDict)
        json_response = res.json()

        print json_response

        team_id = json_response['team_id']
        token = json_response['access_token']
        if 'bot' in json_response:
            bot = json_response['bot']
            bot_user_id = bot['bot_user_id']
            bot_access_token = bot['bot_access_token']
            save_team_bot(team_id, bot_user_id, bot_access_token)

        save_team_token(team_id, token)

        return redirect('http://dev.to/rlyslack', code=302)
    except Exception as e:
        print "Unexpected error:", e.message
        return "Failed:", 500

@app.route("/orly", methods=['POST'])
def orly():
    print request.form
    if not request.form:
        message = """
        Bad Request, Try Again
        """

        return message, 401

    try:
        token = request.form["token"]
        text = request.form["text"]
        # print "text is : ", text
        is_private_channel = request.form["channel_name"] == 'privategroup'
        channel_id = request.form["channel_id"]
        team_id = request.form["team_id"]
        user_name = request.form["user_name"]

        SLASH_COMMAND_TOKEN = os.environ.get("SLACK_SLASH_COMMAND_TOKEN").strip()

        if token != SLASH_COMMAND_TOKEN:
            return "Unauthorized."
        title, topText, author, image_code, theme = parse_text_into_params(text)
    except Exception as e:
        print "Unexpected error:", e.message
        return "Failed: Invalid Parameters", 500

    print "generating image"
    try:
        final_path = generate_image(title, topText, author, image_code, theme)
    except Exception as e:
        print "Unexpected error:", e.message
        return "Failed", 500
    print "image generated"

    try:
        file_name = '%s.png'%datetime.datetime.now()
        file_title = "Posted by %s"%user_name

        slack = Slacker(get_team_token(team_id))
        bot_user_id, bot_access_token = get_team_bot(team_id)

        if bot_access_token is not None:
            bot = Slacker(bot_access_token)
            if is_private_channel:
                response = bot.groups.list()
                groups = response.body['groups']
                print groups
                invited = False
                if groups is not None:
                    for group in groups:
                        if channel_id == group['id']:
                            invited = True
                            break
                if invited == False:
                    slack.groups.invite(channel_id, bot_user_id)

            response = bot.files.upload(final_path, filename=file_name, title=file_title, channels=[channel_id])
        else:
            response = slack.files.upload(final_path, filename=file_name, title=file_title, channels=[channel_id])

        if response.successful:
            print "Succesfully uploaded file"
            return "Success", 200
        else:
            print "Error uploading file"
            print response.error
            return "Failed: Error uploading file", 500
    except Exception as e:
        print "Unexpected error:", e.message
        return "Failed", 500
    finally:
        os.remove(final_path)


@app.route("/generate", methods=['GET'])
def generate():
    if not request.args:
        message = """
        Bad Request, Try Again
        """

        return message, 401

    try:
        print 'generate image'
        body = request.args
        print body
        if 'title' in body and 'top_text' in body and 'author' in body and 'image_code' in body and 'theme' in body:
            title = body['title']
            top_text = body['top_text']
            author = body['author']
            image_code = body['image_code']
            theme = body['theme']

            if 'guide_text' in body:
                guide_text = body['guide_text']
            else:
                guide_text = 'The Definitive Guide'

            if 'guide_text_placement' in body:
                guide_text_placement = body['guide_text_placement']
            else:
                guide_text_placement = 'bottom_right'
        else:
            return "Failed: Invalid Params", 401

    except Exception as e:
        print "Unexpected error:", e.message
        return "Unexpected Error", 500

    try:
        print "generating image"
        final_path = generate_image(title, top_text, author, image_code, theme, guide_text_placement=guide_text_placement, guide_text=guide_text)
        print "image generated"
        return send_file(final_path, mimetype='image/png', cache_timeout=604800)#604800 is one week in seconds
    except Exception as e:
        print "Unexpected error:", e.message
        return "Failed", 500
    finally:
        if os.path.isfile(final_path):
            print 'removing file'
            os.remove(final_path)
