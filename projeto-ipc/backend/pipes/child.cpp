#include <stdio.h>
#include <windows.h>
#include <string.h>

#define BUFFER_SIZE 1024

int main(int argc, char *argv[]) {
    HANDLE hWritePipe;
    char message[BUFFER_SIZE];
    DWORD bytesWritten;
    
    if (argc < 2) {
        printf("{\"type\":\"error\",\"message\":\"No message provided\"}");
        return 1;
    }
    
    // Combinar todos os argumentos em uma única mensagem
    strcpy(message, argv[1]);
    for (int i = 2; i < argc; i++) {
        strcat(message, " ");
        strcat(message, argv[i]);
    }
    
    // Obter handle do pipe (assumindo que é passado como herança)
    hWritePipe = GetStdHandle(STD_OUTPUT_HANDLE);
    
    if (hWritePipe == INVALID_HANDLE_VALUE) {
        printf("{\"type\":\"error\",\"message\":\"Invalid pipe handle\"}");
        return 1;
    }
    
    // Escrever no pipe
    if (!WriteFile(hWritePipe, message, strlen(message) + 1, &bytesWritten, NULL)) {
        printf("{\"type\":\"error\",\"message\":\"Failed to write to pipe\"}");
        return 1;
    }
    
    // Fechar o handle
    CloseHandle(hWritePipe);
    
    return 0;
}