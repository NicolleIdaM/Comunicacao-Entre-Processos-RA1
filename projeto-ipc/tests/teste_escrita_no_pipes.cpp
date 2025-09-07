#include <windows.h>
#include <stdio.h>
#include <string.h>

#define BUFFER_SIZE 1024

int main() {
    HANDLE hReadPipe, hWritePipe;
    SECURITY_ATTRIBUTES sa;
    DWORD bytesWritten;
    const char* teste = "Teste de escrita no pipe";
    
    sa.nLength = sizeof(SECURITY_ATTRIBUTES);
    sa.bInheritHandle = TRUE;
    sa.lpSecurityDescriptor = NULL;
    
    if (!CreatePipe(&hReadPipe, &hWritePipe, &sa, 0)) {
        printf("{\"teste\":\"escrita_pipe\",\"status\":\"erro\",\"type\":\"criacao\",\"code\":%d}\n", GetLastError());
        return 1;
    }
    
    if (!WriteFile(hWritePipe, teste, strlen(teste) + 1, &bytesWritten, NULL)) {
        printf("{\"teste\":\"escrita_pipe\",\"status\":\"erro\",\"type\":\"escrita\",\"code\":%d}\n", GetLastError());
        CloseHandle(hReadPipe);
        CloseHandle(hWritePipe);
        return 1;
    }
    
    printf("{\"teste\":\"escrita_pipe\",\"status\":\"sucesso\",\"bytes\":%lu,\"menssagem\":\"%s\"}\n", bytesWritten, teste);
    
    CloseHandle(hReadPipe);
    CloseHandle(hWritePipe);
    return 0;
}