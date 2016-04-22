import json, os, re, psycopg2, requests, random
from urllib import unquote_plus, quote
from PIL import Image, ImageDraw, ImageFont
import shutil, urllib, os, sys, datetime, requests, json
from slack import cache
from fontTools.ttLib import TTFont

def parse_text_into_params(text):
    text = unquote_plus(text).strip()
    text = text[:-1] if text[-1] == ";" else text

    params = text.split(";")

    title = params[0].strip()
    del params[0]

    subtitle = params[0].strip()
    del params[0]

    author = params[0].strip()
    del params[0]

    if len(params) > 0:
        image_code = params[0].strip()
        del params[0]
    else:
        image_code = str(random.randrange(1,41))

    if len(params) > 0:
        theme = params[0].strip()
        del params[0]
    else:
        theme = str(random.randrange(0,17))
    return title, subtitle, author, image_code, theme


def generate_image(title, topText, author, image_code, theme, guide_text_placement='bottom_right', guide_text='The Definitive Guide'):
    cache_string = title + "_" + topText + "_" + author + "_" + image_code + "_" + theme + "_" + guide_text_placement + "_" + guide_text

    cached = cache.get(cache_string)
    if cached:
        print "Cache hit"
        try:
            final_path = os.path.abspath(os.path.join(os.path.dirname( __file__ ), ('%s.png'%datetime.datetime.now())))
            width = 500
            height = 700
            im = Image.frombytes('RGBA', (width, height), cached)
            im.save(final_path)
            im.close()
            return final_path
        except Exception as e:
            print e.message
    else:
        print "Cache miss"

    themeColors = {
        "0" : (85,19,93,255),
        "1" : (113,112,110,255),
        "2" : (128,27,42,255),
        "3" : (184,7,33,255),
        "4" : (101,22,28,255),
        "5" : (80,61,189,255),
        "6" : (225,17,5,255),
        "7" : (6,123,176,255),
        "8" : (247,181,0,255),
        "9" : (0,15,118,255),
        "10" : (168,0,155,255),
        "11" : (0,132,69,255),
        "12" : (0,153,157,255),
        "13" : (1,66,132,255),
        "14" : (177,0,52,255),
        "15" : (55,142,25,255),
        "16" : (133,152,0,255),
    }
    themeColor = themeColors[theme]

    width = 500
    height = 700
    im = Image.new('RGBA', (width, height), "white")

    font_path = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'fonts', 'Garamond Light.ttf'))
    font_path_helv = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'fonts', 'HelveticaNeue-Medium.otf'))
    font_path_helv_bold = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'fonts', 'Helvetica Bold.ttf'))
    font_path_italic = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'fonts', 'Garamond LightItalic.ttf'))

    topFont = ImageFont.truetype(font_path_italic, 20)
    subtitleFont = ImageFont.truetype(font_path_italic, 34)
    authorFont = ImageFont.truetype(font_path_italic, 24)
    titleFont = ImageFont.truetype(font_path, 62)
    oriellyFont = ImageFont.truetype(font_path_helv, 28)
    questionMarkFont = ImageFont.truetype(font_path_helv_bold, 16)

    dr = ImageDraw.Draw(im)
    dr.rectangle(((20,0),(width-20,10)), fill=themeColor)

    topText = sanitzie_unicode(topText, font_path_italic)
    textWidth, textHeight = dr.textsize(topText, topFont)
    textPositionX = (width/2) - (textWidth/2)

    dr.text((textPositionX,10), topText, fill='black', font=topFont)

    author = sanitzie_unicode(author, font_path_italic)
    textWidth, textHeight = dr.textsize(author, authorFont)
    textPositionX = width - textWidth - 20
    textPositionY = height - textHeight - 20

    dr.text((textPositionX,textPositionY), author, fill='black', font=authorFont)

    oreillyText = "O RLY"

    textWidth, textHeight = dr.textsize(oreillyText, oriellyFont)
    textPositionX = 20
    textPositionY = height - textHeight - 20

    dr.text((textPositionX,textPositionY), oreillyText, fill='black', font=oriellyFont)

    oreillyText = "?"

    textPositionX = textPositionX + textWidth

    dr.text((textPositionX,textPositionY-1), oreillyText, fill=themeColor, font=questionMarkFont)

    titleFont, newTitle = clamp_title_text(sanitzie_unicode(title, font_path), width-80)
    if newTitle == None:
        raise ValueError('Title too long')

    textWidth, textHeight = dr.multiline_textsize(newTitle, titleFont)
    dr.rectangle([(20,400),(width-20,400 + textHeight + 40)], fill=themeColor)

    subtitle = sanitzie_unicode(guide_text, font_path_italic)

    if guide_text_placement == 'top_left':
        textWidth, textHeight = dr.textsize(subtitle, subtitleFont)
        textPositionX = 20
        textPositionY = 400 - textHeight - 2
    elif guide_text_placement == 'top_right':
        textWidth, textHeight = dr.textsize(subtitle, subtitleFont)
        textPositionX = width - 20 - textWidth
        textPositionY = 400 - textHeight - 2
    elif guide_text_placement == 'bottom_left':
        textPositionY = 400 + textHeight + 40
        textWidth, textHeight = dr.textsize(subtitle, subtitleFont)
        textPositionX = 20
    else:#bottom_right is default
        textPositionY = 400 + textHeight + 40
        textWidth, textHeight = dr.textsize(subtitle, subtitleFont)
        textPositionX = width - 20 - textWidth

    dr.text((textPositionX,textPositionY), subtitle, fill='black', font=subtitleFont)

    dr.multiline_text((40,420), newTitle, fill='white', font=titleFont)

    cover_image_path = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'images', ('%s.png'%image_code)))
    coverImage = Image.open(cover_image_path).convert('RGBA')

    offset = (80,40)
    im.paste(coverImage, offset, coverImage)

    final_path = os.path.abspath(os.path.join(os.path.dirname( __file__ ), ('%s.png'%datetime.datetime.now())))
    im.save(final_path)

    cache.set(cache_string, im.tobytes())
    im.close()

    return final_path

