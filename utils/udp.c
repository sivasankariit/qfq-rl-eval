/* Sample UDP client */

#include <sys/socket.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <sys/time.h>
#include <stdarg.h>
#include <sys/resource.h>
#include <sys/mman.h>
#include <time.h>

#define MAX_SOCKS (10000)
#define USEC_PER_SEC (1000000)
#define NSEC_PER_SEC (1000000000LLU)
#define min(a,b) ((a)<(b) ? (a):(b))

int BURST_BYTES = (1 << 22);
int MTU = 9000;
int HEADER_SIZE = 14 + 20 + 8;

int sockfd[MAX_SOCKS];
struct sockaddr_in servaddr[MAX_SOCKS];
char *buff;

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

unsigned long long timespec_diff_nsec(struct timespec *start, struct timespec *end) {
	return (end->tv_sec - start->tv_sec) * 1LLU * NSEC_PER_SEC + (end->tv_nsec - start->tv_nsec);
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

unsigned long long spin_sleep_nsec(int nsec, struct timespec *prev) {
	struct timespec start, curr;
	if (prev->tv_sec == 0 && prev->tv_nsec == 0) {
		clock_gettime(CLOCK_REALTIME, prev);
	} else {
		start = *prev;
	}

	do {
		clock_gettime(CLOCK_REALTIME, &curr);
	} while (timespec_diff_nsec(&start, &curr) < nsec);

	*prev = curr;
	return timespec_diff_nsec(&start, &curr);
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

void set_num_file_limit(int n) {
	rlim_t num_files;
	struct rlimit rl;
	int ret;

	num_files = n;
	ret = getrlimit(RLIMIT_NOFILE, &rl);
	if (ret == 0) {
		rl.rlim_cur = n + 1000;
		rl.rlim_max = n + 1000;
		ret = setrlimit(RLIMIT_NOFILE, &rl);
		if (ret != 0) {
			perror("setrlimit");
			exit(-1);
		}
	} else {
		perror("getrlimit");
		exit(-1);
	}
}

inline int bytes_on_wire(int write_size) {
	int num_packets = (write_size + MTU - 1) / MTU;
	return write_size + num_packets * HEADER_SIZE;
}

int main(int argc, char**argv)
{
	int n, startport, i, rate_mbps, usec = 0, nsec = 0, sent;
	int slept, ret, sendbuff, send_size;
	struct sockaddr_in cliaddr;
	FILE *fp; int fd;
	off_t offset = 0;
	int prio;

	if (argc != 7)
	{
		printf("usage: %s IP start-port num-ports rate_mbps burst-size prio\n", argv[0]);
		exit(1);
	}

	startport = atoi(argv[2]);
	n = atoi(argv[3]);
	rate_mbps = atoi(argv[4]);
	BURST_BYTES = atoi(argv[5]);
	prio = atoi(argv[6]);

	/* First set resource limits */
	set_num_file_limit(n);

	send_size = min(BURST_BYTES, 65536 - HEADER_SIZE);

	fd = open(argv[0], O_RDONLY);

	buff = mmap(NULL, send_size, PROT_READ,
		MAP_SHARED | MAP_ANONYMOUS, -1, 0);

	if (buff == MAP_FAILED) {
		perror("mmap");
		return -1;
	}

	sendbuff = 1 << 20;

	if (rate_mbps > 0) {
		usec = bytes_on_wire(BURST_BYTES) * 8 / rate_mbps;
		nsec = bytes_on_wire(BURST_BYTES) * 8LLU * 1000 / rate_mbps;
		usec = nsec / 1000;

		printf("Sleeping for %dns (%dus), sendbuff %d, send_size %d, burst %d, fd %d, prio %d\n",
		       nsec, usec, sendbuff, send_size, BURST_BYTES, fd, prio);
	} else {
		printf("App rate limiting disabled, sendbuff %d, send_size %d, burst %d, fd %d, prio %d\n",
		       sendbuff, send_size, BURST_BYTES, fd, prio);
	}

	for (i = 0; i < n; i++) {
		sockfd[i] = socket(AF_INET, SOCK_DGRAM, 0);

		if (sockfd[i] < 0) {
			perror("socket");
			return -1;
		}

		//set_non_blocking(sockfd[i]);
		if (setsockopt(sockfd[i], SOL_SOCKET, SO_SNDBUF, &sendbuff, sizeof(sendbuff)) < 0) {
			perror("setsockopt sendbuff");
			return -1;
		}

		if (setsockopt(sockfd[i], SOL_SOCKET, SO_PRIORITY, &prio, sizeof(prio)) < 0) {
			perror("setsockopt sk_prio");
			return -1;
		}

		bzero(&servaddr[i], sizeof(servaddr[i]));
		servaddr[i].sin_family = AF_INET;
		servaddr[i].sin_addr.s_addr = inet_addr(argv[1]);
		servaddr[i].sin_port = htons(startport + i);

		/* No need to connect when using sendto()
		if (connect(sockfd[i], (const struct sockaddr *)&servaddr[i],
			    sizeof servaddr[i]))
		{
			perror("connect");
			return -1;
		}
		*/
	}

	struct timeval prev;
	struct timespec prev_ns;

	prev.tv_sec = 0;
	prev.tv_usec = 0;

	prev_ns.tv_sec = 0;
	prev_ns.tv_nsec = 0;
	printf("Starting %d udp ports of traffic to %s\n", n, argv[1]);

	while (1) {
		i = 0;
		for (i = 0; i < n; i++) {
			offset = 0;
			//ret = sendfile(sockfd[i], fd, &offset, send_size);
			/* Always send on same socket to all dst ports */
			ret = sendto(sockfd[0], buff,
				     send_size, 0,
				     (struct sockaddr *)&servaddr[i],
				     sizeof(servaddr[i]));


			if (ret != -1) {
				sent += bytes_on_wire(send_size);
			}

			if (sent >= BURST_BYTES) {
				sent -= BURST_BYTES;

				if (usec > 0) {
					slept = spin_sleep_nsec(nsec, &prev_ns);
					//print_every(USEC_PER_SEC, "Slept %dus, next %dus\n", slept, usec);
				}
			}
		}
	}

	return 0;
}
