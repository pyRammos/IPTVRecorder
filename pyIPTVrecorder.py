import vlc
from bottle import Bottle, run, get, post, request, static_file
import urllib.request
import urllib
import datetime
import configparser
import os
import sys

# Import Variables
playlist = ""
outputDir = ""

# Global Variables
user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
hdr = { 'User-Agent' : user_agent }
channels = []
urls = []
groups = []
unique_groups = []
channel_to_record = ""
url_to_record = ""
app=Bottle()

style = """

<html>
<head>
<style>
input[type=text] {
  width: 100%;
  padding: 12px 20px;
  margin: 8px 0;
  box-sizing: border-box;
}

input [type=button], input[type=submit], input[type=reset] {
  background-color: #4CAF50;
  border: none;
  color: white;
  padding: 15px 32px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 16px;
  margin: 4px 2px;
  cursor: pointer;
}

select {
  width: 100%;
  padding: 16px 20px;
  border: none;
  border-radius: 4px;
  background-color: #f1f1f1;
}

.styled-select {
   background: url(http://i62.tinypic.com/15xvbd5.png) no-repeat 96% 0;
   height: 29px;
   overflow: hidden;
   width: 240px;
}

select#soflow, select#soflow-color {
   -webkit-appearance: button;
   -webkit-border-radius: 2px;
   -webkit-box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.1);
   -webkit-padding-end: 20px;
   -webkit-padding-start: 2px;
   -webkit-user-select: none;
   background-image: url(http://i62.tinypic.com/15xvbd5.png), -webkit-linear-gradient(#FAFAFA, #F4F4F4 40%, #E5E5E5);
   background-position: 97% center;
   background-repeat: no-repeat;
   border: 1px solid #AAA;
   color: #555;
   font-size: inherit;
   margin: 20px;
   overflow: hidden;
   padding: 5px 10px;
   text-overflow: ellipsis;
   white-space: nowrap;
   width: 300px;
}



.black   { background-color: 779126; }
.slate   { background-color: #ddd; }
.slate select   { color: #000; }
.rounded {
   -webkit-border-radius: 20px;
   -moz-border-radius: 20px;
   border-radius: 20px;
}
</style>
</head>

"""


def debug(message):
    print (str(datetime.datetime.now()) + " --::-- " + str(message))

@app.route('/<filename:path>')
def send_static(filename):
    return static_file(filename, root='/')

@app.get('/category')
@app.get('/')
def select_category():
    html = ""
    html = html + "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">"
    html = html + style
    html = html + "<link rel=\"stylesheet\" href=\"https://www.w3schools.com/w3css/4/w3.css\">"
    html = html + "<form accept-charset=\"UTF-8\" action=\"/channel\" method=\"post\" class=\"w3-container\"> \n"
    html = html + "\t<select name=\"category\" id=\"soflow\">\n"
    for elements in unique_groups:
        html = html + "\t\t<option value = \"" + str(elements) + "\">" + str(elements) + "</option>\n"
    html = html + "\t</select>\n <br> \n"
    html = html + "\t<input type=\"submit\" value=\"Pick Category\">\n"
    html = html + "</form>"
    return html
@app.post('/channel')
def select_channel():
    selected_category = request.forms.getunicode('category')
    html = ""
    html = html + "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">"
    html = html + style
    html = html + "<link rel=\"stylesheet\" href=\"https://www.w3schools.com/w3css/4/w3.css\">"
    html = html + "<form action=\"/time\" method=\"post\" class=\"w3-container\"> \n"
    html = html + "\t<select name=\"channel\"  id=\"soflow\">\n"
    counter = 0
    for elements in groups:
        # print ("For channel [" + channels[counter] +" - Testing " + elements + " vs. " + selected_category + " and it is " + str(elements==selected_category))
        if (elements==selected_category):
            html = html + "\t\t<option value = \"" + str(counter) + "\">" + str(channels[counter]) + "</option>\n"
        counter=counter + 1
    html = html + "\t</select>\n <br> \n"
    html = html + "\t<input type=\"submit\" value=\"Pick Channel\">\n"
    html = html + "</form>"
    return html

