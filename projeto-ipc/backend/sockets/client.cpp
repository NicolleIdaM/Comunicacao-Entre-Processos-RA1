/*****************
 * INCLUDES *
*****************/
#include <winsock2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/*****************
 * DEFINES *
 *****************/
#define PORT 8080
#define SERVER_IP "127.0.0.1"
#define BUFFER_SIZE 1024

/*****************
 * MAIN FUNCTION *
 *****************/
int main() {
    WSADATA wsaData;
    SOCKET sock;
    struct sockaddr_in serv_addr;
    const char *hello = "Olá do cliente!";
    
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

    //Configurar endereço do servidor
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT);
    serv_addr.sin_addr.s_addr = inet_addr(SERVER_IP);
    
    // Verificar se o endereço é válido
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

    // Send data
    if (send(sock, hello, strlen(hello), 0) == SOCKET_ERROR) {
        printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"send\", \"code\": %d}\n", WSAGetLastError());
    } else {
        printf("{\"mechanism\": \"socket\", \"action\": \"sent\", \"data\": \"%s\"}\n", hello);
    }

    // Receber resposta do servidor
    char buffer[BUFFER_SIZE] = {0};
    int bytesReceived = recv(sock, buffer, BUFFER_SIZE, 0);
    if (bytesReceived > 0) {
        printf("{\"mechanism\": \"socket\", \"action\": \"received\", \"data\": \"%s\"}\n", buffer);
    } else if (bytesReceived == 0) {
        printf("{\"mechanism\": \"socket\", \"action\": \"disconnected\", \"reason\": \"server_closed\"}\n");
    } else {
        printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"recv\", \"code\": %d}\n", WSAGetLastError());
    }

    // Close socket
    closesocket(sock);
    WSACleanup();
    
    printf("{\"mechanism\": \"socket\", \"action\": \"closed\"}\n");
    return 0;
}