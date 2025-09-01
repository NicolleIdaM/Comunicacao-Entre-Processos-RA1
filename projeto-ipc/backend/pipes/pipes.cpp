#include <windows.h>
#include <stdio.h>

int main(void) {
    HANDLE hRead, hWrite;
    SECURITY_ATTRIBUTES sa = { sizeof(SECURITY_ATTRIBUTES), NULL, TRUE };
    char write_msg[] = "Hello, World!";
    char read_msg[20];
    DWORD bytesWritten, bytesRead;

    // Create the pipe
    if (!CreatePipe(&hRead, &hWrite, &sa, 0)) {
        fprintf(stderr, "Pipe failed\n");
        return 1;
    }

    // Create child process
    STARTUPINFO si = { sizeof(STARTUPINFO) };
    PROCESS_INFORMATION pi;
    si.dwFlags = STARTF_USESTDHANDLES;
    si.hStdInput = hRead;
    si.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
    si.hStdError = GetStdHandle(STD_ERROR_HANDLE);

    // Prepare command line for child (this example just reads from stdin)
    char cmd[] = "cmd /c more"; // 'more' will echo stdin to stdout

    if (!CreateProcessA(
        NULL, cmd, NULL, NULL, TRUE, 0, NULL, NULL, &si, &pi)) {
        fprintf(stderr, "CreateProcess failed\n");
        CloseHandle(hRead);
        CloseHandle(hWrite);
        return 1;
    }

    // Parent writes to the pipe
    WriteFile(hWrite, write_msg, (DWORD)strlen(write_msg), &bytesWritten, NULL);
    CloseHandle(hWrite); // Done writing

    // Optionally, parent can read from child's stdout if needed

    // Wait for child to finish
    WaitForSingleObject(pi.hProcess, INFINITE);

    // Clean up
    CloseHandle(hRead);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);

    return 0;
}