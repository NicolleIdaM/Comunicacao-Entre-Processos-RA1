/*****************
 * INCLUDES *
*****************/
#include <stdio.h>
#include <stdlib.h>
#include <windows.h>

/*****************
 * DEFINES *
 * *****************/
#define BUFFER_SIZE 25

/*****************
 * MAIN FUNCTION *
 * *****************/
int main(void) {
    HANDLE ReadHandle, WriteHandle;
    STARTUPINFO si;
    PROCESS_INFORMATION pi;
    char message[BUFFER_SIZE] = "Hello from parent!";
    DWORD written;

    SECURITY_ATTRIBUTES sa = { sizeof(SECURITY_ATTRIBUTES), NULL, TRUE };

    // Criando o pipe
    if (!CreatePipe(&ReadHandle, &WriteHandle, &sa, 0)) {
        fprintf(stderr, "Create Pipe Failed");
        return 1;
    }

    // Configurando a estrutura STARTUPINFO
    GetStartupInfo(&si);
    si.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);

    // Redirecionando a entrada padrão do processo filho para o pipe
    si.hStdInput = ReadHandle;
    si.dwFlags |= STARTF_USESTDHANDLES;

    //Não mostrar a janela do processo filho
    SetHandleInformation(WriteHandle, HANDLE_FLAG_INHERIT, 0);

    // Criando o processo filho
    CreateProcess(NULL, "child.exe", NULL, NULL, TRUE, 0, NULL, NULL, &si, &pi);
    
    // Escrevendo a mensagem no pipe
    if(!WriteFile(WriteHandle, message, BUFFER_SIZE, &written, NULL)) {
        fprintf(stderr, "Erro na leitura do pipe.");
        return 1;
    }

    // Fechando o handle de leitura no processo pai
    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);
    return 0;
}