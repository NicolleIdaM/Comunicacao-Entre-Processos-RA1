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
#define PORT 8080
#define BUFFER_SIZE 1024

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

    // Inicializar Winsock
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"WSAStartup\", \"code\": %d}\n", WSAGetLastError());
        return 1;
    }
    
    // Criar socket
    server = socket(AF_INET, SOCK_STREAM, 0);
    if (server == INVALID_SOCKET) {
        printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"socket\", \"code\": %d}\n", WSAGetLastError());
        WSACleanup();
        return 1;
    }

    // Configurar socket
    if (setsockopt(server, SOL_SOCKET, SO_REUSEADDR, (char*)&opt, sizeof(opt)) == SOCKET_ERROR) {
        printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"setsockopt\", \"code\": %d}\n", WSAGetLastError());
        closesocket(server);
        WSACleanup();
        return 1;
    }

    // Configurar endereço
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);

    // Vincular o socket
    if (bind(server, (struct sockaddr *)&address, sizeof(address)) == SOCKET_ERROR) {
        int erro = WSAGetLastError();
        printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"bind\", \"code\": %d, \"port\": %d}\n", erro, PORT);
        closesocket(server);
        WSACleanup();
        return 1;
    }

    // Ouvir conexões
    if (listen(server, 3) == SOCKET_ERROR) {
        printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"listen\", \"code\": %d}\n", WSAGetLastError());
        closesocket(server);
        WSACleanup();
        return 1;
    }

    //Saída JSON para frontend monitorar
    printf("{\"mechanism\": \"socket\", \"action\": \"listening\", \"port\": %d}\n", PORT);

    // Aceitar conexões
    client = accept(server, (struct sockaddr*)&address, &addrlen);
    if (client == INVALID_SOCKET) {
        printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"accept\", \"code\": %d}\n", WSAGetLastError());
        closesocket(server);
        WSACleanup();
        return 1;
    }

    //Cliente conectado em JSON
    printf("{\"mechanism\": \"socket\", \"action\": \"connected\", \"client\": \"%s\"}\n", inet_ntoa(address.sin_addr));

    // Receber dados
    int bytesReceived = recv(client, buffer, BUFFER_SIZE, 0);
    if (bytesReceived > 0) {
        //Mensagem recebida em JSON
        printf("{\"mechanism\": \"socket\", \"action\": \"received\", \"data\": \"%s\"}\n", buffer);
        
        // ENVIAR RESPOSTA
        const char* response = "Mensagem recebida pelo servidor!";
        send(client, response, strlen(response), 0);
        
        //Confirmação de envio em JSON
        printf("{\"mechanism\": \"socket\", \"action\": \"sent\", \"data\": \"%s\"}\n", response);
    } else if (bytesReceived == 0) {
        printf("{\"mechanism\": \"socket\", \"action\": \"disconnected\", \"reason\": \"client_closed\"}\n");
    } else {
        printf("{\"mechanism\": \"socket\", \"action\": \"error\", \"type\": \"recv\", \"code\": %d}\n", WSAGetLastError());
    }

    // Fechar sockets
    closesocket(client);
    closesocket(server);
    WSACleanup();
    
    //Fim da conexão em JSON
    printf("{\"mechanism\": \"socket\", \"action\": \"closed\"}\n");
    return 0;
}