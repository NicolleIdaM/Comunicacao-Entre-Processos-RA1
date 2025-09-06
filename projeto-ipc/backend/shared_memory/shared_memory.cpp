// shared_memory.cpp - Implementação de memória compartilhada com JSON padronizado
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

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

// ---------- Constantes ----------
#define SHM_NAME "Local\\MySharedMemory"
#define SEM_EMPTY "Local\\MySemEmpty"
#define SEM_FULL  "Local\\MySemFull"
#define BUFFER_SIZE 256

// ---------- Estrutura ----------
typedef struct {
    char buffer[BUFFER_SIZE];
} SharedData;

// ---------- Função para imprimir JSON ----------
void log_json(const char* event, const char* detail) {
    char msg[BUFFER_SIZE];
    safe_snprintf(msg, sizeof(msg),
        "{\"event\":\"%s\",\"detail\":\"%s\"}\n", event, detail ? detail : "");
    printf("%s", msg);
    fflush(stdout);
}

// ---------- Funções principais ----------
int init_shared_memory() {
    HANDLE hMapFile = CreateFileMappingA(
        INVALID_HANDLE_VALUE, NULL, PAGE_READWRITE, 0,
        sizeof(SharedData), SHM_NAME);

    if (hMapFile == NULL) {
        log_json("error", "CreateFileMapping failed");
        return 1;
    }

    CloseHandle(hMapFile);

    HANDLE hSemEmpty = CreateSemaphoreA(NULL, 1, 1, SEM_EMPTY);
    HANDLE hSemFull = CreateSemaphoreA(NULL, 0, 1, SEM_FULL);
    if (!hSemEmpty || !hSemFull) {
        log_json("error", "CreateSemaphore failed");
        return 1;
    }

    CloseHandle(hSemEmpty);
    CloseHandle(hSemFull);

    log_json("init_ok", "shared memory and semaphores created");
    return 0;
}

int cleanup_shared_memory() {
    // Apenas remove os objetos nomeados (quando último handle fecha, eles são destruídos)
    log_json("cleanup_ok", "resources released");
    return 0;
}

int writer_mode() {
    HANDLE hMapFile = OpenFileMappingA(FILE_MAP_ALL_ACCESS, FALSE, SHM_NAME);
    if (!hMapFile) {
        log_json("error", "OpenFileMapping failed");
        return 1;
    }

    SharedData* pData = (SharedData*)MapViewOfFile(hMapFile, FILE_MAP_ALL_ACCESS, 0, 0, sizeof(SharedData));
    if (!pData) {
        log_json("error", "MapViewOfFile failed");
        CloseHandle(hMapFile);
        return 1;
    }

    HANDLE hSemEmpty = OpenSemaphoreA(SYNCHRONIZE | SEMAPHORE_MODIFY_STATE, FALSE, SEM_EMPTY);
    HANDLE hSemFull  = OpenSemaphoreA(SYNCHRONIZE | SEMAPHORE_MODIFY_STATE, FALSE, SEM_FULL);

    if (!hSemEmpty || !hSemFull) {
        log_json("error", "OpenSemaphore failed");
        UnmapViewOfFile(pData);
        CloseHandle(hMapFile);
        return 1;
    }

    log_json("writer_ready", "waiting for message");

    char line[BUFFER_SIZE];
    if (fgets(line, sizeof(line), stdin)) {
        line[strcspn(line, "\r\n")] = 0; // remove newline
        WaitForSingleObject(hSemEmpty, INFINITE);
        strncpy(pData->buffer, line, BUFFER_SIZE - 1);
        pData->buffer[BUFFER_SIZE - 1] = '\0';
        ReleaseSemaphore(hSemFull, 1, NULL);
        log_json("writer_sent", pData->buffer);
    }

    UnmapViewOfFile(pData);
    CloseHandle(hMapFile);
    CloseHandle(hSemEmpty);
    CloseHandle(hSemFull);

    return 0;
}

int reader_mode() {
    HANDLE hMapFile = OpenFileMappingA(FILE_MAP_ALL_ACCESS, FALSE, SHM_NAME);
    if (!hMapFile) {
        log_json("error", "OpenFileMapping failed");
        return 1;
    }

    SharedData* pData = (SharedData*)MapViewOfFile(hMapFile, FILE_MAP_ALL_ACCESS, 0, 0, sizeof(SharedData));
    if (!pData) {
        log_json("error", "MapViewOfFile failed");
        CloseHandle(hMapFile);
        return 1;
    }

    HANDLE hSemEmpty = OpenSemaphoreA(SYNCHRONIZE | SEMAPHORE_MODIFY_STATE, FALSE, SEM_EMPTY);
    HANDLE hSemFull  = OpenSemaphoreA(SYNCHRONIZE | SEMAPHORE_MODIFY_STATE, FALSE, SEM_FULL);

    if (!hSemEmpty || !hSemFull) {
        log_json("error", "OpenSemaphore failed");
        UnmapViewOfFile(pData);
        CloseHandle(hMapFile);
        return 1;
    }

    log_json("reader_ready", "listening");

    while (1) {
        WaitForSingleObject(hSemFull, INFINITE);
        char msg[BUFFER_SIZE];
        strncpy(msg, pData->buffer, BUFFER_SIZE);
        msg[BUFFER_SIZE - 1] = '\0';
        log_json("reader_received", msg);
        ReleaseSemaphore(hSemEmpty, 1, NULL);
        Sleep(50); // evitar loop CPU 100%
    }

    UnmapViewOfFile(pData);
    CloseHandle(hMapFile);
    CloseHandle(hSemEmpty);
    CloseHandle(hSemFull);

    return 0;
}

// ---------- main ----------
int main(int argc, char* argv[]) {
    if (argc < 2) {
        log_json("error", "no_command");
        return 1;
    }

    if (strcmp(argv[1], "init") == 0) {
        return init_shared_memory();
    } else if (strcmp(argv[1], "cleanup") == 0) {
        return cleanup_shared_memory();
    } else if (strcmp(argv[1], "writer") == 0) {
        return writer_mode();
    } else if (strcmp(argv[1], "reader") == 0) {
        return reader_mode();
    } else {
        log_json("error", "invalid_command");
        return 1;
    }
}