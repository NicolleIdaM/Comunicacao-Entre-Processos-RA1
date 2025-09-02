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
    STARTUPINFOA si;  // Use STARTUPINFOA para ANSI
    PROCESS_INFORMATION pi;
    char message[BUFFER_SIZE] = "Hello from parent!";
    char childProcess[] = "child.exe";
    DWORD written;

    SECURITY_ATTRIBUTES sa = { sizeof(SECURITY_ATTRIBUTES), NULL, TRUE };

    // Criando o pipe
    if (!CreatePipe(&ReadHandle, &WriteHandle, &sa, 0)) {
        fprintf(stderr, "Create Pipe Failed");
        return 1;
    }

    // Configurar a estrutura STARTUPINFO do processo filho
    ZeroMemory(&si, sizeof(STARTUPINFOA));
    si.cb = sizeof(STARTUPINFOA);

    // Redirecionando os handles padrão do processo filho
    si.hStdInput = ReadHandle;
    si.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
    si.hStdError = GetStdHandle(STD_ERROR_HANDLE);
    si.dwFlags = STARTF_USESTDHANDLES;

    // Processo filho não herda o handle de escrita
    SetHandleInformation(WriteHandle, HANDLE_FLAG_INHERIT, 0);

    // Criando o processo filho com versão ANSI EXPLÍCITA
    if (!CreateProcessA(NULL, childProcess, NULL, NULL, TRUE, 0, NULL, NULL, &si, &pi)) {
        fprintf(stderr, "CreateProcess Failed");
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

    // Fechar todos os handles
    CloseHandle(WriteHandle);
    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);

    return 0;
}