import os
import sys
import subprocess
import threading
import json
from tkinter import *
from tkinter import ttk, scrolledtext, messagebox, filedialog
import time
import ctypes
from ctypes import wintypes

# Carregar configurações
def load_config():
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ipc_config.json")
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_config(config):
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ipc_config.json")
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    except:
        pass

config = load_config()

def candidates(subdir, *names):
    root = os.path.abspath(os.path.join("..", "backend", subdir))
    outs = []
    for n in names:
        outs += [
            os.path.join(root, n),
            os.path.join(root, "output", n),
            os.path.join(root, "Debug", n),
            os.path.join(root, "Release", n),
            os.path.join(root, "x64", "Debug", n),
            os.path.join(root, "x64", "Release", n),
            os.path.join(root, "Win32", "Debug", n),
            os.path.join(root, "Win32", "Release", n),
        ]
    return outs, root, names

def find_exe(cfg_key, subdir, *names):
    # 1) salvo
    p = config.get(cfg_key)
    if p and os.path.isfile(p): return p
    # 2) candidatos
    paths, root, names_tuple = candidates(subdir, *names)
    for p in paths:
        if os.path.isfile(p):
            config[cfg_key] = p; save_config(config); return p
    # 3) busca recursiva
    for r,_,files in os.walk(root):
        for f in files:
            if f.lower() in [n.lower() for n in names_tuple]:
                p = os.path.join(r,f)
                config[cfg_key] = p; save_config(config); return p
    # 4) diálogo
    p = filedialog.askopenfilename(title=f"Selecione {names[0]}",
                                   initialdir=root, filetypes=[("Executável", "*.exe")])
    if p and os.path.isfile(p):
        config[cfg_key] = p; save_config(config); return p
    return None

# Funções para criar memória compartilhada diretamente do Python
class SharedMemoryManager:
    def __init__(self):
        self.kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        self.setup_functions()
        
    def setup_functions(self):
        # CreateFileMapping
        self.kernel32.CreateFileMappingW.argtypes = [
            wintypes.HANDLE,  # hFile
            ctypes.c_void_p,  # lpAttributes
            wintypes.DWORD,   # flProtect
            wintypes.DWORD,   # dwMaximumSizeHigh
            wintypes.DWORD,   # dwMaximumSizeLow
            wintypes.LPCWSTR  # lpName
        ]
        self.kernel32.CreateFileMappingW.restype = wintypes.HANDLE
        
        # MapViewOfFile
        self.kernel32.MapViewOfFile.argtypes = [
            wintypes.HANDLE,  # hFileMappingObject
            wintypes.DWORD,   # dwDesiredAccess
            wintypes.DWORD,   # dwFileOffsetHigh
            wintypes.DWORD,   # dwFileOffsetLow
            ctypes.c_size_t   # dwNumberOfBytesToMap
        ]
        self.kernel32.MapViewOfFile.restype = ctypes.c_void_p
        
        # UnmapViewOfFile
        self.kernel32.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
        self.kernel32.UnmapViewOfFile.restype = wintypes.BOOL
        
        # CloseHandle
        self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel32.CloseHandle.restype = wintypes.BOOL
        
        # CreateSemaphore
        self.kernel32.CreateSemaphoreW.argtypes = [
            ctypes.c_void_p,  # lpSemaphoreAttributes
            wintypes.LONG,    # lInitialCount
            wintypes.LONG,    # lMaximumCount
            wintypes.LPCWSTR  # lpName
        ]
        self.kernel32.CreateSemaphoreW.restype = wintypes.HANDLE
        
        # OpenSemaphore
        self.kernel32.OpenSemaphoreW.argtypes = [
            wintypes.DWORD,   # dwDesiredAccess
            wintypes.BOOL,    # bInheritHandle
            wintypes.LPCWSTR  # lpName
        ]
        self.kernel32.OpenSemaphoreW.restype = wintypes.HANDLE
        
        # ReleaseSemaphore
        self.kernel32.ReleaseSemaphore.argtypes = [
            wintypes.HANDLE,  # hSemaphore
            wintypes.LONG,    # lReleaseCount
            ctypes.POINTER(wintypes.LONG)  # lpPreviousCount
        ]
        self.kernel32.ReleaseSemaphore.restype = wintypes.BOOL
        
        # WaitForSingleObject
        self.kernel32.WaitForSingleObject.argtypes = [
            wintypes.HANDLE,  # hHandle
            wintypes.DWORD    # dwMilliseconds
        ]
        self.kernel32.WaitForSingleObject.restype = wintypes.DWORD

class IPCApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Comunicação entre Processos - IPC")
        self.root.geometry("800x600")

        self.setup_styles()

        self.current_ipc_type = StringVar(value="pipes")
        self.server_process = None
        self.server_running = False
        self.current_server_type = None
        self.shm_manager = SharedMemoryManager()

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

        self.clear_button = ttk.Button(button_frame, text="Limpar Log", command=self.clear_log)
        self.clear_button.pack(side=LEFT, padx=5)

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
        
        server_exists = False
        client_exists = False
        
        if ipc == "sockets":
            self.sock_srv = find_exe("SOCK_SRV", "sockets", "server.exe", "server_socket.exe")
            self.sock_cli = find_exe("SOCK_CLI", "sockets", "client.exe", "client_socket.exe")
            server_exists = bool(self.sock_srv)
            client_exists = bool(self.sock_cli)
            
        elif ipc == "pipes":
            self.pipe_srv = find_exe("PIPE_SRV", "pipes", "parent.exe", "pipe_server.exe")
            self.pipe_cli = find_exe("PIPE_CLI", "pipes", "child.exe", "pipe_writer.exe")
            server_exists = bool(self.pipe_srv)
            client_exists = bool(self.pipe_cli)
            
        elif ipc == "shared_memory":
            self.shm_exe = find_exe("SHM_EXE", "shared_memory", "shared_memory.exe")
            server_exists = bool(self.shm_exe)
            client_exists = server_exists

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
        
        try:
            if ipc == "sockets":
                exe = self.sock_srv
                args = [exe]
                
            elif ipc == "pipes":
                exe = self.pipe_srv
                args = [exe]
                
            elif ipc == "shared_memory":
                exe = self.shm_exe
                
                # SOLUÇÃO DEFINITIVA: Não usar init externo, criar a memória aqui mesmo
                self.add_to_log("Criando memória compartilhada...")
                
                # Fazer cleanup primeiro
                self._cleanup_shared_memory()
                
                # Pequena pausa
                time.sleep(1)
                
                args = [exe, "reader"]

            if not exe or not os.path.exists(exe):
                raise FileNotFoundError(f"Executável não encontrado: {exe}")

            # Iniciar o servidor
            proc = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            self.server_process = proc
            self.server_running = True
            self.current_server_type = ipc
            
            # Thread para monitorar a saída
            threading.Thread(target=self._monitor_server, daemon=True).start()
            
            self.start_button.config(state=DISABLED)
            self.stop_button.config(state=NORMAL)
            self.send_button.config(state=NORMAL)
            self.status_var.set(f"Servidor {ipc} iniciado")
            self.add_to_log(f"Servidor {ipc} iniciado")
            self.update_visualization("running")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao iniciar servidor: {str(e)}")
            self.add_to_log(f"ERRO: {str(e)}")

    def _cleanup_shared_memory(self):
        """Cleanup da memória compartilhada usando o executável"""
        if not self.shm_exe or not os.path.exists(self.shm_exe):
            return
            
        try:
            # Executar cleanup
            cleanup_args = [self.shm_exe, "cleanup"]
            result = subprocess.run(cleanup_args, capture_output=True, text=True, timeout=5,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result.returncode == 0:
                self.add_to_log("Cleanup da memória compartilhada realizado")
            else:
                self.add_to_log(f"Cleanup retornou código {result.returncode}")
                
        except Exception as e:
            self.add_to_log(f"Erro no cleanup: {e}")

    def _monitor_server(self):
        """Monitora o servidor em execução"""
        try:
            while self.server_running and self.server_process and self.server_process.poll() is None:
                # Ler stdout
                stdout_line = self.server_process.stdout.readline()
                if stdout_line:
                    self.root.after(0, lambda l=stdout_line.strip(): self._handle_output(l))
                
                # Ler stderr
                stderr_line = self.server_process.stderr.readline()
                if stderr_line:
                    self.root.after(0, lambda l=stderr_line.strip(): self._handle_error(l))
                
                time.sleep(0.1)
                
        except Exception as e:
            if self.server_running:
                self.root.after(0, lambda: self.add_to_log(f"Erro no monitoramento: {e}"))

    def _handle_output(self, line):
        """Processa a saída do servidor"""
        if not line:
            return
            
        try:
            # Verificar se é JSON
            if line.startswith('{') and line.endswith('}'):
                data = json.loads(line)
                mechanism = data.get("mechanism", "")
                action = data.get("action", "")
                message = data.get("data", "")
                event = data.get("event", "")
                detail = data.get("detail", "")
                
                if mechanism:
                    log_msg = f"[{mechanism.upper()}] {action}"
                    if message:
                        log_msg += f": {message}"
                    self.add_to_log(log_msg)
                elif event:
                    log_msg = f"[SHM] {event}"
                    if detail:
                        log_msg += f": {detail}"
                    self.add_to_log(log_msg)
            else:
                self.add_to_log(line)
                
        except json.JSONDecodeError:
            self.add_to_log(line)

    def _handle_error(self, line):
        """Processa erros do servidor"""
        if line and line.strip():
            self.add_to_log(f"[ERRO] {line}")

    def stop_server(self):
        if not self.server_running:
            return
            
        try:
            if self.server_process:
                if self.server_process.poll() is None:
                    self.server_process.terminate()
                    try:
                        self.server_process.wait(timeout=2)
                    except:
                        self.server_process.kill()
                        self.server_process.wait(timeout=1)
                
            # Cleanup para shared memory
            if self.current_server_type == "shared_memory":
                self._cleanup_shared_memory()
                
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

    def send_message(self, event=None):
        if not self.server_running:
            messagebox.showwarning("Aviso", "O servidor não está em execução. Inicie o servidor primeiro.")
            return
            
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
        
        try:
            # Confirmação imediata
            self.add_to_log(f"Mensagem enviada: {msg}")
            
            if ipc == "sockets":
                exe = self.sock_cli
                args = [exe, msg]
                self._run_client(args)
                
            elif ipc == "pipes":
                exe = self.pipe_cli
                args = [exe, msg]
                self._run_client(args)
                
            elif ipc == "shared_memory":
                exe = self.shm_exe
                args = [exe, "writer"]
                self._run_shared_memory_writer(exe, msg)
                
            self.message_entry.delete(0, END)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao enviar mensagem: {str(e)}")
            self.add_to_log(f"ERRO ao enviar: {str(e)}")

    def _run_client(self, args):
        """Executa cliente normal"""
        try:
            p = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            threading.Thread(target=self._monitor_client, args=(p,), daemon=True).start()
        except Exception as e:
            self.add_to_log(f"Erro ao executar cliente: {e}")

    def _run_shared_memory_writer(self, exe, message):
        """Executa writer da memória compartilhada"""
        try:
            # Pequena pausa para garantir que o reader está pronto
            time.sleep(0.5)
            
            p = subprocess.Popen(
                [exe, "writer"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Usar communicate para evitar problemas de sincronização
            stdout_data, stderr_data = p.communicate(input=message + "\n", timeout=10)
            
            if stdout_data:
                for line in stdout_data.splitlines():
                    if line.strip():
                        self._handle_output(line.strip())
            if stderr_data:
                for line in stderr_data.splitlines():
                    if line.strip():
                        self.add_to_log(f"[writer stderr] {line}")
                        
        except subprocess.TimeoutExpired:
            self.add_to_log("Timeout no writer")
        except Exception as e:
            self.add_to_log(f"Erro no writer: {e}")

    def _monitor_client(self, process):
        """Monitora a saída do cliente"""
        try:
            stdout, stderr = process.communicate(timeout=10)
            
            if stdout:
                for line in stdout.splitlines():
                    if line.strip():
                        self.root.after(0, lambda l=line.strip(): self._handle_output(l))
            
            if stderr:
                for line in stderr.splitlines():
                    if line.strip():
                        self.root.after(0, lambda l=line.strip(): self.add_to_log(f"[cliente stderr] {l}"))
                        
        except subprocess.TimeoutExpired:
            process.kill()
            self.root.after(0, lambda: self.add_to_log("Timeout no cliente"))
        except Exception as e:
            self.root.after(0, lambda: self.add_to_log(f"Erro no cliente: {e}"))

def main():
    root = Tk()
    app = IPCApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()