#include <stdio.h>
#include <stdlib.h>
#include <windows.h>
#include <string.h>

#define BUFFER_SIZE 1024

int main() {
    HANDLE hReadPipe, hWritePipe;
    SECURITY_ATTRIBUTES sa;
    char buffer[BUFFER_SIZE];
    DWORD bytesRead;
    
    // Configurar segurança para o pipe
    sa.nLength = sizeof(SECURITY_ATTRIBUTES);
    sa.bInheritHandle = TRUE;
    sa.lpSecurityDescriptor = NULL;
    
    // Criar o pipe
    if (!CreatePipe(&hReadPipe, &hWritePipe, &sa, 0)) {
        printf("{\"type\":\"error\",\"message\":\"Failed to create pipe\"}");
        return 1;
    }
    
    // Informar ao frontend que estamos prontos
    printf("{\"type\":\"pipe\",\"status\":\"ready\",\"pid\":%lu}", GetCurrentProcessId()); // CORRIGIDO: %d → %lu
    fflush(stdout);
    
    // Loop principal para ler do pipe
    while (1) {
        if (ReadFile(hReadPipe, buffer, BUFFER_SIZE - 1, &bytesRead, NULL) && bytesRead > 0) {
            buffer[bytesRead] = '\0';
            // Enviar mensagem recebida para o frontend
            printf("{\"type\":\"pipe\",\"direction\":\"received\",\"message\":\"%s\"}", buffer);
            fflush(stdout);
        }
        Sleep(100); // Pequena pausa para não sobrecarregar o CPU
    }
    
    CloseHandle(hReadPipe);
    CloseHandle(hWritePipe);
    return 0;
}