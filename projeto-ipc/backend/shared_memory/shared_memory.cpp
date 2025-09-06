// shared_mem_ipc_win_clean.cpp
// Win32: memória compartilhada + semáforos nomeados + JSON no stdout.
// Modos: init | writer | reader | cleanup

#include <windows.h>
#include <iostream>
#include <string>
#include <cstring>

static const wchar_t* SHM_NAME   = L"Local\\IPC_DEMO_SHM";
static const wchar_t* SEM_EMPTY  = L"Local\\IPC_DEMO_EMPTY"; // vaga p/ escrever (inicia 1)
static const wchar_t* SEM_FULL   = L"Local\\IPC_DEMO_FULL";  // msg pronta (inicia 0)
static const size_t   BUF_SIZE   = 1024;

struct Shared {
    char buf[BUF_SIZE];
};

static volatile bool g_running = true;

static BOOL WINAPI on_console_ctrl(DWORD ctrlType) {
    if (ctrlType == CTRL_C_EVENT ||
        ctrlType == CTRL_BREAK_EVENT ||
        ctrlType == CTRL_CLOSE_EVENT ||
        ctrlType == CTRL_LOGOFF_EVENT ||
        ctrlType == CTRL_SHUTDOWN_EVENT) {
        g_running = false;
        return TRUE;
    }
    return FALSE;
}

static void json(const std::string& event, const std::string& detail = "") {
    std::cout << "{\"event\":\"" << event << "\",\"detail\":\"";
    for (char c : detail) {
        if (c == '"' || c == '\\') {
            std::cout << '\\';
        }
        if (c == '\n') {
            std::cout << "\\n";
            continue;
        }
        std::cout << c;
    }
    std::cout << "\"}" << std::endl;
}

struct Resources {
    HANDLE  hMap   = nullptr;
    HANDLE  semE   = nullptr;
    HANDLE  semF   = nullptr;
    Shared* ptr    = nullptr;

    void close_all() {
        if (ptr != nullptr) {
            UnmapViewOfFile(ptr);
            ptr = nullptr;
        }
        if (hMap != nullptr) {
            CloseHandle(hMap);
            hMap = nullptr;
        }
        if (semE != nullptr) {
            CloseHandle(semE);
            semE = nullptr;
        }
        if (semF != nullptr) {
            CloseHandle(semF);
            semF = nullptr;
        }
    }
};

// Cria memória compartilhada + semáforos (zera memória)
static bool create_resources(Resources& r) {
    r.hMap = CreateFileMappingW(INVALID_HANDLE_VALUE, nullptr, PAGE_READWRITE, 0, sizeof(Shared), SHM_NAME);
    if (r.hMap == nullptr) {
        json("error", "CreateFileMapping_failed");
        return false;
    }

    void* view = MapViewOfFile(r.hMap, FILE_MAP_ALL_ACCESS, 0, 0, sizeof(Shared));
    if (view == nullptr) {
        json("error", "MapViewOfFile_failed");
        return false;
    }
    r.ptr = static_cast<Shared*>(view);
    std::memset(r.ptr, 0, sizeof(Shared));

    r.semE = CreateSemaphoreW(nullptr, 1, 1, SEM_EMPTY); // 1 vaga p/ escrever
    if (r.semE == nullptr) {
        json("error", "CreateSemaphore_empty_failed");
        return false;
    }

    r.semF = CreateSemaphoreW(nullptr, 0, 1, SEM_FULL);  // 0 mensagens prontas
    if (r.semF == nullptr) {
        json("error", "CreateSemaphore_full_failed");
        return false;
    }

    return true;
}

