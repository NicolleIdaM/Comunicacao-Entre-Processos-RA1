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
#define SERVER_IP "127.0.0.1"
#define BUFFER_SIZE 1024

/*****************
 * MAIN FUNCTION *
 *****************/
int main(int argc, char* argv[]) {
    WSADATA wsaData;
    SOCKET sock;
    struct sockaddr_in serv_addr;
    
    // Verificar se há mensagem para enviar
    std::string message = "Olá do cliente!";
    if (argc > 1) {
        message = argv[1];
    }

    // Inicializar Winsock
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"WSAStartup\", \"code\": %d}\n", WSAGetLastError());
        return 1;
    }

    // Create socket
    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock == INVALID_SOCKET) {
        printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"socket\", \"code\": %d}\n", WSAGetLastError());
        WSACleanup();
        return 1;
    }

    // Configurar endereço do servidor
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT);
    
    // Usar inet_addr que é mais compatível com Windows
    serv_addr.sin_addr.s_addr = inet_addr(SERVER_IP);
    if (serv_addr.sin_addr.s_addr == INADDR_NONE) {
        printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"inet_addr\", \"server\": \"%s\"}\n", SERVER_IP);
        closesocket(sock);
        WSACleanup();
        return 1;
    }

    // Connect to server
    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) == SOCKET_ERROR) {
        printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"connect\", \"code\": %d, \"server\": \"%s\"}\n", WSAGetLastError(), SERVER_IP);
        closesocket(sock);
        WSACleanup();
        return 1;
    }

    printf("{\"mechanism\": \"socket\", \"action\": \"connected\", \"server\": \"%s\"}\n", SERVER_IP);
    fflush(stdout);

    // Send data
    int bytesSent = send(sock, message.c_str(), message.length(), 0);
    if (bytesSent == SOCKET_ERROR) {
        printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"send\", \"code\": %d}\n", WSAGetLastError());
    } else {
        printf("{\"mechanism\": \"socket\", \"action\": \"sent\", \"data\": \"%s\", \"bytes\": %d}\n", message.c_str(), bytesSent);
        fflush(stdout);
    }

    // Receber resposta do servidor
    char buffer[BUFFER_SIZE] = {0};
    int bytesReceived = recv(sock, buffer, BUFFER_SIZE, 0);
    if (bytesReceived > 0) {
        buffer[bytesReceived] = '\0'; // Garantir terminação da string
        printf("{\"mechanism\": \"socket\", \"action\": \"received\", \"data\": \"%s\", \"bytes\": %d}\n", buffer, bytesReceived);
        fflush(stdout);
    } else if (bytesReceived == 0) {
        printf("{\"mechanism\": \"socket\", \"action\": \"disconnected\", \"reason\": \"server_closed\"}\n");
        fflush(stdout);
    } else {
        printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"recv\", \"code\": %d}\n", WSAGetLastError());
        fflush(stdout);
    }

    // Close socket
    closesocket(sock);
    WSACleanup();
    
    printf("{\"mechanism\": \"socket\", \"action\": \"closed\"}\n");
    fflush(stdout);
    return 0;
}