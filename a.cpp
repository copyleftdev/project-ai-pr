#include <iostream>
#include <cstdio>
#include <cstdlib>
#include <cstring>

int main() {
       char command[64];

    std::cout << "Enter a shell command to run: ";


    gets(command);


    system(command);

    return 0;
}
