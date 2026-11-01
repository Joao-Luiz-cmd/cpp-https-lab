import hmac
import logging
import os

from flask import Flask, jsonify, request
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024  # 1 MiB

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("lab-api")


def required_hex_env(name: str, expected_bytes: int) -> bytes:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Variável de ambiente ausente: {name}")
    try:
        decoded = bytes.fromhex(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} precisa conter hexadecimal válido") from exc
    if len(decoded) != expected_bytes:
        raise RuntimeError(f"{name} precisa ter exatamente {expected_bytes} bytes")
    return decoded


def get_lab_config():
    token = os.environ.get("BEARER_TOKEN", "")
    if not token:
        raise RuntimeError("Variável de ambiente ausente: BEARER_TOKEN")
    key = required_hex_env("AES_KEY_HEX", 16)
    iv = required_hex_env("AES_IV_HEX", 16)
    return token, key, iv


@app.get("/health")
def health():
    return jsonify(status="ok"), 200


@app.post("/log")
def receive_log():
    try:
        expected_token, key, iv = get_lab_config()
    except RuntimeError:
        logger.exception("Configuração do servidor inválida")
        return jsonify(error="server configuration error"), 500

    authorization = request.headers.get("Authorization", "")
    scheme, separator, supplied_token = authorization.partition(" ")
    if (
        not separator
        or scheme.lower() != "bearer"
        or not hmac.compare_digest(supplied_token, expected_token)
    ):
        return jsonify(error="unauthorized"), 401

    ciphertext = request.get_data(cache=False)
    if not ciphertext or len(ciphertext) % AES.block_size != 0:
        return jsonify(error="invalid ciphertext length"), 400

    try:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
        message = plaintext.decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return jsonify(error="could not decrypt valid UTF-8 message"), 400

    # Evita que caracteres de controle alterem a estrutura dos logs.
    safe_message = message.encode("unicode_escape").decode("ascii")
    logger.info("Mensagem sintética recebida: %s", safe_message)
    return jsonify(status="processed"), 200


@app.errorhandler(413)
def request_too_large(_error):
    return jsonify(error="request too large"), 413


if __name__ == "__main__":
    # Render fornece PORT e termina o TLS na borda; não exponha outra porta TLS aqui.
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, debug=False)
