#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdio.h>

#define PORT 8080
#define SERVER_IP "127.0.0.1"

int main() {
    WSADATA wsaData;
    SOCKET sock;
    struct sockaddr_in serv_addr;
    
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        printf("{\"teste\":\"conexao_socket\",\"status\":\"erro\",\"tipo\":\"WSAStartup\",\"code\":%d}\n", WSAGetLastError());
        return 1;
    }
    
    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock == INVALID_SOCKET) {
        printf("{\"teste\":\"conexao_socket\",\"status\":\"erro\",\"tipo\":\"socket\",\"code\":%d}\n", WSAGetLastError());
        WSACleanup();
        return 1;
    }
    
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT);
    serv_addr.sin_addr.s_addr = inet_addr(SERVER_IP);
    
    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) == SOCKET_ERROR) {
        printf("{\"teste\":\"conexao_socket\",\"status\":\"erro\",\"tipo\":\"conectar\",\"code\":%d,\"servidor\":\"%s:%d\"}\n", 
               WSAGetLastError(), SERVER_IP, PORT);
        closesocket(sock);
        WSACleanup();
        return 1;
    }
    
    printf("{\"teste\":\"conexao_socket\",\"status\":\"successo\",\"servidor\":\"%s:%d\"}\n", SERVER_IP, PORT);
    
    closesocket(sock);
    WSACleanup();
    return 0;
}