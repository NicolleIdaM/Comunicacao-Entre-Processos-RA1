#include <windows.h>
#include <stdio.h>
#include <string.h>

#define SHM_NAME "Local\\TestSharedMemory"
#define SHM_SIZE 1024

int main() {
    HANDLE hMapFile;
    LPVOID pBuffer;
    char readBuffer[SHM_SIZE];
    const char* testMessage = "Teste de leitura na memoria compartilhada";
    
    hMapFile = CreateFileMappingA(
        INVALID_HANDLE_VALUE,
        NULL,
        PAGE_READWRITE,
        0,
        SHM_SIZE,
        SHM_NAME
    );
    
    if (hMapFile == NULL) {
        printf("{\"teste\":\"leitura_memoria\",\"status\":\"erro\",\"tipo\":\"criar\",\"code\":%d}\n", GetLastError());
        return 1;
    }
    
    pBuffer = MapViewOfFile(hMapFile, FILE_MAP_ALL_ACCESS, 0, 0, SHM_SIZE);
    if (pBuffer == NULL) {
        printf("{\"teste\":\"leitura_memoria\",\"status\":\"erro\",\"tipo\":\"mapeamento\",\"code\":%d}\n", GetLastError());
        CloseHandle(hMapFile);
        return 1;
    }
    
    // Primeiro escrever para ter dados para ler
    strncpy((char*)pBuffer, testMessage, SHM_SIZE - 1);
    ((char*)pBuffer)[SHM_SIZE - 1] = '\0';
    
    // Agora ler os dados
    strncpy(readBuffer, (char*)pBuffer, SHM_SIZE - 1);
    readBuffer[SHM_SIZE - 1] = '\0';
    
    printf("{\"teste\":\"leitura_memoria\",\"status\":\"successo\",\"mensagem\":\"%s\"}\n", readBuffer);
    
    UnmapViewOfFile(pBuffer);
    CloseHandle(hMapFile);
    return 0;
}