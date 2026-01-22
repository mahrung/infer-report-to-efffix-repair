#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <sys/un.h>

static int helper_function(void) {
    return 0;
}

int lxc_abstract_unix_connect(const char *name, int type) {
    struct sockaddr_un addr;
    int fd;

    fd = socket(AF_UNIX, type, 0);
    if (fd < 0)
        return -1;

    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;

    return fd;
}

void another_function(void) {
    printf("hello\n");
}

int multi_line_function(
    int arg1,
    int arg2,
    int arg3)
{
    return arg1 + arg2 + arg3;
}
