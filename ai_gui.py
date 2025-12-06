from ai_captioner import generate_srt_from_video
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from operator import attrgetter
import random
import time
from google import genai
from google.genai import types

#video_path = "C:/Users/joehu/Downloads/project/screen-rec.mp4"           # your screen recording file
srt_output = "test_output.srt"

# variable initialization
userlist = []
userlistnamed = {}
selected3users = []
userlistsorted = []
i = "1"
counter = 0


# file bool modifications
def UploadStatus(filestatus: int)->int:
    """Rejects a file from being uploaded
        Args:
            filestatus: integers determining upload status of given text/file. (CODE: 0 = Reject Upload, 1 = Accept Upload, 2 = Anything Else)
    """
    global scanvariable
    print("give us a sign!", filestatus)
    if filestatus == 0:
        scanvariable = 0
        return 0
    elif filestatus == 1:
        scanvariable = 1
        return 1
    else:
        scanvariable = 2
        return 2


# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client() # If you're wondering, the API key is directly set as PC user variable right now. Remind me to share later.
config = types.GenerateContentConfig(tools=[UploadStatus]) # adjusts config to use UploadStatus

root = tk.Tk()
root.title("AI Functionality Demonstration GUI")
root.geometry("900x600")
root.resizable(False, False)

class User:
    def __init__(self, username, userid):
        global counter 
        self.username = username
        self.userid = userid
        self.post = ['','','','',''] # list of strings (potential queue implenetation down the line?)
        self.views = 0
        self.likes = 0
        self.comments = 0
        self.weight = 0
        # self.postdate = {} # dictionary for posts containing date:(# of posts), won't include for the time being for simplicity's sake
        # self.followinglist = [] # random assortment of who the user follows
        counter += 1
        userlist.append(self)
        userlistnamed[self.username] = self
        
    def calculateweight(self):
        self.weight = (self.views)+(self.likes*3)+(self.comments*10)


def sortuserlist():
    global userlistsorted
    for user in userlist:
        user.calculateweight()
    userlistsorted = sorted(userlist, key=attrgetter('weight'))
    userlistsorted.reverse()




def updateuserlist(combobox): # updates list of users
    combobox['values'] = list(userlistnamed.keys())

def createuser(combobox): # opens a new window to let user input a new name for a new user
    usertoplevel = tk.Toplevel()
    usertoplevel.geometry("180x140")
    usertoplevel.resizable(False, False)
    usertoplevel.title("Create New User")

    createuserprompt = tk.Label(usertoplevel, text="Enter the new user's name.")
    createuserprompt.grid(row=0,column=0,padx=10,pady=10)

    newusertext = tk.Entry(usertoplevel)
    newusertext.grid(row=1,column=0,padx=10,pady=10)

    def confirmuser(username, userid, combobox): # creates new user and closes this window
        User(username, userid)
        updateuserlist(combobox)
        usertoplevel.destroy()

    confirmuserbutton = tk.Button(usertoplevel,text="Confirm",command=lambda:confirmuser(newusertext.get(), counter, combobox))
    confirmuserbutton.grid(row=2,column=0,padx=10,pady=10)
    usertoplevel.grab_set()


def updateusercheck(selecteduser, msg1, msg2, msg3, msg4, msg5, viewpass, likepass, commentpass): # checks for parameter validity before executing updateuserposts
    try:
        updateuserposts(userlistnamed[selecteduser], msg1, msg2, msg3, msg4, msg5, viewpass, likepass, commentpass)
    except:
        print("ERROR: Invalid user selected.")

def updateuserposts(selecteduser, msg1, msg2, msg3, msg4, msg5, viewpass, likepass, commentpass): # resets post attribute and appends messages to each one
    selecteduser.post = []
    selecteduser.post.append(msg1)
    selecteduser.post.append(msg2)
    selecteduser.post.append(msg3)
    selecteduser.post.append(msg4)
    selecteduser.post.append(msg5)
    selecteduser.views = int(viewpass.get())
    selecteduser.likes = int(likepass.get())
    selecteduser.comments = int(commentpass.get())
    
