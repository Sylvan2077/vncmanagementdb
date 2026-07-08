from apps.account.models import User

KEY = "80ae3923a36d721c254ca57754455a98"


def encode_passwd(new_password):
    """
    加密管理员密码
    """

    encrypt_passwd = ""
    for i, j in zip(new_password, KEY):
        old_temp = str(ord(i) + ord(j)) + "_"
        encrypt_passwd += old_temp
    return encrypt_passwd


def decode_passwd(data):
    """
    解密管理员密码
    """

    if isinstance(data, int):
        user = User.objects.get(id=data)
        encrypt_passwd = user.encrypt_passwd
    else:
        encrypt_passwd = data
    decrypt_passwd = ""
    if encrypt_passwd:
        for i, j in zip(encrypt_passwd.split("_")[:-1], KEY):
            old_tmp = chr(int(i) - ord(j))
            decrypt_passwd += old_tmp
    return decrypt_passwd
