int reader_mode() {
    HANDLE hMapFile = OpenFileMappingA(FILE_MAP_ALL_ACCESS, FALSE, SHM_NAME);
    if (!hMapFile) {
        log_json("error", "OpenFileMapping failed");
        fflush(stdout);
        return 1;
    }

    SharedData* pData = (SharedData*)MapViewOfFile(hMapFile, FILE_MAP_ALL_ACCESS, 0, 0, sizeof(SharedData));
    if (!pData) {
        log_json("error", "MapViewOfFile failed");
        fflush(stdout);
        CloseHandle(hMapFile);
        return 1;
    }

    HANDLE hSemEmpty = OpenSemaphoreA(SYNCHRONIZE | SEMAPHORE_MODIFY_STATE, FALSE, SEM_EMPTY);
    HANDLE hSemFull  = OpenSemaphoreA(SYNCHRONIZE | SEMAPHORE_MODIFY_STATE, FALSE, SEM_FULL);

    if (!hSemEmpty || !hSemFull) {
        log_json("error", "OpenSemaphore failed");
        fflush(stdout);
        UnmapViewOfFile(pData);
        CloseHandle(hMapFile);
        return 1;
    }

    log_json("reader_ready", "listening");
    fflush(stdout);

    bool running = true;
    
    while (running) {
        DWORD result = WaitForSingleObject(hSemFull, 100);
        
        if (result == WAIT_OBJECT_0) {
            char msg[BUFFER_SIZE];
            strncpy(msg, pData->buffer, BUFFER_SIZE);
            msg[BUFFER_SIZE - 1] = '\0';
            
            if (strlen(msg) > 0 && strcmp(msg, "\0") != 0) {
                log_json("received", msg);
                fflush(stdout);
            }
            
            ReleaseSemaphore(hSemEmpty, 1, NULL);
        }
        else if (result == WAIT_TIMEOUT) {
            continue;
        }
        else {
            log_json("error", "WaitForSingleObject failed");
            fflush(stdout);
            break;
        }
    }

    UnmapViewOfFile(pData);
    CloseHandle(hMapFile);
    CloseHandle(hSemEmpty);
    CloseHandle(hSemFull);

    log_json("reader_stopped", "clean exit");
    fflush(stdout);
    return 0;
}