/*****************
 * INCLUDES *
*****************/
#undef UNICODE
#undef _UNICODE

#include <stdio.h>
#include <stdlib.h>
#include <windows.h>

/*****************
 * DEFINES *
 *****************/
#define BUFFER_SIZE 25

/*****************
 * MAIN FUNCTION *
 *****************/
int main(void) {
    HANDLE ReadHandle, WriteHandle;
    STARTUPINFO si;
    PROCESS_INFORMATION pi;
    char message[BUFFER_SIZE] = "Olá! Processo 2";
    char childProcess[] = "child.exe";
    DWORD written;

    SECURITY_ATTRIBUTES sa = { sizeof(SECURITY_ATTRIBUTES), NULL, TRUE };

    // Criando o pipe
    if (!CreatePipe(&ReadHandle, &WriteHandle, &sa, 0)) {
        fprintf(stderr, "Falha na criaçã do Pipe");
        return 1;
    }

    // Configurar a estrutura STARTUPINFO do processo filho
    ZeroMemory(&si, sizeof(STARTUPINFO));
    si.cb = sizeof(STARTUPINFO);

    // Redirecionando os handles padrão do processo filho
    si.hStdInput = ReadHandle;
    si.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
    si.hStdError = GetStdHandle(STD_ERROR_HANDLE);
    si.dwFlags = STARTF_USESTDHANDLES;

    // Processo filho não herda o handle de escrita
    SetHandleInformation(WriteHandle, HANDLE_FLAG_INHERIT, 0);

    // Criando o processo filho
    if (!CreateProcessA(NULL, childProcess, NULL, NULL, 
                      TRUE, 0, NULL, NULL, &si, &pi)) {
        fprintf(stderr, "CreateProcess Falhou");
        CloseHandle(ReadHandle);
        CloseHandle(WriteHandle);
        return 1;
    }
    
    // Fechar o handle de leitura no processo pai
    CloseHandle(ReadHandle);
    
    // Escrevendo a mensagem no pipe
    if(!WriteFile(WriteHandle, message, BUFFER_SIZE, &written, NULL)) {
        fprintf(stderr, "Erro na escrita do pipe.");
    }

    // SAÍDA EM JSON TAMBÉM NO PROCESSO PAI - PARA O FRONTEND
    printf("{Processo 1 enviou: \"%s\"}\n", message);
    fflush(stdout);

    // Fechar todos os handles
    CloseHandle(WriteHandle);
    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);

    return 0;
}