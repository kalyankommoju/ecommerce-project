from itsdangerous import URLSafeSerializer
from key import secret_key,salt,salt2,salt3,salt4
def token(data,salt):
    serializer=URLSafeSerializer(secret_key)
    return serializer.dumps(data,salt=salt)