def clamp_title_text(title, width):
    im = Image.new('RGBA', (500,500), "white")
    dr = ImageDraw.Draw(im)

    font_path_italic = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'fonts', 'Garamond Light.ttf'))
    #try and fit title on one line
    font = None

    startFontSize = 80
    endFontSize = 61

    for fontSize in range(startFontSize,endFontSize,-1):
        font = ImageFont.truetype(font_path_italic, fontSize)
        w, h = dr.textsize(title, font)

        if w < width:
            return font, title

    #try and fit title on two lines
    startFontSize = 80
    endFontSize = 34

    for fontSize in range(startFontSize,endFontSize,-1):
        font = ImageFont.truetype(font_path_italic, fontSize)

        for match in list(re.finditer('\s',title, re.UNICODE)):
            newTitle = u''.join((title[:match.start()], u'\n', title[(match.start()+1):]))
            substringWidth, h = dr.multiline_textsize(newTitle, font)

            if substringWidth < width:
                return font, newTitle

    im.close()

    return None, None

def sanitzie_unicode(string, font_file_path):
    sanitized_string = u''

    font = TTFont(font_file_path)
    cmap = font['cmap'].getcmap(3,1).cmap
    for char in string:
        code_point = ord(char)

        if code_point in cmap.keys():
            sanitized_string = unicode.join(u'',(sanitized_string,char))

    return sanitized_string

