#include <windows.h>
#include <stdio.h>

int main(void) {
    HANDLE hRead, hWrite;
    SECURITY_ATTRIBUTES sa = { sizeof(SECURITY_ATTRIBUTES), NULL, TRUE };
    char write_msg[] = "Hello, World!";
    char read_msg[256];
    DWORD bytesWritten, bytesRead;

    // Create the pipe
    if (!CreatePipe(&hRead, &hWrite, &sa, 0)) {
        fprintf(stderr, "Pipe failed\n");
        return 1;
    }

    // Write JSON to the pipe
    char json_msg[300];
    snprintf(json_msg, sizeof(json_msg), "{ \"mensagem\": \"%s\" }", write_msg);

    WriteFile(hWrite, json_msg, (DWORD)strlen(json_msg), &bytesWritten, NULL);
    CloseHandle(hWrite); // Done writing

    // Read from the pipe
    if (ReadFile(hRead, read_msg, sizeof(read_msg) - 1, &bytesRead, NULL)) {
        read_msg[bytesRead] = '\0';

        // Save to .json file
        FILE* f = fopen("output.json", "w");
        if (f) {
            fprintf(f, "%s\n", read_msg);
            fclose(f);
            printf("Arquivo saida.json gerado com sucesso!\n");
        } else {
            fprintf(stderr, "Erro ao criar arquivo JSON\n");
        }
    } else {
        fprintf(stderr, "Erro ao ler do pipe\n");
    }

    CloseHandle(hRead);

    return 0;
}