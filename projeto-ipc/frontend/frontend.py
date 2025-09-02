from tkinter import *
from PIL import ImageTk,Image
from tkinter import messagebox

root = Tk()
root.title('')
root.iconbitmap('c:/gui/codemy.ico')

def popup():
    response = messagebox.showerror("ALa u popup", "?")
    Label(root, text=response).pack()
   
Button(root, text="Jóia", command=popup).pack()

mainloop()