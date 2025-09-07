#include <windows.h>
#include <stdio.h>

#define SHM_NAME "Local\\TestSharedMemory"
#define SHM_SIZE 1024

int main() {
    HANDLE hMapFile;
    
    hMapFile = CreateFileMappingA(
        INVALID_HANDLE_VALUE,
        NULL,
        PAGE_READWRITE,
        0,
        SHM_SIZE,
        SHM_NAME
    );
    
    if (hMapFile == NULL) {
        printf("{\"teste\":\"criar_memoria\",\"status\":\"erro\",\"code\":%d}\n", GetLastError());
        return 1;
    }
    
    printf("{\"teste\":\"criar_memoria\",\"status\":\"successo\",\"nome\":\"%s\"}\n", SHM_NAME);
    
    CloseHandle(hMapFile);
    return 0;
}