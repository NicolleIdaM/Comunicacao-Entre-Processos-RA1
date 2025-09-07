#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdio.h>

int main() {
    WSADATA wsaData;
    SOCKET sock;
    
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        printf("{\"teste\":\"criacao_socket\",\"status\":\"erro\",\"tipo\":\"WSAStartup\",\"code\":%d}\n", WSAGetLastError());
        return 1;
    }
    
    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock == INVALID_SOCKET) {
        printf("{\"teste\":\"criacao_socket\",\"status\":\"erro\",\"tipo\":\"socket\",\"code\":%d}\n", WSAGetLastError());
        WSACleanup();
        return 1;
    }
    
    printf("{\"teste\":\"criacao_socket\",\"status\":\"sucesso\"}\n");
    
    closesocket(sock);
    WSACleanup();
    return 0;
}