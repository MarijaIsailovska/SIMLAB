import hashlib
import secrets

class AuthManager:
    @staticmethod
    def hash_password(password):
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                           password.encode('utf-8'), 
                                           salt.encode('utf-8'), 
                                           100000)
        return salt + password_hash.hex()
    
    @staticmethod
    def verify_password(password, stored_hash):
        salt = stored_hash[:32]
        stored_password_hash = stored_hash[32:]
        password_hash = hashlib.pbkdf2_hmac('sha256',
                                           password.encode('utf-8'),
                                           salt.encode('utf-8'),
                                           100000)
        return password_hash.hex() == stored_password_hash