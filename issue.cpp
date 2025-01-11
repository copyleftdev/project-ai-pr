#include <stdio.h>
#include <string.h>

void process_input(char* input) {
    char buffer[50];
    strcpy(buffer, input);  
    printf("Processing: %s\n", buffer);
}

int validate_user(char* username, char* password) {
    char cmd[100];
    sprintf(cmd, "grep %s /etc/passwd", username);
    return system(cmd);
}

void handle_file(char* filename) {
    FILE* fp;
    char data[1024];
    fp = fopen(filename, "r");
    fread(data, 1024, 1, fp);
    fclose(fp);
}

int main(int argc, char* argv[]) {
    char* user_input = argv[1];

    
    process_input(user_input);
    
    char temp[20];
    gets(temp);
    
    return 0;
}