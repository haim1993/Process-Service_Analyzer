
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
        self.file_menu.add_command( label="Exit", command=lambda: os.system("killall python") )

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

        self.trv_service = Treeview( self.frame_service, height=30 )
        self.trv_service.heading("#0", text="NAME")
        self.trv_service.column("#0", width=500)
        self.trv_service.pack()


        # right click menu
        self.menu_right_click = Menu( self.trv_process, tearoff=0 )
        self.menu_right_click.add_command( label="Terminate", command=lambda: self.click_on_terminate() )


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

        # write threads to text area & update every X seconds.
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
        global TERMINATE
        id = self.trv_process.identify_row(event.y)
        if id:
            self.trv_process.selection_set(id)
            children = self.trv_process.get_children(id)
            self.menu_right_click.post( event.x_root, event.y_root )
            TERMINATE = id
    def click_on_terminate( self ):
        global TERMINATE
        self.menu_right_click.unpost()
        pid = int(self.trv_process.item(TERMINATE)["text"])
        os.system("kill -9 %s" % pid)


    '''Click anywhere to uppost menu terminate'''
    def click_anywhere_to_unpost( self, event ):
        self.menu_right_click.unpost()


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
            self.menu_right_click.unpost()

            old_data = self.get_rows( "process" )
            self.trv_process.delete(*self.trv_process.get_children())

            process_list = list(psutil.process_iter())
            self.lbl_process_count.config( text="%s\t\t" % len(process_list) )

            item_dictionary = {}
            temp_list = []
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
            old_data = self.get_rows( "service" )
            self.trv_service.delete(*self.trv_service.get_children())

            service_list = os.popen('service --status-all | grep "+"').readlines()
            self.lbl_service_count.config( text="%s\t\t" % len(service_list) )
            for serv in service_list:
                    self.trv_service.insert( '', index=END, text=serv[8:-1] )

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
                data.append( "pid: %s\tppid: %s\t\tname: %s" % (item_text, item_values[0], item_values[1]) )
            else:
                item_text = str(self.trv_service.item(element)["text"])
                data.append( "name: %s" % item_text )
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

        # frame
        frame_old = LabelFrame( window )
        frame_old.pack()

        frame_new = LabelFrame( window )
        frame_new.pack()

        # textarea
        txt_area_old = Text( frame_old )
        txt_area_new = Text( frame_new )

        if (type == "process"):
            frame_old.config(text="Old Processes")
            frame_new.config(text="New Processes")
            compareDifferences(file_data, gui_data, txt_area_old)
            compareDifferences(gui_data, file_data, txt_area_new)
        else:
            frame_old.config(text="Old Services")
            frame_new.config(text="New Services")
            compareDifferences(file_data, gui_data, txt_area_old)
            compareDifferences(gui_data, file_data, txt_area_new)

        txt_area_old.config( state=DISABLED )
        txt_area_new.config( state=DISABLED )
        txt_area_old.pack( side = LEFT )
        txt_area_new.pack( side = LEFT )

        window.mainloop()


    """
    # Comparison between two lists. If not empty, open popup and save
    # changes in folder 'changes' in current directory.
    #
    # input: list_one is the first list. list_two is the second list.
    # output: the difference between list_one and list_two.
    """
    def checkDifferences( self, list_one, list_two, type ):
        global SVCHANGES, ON
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
                self.lbl_process_status.config( text="MODIFIED", fg="red" )
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
            else:
                self.lbl_service_status.config( text="OK", fg="green" )


"""
# Comparison between two lists and insert into TextArea.
#
# input: list_one is the first list. list_two is the second list.
# output: the difference between list_one and list_two.
"""
def compareDifferences(list_one, list_two, text):
    for element in (set(list_one) - set(list_two)):
        text.insert( INSERT, "%s\n" % element )


def main():
    GUI()


if __name__ == '__main__':
    main()
