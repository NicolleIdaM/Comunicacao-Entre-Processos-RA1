from tkinter import *

root = Tk()
root.title('Jorge')

topbar = Frame(root)
topbar.pack(padx=12, pady=12)

def myClick():
    Label(text="Mensagem:").pack()
    e = Entry(width=50)
    e.pack()    

    def mySecondClick():
        resposta =e.get()
        mySecondLabel = Label(root, text=resposta)
        mySecondLabel.pack()

    Button(text="Enviar", command=mySecondClick).pack(anchor='w', pady=4)

Button(topbar, text="pipes", command = myClick).pack(side='left', padx=8)
Button(topbar, text="Sockets", command = myClick).pack(side='left', padx=8)
Button(topbar, text="Memória compartilhada", command = myClick).pack(side='left', padx=8)

root.mainloop()
