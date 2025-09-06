import json
import subprocess
import threading
import sys
import os
from tkinter import *
from tkinter import ttk, scrolledtext, messagebox

class IPCApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Comunicação entre Processos - IPC")
        self.root.geometry("800x600")
        
        # Variáveis de controle
        self.current_ipc_type = StringVar(value="pipes")
        self.parent_process = None
        self.child_process = None
        
        self.create_widgets()
        
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(N, W, E, S))
        
        # Configurar expansão
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Seleção do tipo de IPC
        ttk.Label(main_frame, text="Selecione o mecanismo de IPC:").grid(row=0, column=0, sticky=W, pady=5)
        ipc_combo = ttk.Combobox(main_frame, textvariable=self.current_ipc_type, 
                                values=["pipes", "sockets", "shared_memory"], state="readonly")
        ipc_combo.grid(row=0, column=1, sticky=(W, E), pady=5)
        ipc_combo.bind('<<ComboboxSelected>>', self.on_ipc_change)
        
        # Botões de controle
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Iniciar Parent", command=self.start_parent)
        self.start_button.pack(side=LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Parar Parent", command=self.stop_parent, state=DISABLED)
        self.stop_button.pack(side=LEFT, padx=5)
        
        # Área de mensagem (apenas para pipes e shared_memory)
        ttk.Label(main_frame, text="Mensagem:").grid(row=2, column=0, sticky=W, pady=5)
        self.message_entry = ttk.Entry(main_frame)
        self.message_entry.grid(row=2, column=1, sticky=(W, E), pady=5)
        self.message_entry.bind('<Return>', self.send_message)
        
        self.send_button = ttk.Button(main_frame, text="Enviar via Child", command=self.send_message)
        self.send_button.grid(row=2, column=2, padx=5)
        
        # Área de log
        ttk.Label(main_frame, text="Log de Comunicação:").grid(row=3, column=0, sticky=NW, pady=5)
        self.log_area = scrolledtext.ScrolledText(main_frame, width=70, height=20, state=DISABLED)
        self.log_area.grid(row=4, column=0, columnspan=3, sticky=(N, W, E, S), pady=5)
        
        # Status bar
        self.status_var = StringVar(value="Pronto")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=SUNKEN, anchor=W)
        status_bar.grid(row=1, column=0, sticky=(W, E))
        
        # Atualizar interface baseada no tipo de IPC
        self.update_interface()
        
    def on_ipc_change(self, event):
        ipc_type = self.current_ipc_type.get()
        self.add_to_log(f"Mecanismo de IPC alterado para: {ipc_type}")
        self.update_interface()
        
    def update_interface(self):
        ipc_type = self.current_ipc_type.get()
        
        # Habilitar/desabilitar campos baseado no tipo de IPC
        if ipc_type == "sockets":
            self.message_entry.config(state=DISABLED)
            self.send_button.config(state=DISABLED, text="Testar Conexão")
        else:
            self.message_entry.config(state=NORMAL)
            self.send_button.config(state=NORMAL, text="Enviar via Child")
        
    def add_to_log(self, message):
        self.log_area.config(state=NORMAL)
        self.log_area.insert(END, message + "\n")
        self.log_area.see(END)
        self.log_area.config(state=DISABLED)
        
    def start_parent(self):
        ipc_type = self.current_ipc_type.get()
        parent_exe = f"backend/{ipc_type}/parent.exe"
        
        if not os.path.exists(parent_exe):
            messagebox.showerror("Erro", f"Executável do parent não encontrado: {parent_exe}")
            return
            
        try:
            self.parent_process = subprocess.Popen(
                [parent_exe],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Thread para ler a saída do processo
            threading.Thread(target=self.read_output, args=(self.parent_process,), daemon=True).start()
            
            self.start_button.config(state=DISABLED)
            self.stop_button.config(state=NORMAL)
            self.status_var.set(f"Parent {ipc_type} iniciado")
            self.add_to_log(f"Parent {ipc_type} iniciado")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao iniciar parent: {str(e)}")
            
    def stop_parent(self):
        if self.parent_process:
            self.parent_process.terminate()
            self.parent_process = None
            
        self.start_button.config(state=NORMAL)
        self.stop_button.config(state=DISABLED)
        self.status_var.set("Parent parado")
        self.add_to_log("Parent parado")
        
    def read_output(self, process):
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                try:
                    data = json.loads(output.strip())
                    self.process_backend_data(data)
                except json.JSONDecodeError:
                    self.add_to_log(f"Saída não JSON: {output}")
                    
    def process_backend_data(self, data):
        ipc_type = data.get('type', 'unknown')
        status = data.get('status', '')
        message = data.get('message', '')
        data_content = data.get('data', '')
        action = data.get('action', '')
        
        # Processar diferentes formatos de saída
        if ipc_type == "pipes":
            if status:
                self.add_to_log(f"[PIPES] Status: {status}")
            if message:
                self.add_to_log(f"[PIPES] Mensagem: {message}")
                
        elif ipc_type == "socket":
            if status:
                self.add_to_log(f"[SOCKET] Status: {status}")
            if data_content:
                if action == "sent":
                    self.add_to_log(f"[SOCKET] Enviado: {data_content}")
                elif action == "received":
                    self.add_to_log(f"[SOCKET] Recebido: {data_content}")
            elif message:
                self.add_to_log(f"[SOCKET] Mensagem: {message}")
            
    def send_message(self, event=None):
        ipc_type = self.current_ipc_type.get()
        message = self.message_entry.get().strip()
        
        if ipc_type == "sockets":
            # Para sockets, executar o child para testar conexão
            self.test_socket_connection()
        else:
            # Para pipes e shared_memory, enviar mensagem normal
            if not message:
                messagebox.showwarning("Aviso", "Digite uma mensagem para enviar")
                return
                
            child_exe = f"backend/{ipc_type}/child.exe"
            
            if not os.path.exists(child_exe):
                messagebox.showerror("Erro", f"Executável do child não encontrado: {child_exe}")
                return
                
            try:
                subprocess.Popen([child_exe, message])
                self.add_to_log(f"[{ipc_type.upper()}] Enviado: {message}")
                self.message_entry.delete(0, END)
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao enviar mensagem: {str(e)}")
    
    def test_socket_connection(self):
        """Testar conexão de sockets executando o client"""
        child_exe = "backend/sockets/child.exe"
        
        if not os.path.exists(child_exe):
            messagebox.showerror("Erro", f"Executável do client socket não encontrado: {child_exe}")
            return
            
        try:
            subprocess.Popen([child_exe])
            self.add_to_log("[SOCKET] Teste de conexão iniciado")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao testar conexão: {str(e)}")

def main():
    root = Tk()
    app = IPCApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()