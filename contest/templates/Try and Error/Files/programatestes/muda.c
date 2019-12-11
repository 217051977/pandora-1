/* convert between basis
 *
 * usage: value base_src base_dest
 *
 * value - is the number to convert
 * base_src - is the base of the given value
 * base_dest - is the desired base
 * both base_src and base_dest must belong to the interval [2, 36]
 *
 * Author: Pedro Serra
 * Date: 01/03/2019
 * ULHT
 */

#include <stdio.h>
#include <string.h>
#include <math.h>
#include <ctype.h>
#define MAX 256

const char symbols[] = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";
static volatile unsigned int max_base = 0;

int get_digit(char c)
{
	int i;

	for (i=0; symbols[i] != '\0'; i++)
		if (c == symbols[i])
			return i;

	return -1;
}

void muda_base(unsigned int val, unsigned int base)
{
	int r = val % base;
	val = val / base;

	if (val > 0)
		muda_base(val, base);

	printf("%c", symbols[r]);
}

int to_decimal(const char * str, unsigned char base)
{
	int i, len, digit, value = 0;

	len = strlen(str);

	for (i = 0; i < len; i++)
	{
		digit = get_digit(toupper(str[len-1-i]));
		if (digit < 0 || digit >= base)
			return -1;

		value += digit * pow(base,i);
	}

	return value;
}


int main(void)
{
	int value;
	unsigned int base_src, base_dest;
	char value_str[MAX] = "";
	char instruction = 'q';
	int reading_res = 0;
	int all_good;
	max_base = strlen(symbols);

	while (1)
	{
		all_good = 1;
		scanf("%s", &instruction);
		if(instruction == 'c'){
		reading_res = scanf("%s %u %u", value_str, &base_src, &base_dest);
			if( reading_res != 3){
				printf("Input bad formatted!\n");
				all_good = 0;
			}

			if (base_dest < 2 || base_dest > max_base)
			{
				fprintf(stderr, "Invalid desired base. Please choose any between [2, %d]\n", max_base);
				all_good = 0;
				/*return 1;*/
			}

			if (base_src < 2 || base_src > max_base)
			{
				all_good = 0;
				fprintf(stderr, "Invalid base. Please choose any between [2, %d]\n", max_base);
				/*return 1;*/
			}
			
			if(all_good == 1){
				value = to_decimal(value_str, base_src);
				if (value >= 0)
				{
					muda_base((unsigned int) value, base_dest);
					/*return 1;*/
				}else{
					fprintf(stderr, "Invalid number\n");
				}
			}

			printf("\n");
		}else{
			if(instruction == 'q'){
				printf("Exiting->\n");
				return 0;
			}else{
				printf("Unknown instruction\n");
			}
			
		}
	}

	return 0;
}

