import tkinter as tk
from tkinter import *
from essential_generators import DocumentGenerator
import time
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import date

"""
to do:
    remodel the sentance genarator:
        new and improved generation
        add extra language
        add different difficulties

    add charcount to Total_stats for more precise calculations
"""

#haldels data
class Data():

    #sets the referencetable, paragraphs and smaler variables 
    def __init__(self):

        #generates referencetable to be referenced when event.keysym != character symbol 
        # e.g. "a" == "a" / "-" == "minus"
        with open(r"C:\Users\david\Code\VS-Code\Neuer Ordner\Referencetable.txt", encoding="utf-8") as f:
            self.referencetable = dict(
                line.strip().split(" = ") for line in f if " = " in line
            )

        # px, for calculating text lenght
        self.char_spacing = 22 

        #used in total_average_mistakes
        self.words_completed = 1

        self.input_past_control = False
        self.initialised_fullscreen = False
        self.date = date.today()
        self.mistake_array = []
        self.total_average_wpm = 0

        #prepares textgeneration
        self.gen = DocumentGenerator()

        #X word are generated
        self.gen.init_word_cache(500)

        #X many cnetences are gnenrated
        self.gen.init_sentence_cache(500)

        #generates the paragraph 
        #spaceseeker is for chopping the paragraph into full words by looking for " "
        self.spaceseeker = 0

        self.definedText = []
        self.average_wpm_array = []

        #and makes sure the paragraph is long enough 
        while True:
            self.paragraph = self.gen.paragraph()
            if (len(self.paragraph)) > 100:
                break

        #generates exerpt (e.g. from paragraph[o] to paragraph[5])
        self.generateText(0,5)
    
    #cuts paragraph into exerpts 
    def generateText(self,rangemin,spaceseeker):
            
            self.definedText = []
            self.spaceseeker = spaceseeker
            
            while True:   

                #looks for the next space in paragraph
                if self.paragraph[self.spaceseeker] == " ":
                    break
                self.spaceseeker += 1

            #sets the defined text to the paragraph exerpt
            for i in range(rangemin,self.spaceseeker):
                self.definedText.append(self.paragraph[i])
            

#handels graphics and contents
class GUI():
    #sets the windowd with all its components exept the character wigets
    def __init__(self,controller):

        #controller gets past in the initialisation of GUI ->(self)<- in Controller()
        self.controller = controller

        #root is the main Window in wich every frame is drawn
        self.root = tk.Tk()
        self.root.geometry("800x500")

        #catches the close procedure and asks if you really want to close the window 
        #and calls on_closing on press of the "X" button
        self.root.protocol("WM_DELETE_WINDOW", self.controller.on_closing)

        #for switching the screens (frame,stat_frame) they have to be in the same container: root(container(frame,stat_frame))
        self.container = tk.Frame(self.root)
        self.container.pack(fill="both", expand=True)

        #frame is the main frame (game screen) 
        self.frame = Frame(self.container, bg="black")
        self.frame.place(relheight=1, relwidth=1)

        #stat_frame is the stat screen and both of them have to be placed on top of each 
        #other so that tk.rais() can call one of them to the front
        self.stat_frame = Frame(self.container, bg="black")
        self.stat_frame.place(relheight=1, relwidth=1)  

        #back_button is in the stat_frame
        self.back_button = Button(self.stat_frame,text="Back",activebackground="green",command=self.controller.show_main_frame,font=('Courier New',10),fg="black",bg="orange")
        self.back_button.place(x=0,y=0)
        
        """
        insert everything in stat_frame here
        """
        
        #makes it so that the main frame is above the stats frame
        self.frame.tkraise()

        #declairs the wpm labels 
        self.wpm_meter = Label(self.frame,text="WPM:  0",bg="black",fg="orange",font=('Courier New',20))
        self.average_wpm = Label(self.frame,text="average WPM:  0",fg="orange",bg="black",font=('Courier New',20))

        #sets the textbox so that the focus is on it but it is located out of the frame
        #so that you can tipe but cant see it 
        self.textbox = tk.Text(self.root,height = 0)
        self.textbox.place(y=2000) 
        self.textbox.bind("<KeyPress>", self.controller.handel_keypress)
        self.textbox.focus_set()

        self.stat_button = Button(self.frame,text="Stats",bg="orange",fg="black",activebackground="green",
                                  highlightcolor="orange",font=('Courier New',8),command=self.controller.show_stat_frame)
        self.stat_button.place(x=0,y=0)


