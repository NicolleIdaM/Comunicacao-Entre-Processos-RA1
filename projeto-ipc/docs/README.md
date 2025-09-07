# 🔄 Comunicação Entre Processos - IPC

Este projeto tem como finalidade implementar **três mecanismos de comunicação entre processos (IPC)** em C/C++ com uma interface gráfica em Python para controle e visualização em tempo real.

---

## 📁 Estrutura do Projeto
```
projeto-ipc/
├── 📂 backend/
│ ├── 📂 pipes/
│ │ ├── ⚙️ parent.cpp
│ │ ├── ⚙️ child.cpp
│ │ └── 📂 output/
│ ├── 📂 sockets/
│ │ ├── ⚙️ server.cpp
│ │ ├── ⚙️ client.cpp
│ │ └── 📂 output/
│ ├── 📂 shared_memory/
│ │ ├── ⚙️ shared_memory.cpp
│ │ └── 📂 output/
│ └── 📂 tests/
├── 📂 frontend/
│ └── ⚙️ frontend.py
├── 📂 docs/
│ └── 📄 README.md
└── ⚙️ ipc_config.json
```

---

## 🚀 Mecanismos Implementados

### 1. 🪠 Pipes Anônimos
- **Comunicação unidirecional** entre processos pai e filho
- **Arquivos**: `parent.cpp` (servidor), `child.cpp` (cliente)
- **Protocolo**: Handles de pipe herdados

### 2. 🌐 Sockets Locais
- **Comunicação cliente-servidor** usando sockets TCP
- **Arquivos**: `server.cpp` (servidor), `client.cpp` (cliente)
- **Porta**: 8080 (127.0.0.1)

### 3. 💾 Memória Compartilhada
- **Compartilhamento de dados** entre processos
- **Arquivos**: `shared_memory.cpp`
- **Sincronização**: Semáforos Windows

---

## 🛠️ Instalação e Execução

### 📋 Pré-requisitos
- **Windows 10/11**
- **MinGW Instalado** [Link MinGW](https://sourceforge.net/projects/mingw)
- **Python Instalado** [Link Pyhton](https://www.python.org/downloads)
- **Visual Studio Code Instalado** [Link VSCode](https://code.visualstudio.com/download)
- **Extenção C++** (No Visual Studio)
- **Extenção Python 3.8+** (No Visual Studio)

### 🔧 Compilação

```bash
# Compilar Pipes
cd backend/pipes/
g++ -o parent.exe parent.cpp
g++ -o child.exe child.cpp

# Compilar Sockets
cd ../sockets/
g++ -o server.exe server.cpp -lws2_32
g++ -o client.exe client.cpp -lws2_32

# Compilar Memória Compartilhada
cd ../shared_memory/
g++ -o shared_memory.exe shared_memory.cpp

# Interface Gráfica
cd frontend/
python frontend.py
```

---

# 📚 Referências

### 🔗 **Documentação Técnica**
- **Pipes Anônimos no Windows**: [Windows Anonymous Pipe](https://www.tutorialspoint.com/windows-anonymous-pipe)
- **Programação com Sockets em C++**: [C++ Socket Programming](https://www.tutorialspoint.com/cplusplus/cpp_socket_programming.htm)

### 📖 **Bibliografia Complementar**
- [Documentação oficial da Microsoft sobre Pipes Anônimos](https://learn.microsoft.com/pt-br/windows/win32/ipc/anonymous-pipes) 
- [Documentação oficial da Microsoft sobre Sockets TCP](https://learn.microsoft.com/pt-br/dotnet/fundamentals/networking/sockets/socket-services) 
- [Documentação oficial da Microsoft sobre Memória Compartilhada](https://learn.microsoft.com/pt-br/windows/win32/memory/sharing-files-and-memory)