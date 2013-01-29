/* Sample UDP client */

#include <sys/socket.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>

#define MAX_SOCKS (10000)
int sockfd[MAX_SOCKS];
struct sockaddr_in servaddr[MAX_SOCKS];
char buff[9000];

int set_non_blocking(int fd)
{
    int flags;
    /* If they have O_NONBLOCK, use the Posix way to do it */
#if defined(O_NONBLOCK)
    /* Fixme: O_NONBLOCK is defined but broken on SunOS 4.1.x and AIX 3.2.5. */
    if (-1 == (flags = fcntl(fd, F_GETFL, 0)))
        flags = 0;
    return fcntl(fd, F_SETFL, flags | O_NONBLOCK);
#else
    /* Otherwise, use the old way of doing it */
    flags = 1;
    return ioctl(fd, FIOBIO, &flags);
#endif
}

int main(int argc, char**argv)
{
	int n, startport, i;
	struct sockaddr_in cliaddr;

	if (argc != 4)
	{
		printf("usage: %s IP start-port num-ports\n", argv[0]);
		exit(1);
	}

	startport = atoi(argv[2]);
	n = atoi(argv[3]);

	for (i = 0; i < n; i++) {
		sockfd[i] = socket(AF_INET, SOCK_DGRAM, 0);
		set_non_blocking(sockfd[i]);

		bzero(&servaddr[i], sizeof(servaddr[i]));
		servaddr[i].sin_family = AF_INET;
		servaddr[i].sin_addr.s_addr = inet_addr(argv[1]);
		servaddr[i].sin_port = htons(startport + i);
	}

	printf("Starting %d udp ports of traffic to %s\n", n, argv[1]);
	while (1) {
		i = 0;
		for (i = 0; i < n; i++) {
			sendto(sockfd[i], buff,
			       sizeof(buff), 0,
			       (struct sockaddr *)&servaddr[i],
			       sizeof(servaddr[i]));
		}
	}

	return 0;
}
