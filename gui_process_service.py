
import os
import time
import psutil
import tkMessageBox
import tkFileDialog

from ttk import *
from Tkinter import *
from stat import S_IREAD
from threading import Thread


'''Used as MACRO for treeview on gui'''
OFF = 0
ON = 1
TRVIEW = 0
SVCHANGES = 0
DELAY = 10
TERMINATE = None
PATH = ""
LIST_CHANGES = []

class GUI:

    def __init__( self ):
        # root frame
        self.root = Tk()
        self.root.title( "Currently running" )
        self.root.wm_attributes("-topmost", 1)
        self.root.resizable(width=False, height=False)


        # menu
        self.menu = Menu( self.root )

        self.file_menu = Menu( self.menu, tearoff=0 )
        self.file_menu.add_separator()
        self.file_menu.add_command( label="Exit", command=lambda: os.system("sudo killall python") )

        self.view_menu = Menu( self.menu, tearoff=0 )
        self.view_menu.add_command( label="Process view", command=lambda: self.tree_view_status() )
        self.view_menu.add_command( label="Track tool", command=lambda: self.save_changes_status() )
        self.view_menu.add_command( label="Refresh rate", command=lambda: self.refresh_list_delay() )

        self.menu.add_cascade(label="File", menu=self.file_menu)
        self.menu.add_cascade(label="View", menu=self.view_menu)


        self.root.config( menu=self.menu )

        # frame / notebook
        self.notebook = Notebook(self.root)

        self.frame_process = Frame( self.notebook )
        self.frame_process.pack( side = LEFT )

        self.frame_button_process = Frame( self.frame_process )
        self.frame_button_process.pack( side = BOTTOM )


        self.frame_service = Frame( self.notebook )
        self.frame_service.pack( side = RIGHT )

        self.frame_button_service = Frame( self.frame_service )
        self.frame_button_service.pack( side = BOTTOM )


        self.notebook.add(self.frame_process, text="Processes")
        self.notebook.add(self.frame_service, text="Services")
        self.notebook.pack()


        # treeview
        self.trv_process = Treeview( self.frame_process, columns=("#1", "#2"), height=30 )
        self.trv_process.heading("#0", text="PID")
        self.trv_process.heading("#1", text="PPID")
        self.trv_process.heading("#2", text="NAME")
        self.trv_process.column("#0", width=80) #240
        self.trv_process.column("#1", width=80)  #60
        self.trv_process.column("#2", width=340) #200
        self.trv_process.bind("<Button-1>", self.click_anywhere_to_unpost)
        self.trv_process.bind("<Button-3>", self.terminate_menu)
        self.trv_process.pack()

        self.trv_service = Treeview( self.frame_service, columns=("#1", "#2", "#3", "#4"), height=30 )
        self.trv_service.heading("#0", text="PID")
        self.trv_service.heading("#1", text="NAME")
        self.trv_service.heading("#2", text="CPU")
        self.trv_service.heading("#3", text="MEM")
        self.trv_service.heading("#4", text="PATH")
        self.trv_service.column("#0", width=60)
        self.trv_service.column("#1", width=160)
        self.trv_service.column("#2", width=60)
        self.trv_service.column("#3", width=60)
        self.trv_service.column("#4", width=160)
        self.trv_service.bind("<Button-1>", self.click_anywhere_to_unpost)
        self.trv_service.bind("<Button-3>", self.service_menu)
        self.trv_service.pack()


        # right click menu
        self.menu_right_click_process = Menu( self.trv_process, tearoff=0 )
        self.menu_right_click_process.add_command( label="Terminate", command=lambda: self.click_on_terminate() )

        self.menu_right_click_service = Menu( self.trv_service, tearoff=0 )
        self.menu_right_click_service.add_command( label="Open Folder", command=lambda: self.click_on_open() )


        #image buttons
        self.image_track = PhotoImage(file="track.png")
        self.btn_track_process = Button( self.frame_button_process, command=lambda: self.openSeperateWindowsDifferences("process", LIST_CHANGES[0], LIST_CHANGES[1]),
         state=DISABLED, image = self.image_track, width=18, height=18, relief=FLAT )
        self.btn_track_process.pack( side = LEFT )


        # labels
        self.lbl_p_status = Label( self.frame_button_process, text="STATUS: " )
        self.lbl_p_status.pack( side = LEFT )

        self.lbl_process_status = Label( self.frame_button_process, width=10, anchor="w" )
        self.lbl_process_status.pack( side = LEFT )

        self.lbl_process_info = Label( self.frame_button_process, text="COUNT: " )
        self.lbl_process_info.pack( side = LEFT )

        self.lbl_process_count = Label( self.frame_button_process )
        self.lbl_process_count.pack( side = LEFT )


        self.lbl_s_status = Label( self.frame_button_service, text="STATUS: " )
        self.lbl_s_status.pack( side = LEFT )

        self.lbl_service_status = Label( self.frame_button_service, width=10, anchor="w" )
        self.lbl_service_status.pack( side = LEFT )

        self.lbl_service_info = Label( self.frame_button_service, text="COUNT: " )
        self.lbl_service_info.pack( side = LEFT )

        self.lbl_service_count = Label( self.frame_button_service )
        self.lbl_service_count.pack( side = LEFT )


        # buttons
        self.btn_compare_process = Button( self.frame_button_process, text="Compare", command=lambda: self.openFileToCompare("process") )
        self.btn_compare_process.pack( side = LEFT )

        self.btn_save_process = Button( self.frame_button_process, text="Save", command=lambda: self.saveFileToCurrentDirectory("process") )
        self.btn_save_process.pack( side = LEFT )

        self.btn_compare_service = Button( self.frame_button_service, text="Compare", command=lambda: self.openFileToCompare("service") )
        self.btn_compare_service.pack( side = LEFT )

        self.btn_save_service = Button( self.frame_button_service, text="Save", command=lambda: self.saveFileToCurrentDirectory("service") )
        self.btn_save_service.pack( side = LEFT )

        if not os.path.exists("application by haim"):
            os.mkdir("application by haim")
        os.chdir("application by haim")


        # write threads to treeview & update every X seconds.
        try:
            Thread(target=self.writeProcesses).start()
            Thread(target=self.writeServices).start()
        except Exception, errtxt:
            print errtxt

        self.root.mainloop()


    '''Set/Reset treeview to decadent mode'''
    def tree_view_status( self ):
        global TRVIEW, ON, OFF

        if TRVIEW == ON:
            result = tkMessageBox.askquestion("Change to list-view", "Are You Sure?", icon='warning')
            if result == 'yes':
                TRVIEW = OFF
        else:
            result = tkMessageBox.askquestion("Change to tree-view", "Are You Sure?", icon='warning')
            if result == 'yes':
                TRVIEW = ON


    '''Save/Don't Save the changes that are created when on MODIFIED mode'''
    def save_changes_status( self ):
        global SVCHANGES, ON, OFF

        if SVCHANGES == ON:
            result = tkMessageBox.askquestion("Stop tracking", "Are You Sure?", icon='warning')
            if result == 'yes':
                SVCHANGES = OFF
        else:
            result = tkMessageBox.askquestion("Track modified lists", "Are You Sure?", icon='warning')
            if result == 'yes':
                SVCHANGES = ON


    '''Modify DELAY global variable.'''
    def refresh_list_delay( self ):
        window = Toplevel()
        window.wm_attributes("-topmost", 1)
        window.resizable(width=False, height=False)

        window.title( "Seconds" )
        box = Spinbox( window, from_=20, to=100, width=6 )
        box.pack( side = LEFT )
        Button( window, text="Okay", padx=20, command=lambda: self.set_delay(window, box) ).pack( side = LEFT )
        window.mainloop()
    def set_delay( self, window, box ):
        global DELAY
        DELAY = int(box.get())
        window.destroy()


    '''Open popup menu to terminate the selected process.'''
    def terminate_menu( self, event ):
        self.menu_right_click_process.unpost()
        global TERMINATE
        id = self.trv_process.identify_row(event.y)
        if id:
            self.trv_process.selection_set(id)
            child = self.trv_process.get_children(id)
            self.menu_right_click_process.post( event.x_root, event.y_root )
            TERMINATE = id
    def click_on_terminate( self ):
        global TERMINATE
        self.menu_right_click_process.unpost()
        pid = int(self.trv_process.item(TERMINATE)["text"])
        os.system("sudo kill -9 %s" % pid)


    '''Open popup menu to open the selected service log file.'''
    def service_menu( self, event ):
        self.menu_right_click_service.unpost()
        global PATH
        id = self.trv_service.identify_row(event.y)
        if id:
            self.trv_service.selection_set(id)
            path = str(self.trv_service.item(id)['values'][3])
            if path != "--":
                self.menu_right_click_service.post( event.x_root, event.y_root )
                PATH = "/var/log%s" %path[1:]
            else:
                PATH = ""
    def click_on_open( self ):
        global PATH
        self.menu_right_click_service.unpost()
        if PATH is not "":
            os.system("sudo nautilus %s" % PATH)


    '''Click anywhere to uppost menu terminate'''
    def click_anywhere_to_unpost( self, event ):
        self.menu_right_click_process.unpost()
        self.menu_right_click_service.unpost()


    """
    # Prints on text area the process list that are running currently
    # on the system. Will show the updated list every X seconds depending
    # on the time 'delay'.
    #
    # input: 'delay' is the time that it prints a new list.
    # output: prints on text area the list of processes.
    """
    def writeProcesses( self ):
        global TRVIEW, ON, OFF, DELAY
        while True:
            self.menu_right_click_process.unpost()

            old_data = self.get_rows( "process" )
            self.trv_process.delete(*self.trv_process.get_children())

            process_list = list(psutil.process_iter())
            self.lbl_process_count.config( text="%s\t\t" % len(process_list) )

            item_dictionary = {}
            temp_list = []
            try:
                for proc in process_list[:-1]:
                    process_pid = str(proc.as_dict(attrs=['pid']))[8:-1]
                    process_ppid = str(proc.as_dict(attrs=['ppid']))[9:-1]
                    process_name = str(proc.as_dict(attrs=['name']))[10:-2]

                    if (TRVIEW == ON):
                        self.set_tree_columns_width(240, 60, 200)
                        if (process_ppid == "0"):
                            item_dictionary[process_pid] = \
                            self.trv_process.insert( '', index=END, text=process_pid, values=(process_ppid, process_name), open=True )
                        else:
                            items = item_dictionary
                            index = 0
                            for key in items:
                                if (key == process_ppid):
                                    index = -1
                                    item_dictionary[process_pid] = \
                                    self.trv_process.insert( item_dictionary[key], index=END, text=process_pid, values=(process_ppid, process_name), open=True )
                                    break
                            if index == 0:
                                item_dictionary[process_pid] = \
                                self.trv_process.insert( '', index=END, text=process_pid, values=(process_ppid, process_name), open=True )

                    else:
                        self.set_tree_columns_width(80, 80, 340)
                        self.trv_process.insert( '', index=END, text=process_pid, values=(process_ppid, process_name) )

                process_pid = str(process_list[-1].as_dict(attrs=['pid']))[8:-1]
                process_ppid = str(process_list[-1].as_dict(attrs=['ppid']))[9:-1]
                process_name = str(process_list[-1].as_dict(attrs=['name']))[10:-2]

            except psutil.NoSuchProcess:
                pass

            if (TRVIEW == ON):
                items = item_dictionary
                for key in items:
                    if (key == process_ppid):
                        item_dictionary[process_pid] = \
                        self.trv_process.insert( item_dictionary[key], index=END, text=process_pid, values=(process_ppid, process_name), open=True )
                        break
                children = self.trv_process.get_children()
                for child in children:
                    items_pid = str(self.trv_process.item(child)['text'])
                    items_info = self.trv_process.item(child)['values']
                    for key in item_dictionary:
                        if (key == str(items_info[0])):
                            self.trv_process.delete(child)
                            self.trv_process.insert( item_dictionary[key], index=END, text=items_pid, values=(items_info[0], items_info[1]), open=True )
                            break

            else:
                self.trv_process.insert( '', index=END, text=process_pid, values=(process_ppid, process_name) )

            new_data = self.get_rows( "process" )

            if len(old_data) > 0:
                self.checkDifferences(old_data, new_data, "process")
            else:
                self.lbl_process_status.config( text="OK", fg="green" )

            time.sleep( DELAY )


    """
    # Prints on text area the service list that are running currently
    # on the system. Will show the updated list every X seconds depending
    # on the time 'delay'.
    #
    # input: 'delay' is the time that it prints a new list.
    # output: prints on text area the list of services.
    """
    def writeServices( self ):
        global DELAY
        while True:
            self.menu_right_click_service.unpost()

            old_data = self.get_rows( "service" )
            self.trv_service.delete(*self.trv_service.get_children())

            service_list = os.popen('sudo service --status-all | grep "+"').readlines()
            self.lbl_service_count.config( text="%s\t\t" % len(service_list) )
            for serv in service_list:
                    service = serv[8:-1]
                    pid_number = match_service_to_pid( service )
                    information = ["--", "--"]
                    if pid_number != "":
                        information = get_cpu_and_memory_using_pid ( pid_number ) #cpu & memory usage
                    cwd = os.getcwd()
                    os.chdir("/var/log/")
                    folder = os.popen( 'sudo find -type d -name "%s"' % service ).readlines()
                    if len(folder) is 0:
                        file_log = os.popen( 'sudo find -type f -name "%s.log"' % service ).readlines()
                        if len(file_log) > 0:
                            self.trv_service.insert( '', index=END, text=pid_number, values=(service, information[0], information[1], file_log[0]) )
                        else:
                            self.trv_service.insert( '', index=END, text=pid_number, values=(service, information[0], information[1], "--") )
                    else:
                        self.trv_service.insert( '', index=END, text=pid_number, values=(service, information[0], information[1], folder[0]) )
                    os.chdir(cwd)

            new_data = self.get_rows( "service" )

            if len(old_data) > 0:
                self.checkDifferences(old_data, new_data, "service")
            else:
                self.lbl_service_status.config( text="OK", fg="green" )

            time.sleep( DELAY )


    '''Set width of treeview columns'''
    def set_tree_columns_width( self, value_one, value_two, value_three ):
        self.trv_process.column("#0", width=value_one)
        self.trv_process.column("#1", width=value_two)
        self.trv_process.column("#2", width=value_three)


    """
    # Return the rows of Treeview widget as a list.
    """
    def get_rows( self, type ):
        data = []
        index = 1
        if type == "process":
            list_elements = self.trv_process.get_children()
        else:
            list_elements = self.trv_service.get_children()

        for element in list_elements:

            if (type == "process"):
                item_text = str(self.trv_process.item(element)["text"])
                item_values = self.trv_process.item(element)["values"]
                data.append( "pid: %s;\tppid: %s;\tname: %s;" % (item_text, item_values[0], item_values[1]) )
            else:
                item_text = str(self.trv_service.item(element)["text"])
                item_values = self.trv_service.item(element)["values"]
                data.append( "pid: %s;\tname: %s;" % (item_text, item_values[0]) )
            index += 1
        return data



    """
    # Opens the browse dialog on the screen allowing us to pick
    # a process list file to compare.
    #
    # input:
    # output: prints to console the differences between the current list and uploaded one.
    """
    def openFileToCompare( self, type ):
        file = tkFileDialog.askopenfile(parent=self.root, mode='rb', title='Choose a file')
        if (file != None and (type == "process" and "process," in str(file))
            or (type == "service" and "service," in str(file))):

            file_data = str(file.read()).splitlines()
            if (type == "process"):
                gui_data = self.get_rows( "process" )
                self.openSeperateWindowsDifferences("process", file_data, gui_data)
            else:
                gui_data = self.get_rows( "service" )
                self.openSeperateWindowsDifferences("service", file_data, gui_data)

            file.close()
        else:
            tkMessageBox.showerror("Error", "Opening incorrect file")



    """
    # Saves the current process list on current directory.
    """
    def saveFileToCurrentDirectory( self , type ):
        if (type == "process"):
            gui_data = self.get_rows( "process" )
        else:
            gui_data = self.get_rows( "service" )

        if not os.path.exists("%s list" % type):
            os.mkdir("%s list" % type)
        os.chdir("%s list" % type)
        file = open("%s, %s" %(type, time.strftime("%c")), 'w')
        file.truncate()
        for line in gui_data:
            file.write("%s\n" % line)
        file.close()
        os.chmod("%s, %s" %(type, time.strftime("%c")), S_IREAD)
        os.chdir("..")


    """
    # Opens a seperate windows with the status of the old and new
    # processes / services that have been created.
    """
    def openSeperateWindowsDifferences( self, type, file_data, gui_data ):
        # toplevel window
        window = Toplevel()
        window.wm_attributes("-topmost", 1)
        window.resizable(width=False, height=False)
        if type == "process":
            window.title("Changes in processes")
        else:
            window.title("Changes in services")

        # frame
        frame_old = LabelFrame( window )
        frame_old.pack()

        frame_new = LabelFrame( window )
        frame_new.pack()

        # treeview
        trv_seperate_old = Treeview( frame_old )
        trv_seperate_new = Treeview( frame_new )

        if (type == "process"):
            trv_seperate_old.config( columns=("#1", "#2"), height=10 )
            trv_seperate_old.heading("#0", text="PID")
            trv_seperate_old.heading("#1", text="PPID")
            trv_seperate_old.heading("#2", text="NAME")
            trv_seperate_old.column("#0", width=80) #240
            trv_seperate_old.column("#1", width=80)  #60
            trv_seperate_old.column("#2", width=340) #200
            trv_seperate_old.pack()

            trv_seperate_new.config( columns=("#1", "#2"), height=10 )
            trv_seperate_new.heading("#0", text="PID")
            trv_seperate_new.heading("#1", text="PPID")
            trv_seperate_new.heading("#2", text="NAME")
            trv_seperate_new.column("#0", width=80) #240
            trv_seperate_new.column("#1", width=80)  #60
            trv_seperate_new.column("#2", width=340) #200
            trv_seperate_new.pack()

            frame_old.config(text="Old Processes")
            frame_new.config(text="New Processes")
            compareDifferences("process", file_data, gui_data, trv_seperate_old)
            compareDifferences("process", gui_data, file_data, trv_seperate_new)
        else:
            trv_seperate_old.config( columns=("#1"), height=10 )
            trv_seperate_old.heading("#0", text="PID")
            trv_seperate_old.heading("#1", text="NAME")
            trv_seperate_old.column("#0", width=80)
            trv_seperate_old.column("#1", width=420)
            trv_seperate_old.pack()

            trv_seperate_new.config( columns=("#1"), height=10 )
            trv_seperate_new.heading("#0", text="PID")
            trv_seperate_new.heading("#1", text="NAME")
            trv_seperate_new.column("#0", width=80)
            trv_seperate_new.column("#1", width=420)
            trv_seperate_new.pack()

            frame_old.config(text="Old Services")
            frame_new.config(text="New Services")
            compareDifferences("service", file_data, gui_data, trv_seperate_old)
            compareDifferences("service", gui_data, file_data, trv_seperate_new)

        window.mainloop()


    """
    # Comparison between two lists. If not empty, open popup and save
    # changes in folder 'changes' in current directory.
    #
    # input: list_one is the first list. list_two is the second list.
    # output: the difference between list_one and list_two.
    """
    def checkDifferences( self, list_one, list_two, type ):
        global SVCHANGES, ON, LIST_CHANGES
        list = []
        if (type == "process"):
            list.append("--Old-Processes--\n")
        else:
            list.append("--Old-Services--\n")
        for element in (set(list_one) - set(list_two)):
            list.append("%s\n" % element)

        if (type == "process"):
            list.append("\n--New-Processes--\n")
        else:
            list.append("\n--New-Services--\n")
        for element in (set(list_two) - set(list_one)):
            list.append("%s\n" % element)

        if len(list) > 2:
            if type == "process":
                LIST_CHANGES = []
                self.lbl_process_status.config( text="MODIFIED", fg="red" )
                LIST_CHANGES.append(list_one)
                LIST_CHANGES.append(list_two)
                self.btn_track_process.config( state = 'normal' )

            else:
                self.lbl_service_status.config( text="MODIFIED", fg="red" )

            if (SVCHANGES == ON):
                if not os.path.exists("%s changes" % type):
                    os.mkdir("%s changes" % type)
                os.chdir("%s changes" % type)
                file = open("changes, %s" % time.strftime("%c"), 'w')
                file.truncate()
                for element in list:
                    file.write("%s" % element)
                file.close()
                os.chmod("changes, %s" % time.strftime("%c"), S_IREAD)
                os.chdir("..")
        else:
            if type == "process":
                self.lbl_process_status.config( text="OK", fg="green" )
                self.btn_track_process.config( state = DISABLED )
            else:
                self.lbl_service_status.config( text="OK", fg="green" )


