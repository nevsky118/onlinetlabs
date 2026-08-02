"""Encrypt/decrypt .env files via openssl aes-256-cbc.

Shared by every service. The password goes to openssl on a pipe, not in argv,
so it does not show up in the process table.
"""

import argparse
import atexit
import os
import subprocess
import sys
import tempfile

_CIPHER = ["openssl", "enc", "-aes-256-cbc", "-salt", "-pbkdf2"]


def _run(args: list[str], password: str) -> None:
    read_fd, write_fd = os.pipe()
    try:
        os.write(write_fd, password.encode("utf-8"))
    finally:
        os.close(write_fd)
    try:
        subprocess.run(
            [*args, "-pass", f"fd:{read_fd}"],
            check=True,
            pass_fds=(read_fd,),
        )
    finally:
        os.close(read_fd)


def encrypt_file(filepath: str, password: str) -> str:
    """Encrypt a file into .aes and return the result path."""
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    output = filepath + ".aes"
    _run([*_CIPHER, "-in", filepath, "-out", output], password)
    return output


def decrypt_file(filepath: str, password: str) -> str:
    """Decrypt a .aes file to a temp file removed on process exit.

    Plaintext is never written next to the ciphertext, where it outlives the
    process and is easy to commit by accident.
    """
    if not filepath.endswith(".aes"):
        raise ValueError("File must have .aes extension")
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    fd, output = tempfile.mkstemp(suffix=".env")
    os.close(fd)
    atexit.register(lambda p=output: os.unlink(p) if os.path.exists(p) else None)
    _run([*_CIPHER, "-d", "-in", filepath, "-out", output], password)
    return output


def main() -> None:
    """Parse arguments and encrypt or decrypt the file."""
    parser = argparse.ArgumentParser(description="Encrypt/decrypt .env files")
    parser.add_argument("action", choices=["encrypt", "decrypt"])
    parser.add_argument("file", help="Path to .env (encrypt) or .env.aes (decrypt)")
    parser.add_argument(
        "--password",
        default=os.getenv("CONFIG_PASSWORD"),
        help="Password (default: CONFIG_PASSWORD env var)",
    )
    args = parser.parse_args()
    if not args.password:
        print("Error: provide --password or set CONFIG_PASSWORD env var", file=sys.stderr)
        sys.exit(1)
    if args.action == "encrypt":
        print(f"Encrypted: {encrypt_file(args.file, args.password)}")
    else:
        print(f"Decrypted: {decrypt_file(args.file, args.password)}")


if __name__ == "__main__":  # pragma: no cover
    main()