#handels calculations, checks and coordination
class Controller():
    #initialises variabeles and delays set wigets()
    def __init__(self):

        #be mindfull not to acedentally call the classes again
        self.data = Data()
        self.gui = GUI(self)
        self.stat_manager = Stat_manager(self)

        self.in_stat_frame = False
        self.last_stat_frame_size = (self.gui.stat_frame.winfo_width(), self.gui.stat_frame.winfo_height())
        self.exit_fullscreen_var = False
        self.start_time = None

        # for debouncing
        self.resize_after_id = None
        self.last_size = (self.gui.root.winfo_width(), self.gui.root.winfo_height())

        # binds the scaling of the window to on_resize
        self.gui.root.bind("<Configure>", self.on_resize)

        #makes shure that gui had enougth time to set up so we get 
        #acess to the correct frame info
        self.gui.root.after(50, self.set_wigets)

    #calls set_WPM_Labels(), generateText() and generateCordinates()
    #so it can set the wigets in wigetarray and displays them
    def set_wigets(self):
        
        self.set_WPM_Labels()
        self.data.generateText(self.data.spaceseeker + 1,self.data.spaceseeker + 5)
        self.generateCordinates()

        #sets the wigitarray and displays it
        self.wigetarray = []
        for i in range(len(self.data.definedText)):
            wiget = Label(self.gui.frame,text=str(self.data.definedText[i]),fg="orange",bg="black",font=('Courier New', 25))
            wiget.place(x=self.cordinatarray[i],y=self.frame_height * 0.3)
            self.wigetarray.append(wiget)
    
    #handels the wpm timer, input reference and correction 
    def handel_keypress(self,event):

        self.len_textbox =len(self.gui.textbox.get('0.0',tk.END))
        
        #for WPM, starts of first input and ends on the generation of a new word
        #if event.keysym == self.data.defined_text[0] wäre geil aber sonsterzeichen und so
        if self.start_time == None:
            self.start_time = time.time()
        
        #delets the "f" input after going fullscreen (needs to be in front of the oter shit and idk why)
        if self.data.initialised_fullscreen == True:
            self.gui.textbox.delete("end-1c","end")
            self.data.initialised_fullscreen = False

        #checks if control has been pressed or not 
        if event.keysym == "Control_L":
            self.data.input_past_control = True
        
        if event.keysym not in ("Control_L","f"):
            self.data.input_past_control = False

        #when 'f' follows on control it will initialise the fullscreen
        if event.keysym == "f" and self.data.input_past_control == True:
            self.data.input_past_control = False
            self.handel_fullscreen()
            self.data.initialised_fullscreen = True
            
        #main input check when you are in the defined_text length and you havent gone to fullscreen
        if (len(self.data.definedText)>= self.len_textbox and self.data.initialised_fullscreen == False):
            self.check_input(event)

        #on backspace even if the max length has been reached
        elif event.keysym == 'BackSpace':
            self.input_return()

        #when the text is finished and input is not "BackSpace"
        #checks if the text is wrong
        else:
            self.textwrong = False
            for i in range(len(self.data.definedText)):
                    textboxiterator1=  "1." + str(i)  
                    textboxiterator2 =  "1." + str(i + 1)  
                    if self.gui.textbox.get(textboxiterator1,textboxiterator2) != self.data.definedText[i]:
                        self.textwrong = True

                        #so that only BackSpace is allowed as an input an no further text is written to the 
                        #textbox when the max lenght of defined_text has been reached
                        return "break"
                    
            #if the text is correct 
            if self.textwrong == False and event.keysym == "space":
                
                #handels the rest
                self.after_textcompetion()

            #bloch the input from being insertet in the textbox
            return 'break'

    #checks if the input is the same as the expected input
    def check_input(self,event):
        #checks if input is in referencetable
        for k, v in self.data.referencetable.items():

            #if it finds the keysym in referencetable
            if event.keysym == v:

                # if the definedText is equal to the coresponding string 
                if self.data.definedText[self.len_textbox - 1] == k:
                    self.inutCorrect()
                    break
                else:
                    self.hanel_mistakes(self.data.definedText[self.len_textbox - 1])
                    self.inputInorrect()
                    break
        else:
            #checks if the input is incorect
            if event.keysym not in ('Shift_L', 'BackSpace','Caps_Lock','Multi_key',"Control_L","space"):
                
                if self.data.definedText[self.len_textbox - 1] != event.keysym:
                    
                    #because otherwise space would be couted double
                    if self.data.definedText[self.len_textbox - 1] != " ":
                        self.inputInorrect()
                        self.hanel_mistakes(self.data.definedText[self.len_textbox - 1])
                    
                #on correct
                else:
                    self.inutCorrect()

            #extra rules for space
            if event.keysym == 'space':

                if self.data.definedText[self.len_textbox - 1] == ' ':

                    self.wigetarray[self.len_textbox - 1].config(text=" ")
                else:

                    self.hanel_mistakes(self.data.definedText[self.len_textbox - 1])
                    self.inputInorrect()
            else:

                if self.data.definedText[self.len_textbox - 1] == ' ':

                    if event.keysym != "BackSpace":

                        self.wigetarray[self.len_textbox - 1].config(fg="red",text="_")
                        self.hanel_mistakes("__")
            
            #on backspace
            if event.keysym == 'BackSpace':
                self.input_return()

    #checks if the text is corect, handels the WPM counter as well as general end of exerpt operations
    def after_textcompetion(self):

        self.data.words_completed += 1
        
        #generates new paragraph if the last one is exausted
        if self.data.spaceseeker + 15 >= len(self.data.paragraph):
            self.paragraph = self.data.gen.paragraph()
            self.data.spaceseeker = 10

        #mesures the words per minute
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        
        char_count = len(self.data.definedText)
        self.wpm = (char_count / 5) / (elapsed_time / 60)
        self.start_time = None

        #displays wpm
        self.gui.wpm_meter.config(text="WPM: "+str(math.floor(self.wpm)))

        self.data.average_wpm_array.append(self.wpm)
        
        #calculates the average wpm for the label
        cout_wpm_array = 0
        average_wpm = 0
        for i in self.data.average_wpm_array:
            cout_wpm_array += 1
            average_wpm += i

        #sets the total_average_wpm for the label
        self.data.total_average_wpm = math.floor(average_wpm / cout_wpm_array)
        self.gui.average_wpm.config(text="average WPM: " + str(self.data.total_average_wpm))

        #delets the contents of the textbox
        self.gui.textbox.delete('1.0','2.0')
        self.delete_wigets()
        self.set_wigets()

    #sets the currently last typed wiget to "orange"
    def input_return(self):

        #if the textbox is not empty it behaves diffrently because 
        #there is an extra inupt in textbox that has not been rendert  
        if self.len_textbox - 1 > 0:
            textboxposition = self.len_textbox - 2
        else:
            textboxposition = self.len_textbox - 1

        self.wigetarray[textboxposition].config(fg="orange")

    #sets the currently last typed wiget to "red"
    def inputInorrect(self):
        self.wigetarray[self.len_textbox - 1].config(fg="red")

    #sets the currently last typed wiget to "green"
    def inutCorrect(self):
        self.wigetarray[self.len_textbox - 1].config(fg="green")

    #generates the wiget coordinates to cordinatarray dynamicly bases on the screen width
    def generateCordinates(self):

        #makes shure the window is rendert before trying to get its data
        self.gui.root.update_idletasks()
        
        self.frame_width = self.gui.frame.winfo_width()
        self.frame_height = self.gui.frame.winfo_height()

        #could do it with the acual length of the text with winfo_reqwidth but its close enougth 
        self.total_width = len(self.data.definedText) * self.data.char_spacing
        self.cordinatarray  = []

        #sets the firstpos for the text to be geretated after this pos so that its centert 
        if len(self.data.definedText) % 2 == 0:
            firstpos = int((self.frame_width - self.total_width) / 2)
        else:
            firstpos = int((self.frame_width - (self.total_width + 1)) / 2)

        for i in range(len(self.data.definedText)):
            position = firstpos + i * self.data.char_spacing
            self.cordinatarray.append(position)

    #deletes almost everything in self.gui.frame == all character wigets (not wps Labels,button)
    def delete_wigets(self):
        
        for widget in self.gui.frame.winfo_children():
            if widget not in (self.gui.stat_button, self.gui.wpm_meter, self.gui.average_wpm):
                widget.destroy()
   
    #sets the wpm_Label coordinats dynamicly
    def set_WPM_Labels(self):
        
        frame_height = self.gui.frame.winfo_height()
        frame_width = self.gui.frame.winfo_width()

        total_wpm_meter_width = self.gui.wpm_meter.winfo_reqwidth()
        wpm_meter_pos = int((frame_width - total_wpm_meter_width) / 2)

        total_average_wpm_width = self.gui.average_wpm.winfo_reqwidth()
        average_wpm_pos = int((frame_width - total_average_wpm_width) / 2)

        self.gui.wpm_meter.place(x=wpm_meter_pos,y=int(frame_height * 0.62))
        self.gui.average_wpm.place(x=average_wpm_pos,y=int(frame_height * 0.75))

    #sets the window to fullscreen or back to window size if already in fullscreen
    def handel_fullscreen(self):

        self.fullscreen_var = False
        if self.gui.root.winfo_width() >= self.gui.root.winfo_screenwidth() - 10:
            self.fullscreen_var = True
            
        if self.fullscreen_var == False:
            self.gui.root.attributes("-fullscreen", True)

        else:
            self.gui.root.attributes("-fullscreen", False)

            self.gui.root.state("normal")  # if maximised
            self.gui.root.geometry("800x500")
        
    #when the window gets changed it triggers
    def on_resize(self,event):
        
        #checks if wigetarray exist so no error is thrown 
        if hasattr(controller,"wigetarray"):
            
            #stat_frame has a different rescaling process that gets called here
            if self.in_stat_frame:
                self.resize_after_id = self.gui.root.after(1500,self.handel_stat_resize)
                return
            
            new_size = (event.width, event.height)

            #only rezies if an acual new size is passed 
            if new_size != self.last_size:
                self.last_size = new_size

                #cancels the old resize if a new one is passed
                if self.resize_after_id:
                    self.gui.root.after_cancel(self.resize_after_id)

                #declares resize_after_id and calls handel_resize after waiting for 
                #the resize to happen and then the resize_after_id will be nulled
                self.resize_after_id = self.gui.root.after(5,self.handel_resize)
    
    #it recenters the Labels
    def handel_resize(self):
        
        self.set_WPM_Labels()
        self.generateCordinates()

        #places the text to be typed
        for i,widget in enumerate(self.wigetarray):
            widget.place(x= self.cordinatarray[i],y= self.frame_height * 0.3)
        
        self.resize_after_id = None

    #resizes stat_frame
    def handel_stat_resize(self):    

        new_size = (self.gui.stat_frame.winfo_width(), self.gui.stat_frame.winfo_height())
                
        #cancels the old resize if a new one is passed
        if self.resize_after_id:
            self.gui.root.after_cancel(self.resize_after_id)

        if new_size == self.last_stat_frame_size:
            self.resize_after_id = None
            return

        self.last_stat_frame_size = new_size
        self.delete_stat_frame()
        self.stat_manager.build_graph()
        self.resize_after_id = None

    #documents the mistakes and there frequency 
    def hanel_mistakes(self,char):

        #if the char is not in the array it gets added else the counter gets a +1
        for i in range(len(self.data.mistake_array)):
            if self.data.mistake_array[i][0] == char:
                self.data.mistake_array[i][1] += 1
                break
        else:
            self.data.mistake_array.append([char,1])

        #sorts the array so it looks cool in the graph :)
        self.mistake_array_sorter()

    #sorts the mistake_array via revers bubbel sorter
    def mistake_array_sorter(self):
       
        #goes through the entire array
        for i in range(len(self.data.mistake_array)):
            biggest_int = 0

            #skips the already sorted first positions by having the range be i->len(array)
            for u in range(i,(len(self.data.mistake_array))):
                if self.data.mistake_array[u][1] > biggest_int:
                    biggest_int = self.data.mistake_array[u][1]
                    biggest_int_index = u

            #the bigggest position gets put to the beginning of the array exerpt by 
            #switching the two poitions
            char_storage = self.data.mistake_array[i][0]
            int_storage = self.data.mistake_array[i][1]

            self.data.mistake_array[i][0] = self.data.mistake_array[biggest_int_index][0]
            self.data.mistake_array[i][1] = self.data.mistake_array[biggest_int_index][1]

            self.data.mistake_array[biggest_int_index][0] = char_storage
            self.data.mistake_array[biggest_int_index][1] = int_storage

    #raises the stat_frame to the foreground and calls related methods
    def show_stat_frame(self):
        
        self.in_stat_frame = True
        self.gui.stat_frame.tkraise()

        self.delete_stat_frame()
        self.stat_manager.handel_total_stats()

        self.stat_manager.build_graph()

    #raises the  main frame to the foreground
    def show_main_frame(self):

        self.handel_resize()
        self.in_stat_frame = False
        self.gui.frame.tkraise()
        self.gui.textbox.focus_set()

    #deletes the wigets in stat frame exept the button
    def delete_stat_frame(self):

        for wiget in self.gui.stat_frame.winfo_children():
            #the , is necesssary otherwise it will not cout as an tupe and break
            if wiget not in (self.gui.back_button,):
                wiget.destroy()

    #asks if you really want to close the window and calls handel_totla_stats
    def on_closing(self):

        self.stat_manager.handel_total_stats()
        if tk.messagebox.askokcancel("","Do you really want to quit?"):
            self.gui.root.destroy()


