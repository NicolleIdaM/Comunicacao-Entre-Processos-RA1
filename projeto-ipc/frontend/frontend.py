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
        self.root.geometry("900x650")

        self.setup_styles()
        self.current_ipc_type = StringVar(value="pipes")
        self.server_process = None
        self.shared_memory_processes = {}
        self.socket_process = None
        self.pipes_process = None

        # Garante que o cwd é a pasta do script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)

        self.create_widgets()

    def setup_styles(self):
        style = ttk.Style()
        style.configure('TButton', padding=6)
        style.configure('Selected.TButton', background='#0078D7', foreground='white')
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'))

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(N, W, E, S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)

        # Título
        ttk.Label(main_frame, text="Sistema de Comunicação entre Processos", 
                 style='Title.TLabel').grid(row=0, column=0, columnspan=3, pady=10)

        # Seleção de IPC
        ttk.Label(main_frame, text="Selecione o mecanismo de IPC:").grid(row=1, column=0, sticky=W, pady=5)
        
        ipc_frame = ttk.Frame(main_frame)
        ipc_frame.grid(row=1, column=1, sticky=(W, E), pady=5)

        self.pipes_button = ttk.Button(ipc_frame, text="Pipes",
                                      command=lambda: self.set_ipc_type("pipes"))
        self.pipes_button.pack(side=LEFT, padx=2)

        self.sockets_button = ttk.Button(ipc_frame, text="Sockets",
                                        command=lambda: self.set_ipc_type("sockets"))
        self.sockets_button.pack(side=LEFT, padx=2)

        self.shared_memory_button = ttk.Button(ipc_frame, text="Shared Memory",
                                              command=lambda: self.set_ipc_type("shared_memory"))
        self.shared_memory_button.pack(side=LEFT, padx=2)

        self.highlight_selected_button()

        # Status da memória compartilhada
        self.shared_memory_status = StringVar(value="")
        ttk.Label(main_frame, textvariable=self.shared_memory_status).grid(row=1, column=2, sticky=E, pady=5)

        # Botões de controle
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)

        self.start_button = ttk.Button(button_frame, text="Iniciar Servidor", command=self.start_server)
        self.start_button.pack(side=LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="Parar Servidor", command=self.stop_server, state=DISABLED)
        self.stop_button.pack(side=LEFT, padx=5)

        ttk.Button(button_frame, text="Limpar Log", command=self.clear_log).pack(side=LEFT, padx=5)

        # Entrada de mensagem
        ttk.Label(main_frame, text="Mensagem:").grid(row=3, column=0, sticky=W, pady=5)
        
        self.message_entry = ttk.Entry(main_frame, width=50)
        self.message_entry.grid(row=3, column=1, sticky=(W, E), pady=5)
        self.message_entry.bind('<Return>', self.send_message)

        ttk.Button(main_frame, text="Enviar Mensagem", command=self.send_message).grid(row=3, column=2, padx=5)

        # Área de log
        ttk.Label(main_frame, text="Log de Comunicação:").grid(row=4, column=0, sticky=NW, pady=5)
        
        self.log_area = scrolledtext.ScrolledText(main_frame, width=85, height=25, state=DISABLED)
        self.log_area.grid(row=5, column=0, columnspan=3, sticky=(N, W, E, S), pady=5)

        # Barra de status
        self.status_var = StringVar(value="Pronto. Selecione um mecanismo de IPC.")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=SUNKEN, anchor=W)
        status_bar.grid(row=6, column=0, sticky=(W, E))

    def set_ipc_type(self, ipc_type):
        self.current_ipc_type.set(ipc_type)
        self.highlight_selected_button()
        
        if ipc_type == "shared_memory":
            self.shared_memory_status.set("Memória: Não inicializada")
            self.status_var.set("Shared Memory selecionado. Clique em 'Iniciar Servidor' para inicializar.")
        else:
            self.shared_memory_status.set("")
            self.status_var.set(f"{ipc_type.capitalize()} selecionado. Clique em 'Iniciar Servidor'.")
        
        self.add_to_log(f"Mecanismo alterado para: {ipc_type}")

    def highlight_selected_button(self):
        for btn in [self.pipes_button, self.sockets_button, self.shared_memory_button]:
            btn.state(['!pressed', '!selected'])
        
        current = self.current_ipc_type.get()
        if current == "pipes":
            self.pipes_button.state(['pressed', 'selected'])
        elif current == "sockets":
            self.sockets_button.state(['pressed', 'selected'])
        elif current == "shared_memory":
            self.shared_memory_button.state(['pressed', 'selected'])

    def add_to_log(self, msg):
        self.log_area.config(state=NORMAL)
        self.log_area.insert(END, msg + "\n")
        self.log_area.see(END)
        self.log_area.config(state=DISABLED)

    def clear_log(self):
        self.log_area.config(state=NORMAL)
        self.log_area.delete(1.0, END)
        self.log_area.config(state=DISABLED)
        self.add_to_log("Log limpo.")

    def start_server(self):
        ipc_type = self.current_ipc_type.get()
        
        if ipc_type == "shared_memory":
            self.start_shared_memory()
        elif ipc_type == "sockets":
            self.start_socket_server()
        elif ipc_type == "pipes":
            self.start_pipes_server()

    def stop_server(self):
        ipc_type = self.current_ipc_type.get()
        
        if ipc_type == "shared_memory":
            self.stop_shared_memory()
        elif ipc_type == "sockets":
            self.stop_socket_server()
        elif ipc_type == "pipes":
            self.stop_pipes_server()

    # ========== SHARED MEMORY METHODS ==========
    def start_shared_memory(self):
        try:
            self.run_shared_memory_command("cleanup")
            
            init_proc = self.run_shared_memory_command("init")
            return_code = init_proc.wait()
            
            if return_code == 0:
                self.shared_memory_status.set("Memória: Inicializada ✓")
                self.add_to_log("✅ Memória compartilhada inicializada com sucesso")
                
                self.shared_memory_processes['reader'] = self.run_shared_memory_command("reader")
                threading.Thread(target=self.read_shared_memory_output, 
                                args=(self.shared_memory_processes['reader'],), 
                                daemon=True).start()
                
                self.start_button.config(state=DISABLED)
                self.stop_button.config(state=NORMAL)
                self.status_var.set("Memória compartilhada inicializada e reader ativo")
            else:
                messagebox.showerror("Erro", "Falha ao inicializar memória compartilhada")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao iniciar memória compartilhada: {str(e)}")

    def stop_shared_memory(self):
        try:
            if 'reader' in self.shared_memory_processes:
                self.shared_memory_processes['reader'].terminate()
                try: 
                    self.shared_memory_processes['reader'].wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.shared_memory_processes['reader'].kill()
                del self.shared_memory_processes['reader']
            
            self.run_shared_memory_command("cleanup")
            self.shared_memory_status.set("Memória: Não inicializada")
            
            self.start_button.config(state=NORMAL)
            self.stop_button.config(state=DISABLED)
            self.status_var.set("Memória compartilhada parada")
            self.add_to_log("🛑 Memória compartilhada parada e limpa")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao parar memória compartilhada: {str(e)}")

    def run_shared_memory_command(self, command):
        backend_dir = os.path.join("..", "backend", "shared_memory", "output")
        exe_path = os.path.abspath(os.path.join(backend_dir, "shared_memory.exe"))
        
        if not os.path.exists(exe_path):
            raise FileNotFoundError(f"Executável não encontrado: {exe_path}")
        
        return subprocess.Popen([exe_path, command], 
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True, 
                               bufsize=1,
                               universal_newlines=True)

    def read_shared_memory_output(self, proc):
        while proc.poll() is None:
            out = proc.stdout.readline()
            if out:
                try:
                    self.root.after(0, lambda o=out.strip(): self.process_shared_memory_data(o))
                except:
                    pass

    def process_shared_memory_data(self, raw):
        try:
            if not raw.strip():
                return
            data = json.loads(raw)
            event = data.get('event', '')
            detail = data.get('detail', '')
            
            if event == "reader_received":
                self.add_to_log(f"📥 [SHM] Recebido: {detail}")
            elif event == "writer_sent":
                self.add_to_log(f"📤 [SHM] Enviado: {detail}")
            elif event == "error":
                self.add_to_log(f"❌ [SHM] Erro: {detail}")
            elif event == "reader_ready":
                self.add_to_log("✅ [SHM] Reader pronto e aguardando mensagens")
            elif event == "writer_ready":
                self.add_to_log("✅ [SHM] Writer pronto para enviar")
            elif event == "init_ok":
                self.add_to_log("✅ [SHM] Memória e semáforos inicializados")
            elif event == "cleanup_ok":
                self.add_to_log("✅ [SHM] Cleanup realizado")
            else:
                self.add_to_log(f"ℹ️ [SHM] {event}: {detail}")
        except json.JSONDecodeError:
            self.add_to_log(f"📄 [SHM] Saída: {raw}")

    def send_shared_memory_message(self, message):
        try:
            proc = self.run_shared_memory_command("writer")
            proc.stdin.write(message + "\n")
            proc.stdin.flush()
            proc.stdin.close()
            out, err = proc.communicate()
            if out:
                self.process_shared_memory_data(out.strip())
            if err:
                self.add_to_log(f"⚠️ [SHM] Erro no writer: {err}")
            self.add_to_log(f"📤 [SHM] Mensagem enviada: '{message}'")
            self.message_entry.delete(0, END)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao enviar mensagem: {str(e)}")
            self.add_to_log(f"❌ ERRO ao enviar mensagem: {str(e)}")

    # ========== SOCKETS METHODS (sem mudanças) ==========
    # ... (mantém como no seu arquivo)

    # ========== PIPES METHODS (sem mudanças) ==========
    # ... (mantém como no seu arquivo)

    # ========== SEND MESSAGE DISPATCHER ==========
    def send_message(self, event=None):
        msg = self.message_entry.get().strip()
        if not msg:
            return
        ipc_type = self.current_ipc_type.get()
        if ipc_type == "shared_memory":
            self.send_shared_memory_message(msg)
        elif ipc_type == "sockets":
            self.send_socket_message(msg)
        elif ipc_type == "pipes":
            self.send_pipes_message(msg)

def main():
    root = Tk()
    app = IPCApp(root)
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (900 // 2)
    y = (root.winfo_screenheight() // 2) - (650 // 2)
    root.geometry(f"900x650+{x}+{y}")
    root.mainloop()

if __name__ == "__main__":
    main()