"""
# Comparison between two lists and insert into TextArea.
#
# input: list_one is the first list. list_two is the second list.
# output: the difference between list_one and list_two.
"""
def compareDifferences(type, list_one, list_two, tree):
    for element in (set(list_one) - set(list_two)):
        if type == "process":
            start_pid = element.index("pid")
            end_pid = element.index(";")
            pid = element[start_pid:end_pid][5:]

            start_ppid = element.index("ppid")
            end_ppid = element.index(";", start_ppid)
            ppid = element[start_ppid:end_ppid][6:]

            start_name = element.index("name")
            end_name = element.index(";", start_name)
            name = element[start_name:end_name][6:]
            tree.insert( '', index=END, text=pid, values=(ppid, name) )
        else:
            start_name = element.index("name")
            end_name = element.index(";")
            name = element[start_name:end_name][6:]
            tree.insert( '', index=END, text=name )


'''Get service name, and return pid number if exists of main process'''
def match_service_to_pid( name ):
    pid = os.popen('sudo service %s status | grep "PID"' % name).readlines()
    if len(pid) == 0:
        pid = os.popen('sudo service %s status | grep -i "process"' % name).readlines()
        if len(pid) == 0:
            return "--"
        else:
            pid_number = pid[0]
            index_start = pid_number.index("Process:") + 9
            index_end = pid_number.index(" Exec", index_start)
            return pid_number[index_start:index_end]
    else:
        pid_number = pid[0]
        index_start = pid_number.index("PID:") + 5
        index_end = pid_number.index(" (", index_start)
        return pid_number[index_start:index_end]


'''Get cpu & memory usage using pid if exists. element[0] = cpu. element[1] = memory.'''
def get_cpu_and_memory_using_pid( pid ):
    list_information = os.popen('ps -p %s -o %s,%s' % (pid, "%cpu", "%mem")).readlines()
    if len(list_information) < 2:
        return ["--", "--"]
    information = list_information[1][:-1]
    cpu_end = information.index(" ", 1)
    cpu = information[0:cpu_end]
    memory_start = information.index("  ") + 2
    memory = information[memory_start:]
    return [cpu, memory]


def main():
    GUI()
    # print get_cpu_and_memory_using_pid( 18719 )

if __name__ == '__main__':
    main()
