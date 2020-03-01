#include <stdio.h>
#define REPLACE_CHR '@'

int main(void)
{
	int c;
	while ((c = getchar()) != EOF)
	{
		if ((c > 127 || c < 32) && (c != '\t') && (c != '\n') && (c != '\r')) {
			c = REPLACE_CHR;
		}
		putchar(c);
	}
	return 0;
}
