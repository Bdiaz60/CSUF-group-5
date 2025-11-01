# Currently in progress. Using Google Gemini as a basis.
# Some of the basic AI code was taken from Google, though everything else was our work.

# 10.28.2025: Swapped to using generate_content_stream to input smaller chunks at a time.
# 10.29.2025: Added support for multiple users, added class for User
# 10.31.2025: Converted code into individually front-ended program for demo. Added weighted-sorting function to sort by weights based on user interaction. 

# Code allows user to input sample posts, combining them into a single string and summarizing all of their info.
# NOTE: may need to install google and gen-ai into program if not already done


from google import genai
import tkinter as tk
from tkinter import ttk
from operator import attrgetter
import random
import time

# variable initialization
userlist = []
userlistnamed = {}
selected3users = []
userlistsorted = []
i = "1"
counter = 0

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client() # If you're wondering, the API key is directly set as PC user variable right now. Remind me to share later.

root = tk.Tk()
root.title("AI-Generated Post Summarizer")
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



# frames for establishing user inputs and AI output
leftframe = tk.Frame(root, width=450, height=600,background="#D8D8D8")
leftframe.place(x=0,y=0)
rightframe = tk.Frame(root, width=450,height=600,background="gray")
rightframe.place(x=450,y=0)

# combobox to allow access to multiple users
usercomboboxlabel = tk.Label(leftframe,text="User:",background="#D8D8D8")
usercomboboxlabel.place(x=125,y=50)
usercomboboxval = tk.StringVar()
usercombobox = ttk.Combobox(leftframe, textvariable = usercomboboxval)
usercombobox['values'] = []
usercombobox.place(x=175,y=50)
usercombobox.bind('<<ComboboxSelected>>', lambda event: loaduserposts(userlistnamed[usercomboboxval.get()], [messagetextbox1, messagetextbox2, messagetextbox3, messagetextbox4, messagetextbox5], viewspinbox, likespinbox, commentspinbox))

# textboxes that can have their contents changed, represents user posts (up to 5)
textbox1label = tk.Label(leftframe, text="Message #1:",background="#D8D8D8")
textbox1label.place(x=25,y=100)
messagetextbox1 = tk.Entry(leftframe,width=50)
messagetextbox1.place(x=110,y=100)

textbox2label = tk.Label(leftframe, text="Message #2:",background="#D8D8D8")
textbox2label.place(x=25,y=175)
messagetextbox2 = tk.Entry(leftframe,width=50)
messagetextbox2.place(x=110,y=175)

textbox3label = tk.Label(leftframe, text="Message #3:",background="#D8D8D8")
textbox3label.place(x=25,y=250)
messagetextbox3 = tk.Entry(leftframe,width=50)
messagetextbox3.place(x=110,y=250)

textbox4label = tk.Label(leftframe, text="Message #4:",background="#D8D8D8")
textbox4label.place(x=25,y=325)
messagetextbox4 = tk.Entry(leftframe,width=50)
messagetextbox4.place(x=110,y=325)

textbox5label = tk.Label(leftframe, text="Message #5:",background="#D8D8D8")
textbox5label.place(x=25,y=400)
messagetextbox5 = tk.Entry(leftframe,width=50)
messagetextbox5.place(x=110,y=400)

# AI response variables, set to right half
airesponsevar = tk.StringVar()
airesponsevar.set('')
airesponsevar.set("AI Summary Text goes here.")
airesponsetextbox = tk.Label(rightframe,textvariable=airesponsevar,wraplength=445)
airesponsetextbox.pack()

# Spinboxes for weighted elements
viewspinboxtext = tk.Label(leftframe,text="Views:",background="#D8D8D8")
viewspinboxtext.place(x=15,y=555)
viewspinbox = tk.Spinbox(leftframe,width=10,from_=0,to=999999999999)
viewspinbox.place(x=55,y=555)

likespinboxtext = tk.Label(leftframe,text="Likes:",background="#D8D8D8")
likespinboxtext.place(x=150,y=555)
likespinbox = tk.Spinbox(leftframe,width=10,from_=0,to=999999999999)
likespinbox.place(x=190,y=555)

commentspinboxtext = tk.Label(leftframe,text="Comments:",background="#D8D8D8")
commentspinboxtext.place(x=285,y=555)
commentspinbox = tk.Spinbox(leftframe,width=10,from_=0,to=999999999999)
commentspinbox.place(x=355,y=555)

# Buttons for adding users, updating posts, and generating the AI summary
adduserbutton = tk.Button(leftframe,text="Add User", command=lambda:createuser(usercombobox))
adduserbutton.place(x=150,y=455)
updateuserbutton = tk.Button(leftframe,text="Update Posts", command=lambda:updateusercheck(usercomboboxval.get(), messagetextbox1.get(), messagetextbox2.get(), messagetextbox3.get(), messagetextbox4.get(), messagetextbox5.get(), viewspinbox, likespinbox, commentspinbox))
updateuserbutton.place(x=225,y=455)
generatesummarybutton = tk.Button(leftframe,text="Generate AI Summary", command=lambda:GenerateAISummary(airesponsevar))
generatesummarybutton.place(x=166,y=505)

root.mainloop()