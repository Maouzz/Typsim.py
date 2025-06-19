import tkinter as tk
from tkinter import *
from essential_generators import DocumentGenerator
import time
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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

        self.input_past_control = False

        self.initialised_fullscreen = False

        self.average_mistakes = 0
        self.mistake_array = []

        #prepares textgeneration
        self.gen = DocumentGenerator()

        #X word are generated
        self.gen.init_word_cache(500)

        #X many cnetences are gnenrated
        self.gen.init_sentence_cache(500)

        #generates the paragraph 
        #and makes sure the paragraph is long enough 
        while True:
            self.paragraph = self.gen.paragraph()
            if (len(self.paragraph)) > 100:
                break

        #spaceseeker is for chopping the paragraph into full words by looking for " "
        self.spaceseeker = 0
        self.definedText = []
        self.average_wpm_array = []

        #generates exerpt (e.g. from paragraph[o] to paragraph[5])
        self.generateText(0,5)
    
    #cuts paragraph into exerpts 
    def generateText(self,rangemin,spaceseeker):
            self.definedText = []
            self.spaceseeker = spaceseeker
            
            
            while True:   
                #looks for the next space in paragraph
                if self.paragraph[self.spaceseeker] != " ":
                    self.spaceseeker += 1

                else:
                    break

            #sets the defined text to the paragraph exerpt
            for i in range(rangemin,self.spaceseeker):
                self.definedText.append(self.paragraph[i])
            

#handels graphics and inputs
class GUI():
    #sets the window with all its components exept the character wigets
    def __init__(self,controller):

        self.controller = controller

        self.root = tk.Tk()
        self.root.geometry("800x500")

        self.fullscreen = False

        self.root.bind("<Multi_key>", controller.handel_fullscreen)

        #for switching the screens (frame,stat_frame)
        self.container = tk.Frame(self.root)
        self.container.pack(fill="both", expand=True)

        self.frame = Frame(self.container, bg="black")
        self.frame.place(relheight=1, relwidth=1)

        self.stat_frame = Frame(self.container, bg="black")
        self.stat_frame.place(relheight=1, relwidth=1)

        self.stat_button = Button(self.stat_frame,text="Back",command=self.controller.show_main_frame,font=('Courier New',10),fg="black",bg="orange")
        self.stat_button.place(x=0,y=0)
        
        """
        insert everything in stat_frame here
        """
        
        self.frame.tkraise()

        #declairs the wpm labels 
        self.wpm_meter = Label(self.frame,text="WPM:  ",bg="black",fg="orange",font=('Courier New',20))
        
        self.average_wpm = Label(self.frame,text="average WPM:  ",fg="orange",bg="black",font=('Courier New',20))

        #sets the textbox so that the focus is on it but it is located out of the frame
        #so that you can tipe but cant see it 
        self.textbox = tk.Text(self.root,height = 0)
        self.textbox.place(y=2000) 
        self.textbox.bind("<KeyPress>", self.onKeyPress)
        self.textbox.focus_set()

        self.stat_button = Button(self.frame,text="Stats",bg="orange",fg="black",activebackground="green",
                                  highlightcolor="orange",relief="solid",font=('Courier New',8),command=self.controller.show_stat_frame)
        self.stat_button.place(x=0)

    #binds the textbox inputs to the handel_keypress in controller
    def onKeyPress(self,event):
        return self.controller.handel_keypress(event)
    

