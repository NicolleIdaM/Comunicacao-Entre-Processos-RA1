#include <stdio.h>
#include <windows.h>

#define BUFFER_SIZE 25

int main(void) {
    char buffer[BUFFER_SIZE];
    DWORD read;
    
    // SAaída JSON
    if (ReadFile(GetStdHandle(STD_INPUT_HANDLE), buffer, BUFFER_SIZE, &read, NULL)){
        printf("{Processo 2 recebeu: \"%s\"}\n", buffer);
        fflush(stdout);  // Garante que o JSON seja enviado imediatamente
    } else {
        printf("Erro ao receber mensagem do processo 1\n");
        fflush(stdout);
    }
    
    return 0;
}