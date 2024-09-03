import itertools
import string
import argparse
import random
import os
import multiprocessing
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

class PasswordGenerator:
    def __init__(self, min_length, max_length, charset, patterns=None, common_words=None):
        self.min_length = min_length
        self.max_length = max_length
        self.charset = charset
        self.patterns = patterns
        self.common_words = common_words

    def generate_passwords(self):
        if self.patterns:
            for pattern in self.patterns:
                yield from self._generate_password_from_pattern(pattern)
        else:
            for length in range(self.min_length, self.max_length + 1):
                yield from (''.join(p) for p in itertools.product(self.charset, repeat=length))

    def _generate_password_from_pattern(self, pattern):
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
            elif char == 'w' and self.common_words:
                parts.append(self.common_words)
            else:
                parts.append(self.charset)
        yield from (''.join(p) for p in itertools.product(*parts))

    def generate_smart_mutations(self, word):
        mutations = [
            word,
            word.capitalize(),
            word.upper(),
            word.lower(),
            word[::-1],
            word + str(random.randint(0, 9999)),
            ''.join(c if random.random() > 0.3 else c.upper() for c in word),
        ]
        return mutations

def generate_passwords_chunk(args):
    generator, chunk_size, chunk_number = args
    passwords = list(itertools.islice(generator.generate_passwords(), chunk_number * chunk_size, (chunk_number + 1) * chunk_size))
    return passwords

def save_passwords(passwords, output_file, append=False):
    mode = 'a' if append else 'w'
    with open(output_file, mode) as f:
        for password in passwords:
            f.write(password + '\n')

def estimate_total_passwords(generator):
    if generator.patterns:
        return sum(len(list(generator._generate_password_from_pattern(p))) for p in generator.patterns)
    else:
        return sum(len(generator.charset) ** length for length in range(generator.min_length, generator.max_length + 1))

def main():
    parser = argparse.ArgumentParser(description="Advanced Password List Generator")
    parser.add_argument("-min", type=int, default=8, help="Minimum password length")
    parser.add_argument("-max", type=int, default=12, help="Maximum password length")
    parser.add_argument("-l", action="store_true", help="Use lowercase letters")
    parser.add_argument("-u", action="store_true", help="Use uppercase letters")
    parser.add_argument("-d", action="store_true", help="Use digits")
    parser.add_argument("-s", action="store_true", help="Use special characters")
    parser.add_argument("-c", type=str, help="Custom characters")
    parser.add_argument("-w", type=str, help="File with common words")
    parser.add_argument("-p", type=str, help="Password patterns (e.g., 'luds,llddss')")
    parser.add_argument("-o", type=str, default="passwords.txt", help="Output file name")
    parser.add_argument("--smart", action="store_true", help="Use smart password generation")
    parser.add_argument("--processes", type=int, default=multiprocessing.cpu_count(), help="Number of parallel processes")
    parser.add_argument("--chunk-size", type=int, default=1000000, help="Chunk size for password generation")

    args = parser.parse_args()
    print(colorama.Fore.RED)
    pyfiglet.print_figlet("Asylum")
    print(colorama.Fore.GREEN)
    print("        Password List Generator")
    print(colorama.Fore.RESET)
    print("Advanced Password List Generator")
    print("================================")

    charset = ''
    if args.l:
        charset += string.ascii_lowercase
    if args.u:
        charset += string.ascii_uppercase
    if args.d:
        charset += string.digits
    if args.s:
        charset += string.punctuation
    if args.c:
        charset += args.c

    if not charset:
        print("Error: No character set selected. Please use at least one of -l, -u, -d, -s, or -c options.")
        return

    print(f"Character set: {charset}")

    common_words = []
    if args.w:
        if os.path.exists(args.w):
            with open(args.w, 'r') as f:
                common_words = [line.strip() for line in f]
            print(f"Number of loaded common words: {len(common_words)}")
        else:
            print(f"Warning: Common words file '{args.w}' not found.")

    patterns = args.p.split(',') if args.p else None
    if patterns:
        print(f"Password patterns: {patterns}")

    if args.min > args.max:
        print("Error: Minimum password length cannot be greater than maximum length.")
        return

    generator = PasswordGenerator(args.min, args.max, charset, patterns, common_words)

    total_passwords = estimate_total_passwords(generator)
    print(f"Estimated total passwords: {total_passwords:,}")

    if total_passwords == 0:
        print("Error: No passwords will be generated with current settings.")
        return

    chunk_size = min(args.chunk_size, total_passwords)
    num_chunks = (total_passwords + chunk_size - 1) // chunk_size

    killer = GracefulKiller()
    
    start_time = time.time()

    with multiprocessing.Pool(processes=args.processes) as pool:
        chunks = ((generator, chunk_size, i) for i in range(num_chunks))
        passwords_generated = 0
        try:
            with tqdm(total=total_passwords, desc="Generating passwords") as pbar:
                for passwords in pool.imap_unordered(generate_passwords_chunk, chunks):
                    if killer.kill_now:
                        print("\nStopping password generation...")
                        break
                    if args.smart:
                        smart_passwords = []
                        for password in passwords:
                            smart_passwords.extend(generator.generate_smart_mutations(password))
                        passwords = smart_passwords
                    save_passwords(passwords, args.o, append=(passwords_generated > 0))
                    passwords_generated += len(passwords)
                    pbar.update(len(passwords))
        except KeyboardInterrupt:
            print("\nStopping password generation...")
        finally:
            pool.close()
            pool.join()

    end_time = time.time()
    print(f"\nExecution time: {end_time - start_time:.2f} seconds")
    print(f"Total passwords generated: {passwords_generated:,}")
    print(f"Password list saved to {args.o}")

if __name__ == "__main__":
    main()
