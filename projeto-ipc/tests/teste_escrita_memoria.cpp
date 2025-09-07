#include <windows.h>
#include <stdio.h>
#include <string.h>

#define SHM_NAME "Local\\TestSharedMemory"
#define SHM_SIZE 1024

int main() {
    HANDLE hMapFile;
    LPVOID pBuffer;
    const char* teste = "Teste de escrita na memoria compartilhada";
    
    hMapFile = CreateFileMappingA(
        INVALID_HANDLE_VALUE,
        NULL,
        PAGE_READWRITE,
        0,
        SHM_SIZE,
        SHM_NAME
    );
    
    if (hMapFile == NULL) {
        printf("{\"teste\":\"escrita_memroria\",\"status\":\"erro\",\"tipo\":\"criar\",\"code\":%d}\n", GetLastError());
        return 1;
    }
    
    pBuffer = MapViewOfFile(hMapFile, FILE_MAP_ALL_ACCESS, 0, 0, SHM_SIZE);
    if (pBuffer == NULL) {
        printf("{\"teste\":\"escrita_memroria\",\"status\":\"erro\",\"tipo\":\"mapeamento\",\"code\":%d}\n", GetLastError());
        CloseHandle(hMapFile);
        return 1;
    }
    
    strncpy((char*)pBuffer, teste, SHM_SIZE - 1);
    ((char*)pBuffer)[SHM_SIZE - 1] = '\0';
    
    printf("{\"teste\":\"escrita_memroria\",\"status\":\"successo\",\"mensagem\":\"%s\"}\n", teste);
    
    UnmapViewOfFile(pBuffer);
    CloseHandle(hMapFile);
    return 0;
}