def loaduserposts(selecteduser, msglist, viewpass, likepass, commentpass): # loads saved post values for each user
    for index in range(len(msglist)):
        msglist[index].delete(0,tk.END)
        msglist[index].insert(0,selecteduser.post[index])
    viewpass.delete(0,tk.END)
    viewpass.insert(0,selecteduser.views)
    likepass.delete(0,tk.END)
    likepass.insert(0,selecteduser.likes)
    commentpass.delete(0,tk.END)
    commentpass.insert(0,selecteduser.comments)


def GenerateAISummary(responsevar): # function to generate AI summary
    selected3users = []
    responsevar.set('')
    if len(userlist) == 0: # checks to see if there are any users at all
        responsevar.set("No users to generate summary from.")
    else: 
        if len(userlist) <= 3: # skips randomization if there are <= 3 users
            for indexeduser in userlist:
                selected3users.append(indexeduser)

        else:
            sortuserlist()
            for user in userlistsorted:
                if len(selected3users) < 3:
                    selected3users.append(user)

        # prepares the summary to be prompted by the AI
        summaryrequest = 'Summarize the following posts from the given users with their username given in brackets. Keep the final summary to one paragraph and add a line break between each user. Always open each line with the corresponding username surrounded by square brackets (this is not part of the actual summary). Only talk about non-empty entries. Do not directly restate the posts of each user if more can be said.  If there is no text after the colon, only state "There is no available post data": ' # creating prompt to input into Gemini
        for user in selected3users: # process of adding everything to the summaryrequest for the prompt
            summaryrequest += f" [{user.username}] " 
            for post in user.post:
                summaryrequest += post + " , "
        print(summaryrequest)

        # actually inputs everything into the AI
        response = client.models.generate_content_stream(
                model="gemini-2.5-flash", contents=summaryrequest # setting contents to summaryrequest for the full prompt
        )
        for postinput in response: # loop iterating to output text
                if postinput.text: # scans for text in postinput chunks and outputs it
                    responsevar.set(responsevar.get()+postinput.text)





# selects file to upload from PC
def SelectFile(textboxvar):
    setfile = filedialog.askopenfilename()
    textboxvar.set(setfile)


def ScanFile(filepath, responsevar):
    global srt_output
    responsevar.set('')
    newresponse = ""
    video_path = str(filepath.get())
    #try:
    result = generate_srt_from_video(
        video_path,
        srt_output,
        use_asr="whisper",          # or "vosk"
        whisper_model="tiny",      # choose "tiny", "small", "medium", "large-v3"
        burn_into_video=False       # leave False for now
    )

    newresponse = "SRT created:",str(result)
    responsevar.set(newresponse)

    #except:
    #    responsevar.set('Subtitle creation failed.')

scanvariable = 1
# scans posts for any bad content
def HarmScanText(textboxvar, responsevar):
    responsevar.set('')
    textmodified = str(textboxvar.get())
    textcheck = "Check the following text for any blood, gore, nudity, sexual content, or threats/incitement of violence. Use the given tools to reject or accept the given input based on the above criteria :"+textmodified
     # actually inputs everything into the AI
    response = client.models.generate_content_stream(
            model="gemini-2.5-flash", contents=textcheck, # setting contents to summaryrequest for the full prompt
            config=config
    )
    for postinput in response: # loop iterating to output text
            if postinput.text: # scans for text in postinput chunks and outputs it
                responsevar.set(responsevar.get()+postinput.text)

    if scanvariable == 0:
        responsevar.set('Upload rejected.')
    elif scanvariable == 1:
        responsevar.set('Upload successful.')
    else:
        responsevar.set('Upload error detected.')


