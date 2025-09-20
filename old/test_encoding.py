import os
import sys

# Test token with cyrillic characters
test_token = "ваш_новый_токен"

print(f"Python version: {sys.version}")
print(f"Default encoding: {sys.getdefaultencoding()}")
print(f"File system encoding: {sys.getfilesystemencoding()}")
print(f"\nOriginal token: {test_token!r}")
print(f"Length: {len(test_token)}")
print(f"Hex: {test_token.encode('utf-8').hex()}")

# Set environment variable
os.environ["TEST_TOKEN"] = test_token

# Read it back
read_token = os.getenv("TEST_TOKEN")
print(f"\nRead token: {read_token!r}")
print(f"Length: {len(read_token) if read_token else 0}")
print(f"Hex: {read_token.encode('utf-8').hex() if read_token else ''}")

# Try with raw bytes
print("\nTrying with bytes:")
bytes_token = test_token.encode('utf-8')
print(f"Bytes: {bytes_token}")
os.environ["BYTES_TOKEN"] = bytes_token.decode('latin-1')  # Force latin-1 to preserve bytes
read_bytes = os.getenv("BYTES_TOKEN")
print(f"Read bytes: {read_bytes.encode('latin-1')}")
