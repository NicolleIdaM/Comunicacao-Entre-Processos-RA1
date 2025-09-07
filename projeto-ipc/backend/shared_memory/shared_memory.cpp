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

    // Variável para controlar o loop
    bool running = true;
    
    while (running) {
        // Verificar se há dados disponíveis com timeout
        DWORD result = WaitForSingleObject(hSemFull, 100); // 100ms timeout
        
        if (result == WAIT_OBJECT_0) {
            // Dados disponíveis
            char msg[BUFFER_SIZE];
            strncpy(msg, pData->buffer, BUFFER_SIZE);
            msg[BUFFER_SIZE - 1] = '\0';
            
            // Verificar se a mensagem não está vazia
            if (strlen(msg) > 0) {
                log_json("received", msg);
            }
            
            ReleaseSemaphore(hSemEmpty, 1, NULL);
        }
        else if (result == WAIT_TIMEOUT) {
            // Timeout - verificar se deve continuar executando
            continue;
        }
        else {
            // Erro ou objeto abandonado
            break;
        }
    }

    // Limpeza
    UnmapViewOfFile(pData);
    CloseHandle(hMapFile);
    CloseHandle(hSemEmpty);
    CloseHandle(hSemFull);

    log_json("reader_stopped", "clean exit");
    return 0;
}