def save_team_token(team_id, token):
    DATABASE_NAME = os.environ.get("DATABASE_NAME").strip()
    DATABASE_USER_NAME = os.environ.get("DATABASE_USER_NAME").strip()
    DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD").strip()
    try:
        conn = psycopg2.connect(database=DATABASE_NAME, user=DATABASE_USER_NAME, password=DATABASE_PASSWORD, host="ec2-54-235-85-65.compute-1.amazonaws.com", port="5432")
        cur = conn.cursor()
        TOKENS_TABLE_NAME = os.environ.get("TOKENS_TABLE_NAME").strip()
        if check_team_token(team_id, cur) == True:
            statement = "UPDATE %s SET token='%s' WHERE team_id='%s'"%(TOKENS_TABLE_NAME,token,team_id)
        else:
            statement = "INSERT INTO %s (team_id,token) VALUES ('%s','%s')"%(TOKENS_TABLE_NAME,team_id, token)
        print statement
        cur.execute(statement)
        conn.commit()
        conn.close()
    except Exception as e:
        print "Unexpected error:", e.message
        raise e

def get_team_token(team_id):
    DATABASE_NAME = os.environ.get("DATABASE_NAME").strip()
    DATABASE_USER_NAME = os.environ.get("DATABASE_USER_NAME").strip()
    DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD").strip()
    try:
        conn = psycopg2.connect(database=DATABASE_NAME, user=DATABASE_USER_NAME, password=DATABASE_PASSWORD, host="ec2-54-235-85-65.compute-1.amazonaws.com", port="5432")
        cur = conn.cursor()
        TOKENS_TABLE_NAME = os.environ.get("TOKENS_TABLE_NAME").strip()
        statement = "SELECT token FROM %s WHERE team_id='%s'"%(TOKENS_TABLE_NAME,team_id)
        print statement
        cur.execute(statement)
        row = cur.fetchone()
        conn.close()
        return row[0]
    except Exception as e:
        print "Unexpected error:", e.message
        return None

def check_team_token(team_id, cur):
    TOKENS_TABLE_NAME = os.environ.get("TOKENS_TABLE_NAME").strip()
    cur.execute("SELECT team_id FROM %s WHERE team_id = '%s'"%(TOKENS_TABLE_NAME,team_id))
    return cur.fetchone() is not None

def save_team_bot(team_id, bot_user_id, bot_access_token):
    try:
        conn = psycopg2.connect(database="d1gj7v4n22uqdg", user="fihlxuqpdlhwmd", password="TfByIA-n-mJFkp66NvoZWYCeMz", host="ec2-54-235-85-65.compute-1.amazonaws.com", port="5432")
        cur = conn.cursor()
        BOT_TABLE_NAME = os.environ.get("BOT_TABLE_NAME").strip()
        if check_team_bot(team_id, cur) == True:
            statement = "UPDATE %s SET bot_user_id='%s',bot_access_token='%s' WHERE team_id='%s'"%(BOT_TABLE_NAME,bot_user_id,bot_access_token, team_id)
        else:
            statement = "INSERT INTO %s (team_id,bot_user_id,bot_access_token) VALUES ('%s','%s','%s')"%(BOT_TABLE_NAME,team_id, bot_user_id,bot_access_token)
        print statement
        cur.execute(statement)
        conn.commit()
        conn.close()
    except Exception as e:
        print "Unexpected error:", e.message
        raise e

def get_team_bot(team_id):
    try:
        conn = psycopg2.connect(database="d1gj7v4n22uqdg", user="fihlxuqpdlhwmd", password="TfByIA-n-mJFkp66NvoZWYCeMz", host="ec2-54-235-85-65.compute-1.amazonaws.com", port="5432")
        cur = conn.cursor()
        BOT_TABLE_NAME = os.environ.get("BOT_TABLE_NAME").strip()
        statement = "SELECT bot_user_id,bot_access_token FROM %s WHERE team_id='%s'"%(BOT_TABLE_NAME,team_id)
        print statement
        cur.execute(statement)
        row = cur.fetchone()
        conn.close()
        if row is not None:
            return row[0], row[1]
        else:
            return None, None
    except Exception as e:
        print "Unexpected error:", e.message
        return None, None

def check_team_bot(team_id, cur):
    BOT_TABLE_NAME = os.environ.get("BOT_TABLE_NAME").strip()
    cur.execute("SELECT team_id FROM %s WHERE team_id = '%s'"%(BOT_TABLE_NAME,team_id))
    return cur.fetchone() is not None