# scans files for any bad content
def HarmScanFile(filepath, responsevar):
    responsevar.set('')
    newresponse = ""
    filepathmodified = str(filepath.get())
    
    try:
        targetfile = client.files.upload(file=filepathmodified)
    except Exception as e: # chatgpt modified except block to show what the error is
        errortext = (f"Upload failed: {e}")
        responsevar.set(errortext)
    
    filecheck = "Check the following image/video for any blood, gore, nudity, sexual content, or threats/incitement of violence. This includes any depictions or imitations of these."
     # actually inputs everything into the AI
    response = client.models.generate_content_stream(
            model="gemini-2.5-flash", contents=[targetfile, filecheck] # setting contents to summaryrequest for the full prompt
    )
    for postinput in response: # loop iterating to output text
            if postinput.text: # scans for text in postinput chunks and outputs it
                responsevar.set(responsevar.get()+postinput.text)
                newresponse += postinput.text
                newresponse += " "

    newfilecheck = "Use the given tools as well as your given assessment to accept or reject the input. If there is anything matching the description from before, reject the input.: " + newresponse
    print(newfilecheck)
    updatedresponse = client.models.generate_content_stream(
        model="gemini-2.5-flash", contents=newfilecheck, # setting contents to summaryrequest for the full prompt
        config=config
    )
    
    responsevar.set('')
    for postinput in updatedresponse: # loop iterating to output text
        if postinput.text: # scans for text in postinput chunks and outputs it
            responsevar.set(responsevar.get()+postinput.text)
            print()

    if scanvariable == 0:
        print("wheat")
        responsevar.set('Upload rejected.')
    elif scanvariable == 1:
        print("bread")
        responsevar.set('Upload successful.')
    else:
        print("toast")
        responsevar.set('Upload error detected.')









# frames for establishing user inputs and AI output
leftframe = tk.Frame(root, width=450, height=600,background="#D8D8D8")
leftframe.place(x=0,y=0)
rightframe = tk.Frame(root, width=450,height=600,background="gray")
rightframe.place(x=450,y=0)

# tabs
tabs = ttk.Notebook(leftframe)
summtab = ttk.Frame(tabs)
substab = ttk.Frame(tabs)
harmtab = ttk.Frame(tabs)

tabs.add(summtab, text="Summarizer")
tabs.add(substab, text="Subtitler")
tabs.add(harmtab, text="Scanner")
tabs.pack(expand=1,fill='both')







summfactor = tk.Frame(summtab, width=450,height=600)
summfactor.pack()

# combobox to allow access to multiple users
usercomboboxlabel = tk.Label(summfactor,text="User:",background="#D8D8D8")
usercomboboxlabel.place(x=125,y=50)
usercomboboxval = tk.StringVar()
usercombobox = ttk.Combobox(summfactor, textvariable = usercomboboxval)
usercombobox['values'] = []
usercombobox.place(x=175,y=50)
usercombobox.bind('<<ComboboxSelected>>', lambda event: loaduserposts(userlistnamed[usercomboboxval.get()], [messagetextbox1, messagetextbox2, messagetextbox3, messagetextbox4, messagetextbox5], viewspinbox, likespinbox, commentspinbox))

# textboxes that can have their contents changed, represents user posts (up to 5)
textbox1label = tk.Label(summfactor, text="Message #1:",background="#D8D8D8")
textbox1label.place(x=25,y=100)
messagetextbox1 = tk.Entry(summfactor,width=50)
messagetextbox1.place(x=110,y=100)

textbox2label = tk.Label(summfactor, text="Message #2:",background="#D8D8D8")
textbox2label.place(x=25,y=175)
messagetextbox2 = tk.Entry(summfactor,width=50)
messagetextbox2.place(x=110,y=175)

textbox3label = tk.Label(summfactor, text="Message #3:",background="#D8D8D8")
textbox3label.place(x=25,y=250)
messagetextbox3 = tk.Entry(summfactor,width=50)
messagetextbox3.place(x=110,y=250)

textbox4label = tk.Label(summfactor, text="Message #4:",background="#D8D8D8")
textbox4label.place(x=25,y=325)
messagetextbox4 = tk.Entry(summfactor,width=50)
messagetextbox4.place(x=110,y=325)

textbox5label = tk.Label(summfactor, text="Message #5:",background="#D8D8D8")
textbox5label.place(x=25,y=400)
messagetextbox5 = tk.Entry(summfactor,width=50)
messagetextbox5.place(x=110,y=400)

