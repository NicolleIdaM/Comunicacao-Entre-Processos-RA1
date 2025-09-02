/*****************
 * INCLUDES *
*****************/
#include <winsock2.h>
#include <ws2tcpip.h>

#include <stdio.h>
#include <stdlib.h>
#include <windows.h>

#pragma comment(lib, "ws2_32.lib")

/*****************
 * DEFINES *
 *****************/
#define PORT 8080 // Porta para escutar conexões
#define BUFFER_SIZE 1024 // Tamanho do buffer de recepção

/*****************
 * MAIN FUNCTION *
 *****************/
int main() {
    WSADATA wsaData;
    SOCKET client;
    struct sockaddr_in serverAddr;
    char buffer[BUFFER_SIZE] = {0};
    
    // Inicializar Winsock
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        printf("WSAStartup falhou: %d\n", WSAGetLastError());
        return 1;
    }
    
    // Criar socket
    client = socket(AF_INET, SOCK_STREAM, 0);
    if (client == INVALID_SOCKET) {
        printf("Erro na criação do socket: %d\n", WSAGetLastError());
        WSACleanup();
        return 1;
    }
    
    // Configurar endereço do servidor
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(PORT);
    inet_pton(AF_INET, SERVER_IP, &serverAddr.sin_addr);
    
    // Conectar ao servidor
    if (connect(client, (struct sockaddr*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR) {
        printf("Falha na conexão: %d\n", WSAGetLastError());
        closesocket(client);
        WSACleanup();
        return 1;
    }
    
    printf("Conectado ao servidor!\n");
    
    // ENVIAR MENSAGEM PARA O SERVIDOR
    char* message = "Olá do cliente!";
    if (send(client, message, strlen(message), 0) == SOCKET_ERROR) {
        printf("Falaha no envio: %d\n", WSAGetLastError());
    } else {
        printf("Mensagem enviada: %s\n", message);
    }
    
    // (OPCIONAL) RECEBER RESPOSTA DO SERVIDOR
    int bytesReceived = recv(client, buffer, BUFFER_SIZE, 0);
    if (bytesReceived > 0) {
        printf("Resposta do servidor: %s\n", buffer);
    }
    
    // Fechar conexão
    closesocket(client);
    WSACleanup();
    return 0;
}