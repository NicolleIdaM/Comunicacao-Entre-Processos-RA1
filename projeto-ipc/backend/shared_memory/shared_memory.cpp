// shared_memory_portable.c
// Windows: Memória compartilhada + semáforos nomeados + JSON no stdout.
// Modos: init | writer | reader | cleanup
// Portável entre MSVC e MinGW/GCC (sem _snprintf_s, strncpy_s, _TRUNCATE).

#define UNICODE
#define _UNICODE
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <stdbool.h>

static const wchar_t* SHM_NAME   = L"Local\\IPC_DEMO_SHM";
static const wchar_t* SEM_EMPTY  = L"Local\\IPC_DEMO_EMPTY"; // vaga p/ escrever (inicia 1)
static const wchar_t* SEM_FULL   = L"Local\\IPC_DEMO_FULL";  // msg pronta (inicia 0)

enum { BUF_SIZE = 1024 };
static const DWORD WAIT_SLICE_MS = 200;

// ---------- Helpers portáveis (sem *_s) ----------
static void safe_vsnprintf(char* dst, size_t size, const char* fmt, va_list ap) {
    if (!dst || size == 0) return;
    int n = vsnprintf(dst, size, fmt, ap);
    if (n < 0 || (size_t)n >= size) {
        dst[size - 1] = '\0';
    }
}
static void safe_snprintf(char* dst, size_t size, const char* fmt, ...) {
    va_list ap; va_start(ap, fmt);
    safe_vsnprintf(dst, size, fmt, ap);
    va_end(ap);
}
static void safe_strcpy(char* dst, size_t size, const char* src) {
    if (!dst || size == 0) return;
    if (!src) { dst[0] = '\0'; return; }
    strncpy(dst, src, size - 1);
    dst[size - 1] = '\0';
}
// -----------------------------------------------

struct Shared {
    char buf[BUF_SIZE];
};

static volatile BOOL g_running = TRUE;

static BOOL WINAPI on_console_ctrl(DWORD c) {
    switch (c) {
        case CTRL_C_EVENT:
        case CTRL_BREAK_EVENT:
        case CTRL_CLOSE_EVENT:
        case CTRL_LOGOFF_EVENT:
        case CTRL_SHUTDOWN_EVENT:
            g_running = FALSE;
            return TRUE;
    }
    return FALSE;
}

static void json(const char* event, const char* detail) {
    fputs("{\"event\":\"", stdout);
    fputs(event, stdout);
    fputs("\",\"detail\":\"", stdout);
    if (detail) {
        for (const char* p = detail; *p; ++p) {
            char ch = *p;
            if (ch == '"' || ch == '\\') fputc('\\', stdout);
            if (ch == '\n') { fputs("\\n", stdout); continue; }
            fputc(ch, stdout);
        }
    }
    fputs("\"}\n", stdout);
    fflush(stdout);
}
static void json_winerr(const char* what) {
    DWORD e = GetLastError();
    char msg[128];
    safe_snprintf(msg, sizeof(msg), "%s code=%lu", what, (unsigned long)e);
    json("error", msg);
}

struct Resources {
    HANDLE  hMap;
    HANDLE  semE;
    HANDLE  semF;
    struct Shared* ptr;
};

static void close_all(struct Resources* r) {
    if (!r) return;
    if (r->ptr) { UnmapViewOfFile(r->ptr); r->ptr = NULL; }
    if (r->hMap) { CloseHandle(r->hMap); r->hMap = NULL; }
    if (r->semE) { CloseHandle(r->semE); r->semE = NULL; }
    if (r->semF) { CloseHandle(r->semF); r->semF = NULL; }
}

// Cria memória + semáforos (zera memória)
static bool create_resources(struct Resources* r) {
    memset(r, 0, sizeof(*r));

    r->hMap = CreateFileMappingW(INVALID_HANDLE_VALUE, NULL, PAGE_READWRITE,
                                 0, (DWORD)sizeof(struct Shared), SHM_NAME);
    if (!r->hMap) { json_winerr("CreateFileMapping"); return false; }

    {
        void* view = MapViewOfFile(r->hMap, FILE_MAP_ALL_ACCESS, 0, 0, sizeof(struct Shared));
        if (!view) { json_winerr("MapViewOfFile"); return false; }
        r->ptr = (struct Shared*)view;
        memset(r->ptr, 0, sizeof(struct Shared));
    }

    r->semE = CreateSemaphoreW(NULL, 1, 1, SEM_EMPTY); // 1 vaga p/ escrever
    if (!r->semE) { json_winerr("CreateSemaphore(EMPTY)"); return false; }

    r->semF = CreateSemaphoreW(NULL, 0, 1, SEM_FULL);  // 0 mensagens prontas
    if (!r->semF) { json_winerr("CreateSemaphore(FULL)"); return false; }

    return true;
}

