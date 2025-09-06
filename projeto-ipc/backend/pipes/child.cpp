#include <stdio.h>
#include <windows.h>
#include <string.h>

#define BUFFER_SIZE 1024

int main(int argc, char *argv[]) {
    HANDLE hWritePipe;
    char message[BUFFER_SIZE];
    DWORD bytesWritten;
    
    if (argc < 2) {
        printf("{\"mechanism\":\"pipe\",\"action\":\"error\",\"type\":\"no_message\"}\n");
        return 1;
    }
    
    // Montar a mensagem com todos os argumentos
    strcpy(message, argv[1]);
    for (int i = 2; i < argc; i++) {
        strcat(message, " ");
        strcat(message, argv[i]);
    }
    
    // Obter handle do pipe (herdado)
    hWritePipe = GetStdHandle(STD_OUTPUT_HANDLE);
    
    if (hWritePipe == INVALID_HANDLE_VALUE) {
        printf("{\"mechanism\":\"pipe\",\"action\":\"error\",\"type\":\"invalid_handle\"}\n");
        return 1;
    }
    
    // Escrever no pipe
    if (!WriteFile(hWritePipe, message, strlen(message) + 1, &bytesWritten, NULL)) {
        printf("{\"mechanism\":\"pipe\",\"action\":\"error\",\"type\":\"write_failed\"}\n");
        return 1;
    }
    
    // Confirmar envio
    printf("{\"mechanism\":\"pipe\",\"action\":\"sent\",\"data\":\"%s\",\"bytes\":%lu}\n", message, bytesWritten);
    fflush(stdout);
    
    CloseHandle(hWritePipe);
    return 0;
}
