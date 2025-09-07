#include <windows.h>
#include <stdio.h>

#define SHM_NAME "Local\\TestSharedMemory"
#define SHM_SIZE 1024

int main() {
    HANDLE hMapFile;
    LPVOID pBuffer;
    
    hMapFile = CreateFileMappingA(
        INVALID_HANDLE_VALUE,
        NULL,
        PAGE_READWRITE,
        0,
        SHM_SIZE,
        SHM_NAME
    );
    
    if (hMapFile == NULL) {
        printf("{\"teste\":\"mapeamento_memoria\",\"status\":\"erro\",\"tipo\":\"criar\",\"code\":%d}\n", GetLastError());
        return 1;
    }
    
    pBuffer = MapViewOfFile(hMapFile, FILE_MAP_ALL_ACCESS, 0, 0, SHM_SIZE);
    if (pBuffer == NULL) {
        printf("{\"teste\":\"mapeamento_memoria\",\"status\":\"erro\",\"tipo\":\"mapeamento\",\"code\":%d}\n", GetLastError());
        CloseHandle(hMapFile);
        return 1;
    }
    
    printf("{\"teste\":\"mapeamento_memoria\",\"status\":\"successo\",\"endereco\":\"%p\"}\n", pBuffer);
    
    UnmapViewOfFile(pBuffer);
    CloseHandle(hMapFile);
    return 0;
}