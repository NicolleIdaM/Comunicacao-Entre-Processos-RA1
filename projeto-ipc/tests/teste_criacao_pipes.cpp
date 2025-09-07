#include <windows.h>
#include <stdio.h>
#include <string.h>

#define BUFFER_SIZE 1024

int main() {
    HANDLE hReadPipe, hWritePipe;
    SECURITY_ATTRIBUTES sa;
    
    // Configurar segurança para o pipe
    sa.nLength = sizeof(SECURITY_ATTRIBUTES);
    sa.bInheritHandle = TRUE;
    sa.lpSecurityDescriptor = NULL;
    
    // Criar o pipe
    if (!CreatePipe(&hReadPipe, &hWritePipe, &sa, 0)) {
        printf("{\"test\":\"pipe_create\",\"status\":\"error\",\"code\":%d}\n", GetLastError());
        return 1;
    }
    
    printf("{\"test\":\"pipe_create\",\"status\":\"success\"}\n");
    
    // Fechar handles
    CloseHandle(hReadPipe);
    CloseHandle(hWritePipe);
    
    return 0;
}