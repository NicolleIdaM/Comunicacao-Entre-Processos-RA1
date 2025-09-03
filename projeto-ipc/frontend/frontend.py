from tkinter import *

root = Tk()
root.title('Jorge')

topbar = Frame(root)
topbar.pack(padx=12, pady=12)

area = Frame(root)
area.pack(fill='x', padx=12, pady=(0, 12))

Label(area, text="Mensagem:").pack(anchor='w')
e = Entry(area, width=50)
e.pack(anchor='w', pady=4)

resp_var = StringVar(value="")
Label(root, textvariable=resp_var).pack(pady=(4, 10))

def enviar():
    resp_var.set(e.get())

Button(area, text="Enviar", command=enviar).pack(anchor='w', pady=4)

def myClick(tipo):
    
    e.insert(0, f"{tipo}: ")

Button(topbar, text="pipes", command=lambda: myClick("pipes")).pack(side='left', padx=8)
Button(topbar, text="Sockets", command=lambda: myClick("Sockets")).pack(side='left', padx=8)
Button(topbar, text="Memória compartilhada", command=lambda: myClick("Memória compartilhada")).pack(side='left', padx=8)

root.mainloop()
