from tkinter import *
from PIL import ImageTk,Image
from tkinter import messagebox

root = Tk()
root.title('Jorge')
root.iconbitmap()

def myClick():
    e = Entry(root, width=50)
    e.pack()
    e.insert(0, "Mensagem: ")

    def mySecondClick():
            resposta =e.get()
            mySecondLabel = Label(root, text=resposta)
            mySecondLabel.pack()

    QuatroBotaum = Button(root, text="Enviar", command=mySecondClick)
    QuatroBotaum.pack()
            
    

umbutaum = Button(root, text="pipes", command=myClick)
umbutaum.pack(side='left')
doisbutaum = Button(root, text="Sockets",command=myClick)
doisbutaum.pack(side='left')
treisbutaum = Button(root, text="Memória compartilhada",command=myClick)
treisbutaum.pack(side='left')

root.mainloop()