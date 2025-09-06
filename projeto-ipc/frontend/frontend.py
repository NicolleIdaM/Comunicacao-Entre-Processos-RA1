import os
import sys
import subprocess
import threading
import json
from tkinter import *
from tkinter import ttk, scrolledtext, messagebox

class IPCApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Comunicação entre Processos - IPC")
        self.root.geometry("800x600")

        self.setup_styles()

        self.current_ipc_type = StringVar(value="pipes")
        self.server_process = None

        # === Aqui garantimos que o cwd é o da pasta do script ===
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)

        self.create_widgets()

    def setup_styles(self):
        style = ttk.Style()
        style.configure('Selected.TButton', background='#0078D7', foreground='white')

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(N, W, E, S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)

        ttk.Label(main_frame, text="Selecione o mecanismo de IPC:")\
            .grid(row=0, column=0, sticky=W, pady=5)
        ipc_button_frame = ttk.Frame(main_frame)
        ipc_button_frame.grid(row=0, column=1, sticky=(W, E), pady=5)

        self.pipes_button = ttk.Button(ipc_button_frame, text="Pipes",
                                      command=lambda: self.set_ipc_type("pipes"))
        self.pipes_button.pack(side=LEFT, padx=2)

        self.sockets_button = ttk.Button(ipc_button_frame, text="Sockets",
                                         command=lambda: self.set_ipc_type("sockets"))
        self.sockets_button.pack(side=LEFT, padx=2)

        self.shared_memory_button = ttk.Button(ipc_button_frame, text="Shared Memory",
                                               command=lambda: self.set_ipc_type("shared_memory"))
        self.shared_memory_button.pack(side=LEFT, padx=2)

        self.highlight_selected_button()

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)

        self.start_button = ttk.Button(button_frame, text="Iniciar Servidor", command=self.start_server)
        self.start_button.pack(side=LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="Parar Servidor", command=self.stop_server, state=DISABLED)
        self.stop_button.pack(side=LEFT, padx=5)

        ttk.Label(main_frame, text="Mensagem:").grid(row=2, column=0, sticky=W, pady=5)
        self.message_entry = ttk.Entry(main_frame, width=40)
        self.message_entry.grid(row=2, column=1, sticky=(W, E), pady=5)
        self.message_entry.bind('<Return>', self.send_message)

        ttk.Button(main_frame, text="Enviar via Cliente", command=self.send_message)\
            .grid(row=2, column=2, padx=5)

        ttk.Label(main_frame, text="Log de Comunicação:").grid(row=3, column=0, sticky=NW, pady=5)
        self.log_area = scrolledtext.ScrolledText(main_frame, width=70, height=20, state=DISABLED)
        self.log_area.grid(row=4, column=0, columnspan=3, sticky=(N, W, E, S), pady=5)

        self.status_var = StringVar(value="Pronto")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=SUNKEN, anchor=W)
        status_bar.grid(row=1, column=0, sticky=(W, E))

    def set_ipc_type(self, ipc_type):
        self.current_ipc_type.set(ipc_type)
        self.highlight_selected_button()
        self.add_to_log(f"Mecanismo de IPC alterado para: {ipc_type}")

    def highlight_selected_button(self):
        for b in [self.pipes_button, self.sockets_button, self.shared_memory_button]:
            b.state(['!pressed', '!selected'])
        cur = self.current_ipc_type.get()
        if cur == "pipes":
            self.pipes_button.state(['pressed', 'selected'])
        elif cur == "sockets":
            self.sockets_button.state(['pressed', 'selected'])
        elif cur == "shared_memory":
            self.shared_memory_button.state(['pressed', 'selected'])

    def add_to_log(self, msg):
        self.log_area.config(state=NORMAL)
        self.log_area.insert(END, msg + "\n")
        self.log_area.see(END)
        self.log_area.config(state=DISABLED)

    def start_server(self):
        ipc = self.current_ipc_type.get()
        backend = os.path.join("..", "backend", ipc, "output")
        exe = "server.exe" if ipc == "sockets" else "parent.exe"
        server_exe = os.path.abspath(os.path.join(backend, exe))

        if not os.path.exists(server_exe):
            messagebox.showerror("Erro", f"Executável do servidor não encontrado: {server_exe}")
            self.add_to_log(f"ERRO: Executável não encontrado: {server_exe}")
            return

        try:
            self.server_process = subprocess.Popen([server_exe], stdout=subprocess.PIPE,
                                                   stderr=subprocess.PIPE, text=True, bufsize=1,
                                                   universal_newlines=True)
            threading.Thread(target=self.read_server_output,
                             args=(self.server_process,), daemon=True).start()
            self.start_button.config(state=DISABLED)
            self.stop_button.config(state=NORMAL)
            self.status_var.set(f"Servidor {ipc} iniciado")
            self.add_to_log(f"Servidor {ipc} iniciado")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao iniciar servidor: {e}")
            self.add_to_log(f"ERRO ao iniciar servidor: {e}")

    def stop_server(self):
        if self.server_process:
            self.server_process.terminate()
            try: self.server_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            self.server_process = None
        self.start_button.config(state=NORMAL)
        self.stop_button.config(state=DISABLED)
        self.status_var.set("Servidor parado")
        self.add_to_log("Servidor parado")

    def read_server_output(self, proc):
        while proc.poll() is None:
            out = proc.stdout.readline()
            if out:
                self.root.after(0, lambda o=out.strip(): self.process_backend_data(o))
        # pode adicionar leitura de stderr se quiser

    def process_backend_data(self, raw):
        try:
            data = json.loads(raw)
            action = data.get('action', '')
            mech = data.get('mechanism', '').upper()
            msg = data.get('data', '')
            if action == 'received':
                self.add_to_log(f"[{mech}] Recebido: {msg}")
            elif action == 'sent':
                self.add_to_log(f"[{mech}] Enviado: {msg}")
            elif action == 'connected':
                self.add_to_log(f"[{mech}] Cliente conectado")
            elif action == 'error':
                self.add_to_log(f"[{mech}] Erro: {data.get('type')} - código {data.get('code')}")
            else:
                self.add_to_log(f"[{mech}] Ação: {action}")
        except json.JSONDecodeError:
            self.add_to_log(f"Saída não JSON: {raw}")

    def send_message(self, event=None):
        msg = self.message_entry.get().strip()
        if not msg: return
        ipc = self.current_ipc_type.get()
        backend = os.path.join("..", "backend", ipc, "output")
        exe = "client.exe" if ipc == "sockets" else "child.exe"
        client_exe = os.path.abspath(os.path.join(backend, exe))

        if not os.path.exists(client_exe):
            messagebox.showerror("Erro", f"Executável do cliente não encontrado: {client_exe}")
            self.add_to_log(f"ERRO: Executável não encontrado: {client_exe}")
            return

        try:
            threading.Thread(target=self.run_socket_client, args=([client_exe, msg],), daemon=True).start()
            self.add_to_log(f"[{ipc.upper()}] Enviado via Cliente: {msg}")
            self.message_entry.delete(0, END)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao enviar mensagem via cliente: {e}")
            self.add_to_log(f"ERRO ao enviar mensagem: {e}")

    def run_socket_client(self, args):
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, bufsize=1, universal_newlines=True)
        out, err = proc.communicate()
        if out:
            self.root.after(0, lambda: self.process_backend_data(out.strip()))
        if err:
            self.root.after(0, lambda: self.add_to_log(f"Erro do cliente: {err}"))

def main():
    root = Tk()
    app = IPCApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