// Abre memória/semáforos existentes
static bool open_resources(struct Resources* r) {
    memset(r, 0, sizeof(*r));

    r->hMap = OpenFileMappingW(FILE_MAP_ALL_ACCESS, FALSE, SHM_NAME);
    if (!r->hMap) { json_winerr("OpenFileMapping"); return false; }

    {
        void* view = MapViewOfFile(r->hMap, FILE_MAP_ALL_ACCESS, 0, 0, sizeof(struct Shared));
        if (!view) { json_winerr("MapViewOfFile"); return false; }
        r->ptr = (struct Shared*)view;
    }

    r->semE = OpenSemaphoreW(SYNCHRONIZE | SEMAPHORE_MODIFY_STATE, FALSE, SEM_EMPTY);
    r->semF = OpenSemaphoreW(SYNCHRONIZE | SEMAPHORE_MODIFY_STATE, FALSE, SEM_FULL);
    if (!r->semE || !r->semF) { json_winerr("OpenSemaphore"); return false; }

    return true;
}

// init
static int cmd_init(void) {
    struct Resources r;
    if (!create_resources(&r)) { close_all(&r); return 1; }
    json("init_ok", "shm_and_semaphores_ready");
    close_all(&r);
    return 0;
}

// writer (produtor)
static int cmd_writer(void) {
    SetConsoleCtrlHandler(on_console_ctrl, TRUE);

    struct Resources r;
    if (!open_resources(&r)) { close_all(&r); return 1; }

    json("writer_ready", "stdin_lines");
    while (g_running) {
        char line[BUF_SIZE];
        if (!fgets(line, (int)sizeof(line), stdin)) break;

        // remove \r\n
        size_t len = strcspn(line, "\r\n");
        line[len] = '\0';
        if (len >= BUF_SIZE - 1) json("warn", "message_truncated");

        for (;;) {
            DWORD w = WaitForSingleObject(r.semE, WAIT_SLICE_MS);
            if (w == WAIT_OBJECT_0) break;
            if (w == WAIT_TIMEOUT && !g_running) { json("writer_exit", "stopping"); close_all(&r); return 0; }
            if (w != WAIT_TIMEOUT) { json_winerr("Wait(semE)"); close_all(&r); return 1; }
        }

        memset(r.ptr->buf, 0, BUF_SIZE);
        memcpy(r.ptr->buf, line, len);

        if (!ReleaseSemaphore(r.semF, 1, NULL)) { json_winerr("Release(semF)"); close_all(&r); return 1; }
        json("writer_sent", line);
    }

    json("writer_exit", "stopping");
    close_all(&r);
    return 0;
}

// reader (consumidor)
static int cmd_reader(void) {
    SetConsoleCtrlHandler(on_console_ctrl, TRUE);

    struct Resources r;
    if (!open_resources(&r)) { close_all(&r); return 1; }

    json("reader_ready", "waiting");
    while (g_running) {
        DWORD w = WaitForSingleObject(r.semF, WAIT_SLICE_MS);
        if (w == WAIT_OBJECT_0) {
            char msg[BUF_SIZE];
            safe_strcpy(msg, sizeof(msg), r.ptr->buf);

            if (!ReleaseSemaphore(r.semE, 1, NULL)) { json_winerr("Release(semE)"); close_all(&r); return 1; }
            json("reader_received", msg);
        } else if (w == WAIT_TIMEOUT) {
            continue;
        } else {
            json_winerr("Wait(semF)");
            close_all(&r);
            return 1;
        }
    }

    json("reader_exit", "stopping");
    close_all(&r);
    return 0;
}

// cleanup
static int cmd_cleanup(void) {
    struct Resources r;
    if (open_resources(&r)) { close_all(&r); json("cleanup_ok", "handles_closed"); }
    else { json("cleanup_ok", "nothing_open"); }
    return 0;
}

// Entrada padrão (ASCII) para evitar -municode
int main(int argc, char** argv) {
    if (argc != 2) {
        json("usage", "shared_memory.exe [init|writer|reader|cleanup]");
        return 1;
    }
    if (strcmp(argv[1], "init")    == 0) return cmd_init();
    if (strcmp(argv[1], "writer")  == 0) return cmd_writer();
    if (strcmp(argv[1], "reader")  == 0) return cmd_reader();
    if (strcmp(argv[1], "cleanup") == 0) return cmd_cleanup();

    json("usage", "shared_memory.exe [init|writer|reader|cleanup]");
    return 1;
}
