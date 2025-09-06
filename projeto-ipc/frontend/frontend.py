# ipc_frontend_sockets_fixed.py
import os, sys, subprocess, threading, json, time
from tkinter import *
from tkinter import ttk, scrolledtext, messagebox, filedialog

BASE = os.path.abspath(os.path.dirname(__file__))
CFG  = os.path.join(BASE, "ipc_config.json")

def load_cfg():
    try:
        import json
        with open(CFG, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def save_cfg(d):
    try:
        import json
        with open(CFG, "w", encoding="utf-8") as f: json.dump(d, f, ensure_ascii=False, indent=2)
    except: pass

cfg = load_cfg()

def candidates(subdir, *names):
    root = os.path.abspath(os.path.join(BASE, "..", "backend", subdir))
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
    p = cfg.get(cfg_key)
    if p and os.path.isfile(p): return p
    # 2) candidatos
    paths, root, names_tuple = candidates(subdir, *names)
    for p in paths:
        if os.path.isfile(p):
            cfg[cfg_key] = p; save_cfg(cfg); return p
    # 3) busca recursiva
    for r,_,files in os.walk(root):
        for f in files:
            if f.lower() in [n.lower() for n in names_tuple]:
                p = os.path.join(r,f)
                cfg[cfg_key] = p; save_cfg(cfg); return p
    # 4) diálogo
    p = filedialog.askopenfilename(title=f"Selecione {names[0]}",
                                   initialdir=root, filetypes=[("Executável", "*.exe")])
    if p and os.path.isfile(p):
        cfg[cfg_key] = p; save_cfg(cfg); return p
    return None

class IPCApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Comunicação entre Processos - IPC")
        self.root.geometry("900x650")

        self.current_ipc_type = StringVar(value="sockets")
        self.server_process = None
        self.server_running = False

        self._build_ui()
        self._refresh_exec_status()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10); main.grid(row=0, column=0, sticky="nsew")
        self.root.rowconfigure(0, weight=1); self.root.columnconfigure(0, weight=1)
        for c in range(3): main.columnconfigure(c, weight=1)
        main.rowconfigure(5, weight=1)

        # seleção
        ttk.Label(main, text="Selecione o mecanismo de IPC:").grid(row=0, column=0, sticky="w")
        sel = ttk.Frame(main); sel.grid(row=0, column=1, sticky="w")
        self.btn_pipes   = ttk.Button(sel, text="Pipes", command=lambda:self.set_ipc("pipes")); self.btn_pipes.pack(side=LEFT, padx=2)
        self.btn_sockets = ttk.Button(sel, text="Sockets", command=lambda:self.set_ipc("sockets")); self.btn_sockets.pack(side=LEFT, padx=2)
        self.btn_shm     = ttk.Button(sel, text="Shared Memory", command=lambda:self.set_ipc("shared_memory")); self.btn_shm.pack(side=LEFT, padx=2)

        # controles
        cframe = ttk.Frame(main); cframe.grid(row=1, column=0, columnspan=3, pady=8, sticky="w")
        self.btn_start = ttk.Button(cframe, text="Iniciar Servidor", command=self.start_server); self.btn_start.pack(side=LEFT, padx=5)
        self.btn_stop  = ttk.Button(cframe, text="Parar Servidor", command=self.stop_server, state=DISABLED); self.btn_stop.pack(side=LEFT, padx=5)
        self.lbl_exec  = ttk.Label(cframe, text=""); self.lbl_exec.pack(side=LEFT, padx=10)

        ttk.Label(main, text="Mensagem:").grid(row=2, column=0, sticky="w")
        self.ent_msg = ttk.Entry(main); self.ent_msg.grid(row=2, column=1, sticky="ew"); self.ent_msg.bind("<Return>", self.send_message)
        self.btn_send = ttk.Button(main, text="Enviar via Cliente", command=self.send_message, state=DISABLED)
        self.btn_send.grid(row=2, column=2, sticky="e")

        ttk.Label(main, text="Estado do Mecanismo:").grid(row=3, column=0, sticky="w")
        self.status_label = ttk.Label(main, text="Servidor parado"); self.status_label.grid(row=3, column=1, columnspan=2, sticky="ew")

        ttk.Label(main, text="Log de Comunicação:").grid(row=4, column=0, sticky="w", pady=(10,0))
        self.log = scrolledtext.ScrolledText(main, height=24, state=DISABLED); self.log.grid(row=5, column=0, columnspan=3, sticky="nsew")

    def _log(self, s):
        self.log.config(state=NORMAL); self.log.insert(END, f"{time.strftime('%H:%M:%S')} - {s}\n")
        self.log.see(END); self.log.config(state=DISABLED)

    def set_ipc(self, kind):
        self.current_ipc_type.set(kind); self._log(f"Mecanismo de IPC alterado para: {kind}")
        self._refresh_exec_status()

    def _refresh_exec_status(self):
        kind = self.current_ipc_type.get()
        ok = False
        if kind == "sockets":
            self.sock_srv = find_exe("SOCK_SRV", "sockets", "server_socket.exe", "server.exe")
            self.sock_cli = find_exe("SOCK_CLI", "sockets", "client_socket.exe", "client.exe")
            ok = bool(self.sock_srv and self.sock_cli)
        elif kind == "pipes":
            self.pipe_srv = find_exe("PIPE_SRV", "pipes", "pipe_server_plus.exe", "parent.exe", "pipe_server.exe")
            self.pipe_cli = find_exe("PIPE_CLI", "pipes", "pipe_writer.exe", "child.exe")
            ok = bool(self.pipe_srv and self.pipe_cli)
        elif kind == "shared_memory":
            self.shm_exe  = find_exe("SHM_EXE", "shared_memory", "shared_memory_portable.exe", "shared_memory.exe")
            ok = bool(self.shm_exe)

        self.lbl_exec.config(text="✓ Executáveis OK" if ok else "✗ Executáveis faltando")
        self.btn_start.config(state=NORMAL if ok else DISABLED)
        if not ok: self.btn_send.config(state=DISABLED)

    # ---------- servidor ----------
    def start_server(self):
        if self.server_running: return
        kind = self.current_ipc_type.get()
        try:
            if kind == "sockets":
                exe = self.sock_srv; args = [exe]
            elif kind == "pipes":
                exe = self.pipe_srv; args = [exe]
            elif kind == "shared_memory":
                exe = self.shm_exe;  args = [exe, "reader"]
            else: return

            if not (exe and os.path.isfile(exe)):
                raise FileNotFoundError(f"Executável não encontrado: {exe}")

            # referência local evita 'NoneType.stderr'
            proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True, bufsize=1, universal_newlines=True)
            self.server_process = proc; self.server_running = True
            threading.Thread(target=self._reader_thread, args=(proc,), daemon=True).start()

            self.btn_start.config(state=DISABLED); self.btn_stop.config(state=NORMAL); self.btn_send.config(state=NORMAL)
            self.status_label.config(text=f"Servidor {kind} iniciado")
            self._log(f"Servidor {kind} iniciado: {exe}")

        except OSError as e:
            # 193 -> não é executável válido (caminho errado/arquivo inválido/arquitetura errada)
            messagebox.showerror("Erro", f"Falha ao iniciar servidor: {e}")
            self._log(f"ERRO: {e} - verifique se é realmente um .exe (server_socket.exe) do Windows")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao iniciar servidor: {e}")
            self._log(f"ERRO: {e}")

    def stop_server(self):
        if not self.server_running: return
        p = self.server_process; self.server_running = False; self.server_process = None
        try:
            if p:
                p.terminate()
                try: p.wait(timeout=2)
                except subprocess.TimeoutExpired: p.kill()
        finally:
            self.btn_start.config(state=NORMAL); self.btn_stop.config(state=DISABLED); self.btn_send.config(state=DISABLED)
            self.status_label.config(text="Servidor parado"); self._log("Servidor parado")

    def _reader_thread(self, proc):
        try:
            while proc.poll() is None:
                out = proc.stdout.readline()
                if out: self._handle_line(out.strip())
                err = proc.stderr.readline()
                if err: self._log(f"[stderr] {err.strip()}")
            # dreno final
            for s in (proc.stdout, proc.stderr):
                if s:
                    rest = s.read()
                    for ln in rest.splitlines():
                        if ln.strip(): self._handle_line(ln.strip())
        except Exception as e:
            self._log(f"Erro na leitura do servidor: {e}")

    def _handle_line(self, data):
        if not data: return
        try:
            obj = json.loads(data)
            mech = obj.get("mechanism","").upper()
            act  = obj.get("action","")
            msg  = obj.get("data","")
            self._log(f"[{mech}] {act}" + (f": {msg}" if msg else ""))
        except json.JSONDecodeError:
            self._log(data)

    # ---------- envio ----------
    def send_message(self, event=None):
        if not self.server_running:
            messagebox.showwarning("Aviso", "Inicie o servidor primeiro."); return
        msg = self.ent_msg.get().strip()
        if not msg: return
        kind = self.current_ipc_type.get()
        try:
            if kind == "sockets":
                exe = self.sock_cli; args = [exe, msg]
            elif kind == "pipes":
                exe = self.pipe_cli; args = [exe, msg]
            elif kind == "shared_memory":
                exe = self.shm_exe;  args = [exe, "writer"]
            else: return

            if not (exe and os.path.isfile(exe)):
                raise FileNotFoundError(f"Cliente não encontrado: {exe}")

            if kind == "shared_memory":
                p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     text=True, bufsize=1, universal_newlines=True)
                p.stdin.write(msg + "\n"); p.stdin.flush(); p.stdin.close()
            else:
                p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     text=True, bufsize=1, universal_newlines=True)
            threading.Thread(target=self._collect_client, args=(p,kind), daemon=True).start()
            self._log(f"Enviando mensagem: {msg}"); self.ent_msg.delete(0, END)
        except OSError as e:
            messagebox.showerror("Erro", f"Falha ao iniciar cliente: {e}")
            self._log(f"ERRO cliente: {e}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao enviar: {e}")
            self._log(f"ERRO ao enviar: {e}")

    def _collect_client(self, p, kind):
        try:
            out, err = p.communicate(timeout=10)
            for ln in (out or "").splitlines():
                if ln.strip(): self._handle_line(ln.strip())
            for ln in (err or "").splitlines():
                if ln.strip(): self._log(f"[{kind} stderr] {ln.strip()}")
        except subprocess.TimeoutExpired:
            p.kill(); self._log("Timeout no cliente")

if __name__ == "__main__":
    root = Tk(); app = IPCApp(root); root.mainloop()
