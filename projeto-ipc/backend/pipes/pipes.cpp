#include <sys/types.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#define READ_END 0
#define WRITE_END 1

int main(void) {
    char write_msg[20] = "Hello, World!";
    char read_msg[20];
    int fd[2];
    pid_t pid;

    // Create the pipe
    if (pipe(fd) == -1) {
        fprintf(stderr, "Pipe failed");
        return 1;
    }

    // Fork a child process
    pid = fork();
    if (pid < 0) {
        fprintf(stderr, "Fork failed");
        return 1;
    }

    if (pid > 0) { // Parent process
        close(fd[READ_END]); // Close unused read end

        // Write to the pipe
        write(fd[WRITE_END], write_msg, strlen(write_msg) + 1);
        close(fd[WRITE_END]); // Close write end after writing
    } else { // Child process
        close(fd[WRITE_END]); // Close unused write end

        // Read from the pipe
        read(fd[READ_END], read_msg, sizeof(read_msg));
        printf("Child received: %s\n", read_msg);
        close(fd[READ_END]); // Close read end after reading
    }

    return 0;
}