#include <windows.h>
#include <stdio.h>
#include <string.h>

#define BUFFER_SIZE 1024

int main() {
    HANDLE hReadPipe, hWritePipe;
    SECURITY_ATTRIBUTES sa;
    char buffer[BUFFER_SIZE];
    DWORD bytesRead;
    const char* teste = "Teste de leitura no pipe";
    
    sa.nLength = sizeof(SECURITY_ATTRIBUTES);
    sa.bInheritHandle = TRUE;
    sa.lpSecurityDescriptor = NULL;
    
    if (!CreatePipe(&hReadPipe, &hWritePipe, &sa, 0)) {
        printf("{\"teste\":\"leitura_pipes\",\"status\":\"erro\",\"tipo\":\"criacao\",\"code\":%d}\n", GetLastError());
        return 1;
    }
    
    // Primeiro escrever para ter dados para ler
    DWORD bytesWritten;
    if (!WriteFile(hWritePipe, teste, strlen(teste) + 1, &bytesWritten, NULL)) {
        printf("{\"teste\":\"leitura_pipes\",\"status\":\"erro\",\"tipo\":\"escrita\",\"code\":%d}\n", GetLastError());
        CloseHandle(hReadPipe);
        CloseHandle(hWritePipe);
        return 1;
    }
    
    // Agora ler os dados
    if (!ReadFile(hReadPipe, buffer, BUFFER_SIZE - 1, &bytesRead, NULL)) {
        printf("{\"teste\":\"leitura_pipes\",\"status\":\"erro\",\"tipo\":\"leitura\",\"code\":%d}\n", GetLastError());
        CloseHandle(hReadPipe);
        CloseHandle(hWritePipe);
        return 1;
    }
    
    buffer[bytesRead] = '\0';
    printf("{\"teste\":\"leitura\",\"status\":\"sucesso\",\"bytes\":%lu,\"mensagem\":\"%s\"}\n", bytesRead, buffer);
    
    CloseHandle(hReadPipe);
    CloseHandle(hWritePipe);
    return 0;
}