# frontend/frontend.py
# IPC Demo - UI para Shared Memory, Sockets e Pipes
# Windows-ready (VS/MinGW). Auto-descobre os .exe e persiste escolhas.


import os, sys, json, threading, queue, subprocess, time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

# ---------- UTIL: base e config ----------
APP_DIR = os.path.abspath(os.path.dirname(__file__))
BASE    = os.path.abspath(os.path.join(APP_DIR, ".."))
CFGFILE = os.path.join(BASE, "ipc_config.json")
CREATE_NO_WINDOW = 0x08000000  # evitar console piscando no Windows

def load_cfg():
    try:
        with open(CFGFILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_cfg(cfg):
    try:
        with open(CFGFILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
=======
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
>>>>>>> baf3f0427a609b952a3f34e7e89b7e55ea3c2426

CFG = load_cfg()


def _candidates(subdir, *names):
    """Locais comuns de build do Visual Studio / MinGW."""
    root = os.path.join(BASE, "backend", subdir)
    xs = []
    for n in names:
        xs += [
            os.path.join(root, n),
            os.path.join(root, "Debug", n),
            os.path.join(root, "Release", n),
            os.path.join(root, "x64", "Debug", n),
            os.path.join(root, "x64", "Release", n),
            os.path.join(root, "Win32", "Debug", n),
            os.path.join(root, "Win32", "Release", n),
        ]
    return xs

def _find_first(paths, walk_root=None, walk_names=None):
    for p in paths:
        if os.path.isfile(p):
            return p
    if walk_root and walk_names:
        for r, _, files in os.walk(walk_root):
            low = [f.lower() for f in files]
            for target in walk_names:
                if target.lower() in low:
                    return os.path.join(r, files[low.index(target.lower())])
    return None

def ensure_exe(cfg_key, subdir, names, dialog_title):
    """
    Tenta na ordem:
      1) Caminho salvo no ipc_config.json (se existir)
      2) Locais típicos de build (Debug/Release/x64)
      3) Busca recursiva no subdir por qualquer 'names'
      4) Dialog para o usuário apontar o .exe
    """
    # 1) Config salvo
    p = CFG.get(cfg_key, "")
    if p and os.path.isfile(p):
        return p

    # 2) Candidatos comuns
    cand = _candidates(subdir, *names)
    p = _find_first(cand)
    if p:
        CFG[cfg_key] = p
        save_cfg(CFG)
        return p

    # 3) Busca recursiva
    p = _find_first([], walk_root=os.path.join(BASE, "backend", subdir), walk_names=names)
    if p:
        CFG[cfg_key] = p
        save_cfg(CFG)
        return p

    # 4) Dialog
    p = filedialog.askopenfilename(
        title=dialog_title,
        filetypes=[("Executável", "*.exe")],
        initialdir=os.path.join(BASE, "backend", subdir),
    )
    if p:
        CFG[cfg_key] = p
        save_cfg(CFG)
        return p
    return None
=======
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
>>>>>>> baf3f0427a609b952a3f34e7e89b7e55ea3c2426

# ---------- Infra de processos async ----------
class Proc:
    def __init__(self, name, cmd, cwd=None, stdin=False):
        self.name = name
        self.cmd = cmd
        self.cwd = cwd or (os.path.dirname(cmd[0]) if isinstance(cmd, (list, tuple)) else None)
        self.stdin_enabled = stdin
        self.p = None
        self.q = queue.Queue()
        self.reader_t = None
        self.alive = False

<<<<<<< HEAD
    def start(self):
        if self.p and self.p.poll() is None:
            return
        stdin = subprocess.PIPE if self.stdin_enabled else None
        self.p = subprocess.Popen(
            self.cmd,
            cwd=self.cwd,
            stdin=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
            creationflags=CREATE_NO_WINDOW
        )
        self.alive = True
        self.reader_t = threading.Thread(target=self._reader, daemon=True)
        self.reader_t.start()

    def _reader(self):
        try:
            for line in self.p.stdout:
                if not line:
                    break
                self.q.put(line.rstrip("\r\n"))
        except Exception as e:
            self.q.put(json.dumps({"event": "frontend_error", "detail": f"{self.name}: {e}"}))
        finally:
            self.alive = False

    def write_line(self, text):
        if not (self.p and self.stdin_enabled and self.p.poll() is None):
            return False
        try:
            self.p.stdin.write(text + "\n")
            self.p.stdin.flush()
            return True
        except Exception:
            return False

    def stop(self, kill=False):
        if self.p:
            if kill:
                self.p.kill()
            else:
                self.p.terminate()
            try:
                self.p.wait(timeout=1.2)
            except subprocess.TimeoutExpired:
                self.p.kill()
        self.p = None
        self.alive = False

# ---------- UI: Log ----------
class LogView:
    def __init__(self, parent):
        self.txt = scrolledtext.ScrolledText(parent, height=18, wrap="word", state="disabled")
        self.txt.pack(fill="both", expand=True, pady=(6,0))

    def _append(self, s):
        self.txt.configure(state="normal")
        self.txt.insert("end", s + "\n")
        self.txt.see("end")
        self.txt.configure(state="disabled")

    def add_raw(self, line):
        try:
            obj = json.loads(line)
            self._append(json.dumps(obj, ensure_ascii=False))
        except Exception:
            self._append(line)

# ---------- App ----------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("IPC Demo – Pipes | Sockets | Shared Memory")
        self.geometry("960x640")

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        self.tabs = {}
        self.tabs["shm"]     = self._build_shm_tab(nb)
        self.tabs["sockets"] = self._build_socket_tab(nb)
        self.tabs["pipes"]   = self._build_pipe_tab(nb)

        self.after(120, self._pump)

    # ===== SHM =====
    def _build_shm_tab(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="Memória Compartilhada")
        top = ttk.Frame(f); top.pack(fill="x", padx=10, pady=10)
        self.shm_log = LogView(f)
        self.shm_reader = None
        self.shm_writer = None

        ttk.Button(top, text="Init (shm+sems)", command=self.shm_init).pack(side="left", padx=5)
        ttk.Button(top, text="Start Reader",     command=self.shm_start_reader).pack(side="left", padx=5)
        ttk.Button(top, text="Stop Reader",      command=self.shm_stop_reader).pack(side="left", padx=5)
        ttk.Separator(top, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Button(top, text="Start Writer",     command=self.shm_start_writer).pack(side="left", padx=5)
        ttk.Button(top, text="Stop Writer",      command=self.shm_stop_writer).pack(side="left", padx=5)

        msgf = ttk.Frame(f); msgf.pack(fill="x", padx=10, pady=(0,10))
        ttk.Label(msgf, text="Mensagem:").pack(side="left")
        self.shm_msg = ttk.Entry(msgf, width=60); self.shm_msg.pack(side="left", padx=6)
        ttk.Button(msgf, text="Enviar", command=self.shm_send).pack(side="left", padx=5)
        return f

    def _shm_exe(self):
        p = ensure_exe(
            "EXE_SHM",
            "shared_memory",
            names=("shared_memory_portable.exe", "shared_memory.exe"),
            dialog_title="Selecione shared_memory*.exe"
        )
        if not p:
            messagebox.showerror("Erro", "shared_memory*.exe não encontrado.")
        return p

    def shm_init(self):
        exe = self._shm_exe()
        if not exe: return
        proc = Proc("shm_init", [exe, "init"])
        proc.start()
        time.sleep(0.2)
        while not proc.q.empty():
            self.shm_log.add_raw(proc.q.get_nowait())
        proc.stop()

    def shm_start_reader(self):
        exe = self._shm_exe()
        if not exe: return
        if self.shm_reader and self.shm_reader.alive: return
        self.shm_reader = Proc("shm_reader", [exe, "reader"])
        self.shm_reader.start()

    def shm_stop_reader(self):
        if self.shm_reader: self.shm_reader.stop()

    def shm_start_writer(self):
        exe = self._shm_exe()
        if not exe: return
        if self.shm_writer and self.shm_writer.alive: return
        self.shm_writer = Proc("shm_writer", [exe, "writer"], stdin=True)
        self.shm_writer.start()

    def shm_stop_writer(self):
        if self.shm_writer: self.shm_writer.stop()

    def shm_send(self):
        if not (self.shm_writer and self.shm_writer.alive):
            messagebox.showwarning("Aviso", "Inicie o Writer antes de enviar.")
            return
        msg = self.shm_msg.get().strip()
        if not msg: return
        if not self.shm_writer.write_line(msg):
            messagebox.showerror("Erro", "Falha ao escrever no stdin do writer.")

    # ===== SOCKETS =====
    def _build_socket_tab(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="Sockets (TCP localhost)")
        top = ttk.Frame(f); top.pack(fill="x", padx=10, pady=10)
        self.sock_log = LogView(f)
        self.sock_srv = None

        ttk.Button(top, text="Start Server", command=self.sock_start_server).pack(side="left", padx=5)
        ttk.Button(top, text="Stop Server",  command=self.sock_stop_server).pack(side="left", padx=5)

        ttk.Separator(top, orient="vertical").pack(side="left", fill="y", padx=8)
        msgf = ttk.Frame(f); msgf.pack(fill="x", padx=10, pady=(0,10))
        ttk.Label(msgf, text="Mensagem Cliente:").pack(side="left")
        self.sock_msg = ttk.Entry(msgf, width=60); self.sock_msg.pack(side="left", padx=6)
        ttk.Button(msgf, text="Send via Client", command=self.sock_send_client).pack(side="left", padx=5)
        return f

    def _sock_srv_exe(self):
        p = ensure_exe(
            "EXE_SOCK_SRV", "sockets",
            names=("server_socket.exe",),
            dialog_title="Selecione server_socket.exe"
        )
        if not p: messagebox.showerror("Erro", "server_socket.exe não encontrado.")
        return p

    def _sock_cli_exe(self):
        p = ensure_exe(
            "EXE_SOCK_CLI", "sockets",
            names=("client_socket.exe",),
            dialog_title="Selecione client_socket.exe"
        )
        if not p: messagebox.showerror("Erro", "client_socket.exe não encontrado.")
        return p

    def sock_start_server(self):
        exe = self._sock_srv_exe()
        if not exe: return
        if self.sock_srv and self.sock_srv.alive: return
        self.sock_srv = Proc("socket_server", [exe])
        self.sock_srv.start()

    def sock_stop_server(self):
        if self.sock_srv: self.sock_srv.stop()

    def sock_send_client(self):
        exe = self._sock_cli_exe()
        if not exe: return
        msg = self.sock_msg.get().strip()
        cmd = [exe] + ([msg] if msg else [])
        cli = Proc("socket_client", cmd)
        cli.start()
        time.sleep(0.25)
        while not cli.q.empty():
            self.sock_log.add_raw(cli.q.get_nowait())
        cli.stop()

    # ===== PIPES =====
    def _build_pipe_tab(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="Pipes Anônimos")
        top = ttk.Frame(f); top.pack(fill="x", padx=10, pady=10)
        self.pipe_log = LogView(f)
        self.pipe_srv = None

        ttk.Button(top, text="Start Pipe Server", command=self.pipe_start_server).pack(side="left", padx=5)
        ttk.Button(top, text="Stop Pipe Server",  command=self.pipe_stop_server).pack(side="left", padx=5)

        ttk.Separator(top, orient="vertical").pack(side="left", fill="y", padx=8)
        msgf = ttk.Frame(f); msgf.pack(fill="x", padx=10, pady=(0,10))
        ttk.Label(msgf, text="Mensagem:").pack(side="left")
        self.pipe_msg = ttk.Entry(msgf, width=60); self.pipe_msg.pack(side="left", padx=6)
        ttk.Button(msgf, text="Enviar (spawn writer)", command=self.pipe_send).pack(side="left", padx=5)
        return f

    def _pipe_srv_exe(self):
        p = ensure_exe(
            "EXE_PIPE_SRV", "pipes",
            names=("pipe_server_plus.exe", "pipe_server.exe"),
            dialog_title="Selecione pipe_server_plus.exe (ou pipe_server.exe)"
        )
        if not p: messagebox.showerror("Erro", "pipe_server_plus.exe não encontrado.")
        return p

    def pipe_start_server(self):
        exe = self._pipe_srv_exe()
        if not exe: return
        if self.pipe_srv and self.pipe_srv.alive: return
        self.pipe_srv = Proc("pipe_server", [exe], stdin=True)
        self.pipe_srv.start()

    def pipe_stop_server(self):
        if self.pipe_srv: self.pipe_srv.stop()

    def pipe_send(self):
        if not (self.pipe_srv and self.pipe_srv.alive):
            messagebox.showwarning("Aviso", "Inicie o Pipe Server antes de enviar.")
            return
        msg = self.pipe_msg.get().strip()
        if not msg: return
        if not self.pipe_srv.write_line(msg):
            messagebox.showerror("Erro", "Falha ao enviar para o servidor de pipe.")

    # ===== Pump das filas =====
    def _pump(self):
        # SHM
        for p, log in ((self.shm_reader, self.shm_log),
                       (self.shm_writer, self.shm_log),
                       (self.sock_srv,  self.sock_log),
                       (self.pipe_srv,  self.pipe_log)):
            if p:
                while not p.q.empty():
                    log.add_raw(p.q.get_nowait())
        self.after(120, self._pump)
=======
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
    App().mainloop()
