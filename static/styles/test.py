from cryptography.fernet import Fernet

ogfile = 'stylesheet.txt'

def keyGen():
    key = Fernet.generate_key()

    with open('withStyle.txt', 'wb') as filekey:
        filekey.write(key)

def encryptFile(ogfile):
    with open('withStyle.txt', 'rb') as filekey:
        key = filekey.read()

    fernet = Fernet(key)
    with open(ogfile, 'rb') as file:
        original = file.read()

    encrypted = fernet.encrypt(original)

    with open(ogfile, 'wb') as encrypted_file:
        encrypted_file.write(encrypted)

def decryptFile(ogfile):
    with open('withStyle.txt', 'rb') as filekey:
        key = filekey.read()
    
    fernet = Fernet(key)

    with open(ogfile, 'rb') as enc_file:
        encrypted = enc_file.read()

    decrypted = fernet.decrypt(encrypted)

    with open(ogfile, 'wb') as dec_file:
        dec_file.write(decrypted)

encryptFile(ogfile)
