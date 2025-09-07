#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdio.h>

#define PORT 8080

int main() {
    WSADATA wsaData;
    SOCKET sock;
    struct sockaddr_in address;
    
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
    
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);
    
    if (bind(sock, (struct sockaddr *)&address, sizeof(address)) == SOCKET_ERROR) {
        printf("{\"teste\":\"conexao_socket\",\"status\":\"erro\",\"tipo\":\"bind\",\"code\":%d}\n", WSAGetLastError());
        closesocket(sock);
        WSACleanup();
        return 1;
    }
    
    if (listen(sock, 3) == SOCKET_ERROR) {
        printf("{\"teste\":\"conexao_socket\",\"status\":\"erro\",\"tipo\":\"conexao\",\"code\":%d}\n", WSAGetLastError());
        closesocket(sock);
        WSACleanup();
        return 1;
    }
    
    printf("{\"teste\":\"conexao_socket\",\"status\":\"successo\",\"porta\":%d}\n", PORT);
    
    closesocket(sock);
    WSACleanup();
    return 0;
}