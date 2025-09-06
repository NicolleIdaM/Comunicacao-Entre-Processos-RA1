/*****************
 * INCLUDES *
*****************/
#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <iostream>
#include <string>

/*****************
 * DEFINES *
 *****************/
#define PORT 8080
#define BUFFER_SIZE 1024

/*****************
 * MAIN FUNCTION *
 *****************/
int main() {  // Removidos os parâmetros não utilizados
    WSADATA wsaData;
    SOCKET server_fd, new_socket;
    struct sockaddr_in address;
    int opt = 1;
    int addrlen = sizeof(address);
    char buffer[BUFFER_SIZE] = {0};

    // Inicializar Winsock
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"WSAStartup\", \"code\": %d}\n", WSAGetLastError());
        return 1;
    }

    // Create socket file descriptor
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd == INVALID_SOCKET) {
        printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"socket\", \"code\": %d}\n", WSAGetLastError());
        WSACleanup();
        return 1;
    }

    // Configurar opções do socket
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, (char*)&opt, sizeof(opt)) == SOCKET_ERROR) {
        printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"setsockopt\", \"code\": %d}\n", WSAGetLastError());
        closesocket(server_fd);
        WSACleanup();
        return 1;
    }

    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);

    // Bind do socket
    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) == SOCKET_ERROR) {
        printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"bind\", \"code\": %d, \"port\": %d}\n", WSAGetLastError(), PORT);
        closesocket(server_fd);
        WSACleanup();
        return 1;
    }

    // Listen
    if (listen(server_fd, 3) == SOCKET_ERROR) {
        printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"listen\", \"code\": %d}\n", WSAGetLastError());
        closesocket(server_fd);
        WSACleanup();
        return 1;
    }

    printf("{\"mechanism\": \"socket\", \"action\": \"listening\", \"port\": %d}\n", PORT);
    fflush(stdout);

    // Accept conexão
    new_socket = accept(server_fd, (struct sockaddr *)&address, &addrlen);
    if (new_socket == INVALID_SOCKET) {
        printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"accept\", \"code\": %d}\n", WSAGetLastError());
        closesocket(server_fd);
        WSACleanup();
        return 1;
    }

    printf("{\"mechanism\": \"socket\", \"action\": \"accepted\"}\n");
    fflush(stdout);

    // Ler dados do cliente
    int bytesRead = recv(new_socket, buffer, BUFFER_SIZE, 0);
    if (bytesRead > 0) {
        buffer[bytesRead] = '\0'; // Garantir terminação da string
        printf("{\"mechanism\": \"socket\", \"action\": \"received\", \"data\": \"%s\", \"bytes\": %d}\n", buffer, bytesRead);
        fflush(stdout);

        // Enviar resposta
        std::string response = "Mensagem recebida: ";
        response += buffer;
        int bytesSent = send(new_socket, response.c_str(), response.length(), 0);
        if (bytesSent == SOCKET_ERROR) {
            printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"send\", \"code\": %d}\n", WSAGetLastError());
        } else {
            printf("{\"mechanism\": \"socket\", \"action\": \"sent\", \"data\": \"%s\", \"bytes\": %d}\n", response.c_str(), bytesSent);
            fflush(stdout);
        }
    } else if (bytesRead == 0) {
        printf("{\"mechanism\": \"socket\", \"action\": \"disconnected\", \"reason\": \"client_closed\"}\n");
        fflush(stdout);
    } else {
        printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"recv\", \"code\": %d}\n", WSAGetLastError());
        fflush(stdout);
    }

    // Fechar sockets
    closesocket(new_socket);
    closesocket(server_fd);
    WSACleanup();

    printf("{\"mechanism\": \"socket\", \"action\": \"closed\"}\n");
    fflush(stdout);
    return 0;
}