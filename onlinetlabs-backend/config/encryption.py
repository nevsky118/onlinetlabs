import argparse
import os
import subprocess
import sys


def encrypt_file(filepath: str, password: str) -> str:
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    output = filepath + ".aes"
    subprocess.run(
        [
            "openssl",
            "enc",
            "-aes-256-cbc",
            "-salt",
            "-pbkdf2",
            "-in",
            filepath,
            "-out",
            output,
            "-pass",
            f"pass:{password}",
        ],
        check=True,
    )
    return output


def decrypt_file(filepath: str, password: str) -> str:
    if not filepath.endswith(".aes"):
        raise ValueError("File must have .aes extension")
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    output = filepath.removesuffix(".aes")
    subprocess.run(
        [
            "openssl",
            "enc",
            "-aes-256-cbc",
            "-d",
            "-salt",
            "-pbkdf2",
            "-in",
            filepath,
            "-out",
            output,
            "-pass",
            f"pass:{password}",
        ],
        check=True,
    )
    return output


def main() -> None:
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
        print(
            "Error: provide --password or set CONFIG_PASSWORD env var", file=sys.stderr
        )
        sys.exit(1)
    if args.action == "encrypt":
        result = encrypt_file(args.file, args.password)
        print(f"Encrypted: {result}")
    else:
        result = decrypt_file(args.file, args.password)
        print(f"Decrypted: {result}")


if __name__ == "__main__":  # pragma: no cover
    main()
