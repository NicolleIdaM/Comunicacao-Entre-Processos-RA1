#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <iostream>
#include <fstream>
#include <signal.h>

#ifdef _WIN32
#include <windows.h>
#define SLEEP_MS(ms) Sleep(ms)
#else
#include <unistd.h>
#define SLEEP_MS(ms) usleep(ms * 1000)
#endif

// Variável global para controle do loop
volatile sig_atomic_t keep_running = 1;

void handle_signal(int signal) {
    keep_running = 0;
}

void log_json(const char* action, const char* data = nullptr, const char* type = nullptr, int code = 0) {
    if (type && code != 0) {
        printf("{\"mechanism\":\"shared_memory\",\"action\":\"%s\",\"type\":\"%s\",\"code\":%d}\n",
               action, type, code);
    } else if (data) {
        printf("{\"mechanism\":\"shared_memory\",\"action\":\"%s\",\"data\":\"%s\"}\n",
               action, data);
    } else {
        printf("{\"mechanism\":\"shared_memory\",\"action\":\"%s\"}\n", action);
    }
    fflush(stdout);
}

void write_to_shared_memory(const char* message) {
    std::ofstream file("shared_memory.tmp");
    if (file) {
        file << message;
        file.close();
        log_json("sent", message);
    } else {
        log_json("error", nullptr, "file_write", 1);
    }
}

void read_from_shared_memory() {
    std::ifstream file("shared_memory.tmp");
    if (file) {
        std::string content;
        std::getline(file, content);
        file.close();
        
        if (!content.empty()) {
            log_json("received", content.c_str());
            // Limpar o conteúdo após ler
            std::ofstream clear_file("shared_memory.tmp");
            clear_file.close();
        }
    }
}

int main(int argc, char* argv[]) {
    // Registrar handler de sinal
    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);

    if (argc < 2) {
        log_json("error", "no_command");
        return 1;
    }

    if (strcmp(argv[1], "init") == 0) {
        std::ofstream file("shared_memory.tmp");
        file.close();
        log_json("init_ok", "shared memory initialized");
        return 0;
    }
    else if (strcmp(argv[1], "cleanup") == 0) {
        remove("shared_memory.tmp");
        log_json("cleanup_ok", "resources released");
        return 0;
    }
    else if (strcmp(argv[1], "writer") == 0) {
        if (argc < 3) {
            log_json("error", "no_message");
            return 1;
        }
        write_to_shared_memory(argv[2]);
        return 0;
    }
    else if (strcmp(argv[1], "reader") == 0) {
        log_json("reader_ready", "listening");
        
        // Ler com condição de parada
        while (keep_running) {
            read_from_shared_memory();
            SLEEP_MS(500);
        }
        
        log_json("reader_stopped", "stopped by signal");
        return 0;
    }
    else {
        log_json("error", "invalid_command");
        return 1;
    }
}