# Spinboxes for weighted elements
viewspinboxtext = tk.Label(summfactor,text="Views:",background="#D8D8D8")
viewspinboxtext.place(x=15,y=555)
viewspinbox = tk.Spinbox(summfactor,width=10,from_=0,to=999999999999)
viewspinbox.place(x=55,y=555)

likespinboxtext = tk.Label(summfactor,text="Likes:",background="#D8D8D8")
likespinboxtext.place(x=150,y=555)
likespinbox = tk.Spinbox(summfactor,width=10,from_=0,to=999999999999)
likespinbox.place(x=190,y=555)

commentspinboxtext = tk.Label(summfactor,text="Comments:",background="#D8D8D8")
commentspinboxtext.place(x=285,y=555)
commentspinbox = tk.Spinbox(summfactor,width=10,from_=0,to=999999999999)
commentspinbox.place(x=355,y=555)

# Buttons for adding users, updating posts, and generating the AI summary
adduserbutton = tk.Button(summfactor,text="Add User", command=lambda:createuser(usercombobox))
adduserbutton.place(x=150,y=455)
updateuserbutton = tk.Button(summfactor,text="Update Posts", command=lambda:updateusercheck(usercomboboxval.get(), messagetextbox1.get(), messagetextbox2.get(), messagetextbox3.get(), messagetextbox4.get(), messagetextbox5.get(), viewspinbox, likespinbox, commentspinbox))
updateuserbutton.place(x=225,y=455)
generatesummarybutton = tk.Button(summfactor,text="Generate AI Summary", command=lambda:GenerateAISummary(airesponsevar))
generatesummarybutton.place(x=166,y=505)










# textboxes that can have their contents changed, represents user posts (up to 5)
subsfactor = tk.Frame(substab, width=450,height=600)
subsfactor.pack()


fileselectbutton = tk.Button(subsfactor,text="Browse...", command=lambda:SelectFile(filetextvar))
fileselectbutton.place(x=166,y=265)
filetextvar = tk.StringVar()
filetext = tk.Entry(subsfactor, width=60, textvariable=filetextvar, state='readonly')
filetext.place(x=50,y=235)
filescanbutton = tk.Button(subsfactor,text="Scan File", command=lambda:ScanFile(filetextvar, airesponsevar))
filescanbutton.place(x=166,y=295)







# textboxes that can have their contents changed, represents user posts (up to 5)
harmfactor = tk.Frame(harmtab, width=450,height=600)
harmfactor.pack()

textboxharmlabel = tk.Label(harmfactor, text="Example Post:",background="#D8D8D8")
textboxharmlabel.place(x=25,y=100)

harmmessagetextboxvar = tk.StringVar()
harmmessagetextbox = tk.Entry(harmfactor,width=50, textvariable=harmmessagetextboxvar)
harmmessagetextbox.place(x=110,y=100)
harmfileselectbutton = tk.Button(harmfactor,text="Text Check", command=lambda:HarmScanText(harmmessagetextboxvar, airesponsevar))
harmfileselectbutton.place(x=166,y=150)

harmfileselectbutton = tk.Button(harmfactor,text="Browse...", command=lambda:SelectFile(harmfiletextvar))
harmfileselectbutton.place(x=166,y=505)
harmfiletextvar = tk.StringVar()
harmfiletext = tk.Entry(harmfactor, width=60, textvariable=harmfiletextvar, state='readonly')
harmfiletext.place(x=50,y=455)
harmfilescanbutton = tk.Button(harmfactor,text="Scan File", command=lambda:HarmScanFile(harmfiletextvar, airesponsevar))
harmfilescanbutton.place(x=166,y=555)










# AI response variables, set to right half
airesponsevar = tk.StringVar()
airesponsevar.set('')
airesponsevar.set("Action output (AI) goes here.")
airesponsetextbox = tk.Label(rightframe,textvariable=airesponsevar,wraplength=445)
airesponsetextbox.pack()




root.mainloop()
