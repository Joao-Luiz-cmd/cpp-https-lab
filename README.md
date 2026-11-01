# API Flask para laboratório AES-128-CBC

## Contrato do endpoint

`POST /log`

- Cabeçalho: `Authorization: Bearer <BEARER_TOKEN>`
- Corpo: somente o ciphertext AES-CBC, em bytes brutos (não Base64).
- Padding: PKCS#7.
- Codificação após descriptografia: UTF-8.
- Resposta de sucesso: HTTP 200 com `{"status":"processed"}`.

O IV é configurado no servidor por `AES_IV_HEX`; portanto, o cliente deve
criptografar com exatamente o mesmo IV e com a mesma chave.

## Configuração local

Use uma chave de teste de exatamente 16 bytes e um IV de teste de 16 bytes,
ambos representados por 32 caracteres hexadecimais. Defina as variáveis de
ambiente `BEARER_TOKEN`, `AES_KEY_HEX` e `AES_IV_HEX`, instale as dependências
e execute:

```bash
pip install -r requirements.txt
python app.py
```

O servidor escuta em `0.0.0.0` e usa `PORT` quando definido.

## Publicação na Render

1. Envie estes arquivos para um repositório Git.
2. Na Render, crie um Web Service a partir do repositório.
3. Use `render.yaml` (ou configure o build command como `pip install -r requirements.txt`
   e o start command como `python app.py`).
4. Cadastre `BEARER_TOKEN`, `AES_KEY_HEX` e `AES_IV_HEX` como variáveis secretas
   no painel da Render. Não coloque valores reais no repositório.
5. A Render fornece HTTPS público e encaminha as requisições para a porta
   interna indicada por `PORT`.

## Teste do endpoint

Com um ciphertext válido já produzido pelo cliente de laboratório:

```bash
curl -i -X POST "https://SEU-SERVICO.onrender.com/log" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/octet-stream" \
  --data-binary "@ciphertext.bin"
```

## Limitações importantes

- `app.run` é o servidor de desenvolvimento do Flask e não é recomendado para
  produção ou tráfego real. Foi mantido aqui porque faz parte dos requisitos
  deste exercício; use apenas para laboratório controlado.
- AES-CBC não autentica o ciphertext. Um Bearer Token autentica o cliente,
  mas não garante a integridade criptográfica de cada mensagem. Para sistemas
  reais, prefira AES-GCM ou outro modo autenticado.
- Chave e IV fixos servem somente para dados sintéticos de laboratório.
  Não reutilize IV fixo em mensagens reais.
- A Render termina o TLS no seu proxy público. O processo Flask recebe o tráfego
  encaminhado na porta interna `PORT`; não precisa abrir a porta 443 no código.