// Abre memória/semáforos já existentes (após init)
static bool open_resources(Resources& r) {
    r.hMap = OpenFileMappingW(FILE_MAP_ALL_ACCESS, FALSE, SHM_NAME);
    if (r.hMap == nullptr) {
        json("error", "OpenFileMapping_failed");
        return false;
    }

    void* view = MapViewOfFile(r.hMap, FILE_MAP_ALL_ACCESS, 0, 0, sizeof(Shared));
    if (view == nullptr) {
        json("error", "MapViewOfFile_failed");
        return false;
    }
    r.ptr = static_cast<Shared*>(view);

    r.semE = OpenSemaphoreW(SYNCHRONIZE | SEMAPHORE_MODIFY_STATE, FALSE, SEM_EMPTY);
    r.semF = OpenSemaphoreW(SYNCHRONIZE | SEMAPHORE_MODIFY_STATE, FALSE, SEM_FULL);
    if (r.semE == nullptr || r.semF == nullptr) {
        json("error", "OpenSemaphore_failed");
        return false;
    }

    return true;
}

// init: cria/zera tudo
static int cmd_init() {
    Resources r;
    if (!create_resources(r)) {
        r.close_all();
        return 1;
    }
    json("init_ok", "shm_and_semaphores_ready");
    r.close_all();
    return 0;
}

// writer: lê stdin e publica no buffer (produtor)
static int cmd_writer() {
    SetConsoleCtrlHandler(on_console_ctrl, TRUE);
    Resources r;
    if (!open_resources(r)) {
        r.close_all();
        return 1;
    }

    json("writer_ready", "stdin_lines");
    std::string line;
    while (g_running && std::getline(std::cin, line)) {
        if (line.size() >= BUF_SIZE) {
            line.resize(BUF_SIZE - 1);
            json("warn", "message_truncated");
        }

        DWORD w = WaitForSingleObject(r.semE, INFINITE);
        if (w != WAIT_OBJECT_0) {
            json("error", "sem_empty_wait_failed");
            break;
        }

        std::memset(r.ptr->buf, 0, BUF_SIZE);
        std::memcpy(r.ptr->buf, line.c_str(), line.size());

        if (!ReleaseSemaphore(r.semF, 1, nullptr)) {
            json("error", "sem_full_release_failed");
            break;
        }

        json("writer_sent", line);
    }

    json("writer_exit", "stopping");
    r.close_all();
    return 0;
}

// reader: consome mensagens do buffer (consumidor)
static int cmd_reader() {
    SetConsoleCtrlHandler(on_console_ctrl, TRUE);
    Resources r;
    if (!open_resources(r)) {
        r.close_all();
        return 1;
    }

    json("reader_ready", "waiting");
    while (g_running) {
        DWORD w = WaitForSingleObject(r.semF, INFINITE);
        if (w != WAIT_OBJECT_0) {
            json("error", "sem_full_wait_failed");
            break;
        }

        std::string msg(r.ptr->buf);

        if (!ReleaseSemaphore(r.semE, 1, nullptr)) {
            json("error", "sem_empty_release_failed");
            break;
        }

        json("reader_received", msg);
    }

    json("reader_exit", "stopping");
    r.close_all();
    return 0;
}

// cleanup: no Windows, objetos somem quando o último handle fecha.
// Aqui apenas garantimos que seus handles locais estão fechados.
static int cmd_cleanup() {
    Resources r;
    if (open_resources(r)) {
        r.close_all();
        json("cleanup_ok", "handles_closed");
    } else {
        json("cleanup_ok", "nothing_open");
    }
    return 0;
}

int wmain(int argc, wchar_t** argv) {
    if (argc != 2) {
        json("usage", "shm_ipc_win.exe [init|writer|reader|cleanup]");
        return 1;
    }

    std::wstring mode = argv[1];
    if (mode == L"init") {
        return cmd_init();
    } else if (mode == L"writer") {
        return cmd_writer();
    } else if (mode == L"reader") {
        return cmd_reader();
    } else if (mode == L"cleanup") {
        return cmd_cleanup();
    } else {
        json("usage", "shm_ipc_win.exe [init|writer|reader|cleanup]");
        return 1;
    }
}