@app.post('/time')
def select_time():
    selected_channel = int(request.forms.getunicode('channel'))
    global channel_to_record
    channel_to_record= channels[selected_channel]
    global url_to_record
    url_to_record = urls[selected_channel]
    html = ""
    html = html + "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">"
    html = html + style
    html = html + "<link rel=\"stylesheet\" href=\"https://www.w3schools.com/w3css/4/w3.css\">"
    html = html + "<form action=\"/record\" method=\"post\" class=\"w3-container\">  \n"
    html = html + "\t<p> \n"
    html = html + "\t\t<label for=\"title\">Title</label> \n \t\t <br>"
    html= html + "\t\t<input id=\"Title\" name=\"title\" type=\"text\" /> </br>"
    html = html + "\t<p> \n"
    html = html + "\t\t<label for=\"duration\">Duration (in minutes)</label> \n \t\t <br>"
    html = html + "\t\t<input name=\"duration\" id=\"duration \" type=\"text\" /> </br>\n"
    html = html + "\t<input value=\"Record\" type=\"submit\" />\n"
    html = html + "</form>"
    return html

@app.post('/record')
def record():
    title = request.forms.getunicode('title')
    duration_str = request.forms.getunicode('duration')
    try:
        duration = int(duration_str)
    except ValueError:
        return "Duration must be a number. You set it to " + duration_str+". Go back and try again"


    recordVideo(title,duration,url_to_record)
    return ("I will record " + channel_to_record + " from " + url_to_record + " as " + title + " for " + str(
        duration) + " minutes")

def loadlist():
    print ("Debug : Downloading playlist")
    req = urllib.request.Request(playlist, headers=hdr)
    response= urllib.request.urlopen(req)
    print("Debug : Openned URL")
    file = response.read()
    file = file.decode('UTF8')
    file = file.splitlines()
    #print(file)
    temp = 0
    for line in file:
        if (line[:7] == "#EXTINF"):

            name_tag_position = line.find("tvg-name")
            name_start = line.find("\"",name_tag_position)+1
            name_end = line.find("\"", name_start)

            group_tag_position = line.find("group-title")
            group_start = line.find("\"",group_tag_position)+1
            group_end = line.find("\"", group_start)
            # print(line)
            temp_channel = line[name_start:name_end]
            temp_group = line[group_start:group_end]
            channels.append(temp_channel)
            groups.append(temp_group)
            if temp_group not in unique_groups:
                unique_groups.append(temp_group)
            # print ( temp_channel+ " in category " + temp_group )

        if (line[:4] == "http"):
            urls.append(line)
            # print ("Name = " + channels[temp] + " link=" + urls[temp])
            temp=temp+1
        #print (temp)
        #if (temp>10):
        #    break

def recordVideo(title, duration, url):
    now = datetime.datetime.now()
    end = now + datetime.timedelta(minutes=duration)
    print("Starting at " + str(now))
    print("Will stop at " + str(end))
    today = now.isoformat()
    today = str(today[:10]).replace("-", "")
    today = today[2:]
    today = today + "-" + now.strftime('%a')
    streamName = title
    stream = url_to_record
    filename = outputDir+ "/" + title + "-" + today + ".mp4"
    print ("Will record to " + filename)
   # parameters = "sout=#transcode{vcodec=h264,acodec=mp4a,ab=128,channels=2,deinterlace,threads=4,vb=2000,venc=x264}:duplicate{dst=std{access=file,mux=mp4,dst='"+filename+"'"
    parameters = "sout=#transcode{vcodec=h264,acodec=mp4a,ab=128,channels=2,venc=x264}:duplicate{dst=std{access=file,mux=mp4,dst='"+filename+"'"

    caching_parameters = "--network-caching=5000"
    reconnect_parameters = "--http-reconnect"
    quiet_parameters = "--quiet"
    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new(stream, parameters, caching_parameters, reconnect_parameters, quiet_parameters)
    media.get_mrl()
    player.set_media(media)
    try:
        player.play()
    except Exception as e:
        debug("Cannot record from that stream")
        debug("Error = " + str(e))
        debug("/OpensWindowAndJumpsOut")
        exit(2)
    recording = True
    while recording:
        now = datetime.datetime.now()
        if str(player.get_state()) == "State.Ended":
            debug("Cannot record from that stream or connection lost")
            exit(1)
        if now > end:
            player.stop()
            debug("OK. We are done recording")
            exit(0)

try:
    pathname = os.path.abspath(os.path.dirname(sys.argv[0]))
    print ("Will read from " + pathname + "/settings.cfg")
    config = configparser.ConfigParser()
    config.read(pathname + "/settings.cfg")
    config = configparser.ConfigParser()
except Exception:
    print("Unable to load values from the config file. Check the file exists in the same directory as the script and it has the right format and values")
    exit(10)

playlist = str(config['DEFAULT']['playlist'])
outputDir = str(config['DEFAULT']['outputDir'])
loadlist()

run(app, host='localhost', port=8080)