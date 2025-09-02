/*****************
 * INCLUDES *
*****************/
#include <winsock2.h>
#include <ws2tcpip.h>

#include <stdio.h>
#include <stdlib.h>
#include <windows.h>

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
    SOCKET server, client;
    struct sockaddr_in address;
    int addrlen = sizeof(address);
    char buffer[BUFFER_SIZE] = {0};
    int opt = 1;

    // Inicializar Winsock (OBRIGATÓRIO no Windows)
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        printf("WSAStartup failed: %d\n", WSAGetLastError());
        return 1;
    }
    
    //Criar socket
    server = socket(AF_INET, SOCK_STREAM, 0);
    if (server == 0) {
        printf("Socket falhou: %d\n", WSAGetLastError());
        WSACleanup();
        return 1;
    }

    // Configurar socket
    if (setsockopt(server, SOL_SOCKET, SO_REUSEADDR, (char*)&opt, sizeof(opt)) == SOCKET_ERROR) {
        printf("Setsockopt falhou: %d\n", WSAGetLastError());
        closesocket(server);
        WSACleanup();
        return 1;
    }

    // Anexar socket à porta
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);

    // Vincular o socket
    if (bind(server, (struct sockaddr *)&address, sizeof(address)) == SOCKET_ERROR) {
        int erro = WSAGetLastError();
        printf("Bind falhou: %d\n", erro);

        if (erro == WSAEADDRINUSE) {
            printf("A porta %d já está em uso!\n", PORT);
            printf("Execute: netstat -ano | findstr :%d\n", PORT);
        }
    
        closesocket(server);
        WSACleanup();
        return 1;
    }

    //Ouvir conexões
    if (listen(server, 3) == SOCKET_ERROR) {
        printf("Listen falhou: %d\n", WSAGetLastError());
        closesocket(server);
        WSACleanup();
        return 1;
    }

    printf("Servidor ouvindo na porta %d...\n", PORT);

    // Aceitar conexões
    client = accept(server, (struct sockaddr*)&address, &addrlen);
    if (client == INVALID_SOCKET) {
        printf("Accept falhou: %d\n", WSAGetLastError());
        closesocket(server);
        WSACleanup();
        return 1;
    }

    printf("Cliente conectado!\n");

    // Receber dados
    int bytesReceived = recv(client, buffer, BUFFER_SIZE, 0);
    if (bytesReceived > 0) {
        printf("Mensagem recebida: %s\n", buffer);
        
        // ENVIAR RESPOSTA (opcional)
        const char* response = "Mensagem recebida pelo servidor!";
        send(client, response, strlen(response), 0);
    } else if (bytesReceived == 0) {
        printf("Conexão encerrada pelo cliente.\n");
    } else {
        printf("Erro ao receber dados: %d\n", WSAGetLastError());
    }

    // Fechar sockets
    closesocket(client);
    closesocket(server);
    WSACleanup();
    return 0;
}