#manages the gui and relevant data in the stat_frame
class Stat_manager():
    
    #sets controller (be carefull not to create a new one with Controller())
    def __init__(self,controller):
        self.controller = controller
        self.frame = self.controller.gui.stat_frame

    #creates the graphs
    def build_graph(self):

        #generates the arrays for the total_stats graph
        self.set_total_stats_array()

        #set parameters, figsize is a rescaling var that makes the figs fit the frame
        # dpi = dotts per inch = resolution
        frame_width = self.controller.gui.stat_frame.winfo_width()
        frame_height = self.controller.gui.stat_frame.winfo_height()
        dpi = 100
        figsize = ((frame_width / dpi) / 2,((frame_height - 30) / dpi) / 2)

        # WPM graph---
        self.fig1 = plt.Figure(figsize= figsize, dpi=dpi)
        self.fig1.patch.set_facecolor('black')

        ax1 = self.fig1.add_subplot(111)
        ax1.plot(self.controller.data.average_wpm_array, marker='o', color='orange')
        ax1.set_title("WPM", color = "orange")
        ax1.tick_params(axis='x', colors='orange',length = 1)  
        ax1.tick_params(axis='y', colors='orange')  
        ax1.spines["left"].set_color("orange")
        ax1.spines["bottom"].set_color("orange")
        ax1.set_facecolor("black")

        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self.frame)
        self.canvas1.draw()

        #mistake graph----
        self.fig2 = plt.Figure(figsize= figsize, dpi=dpi)
        self.fig2.patch.set_facecolor('black')

        chars = [x[0] for x in self.controller.data.mistake_array]
        counts = [x[1] for x in self.controller.data.mistake_array]

        ax2 = self.fig2.add_subplot(111)
        ax2.bar(chars, counts, color='red')
        ax2.set_title("mistakes", color = "orange")
        ax2.tick_params(axis='x', colors='orange')  
        ax2.tick_params(axis='y', colors='orange')  
        ax2.spines["left"].set_color("orange")
        ax2.spines["bottom"].set_color("orange")
        ax2.set_facecolor("black")

        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.frame)
        self.canvas2.draw()

        #total stats graph---
        figsize = ((frame_width / dpi),((frame_height - 30) / dpi) / 2)

        self.fig3 = plt.Figure(figsize=figsize, dpi=dpi)
        self.fig3.patch.set_facecolor('black')

        ax3 = self.fig3.add_subplot(111)
        ax3.plot(self.date_array,self.WPM_array, marker='o', color='orange', zorder=2)
        ax3.set_title("Total stats", color="orange")
        ax3.tick_params(axis='x', colors='orange')
        ax3.tick_params(axis='y', colors='orange')
        ax3.patch.set_visible(False)
        ax3.set_ylabel("WPM",color="orange")

        
        # Twin-axie ax4
        ax4 = ax3.twinx()
        ax4.plot(self.date_array,self.mistakes_array, marker='o', color='red', zorder=1)
        ax4.set_facecolor("none")
        ax4.set_label("mistakes")
        ax4.tick_params(axis='y', colors='red')
        ax4.spines["right"].set_color("red")
        ax4.spines["left"].set_color("orange")
        ax4.spines["bottom"].set_color("orange")
        ax4.set_zorder(1)
        ax4.set_ylabel("av. mistakes",color="red")
        #ax4.legend(loc="upper left",facecolor="black",edgecolor="black",labelcolor="orange",bbox_to_anchor=(0.000001, 1),borderaxespad=0.)
        
        self.canvas3 = FigureCanvasTkAgg(self.fig3, master=self.frame)
        self.canvas3.draw()

        #places the canv(y?) in the frame 
        self.canvas1.get_tk_widget().place(x=frame_width * 0.0, y=(frame_height * 0.0) + 30)
        self.canvas2.get_tk_widget().place(x=frame_width * 0.5, y=(frame_height * 0.0) + 30)
        self.canvas3.get_tk_widget().place(x=-17, y=(frame_height * 0.5) + 10)
        
    #adds new day based entrys in Totals_stats
    def handel_total_stats(self):
        
        total_mistakes = 0
        previous_WPM = 0
        total_previous_mistakes = 0
        previous_words_written = 0

        #calculates the mistakes made in a session
        for i in range(len(self.controller.data.mistake_array)):
            total_mistakes = total_mistakes + self.controller.data.mistake_array[i][1]
        
        total_average_mistakes = round(total_mistakes/self.controller.data.words_completed,3)

        text = f"{self.controller.data.date} : average WPM= {self.controller.data.total_average_wpm} , mistakes= {total_average_mistakes} , words written= {self.controller.data.words_completed} \n"
        
        #checks all rows for the same date
        with open(r"C:\Users\david\Code\VS-Code\Neuer Ordner\Total_stats.txt","r",encoding="utf-8") as k:

            for row in k:

                #turns the String into an array
                row_exerpt = row.strip()
                row_exerpt = row_exerpt.split()

                if row.startswith(str(self.controller.data.date)):

                    #copys the wpm average 
                    for i in range(len(row_exerpt)):

                        if row_exerpt[i] == "WPM=":
                            previous_WPM = row_exerpt[i + 1]
                            break

                    #copys the words written
                    for i in range(len(row_exerpt)):

                        if row_exerpt[i] == "written=":
                            previous_words_written = row_exerpt[i + 1]
                            break

                    #copy the mistakes
                    for i in range(len(row_exerpt)):
                        if row_exerpt[i] == "mistakes=":
                            total_previous_mistakes = row_exerpt[i + 1]

                    #to prevent the average from going down if you never type
                    if self.controller.data.words_completed == 1:
                        self.controller.data.words_completed = int(previous_words_written)
                        self.controller.data.total_average_wpm = int(previous_WPM)
                        total_average_mistakes = round(float(total_previous_mistakes),3)

                    text = f"{self.controller.data.date} : average WPM= {math.floor((self.controller.data.total_average_wpm + int(previous_WPM))/2)} ,average mistakes= {round((float(total_average_mistakes) + float(total_previous_mistakes))/2,3)} , words written= {math.floor((int(previous_words_written) + self.controller.data.words_completed)/2)} \n"
                    break
            
        #prints to the txt---
        #reads all lines in the txt to lines
        with open(r"C:\Users\david\Code\VS-Code\Neuer Ordner\Total_stats.txt","r",encoding="utf-8") as k: 
            lines = k.readlines() 
        
        #deletes everything in Total_stats that has the same date or 
        #an WPS of 0
        with open(r"C:\Users\david\Code\VS-Code\Neuer Ordner\Total_stats.txt","w",encoding="utf-8") as k: 
            
            for line in lines:
                
                line_exerpt = line.strip()
                line_exerpt = line_exerpt.split()

                for i in range(len(line_exerpt)):
                    
                    if line_exerpt[i] == "WPM=":
                        if line_exerpt[i+1] != "0":
                            
                            #only writes lines that are not of the same day
                            #and dont have a WPM of 0
                            if not line_exerpt[0] == (str(self.controller.data.date)):
                                k.write(line)
                        break
                            
        with open(r"C:\Users\david\Code\VS-Code\Neuer Ordner\Total_stats.txt","a",encoding="utf-8") as k: 
           k.write(text)
    
    #reads the Total_stats txt to import all stats
    def set_total_stats_array(self):

        self.WPM_array = []
        self.mistakes_array = []
        self.date_array = []

        with open(r"C:\Users\david\Code\VS-Code\Neuer Ordner\Total_stats.txt","r",encoding="utf-8") as k:
            rows = k.readlines()

            for row in rows:

                #turns the string row to an array
                row_exerpt = row.strip()
                row_exerpt = row_exerpt.split()

                #copys the WPM
                for i in range(len(row_exerpt)):
                    if row_exerpt[i] == "WPM=":
                        self.WPM_array.append(int(row_exerpt[i + 1]))
                        break

                #copys the mistakes
                for i in range(len(row_exerpt)):
                    if row_exerpt[i] == "mistakes=":
                        self.mistakes_array.append(float(row_exerpt[i + 1]))
                        break

                self.date_array.append(row_exerpt[0])




if __name__ == "__main__":

    controller = Controller()
    controller.gui.root.mainloop()