#handels calculations, checks and coordination
class Controller():
    #initialises variabeles and delays set wigets()
    def __init__(self):

        self.data = Data()
        self.gui = GUI(self)
        self.stat_manager = Stat_manager(self)

        self.exit_fullscreen_var = False
        self.start_time = None
        
        # for debouncing
        self.resize_after_id = None
        self.last_size = (self.gui.root.winfo_width(), self.gui.root.winfo_height())

        # bind to on_redize
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
    #as well as end of exerpt operations
    def handel_keypress(self,event):
        #print(event.keysym)

        self.len_textbox =len(self.gui.textbox.get('0.0',tk.END))
        #for WPM
        if self.start_time == None:
            self.start_time = time.time()
        
        #delets the "f" input after going fullscreen 
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
            
        if (len(self.data.definedText)>= self.len_textbox and self.data.initialised_fullscreen == False):
            
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
                if event.keysym not in ('Shift_L', 'BackSpace','Caps_Lock','Multi_key',"Control_L"):
                    if self.data.definedText[self.len_textbox - 1] != event.keysym:
                        self.inputInorrect()
                        self.hanel_mistakes(self.data.definedText[self.len_textbox - 1])
                        
                    #on correct
                    else:
                        self.inutCorrect()

                #extra rules for space
                if event.keysym != 'space' and self.data.definedText[self.len_textbox - 1] == ' ':
                    self.wigetarray[self.len_textbox - 1].config(fg="red",text="_")
                
                if event.keysym == 'space' and self.data.definedText[self.len_textbox - 1] == ' ':
                    self.wigetarray[self.len_textbox - 1].config(text=" ")

            #on backspace
            if event.keysym == 'BackSpace':
                self.input_return()

        #on backspace
        elif event.keysym == 'BackSpace':
            self.input_return()

        #when the text is finished and input is not "BackSpace"
        else:
            
            #checks if the text is wrong
            textwrong = False
            for i in range(len(self.data.definedText)):
                    textboxiterator1=  "1." + str(i)  
                    textboxiterator2 =  "1." + str(i + 1)  
                    if self.gui.textbox.get(textboxiterator1,textboxiterator2) != self.data.definedText[i]:
                        textwrong = True
                        if event.keysym != "BackSpace":
                            return "break"
                        else:
                            self.input_return()
            
            #if its correct               
            if textwrong == False and event.keysym == "space":

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
                
                #calculates and displays average wpm
                cout_wpm_array = 0
                average_wpm = 0
                for i in self.data.average_wpm_array:
                    cout_wpm_array += 1
                    average_wpm += i

                self.gui.average_wpm.config(text="average WPM: " + str(math.floor(average_wpm / cout_wpm_array)))

                #delets the contents of the textbox
                self.gui.textbox.delete('1.0','2.0')
                self.delete_wigets()
                self.set_wigets()
                
            #bloch the input from being insertet in the textbox
            return 'break'

    #sets the currently last typed wiget to "orange"
    def input_return(self):
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
        frame_width = self.gui.frame.winfo_width()
        self.frame_height = self.gui.frame.winfo_height()

        self.total_width = len(self.data.definedText) * self.data.char_spacing

        self.cordinatarray  = []

        if len(self.data.definedText) % 2 == 0:
            firstpos = int((frame_width - self.total_width) / 2)

        else:
            firstpos = int((frame_width - (self.total_width + 1)) / 2)

        for i in range(len(self.data.definedText)):
            position = firstpos + i*self.data.char_spacing
            self.cordinatarray.append(position)

    #deletes everything in self.gui.frame == all character wigets (not wps Labels)
    def delete_wigets(self):
        #delete everything in frame
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
    def handel_fullscreen(self,event=None):

        self.fullscreen_var = False
        if self.gui.root.winfo_width() >= self.gui.root.winfo_screenwidth() - 10:
            self.fullscreen_var = True
            
        if self.fullscreen_var == False:
            self.gui.root.attributes("-fullscreen", True)

        else:
            self.gui.root.attributes("-fullscreen", False)

            self.gui.root.state("normal")  # if maximised
            self.gui.root.geometry("800x500")
        
    #when the window gets changed it checks if a new resize is apropriate
    def on_resize(self,event):
        
        #checks if wigetarray exist so no error is thrown 
        if hasattr(controller,"wigetarray"):
            
            new_size = (event.width, event.height)

            if new_size != self.last_size:
                self.last_size = new_size

                if self.resize_after_id:
                    self.gui.root.after_cancel(self.resize_after_id)
                
                self.resize_after_id = self.gui.root.after(5,self.handel_resize)
    
    #when a resize is apropriate it recenters the Labels
    def handel_resize(self):

        self.set_WPM_Labels()
        self.generateCordinates()

        for i,widget in enumerate(self.wigetarray):
            widget.place(x= self.cordinatarray[i],y= self.frame_height * 0.3)
        
        self.resize_after_id = None
             
    #documents the mistakes and there frequency 
    def hanel_mistakes(self,char):

        for i in range(len(self.data.mistake_array)):

            if self.data.mistake_array[i][0] == char:
                self.data.mistake_array[i][1] += 1
                break

        else:
            self.data.mistake_array.append([char,1])

        self.mistake_array_sorter()

    #sorts the mistake_array
    def mistake_array_sorter(self):

        #so that the len is sutibel
        len_mistake_array = len(self.data.mistake_array) - 1
        
        #goes through the entire array
        for i in range(len_mistake_array):

            biggest_int = 0

            #skips the already sorted rear positions 
            for u in range((len_mistake_array - i) + 1):

                if self.data.mistake_array[u][1] > biggest_int:

                    biggest_int = self.data.mistake_array[u][1]
                    biggest_int_index = u

            #the bigggest position gets put to the end of the array exerpt by 
            #switching the two poitions
            char_storage = self.data.mistake_array[len_mistake_array - i][0]
            int_storage = self.data.mistake_array[len_mistake_array - i][1]

            self.data.mistake_array[(len_mistake_array - i)][0] = self.data.mistake_array[biggest_int_index][0]
            self.data.mistake_array[(len_mistake_array - i)][1] = self.data.mistake_array[biggest_int_index][1]

            self.data.mistake_array[biggest_int_index][0] = char_storage
            self.data.mistake_array[biggest_int_index][1] = int_storage

    #raises the stat_frame to the foreground
    def show_stat_frame(self):
        
        self.stat_manager.build_graph()
        self.gui.stat_frame.tkraise()

    
    #raises the  main frame to the foreground
    def show_main_frame(self):

        self.gui.frame.tkraise()



class Stat_manager():
    
    def __init__(self,controller):
        self.controller = controller
        self.frame = self.controller.gui.stat_frame


    def build_graph(self):
        
        # WPM graph
        fig1 = plt.Figure(figsize=(4, 2.5), dpi=100)
        ax1 = fig1.add_subplot(111)
        ax1.plot(self.controller.data.average_wpm_array, marker='o', color='orange')
        ax1.set_title("WPM graph")
        ax1.set_ylabel("WPM")
        ax1.set_xlabel("Session")

        canvas1 = FigureCanvasTkAgg(fig1, master=self.frame)
        canvas1.draw()
        canvas1.get_tk_widget().place(x=20, y=20)

        # Beispiel 2: Fehlerhäufigkeit
        fig2 = plt.Figure(figsize=(4, 2.5), dpi=100)
        ax2 = fig2.add_subplot(111)

        # Zeichne die häufigsten Fehlerzeichen
        chars = [x[0] for x in self.controller.data.mistake_array]
        counts = [x[1] for x in self.controller.data.mistake_array]
        ax2.bar(chars, counts, color='red')
        ax2.set_title("Häufige Fehler")
        ax2.set_ylabel("Anzahl")
        ax2.set_xlabel("Zeichen")

        canvas2 = FigureCanvasTkAgg(fig2, master=self.frame)
        canvas2.draw()
        canvas2.get_tk_widget().place(x=450, y=20)




controller = Controller()
controller.gui.root.mainloop()