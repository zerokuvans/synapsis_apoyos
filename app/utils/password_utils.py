import secrets
import string
import bcrypt

def generate_temporary_password(length=12):
    """
    Genera una contraseña temporal segura.
    
    Args:
        length (int): Longitud de la contraseña (por defecto 12)
    
    Returns:
        str: Contraseña temporal generada
    """
    # Definir caracteres permitidos
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special_chars = "!@#$%&*"
    
    # Asegurar que la contraseña tenga al menos un carácter de cada tipo
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special_chars)
    ]
    
    # Completar el resto de la longitud con caracteres aleatorios
    all_chars = lowercase + uppercase + digits + special_chars
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))
    
    # Mezclar la contraseña para que no tenga un patrón predecible
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)

def hash_password(password):
    """
    Hashea una contraseña usando bcrypt.
    
    Args:
        password (str): Contraseña en texto plano
    
    Returns:
        str: Contraseña hasheada
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(password, hashed_password):
    """
    Verifica si una contraseña coincide con su hash.
    
    Args:
        password (str): Contraseña en texto plano
        hashed_password (str): Contraseña hasheada
    
    Returns:
        bool: True si la contraseña es correcta, False en caso contrario
    """
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)