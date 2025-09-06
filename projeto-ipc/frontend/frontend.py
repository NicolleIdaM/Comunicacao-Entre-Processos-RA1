import os
import sys
import subprocess
import threading
import json
from tkinter import *
from tkinter import ttk, scrolledtext, messagebox
import time

class IPCApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Comunicação entre Processos - IPC")
        self.root.geometry("800x600")

        self.setup_styles()

        self.current_ipc_type = StringVar(value="pipes")
        self.server_process = None
        self.client_processes = []
        self.server_running = False
        self.current_server_type = None  # Para controlar qual IPC está rodando

        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)

        self.create_widgets()
        self.check_executables()

    def setup_styles(self):
        style = ttk.Style()
        style.configure('Selected.TButton', background='#0078D7', foreground='white')
        style.configure('Disabled.TButton', background='#cccccc')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Success.TLabel', foreground='green')

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(N, W, E, S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)

        # Seleção de IPC
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

        # Controles do servidor
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)

        self.start_button = ttk.Button(button_frame, text="Iniciar Servidor", command=self.start_server)
        self.start_button.pack(side=LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="Parar Servidor", command=self.stop_server, state=DISABLED)
        self.stop_button.pack(side=LEFT, padx=5)

        # Botão para limpar log
        self.clear_button = ttk.Button(button_frame, text="Limpar Log", command=self.clear_log)
        self.clear_button.pack(side=LEFT, padx=5)

        # Status do executável
        self.exe_status = ttk.Label(button_frame, text="", style='Error.TLabel')
        self.exe_status.pack(side=LEFT, padx=10)

        # Entrada de mensagem
        ttk.Label(main_frame, text="Mensagem:").grid(row=2, column=0, sticky=W, pady=5)
        self.message_entry = ttk.Entry(main_frame, width=40)
        self.message_entry.grid(row=2, column=1, sticky=(W, E), pady=5)
        self.message_entry.bind('<Return>', self.send_message)

        self.send_button = ttk.Button(main_frame, text="Enviar via Cliente", command=self.send_message, state=DISABLED)
        self.send_button.grid(row=2, column=2, padx=5)

        # Frame de visualização
        ttk.Label(main_frame, text="Estado do Mecanismo:").grid(row=3, column=0, sticky=NW, pady=5)
        self.status_frame = ttk.Frame(main_frame, relief=SUNKEN, padding=5)
        self.status_frame.grid(row=3, column=1, columnspan=2, sticky=(W, E), pady=5)
        
        self.status_label = ttk.Label(self.status_frame, text="Selecione um mecanismo e inicie o servidor")
        self.status_label.pack()

        # Área de log
        ttk.Label(main_frame, text="Log de Comunicação:").grid(row=4, column=0, sticky=NW, pady=5)
        self.log_area = scrolledtext.ScrolledText(main_frame, width=70, height=15, state=DISABLED)
        self.log_area.grid(row=5, column=0, columnspan=3, sticky=(N, W, E, S), pady=5)

        # Barra de status
        self.status_var = StringVar(value="Pronto")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=SUNKEN, anchor=W)
        status_bar.grid(row=1, column=0, sticky=(W, E))

    def clear_log(self):
        self.log_area.config(state=NORMAL)
        self.log_area.delete(1.0, END)
        self.log_area.config(state=DISABLED)
        self.add_to_log("Log limpo")

    def check_executables(self):
        self.set_ipc_type(self.current_ipc_type.get())

    def set_ipc_type(self, ipc_type):
        # Se já tem um servidor rodando de outro tipo, não permite mudar
        if self.server_running and ipc_type != self.current_server_type:
            messagebox.showwarning("Aviso", 
                f"Pare o servidor {self.current_server_type} primeiro antes de mudar para {ipc_type}")
            return
            
        self.current_ipc_type.set(ipc_type)
        self.highlight_selected_button()
        self.update_visualization()
        self.verify_executables()
        self.add_to_log(f"Mecanismo de IPC alterado para: {ipc_type}")

    def verify_executables(self):
        ipc = self.current_ipc_type.get()
        backend = os.path.join("..", "backend", ipc, "output")
        
        server_exists = False
        client_exists = False
        
        if ipc == "sockets":
            server_exe = os.path.join(backend, "server.exe")
            client_exe = os.path.join(backend, "client.exe")
            server_exists = os.path.exists(server_exe)
            client_exists = os.path.exists(client_exe)
            
        elif ipc == "pipes":
            server_exe = os.path.join(backend, "parent.exe")
            client_exe = os.path.join(backend, "child.exe")
            server_exists = os.path.exists(server_exe)
            client_exists = os.path.exists(client_exe)
            
        elif ipc == "shared_memory":
            server_exe = os.path.join(backend, "shared_memory.exe")
            server_exists = os.path.exists(server_exe)
            client_exists = server_exists  # Usa o mesmo executável

        if server_exists and client_exists:
            self.exe_status.config(text="✓ Executáveis OK", style='Success.TLabel')
            self.start_button.config(state=NORMAL)
        else:
            self.exe_status.config(text="✗ Executáveis faltando", style='Error.TLabel')
            self.start_button.config(state=DISABLED)
            self.send_button.config(state=DISABLED)

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

    def update_visualization(self, status="stopped"):
        ipc_type = self.current_ipc_type.get()
        
        if ipc_type == "pipes":
            if status == "running":
                self.status_label.config(text="Pipe: Ativo | Buffer: Pronto | Processos: 1+")
            else:
                self.status_label.config(text="Pipe: Inativo | Buffer: Vazio | Processos: 0")
                
        elif ipc_type == "sockets":
            if status == "running":
                self.status_label.config(text="Socket: Escutando | Porta: 8080 | Conexões: 0")
            else:
                self.status_label.config(text="Socket: Desconectado | Porta: 8080 | Conexões: 0")
                
        elif ipc_type == "shared_memory":
            if status == "running":
                self.status_label.config(text="Memória: Ativa | Tamanho: 256B | Semáforos: Ok")
            else:
                self.status_label.config(text="Memória: Inativa | Tamanho: 256B | Semáforos: -")

    def add_to_log(self, msg):
        self.log_area.config(state=NORMAL)
        self.log_area.insert(END, f"{time.strftime('%H:%M:%S')} - {msg}\n")
        self.log_area.see(END)
        self.log_area.config(state=DISABLED)

    def start_server(self):
        if self.server_running:
            return
            
        ipc = self.current_ipc_type.get()
        backend = os.path.join("..", "backend", ipc, "output")
        
        try:
            if ipc == "sockets":
                server_exe = os.path.abspath(os.path.join(backend, "server.exe"))
                args = [server_exe]
                
            elif ipc == "pipes":
                server_exe = os.path.abspath(os.path.join(backend, "parent.exe"))
                args = [server_exe]
                
            elif ipc == "shared_memory":
                server_exe = os.path.abspath(os.path.join(backend, "shared_memory.exe"))
                # Primeiro inicializa a memória compartilhada
                init_args = [server_exe, "init"]
                try:
                    init_process = subprocess.run(init_args, capture_output=True, text=True, timeout=5)
                    if init_process.returncode != 0:
                        error_msg = init_process.stderr if init_process.stderr else "Erro desconhecido na inicialização"
                        raise Exception(f"Erro na inicialização: {error_msg}")
                except FileNotFoundError:
                    raise Exception("Executável não encontrado. Execute compile.bat primeiro!")
                
                args = [server_exe, "reader"]

            # Verificar se o executável existe
            if not os.path.exists(server_exe):
                raise FileNotFoundError(f"Executável não encontrado: {server_exe}")

            # Iniciar o servidor
            self.server_process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            self.server_running = True
            self.current_server_type = ipc
            threading.Thread(target=self.read_server_output, daemon=True).start()
            
            self.start_button.config(state=DISABLED)
            self.stop_button.config(state=NORMAL)
            self.send_button.config(state=NORMAL)
            self.status_var.set(f"Servidor {ipc} iniciado")
            self.add_to_log(f"Servidor {ipc} iniciado")
            self.update_visualization("running")
            
        except FileNotFoundError:
            messagebox.showerror("Erro", 
                "Executável não encontrado.\n\n"
                "Execute os arquivos compile.bat nas pastas do backend:\n"
                "1. backend\\pipes\\compile.bat\n"
                "2. backend\\sockets\\compile.bat\n" 
                "3. backend\\shared_memory\\compile.bat")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao iniciar servidor: {str(e)}")
            self.add_to_log(f"ERRO: {str(e)}")

    def stop_server(self):
        if not self.server_running:
            return
            
        try:
            if self.server_process:
                # Tentar terminar gracefulmente
                self.server_process.terminate()
                try:
                    self.server_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    # Forçar término se não responder
                    self.server_process.kill()
                    self.server_process.wait(timeout=1)
                
            self.server_running = False
            self.current_server_type = None
            self.server_process = None
            
            self.start_button.config(state=NORMAL)
            self.stop_button.config(state=DISABLED)
            self.send_button.config(state=DISABLED)
            self.status_var.set("Servidor parado")
            self.add_to_log("Servidor parado")
            self.update_visualization("stopped")
            
        except Exception as e:
            self.add_to_log(f"Erro ao parar servidor: {e}")

    def read_server_output(self):
        while self.server_running and self.server_process:
            try:
                # Ler stdout
                if self.server_process.stdout:
                    line = self.server_process.stdout.readline()
                    if line:
                        self.process_backend_data(line.strip())
                
                # Ler stderr
                if self.server_process and self.server_process.stderr:
                    err_line = self.server_process.stderr.readline()
                    if err_line and err_line.strip():
                        self.add_to_log(f"ERRO: {err_line.strip()}")
                        
                # Pequena pausa para não sobrecarregar
                time.sleep(0.1)
                    
            except Exception as e:
                if self.server_running:  # Só logar se ainda deveria estar rodando
                    self.add_to_log(f"Erro na leitura do servidor: {e}")
                break

    def process_backend_data(self, data):
        try:
            if not data or not data.strip():
                return
                
            # Tentar parsear como JSON
            try:
                json_data = json.loads(data)
                mechanism = json_data.get('mechanism', '')
                action = json_data.get('action', '')
                message_data = json_data.get('data', '')
                
                log_msg = f"[{mechanism.upper()}] {action}"
                if message_data:
                    log_msg += f": {message_data}"
                
                self.add_to_log(log_msg)
                
                # Atualizar visualização para shared memory
                if self.current_ipc_type.get() == "shared_memory" and action == "received":
                    self.status_label.config(text=f"Memória: Ativa | Conteúdo: {message_data}")
                    
            except json.JSONDecodeError:
                # Se não for JSON, mostrar como texto simples
                if data.strip() and not data.startswith('{') and not data.startswith('['):
                    self.add_to_log(f"Saída: {data}")
                
        except Exception as e:
            self.add_to_log(f"Erro ao processar dados: {e}")

    def send_message(self, event=None):
        if not self.server_running:
            messagebox.showwarning("Aviso", "O servidor não está em execução. Inicie o servidor primeiro.")
            return
            
        # Verificar se está tentando enviar para o IPC correto
        if self.current_ipc_type.get() != self.current_server_type:
            messagebox.showwarning("Aviso", 
                f"Você está tentando enviar para {self.current_ipc_type.get()}, "
                f"mas o servidor ativo é {self.current_server_type}. "
                "Pare o servidor atual primeiro.")
            return
            
        msg = self.message_entry.get().strip()
        if not msg:
            return
            
        ipc = self.current_ipc_type.get()
        backend = os.path.join("..", "backend", ipc, "output")
        
        try:
            if ipc == "sockets":
                client_exe = os.path.abspath(os.path.join(backend, "client.exe"))
                args = [client_exe, msg]
                
            elif ipc == "pipes":
                client_exe = os.path.abspath(os.path.join(backend, "child.exe"))
                args = [client_exe, msg]
                
            elif ipc == "shared_memory":
                client_exe = os.path.abspath(os.path.join(backend, "shared_memory.exe"))
                args = [client_exe, "writer"]

            # Verificar se o cliente existe
            if not os.path.exists(client_exe):
                raise FileNotFoundError(f"Cliente não encontrado: {client_exe}")

            # Executar o cliente
            if ipc == "shared_memory":
                # Para shared memory, enviar mensagem via stdin
                proc = subprocess.Popen(
                    args,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                proc.stdin.write(msg + "\n")
                proc.stdin.flush()
            else:
                proc = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

            threading.Thread(target=self.read_client_output, args=(proc,), daemon=True).start()
            self.add_to_log(f"Enviando mensagem: {msg}")
            self.message_entry.delete(0, END)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao enviar mensagem: {str(e)}")
            self.add_to_log(f"ERRO ao enviar: {str(e)}")

    def read_client_output(self, proc):
        try:
            stdout, stderr = proc.communicate(timeout=10)
            
            if stdout:
                for line in stdout.splitlines():
                    if line.strip():
                        self.root.after(0, lambda l=line.strip(): self.process_backend_data(l))
            
            if stderr:
                for line in stderr.splitlines():
                    if line.strip():
                        self.root.after(0, lambda l=line.strip(): self.add_to_log(f"ERRO Cliente: {l}"))
                        
        except subprocess.TimeoutExpired:
            if proc:
                proc.kill()
            self.add_to_log("Timeout no cliente")
        except Exception as e:
            self.add_to_log(f"Erro no cliente: {e}")

def main():
    root = Tk()
    app = IPCApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()