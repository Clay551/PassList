import itertools
import string
import argparse
import random
import os
import time
import signal
from tqdm import tqdm
import pyfiglet
from colorama import Fore, init 
import colorama

class GracefulKiller:
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        self.kill_now = True

def generate_passwords(charset, min_length, max_length, patterns=None):
    if patterns:
        for pattern in patterns:
            yield from generate_password_from_pattern(pattern, charset)
    else:
        for length in range(min_length, max_length + 1):
            yield from (''.join(p) for p in itertools.product(charset, repeat=length))

def generate_password_from_pattern(pattern, charset):
    parts = []
    for char in pattern:
        if char == 'l':
            parts.append(string.ascii_lowercase)
        elif char == 'u':
            parts.append(string.ascii_uppercase)
        elif char == 'd':
            parts.append(string.digits)
        elif char == 's':
            parts.append(string.punctuation)
        else:
            parts.append(charset)
    yield from (''.join(p) for p in itertools.product(*parts))

def generate_smart_mutations(word):
    yield word
    yield word.capitalize()
    yield word.upper()
    yield word.lower()
    yield word[::-1]
    yield word + str(random.randint(0, 9999))
    yield ''.join(c if random.random() > 0.3 else c.upper() for c in word)

def save_passwords(passwords, output_file, append=False):
    mode = 'a' if append else 'w'
    with open(output_file, mode) as f:
        for password in passwords:
            f.write(password + '\n')

def main():
    parser = argparse.ArgumentParser(description="Advanced Password List Generator")
    parser.add_argument("-min", type=int, default=4, help="Minimum password length")
    parser.add_argument("-max", type=int, default=12, help="Maximum password length")
    parser.add_argument("-l", action="store_true", help="Use lowercase letters")
    parser.add_argument("-u", action="store_true", help="Use uppercase letters")
    parser.add_argument("-d", action="store_true", help="Use digits")
    parser.add_argument("-s", action="store_true", help="Use special characters")
    parser.add_argument("-c", type=str, help="Custom characters")
    parser.add_argument("-p", type=str, help="Password patterns (e.g., 'luds,llddss')")
    parser.add_argument("-o", type=str, default="passwords.txt", help="Output file name")
    parser.add_argument("--smart", action="store_true", help="Use smart password generation")
    parser.add_argument("--chunk-size", type=int, default=10000, help="Chunk size for password generation")
    args = parser.parse_args()

    print(colorama.Fore.RED)
    pyfiglet.print_figlet("Asylum")
    print(colorama.Fore.GREEN)
    print("        Password List Generator")
    print(colorama.Fore.RESET)
    print("Advanced Password List Generator")
    print("================================")

    charset = ''
    if args.l: charset += string.ascii_lowercase
    if args.u: charset += string.ascii_uppercase
    if args.d: charset += string.digits
    if args.s: charset += string.punctuation
    if args.c: charset += args.c

    if not charset:
        print("Error: No character set selected. Please use at least one of -l, -u, -d, -s, or -c options.")
        return

    print(f"Character set: {charset}")

    patterns = args.p.split(',') if args.p else None
    if patterns:
        print(f"Password patterns: {patterns}")

    if args.min > args.max:
        print("Error: Minimum password length cannot be greater than maximum length.")
        return

    killer = GracefulKiller()
    
    start_time = time.time()
    passwords_generated = 0

    print(f"Starting password generation...")

    try:
        with open(args.o, 'w') as outfile:
            for password in generate_passwords(charset, args.min, args.max, patterns):
                if killer.kill_now:
                    print("\nStopping password generation...")
                    break

                if args.smart:
                    for smart_password in generate_smart_mutations(password):
                        outfile.write(smart_password + '\n')
                        passwords_generated += 1
                else:
                    outfile.write(password + '\n')
                    passwords_generated += 1

                if passwords_generated % args.chunk_size == 0:
                    print(f"Progress: {passwords_generated:,} passwords generated")

    except IOError as e:
        print(f"Error writing to file: {e}")
        return

    end_time = time.time()
    print(f"\nPassword generation completed.")
    print(f"Execution time: {end_time - start_time:.2f} seconds")
    print(f"Total passwords generated: {passwords_generated:,}")
    print(f"Password list saved to {args.o}")

if __name__ == "__main__":
    main()
