#include <windows.h>
#include <stdio.h>

int main() {
    HANDLE hReadPipe, hWritePipe;
    SECURITY_ATTRIBUTES sa;
    
    sa.nLength = sizeof(SECURITY_ATTRIBUTES);
    sa.bInheritHandle = TRUE;
    sa.lpSecurityDescriptor = NULL;
    
    if (!CreatePipe(&hReadPipe, &hWritePipe, &sa, 0)) {
        printf("{\"teste\":\"criar_pipes\",\"status\":\"erro\",\"erro\":%d}\n", GetLastError());
        return 1;
    }
    
    printf("{\"teste\":\"criar_pipes\",\"status\":\"sucesso\"}\n");
    
    CloseHandle(hReadPipe);
    CloseHandle(hWritePipe);
    return 0;
}