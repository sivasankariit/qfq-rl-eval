/* Sample UDP client */

#include <sys/socket.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <sys/time.h>
#include <stdarg.h>

#define MAX_SOCKS (10000)
#define USEC_PER_SEC (1000000)
#define min(a,b) ((a)<(b) ? (a):(b))

int BURST_BYTES = (1 << 22);

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

unsigned long long timeval_diff_usec(struct timeval *start, struct timeval *end) {
	return (end->tv_sec - start->tv_sec) * 1LLU * USEC_PER_SEC + end->tv_usec - start->tv_usec;
}

/* Returns the time it actually slept for.
 * Sets prev to the last measured timeval after the sleeptime.
 * If prev is not 0, then the function uses prev as the start time to sleep from
 * instead of taking the current time.
 */
unsigned long long spin_sleep(int usec, struct timeval *prev) {
	struct timeval start, curr;
	if (prev->tv_sec == 0 && prev->tv_usec == 0) {
		gettimeofday(&start, NULL);
	} else {
		start = *prev;
	}

	do {
		gettimeofday(&curr, NULL);
	} while (timeval_diff_usec(&start, &curr) < usec);

	*prev = curr;
	return timeval_diff_usec(&start, &curr);
}

int print_every(int usec, char *fmt, ...) {
	static struct timeval prev;
	int ret;
	struct timeval curr;
	va_list args;
	va_start(args, fmt);
	gettimeofday(&curr, NULL);

	if (timeval_diff_usec(&prev, &curr) > usec) {
		prev = curr;
		ret = vprintf(fmt, args);
	}

	va_end(args);
	return ret;
}

int main(int argc, char**argv)
{
	int n, startport, i, rate_mbps, usec, sent;
	int slept, TARGET, ret, sendbuff, send_size;
	struct sockaddr_in cliaddr;

	if (argc < 5)
	{
		printf("usage: %s IP start-port num-ports rate_mbps [burst-size]\n", argv[0]);
		exit(1);
	}

	startport = atoi(argv[2]);
	n = atoi(argv[3]);
	rate_mbps = atoi(argv[4]);

	if (argc > 5) {
		BURST_BYTES = atoi(argv[5]);
	}

	usec = BURST_BYTES * 8 / rate_mbps;
	TARGET = usec;

	send_size = min(BURST_BYTES, sizeof(buff));
	sendbuff = 1 << 20;

	printf("Sleeping for %dus, sendbuff %d, send_size %d, burst %d\n",
	       usec, sendbuff, send_size, BURST_BYTES);

	for (i = 0; i < n; i++) {
		sockfd[i] = socket(AF_INET, SOCK_DGRAM, 0);
		set_non_blocking(sockfd[i]);
		if (setsockopt(sockfd[i], SOL_SOCKET, SO_SNDBUF, &sendbuff, sizeof(sendbuff)) < 0) {
			perror("setsockopt sendbuff");
			return -1;
		}

		bzero(&servaddr[i], sizeof(servaddr[i]));
		servaddr[i].sin_family = AF_INET;
		servaddr[i].sin_addr.s_addr = inet_addr(argv[1]);
		servaddr[i].sin_port = htons(startport + i);
	}

	struct timeval prev;
	prev.tv_sec = 0;
	prev.tv_usec = 0;
	printf("Starting %d udp ports of traffic to %s\n", n, argv[1]);
	while (1) {
		i = 0;
		for (i = 0; i < n; i++) {
			ret = sendto(sockfd[i], buff,
				     send_size, 0,
				     (struct sockaddr *)&servaddr[i],
				     sizeof(servaddr[i]));

			if (ret > 0) {
				sent += ret;
			}

			if (sent >= BURST_BYTES) {
				sent -= BURST_BYTES;
				slept = spin_sleep(usec, &prev);
				//print_every(USEC_PER_SEC, "Slept %dus, next %dus\n", slept, usec);
			}
		}
	}

	return 0;
}
