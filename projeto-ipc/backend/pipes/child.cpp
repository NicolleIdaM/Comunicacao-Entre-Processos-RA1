#include <stdio.h>
#include <windows.h>

#define BUFFER_SIZE 25

int main(void) {
    char buffer[BUFFER_SIZE];
    DWORD read;
    
    if (ReadFile(GetStdHandle(STD_INPUT_HANDLE), buffer, BUFFER_SIZE, &read, NULL)) {
        printf("Filho recebeu: %s\n", buffer);
    }
    
    return 0;
}