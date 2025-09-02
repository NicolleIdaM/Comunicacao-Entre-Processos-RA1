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
    int server, socket;
    struct sockaddr_in address;
    int opt = 1;

    //Criar socket
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd == 0) {
        perror("Socket falhou");
        exit(EXIT_FAILURE);
    }

    // Anexar socket à porta
    setsockopt(server, SOL_SOCKET, SO_REUSEADDR, (char *)&opt, sizeof(opt));
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);

    // Vincular o socket
    if (bind(server, (struct sockaddr *)&address, sizeof(address)) < 0) {
        perror("Bind falhou");
        exit(EXIT_FAILURE);
    }

    //Ouvir conexões
    if (listen(server, 3) < 0) {
        perror("Listen falhou");
        exit(EXIT_FAILURE);
    }

    // Aceitar conexões
    socket = accept(server, (struct sockaddr *)&address, (socklen_t *)&addrlen);
    if (socket < 0) {
        perror("Accept falhou");
        exit(EXIT_FAILURE);
    }

    // Receber dados
    read(socket, buffer, BUFFER_SIZE);
    std::cout << "Mensagem recebida: " << buffer << std::endl;

    // Fechar sockets
    closesocket(socket);
    closesocket(server);
    return 0;
}