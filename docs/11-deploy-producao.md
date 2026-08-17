# 11 — Deploy em Produção

[← Sumário](README.md)

Guia genérico para rodar o bot 24/7 num servidor, sem depender de terminal aberto ou do computador local ligado. Nenhum dado real de nenhum deploy específico aparece aqui — isso é infraestrutura operacional, não código versionado, e cada deploy tem seu próprio IP/credenciais.

## Por que uma VPS

O bot roda em loop contínuo (poll de 60s) e paper mode precisa acumular tempo real decorrido pra gerar amostra estatisticamente válida (ver [13 — Metodologia SDD](13-metodologia-sdd.md)) — isso exige um processo vivo 24/7, o que uma máquina local que hiberna/desliga não oferece. Provedores com camada gratuita ou baixo custo (Oracle Cloud, DigitalOcean, Hostinger) são suficientes — o bot não é intensivo em CPU/RAM.

**Escolha de datacenter:** evite datacenters em jurisdições que a Binance pode geobloquear (verifique a documentação da exchange antes de escolher a região).

## Passo a passo

### 1. Provisionar e proteger o acesso SSH

```bash
# gerar um par de chaves dedicado a este deploy (não reaproveitar chave pessoal)
ssh-keygen -t ed25519 -C "nome-do-deploy"

# copiar a chave pública para a VPS na criação (a maioria dos provedores oferece isso)
# depois, desabilitar login por senha:
```

No servidor, em `/etc/ssh/sshd_config` (ou no arquivo de override específico da distro — em imagens com `cloud-init`, geralmente `/etc/ssh/sshd_config.d/50-cloud-init.conf`, que carrega **antes** e pode silenciar um override adicionado depois, já que o `sshd` usa "primeira ocorrência vale" entre arquivos incluídos):

```
PasswordAuthentication no
PermitRootLogin prohibit-password
```

### 2. Hardening básico

```bash
# firewall: só a porta SSH aberta
ufw allow 22/tcp
ufw enable

# fail2ban contra brute-force
apt install fail2ban -y
systemctl enable --now fail2ban
```

### 3. Clonar e configurar

```bash
git clone https://github.com/fisaarpelesjo/nautilus.git
cd nautilus
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
chmod 600 .env   # legível só pelo dono
nano .env        # preencher chaves e parâmetros
```

### 4. Rodar como serviço systemd (não `nohup`/`screen`)

Um serviço systemd sobrevive a reinício do servidor e reinicia sozinho se o processo morrer — nenhuma das duas coisas acontece com `nohup` ou `screen`.

```ini
# /etc/systemd/system/nautilus-bot.service
[Unit]
Description=Nautilus crypto trading bot
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/root/nautilus
ExecStart=/root/nautilus/.venv/bin/python main.py bot
Restart=always
RestartSec=10
StandardOutput=append:/root/nautilus/logs/systemd-stdout.log
StandardError=append:/root/nautilus/logs/systemd-stderr.log

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now nautilus-bot
systemctl status nautilus-bot
```

### 5. Rotação de log

Sem rotação, `logs/systemd-stdout.log` cresce indefinidamente.

```
# /etc/logrotate.d/nautilus-bot
/root/nautilus/logs/systemd-std*.log {
    daily
    rotate 10
    compress
    copytruncate
    missingok
    notifempty
}
```

`copytruncate` é necessário aqui porque o processo mantém o arquivo aberto continuamente (systemd redireciona stdout/stderr direto pro arquivo) — um `rotate` comum que renomeia o arquivo deixaria o processo escrevendo no inode antigo, já desconectado do nome novo.

## Deploy contínuo (manual, não CI/CD)

Este projeto não tem deploy automático — depois de um `git push` local, sincronizar a VPS é manual:

```bash
ssh usuario@servidor "cd /root/nautilus && git pull --quiet && systemctl restart nautilus-bot"
```

O restart é seguro para o estado do bot: posições abertas, saldo paper e contadores de proteção são restaurados de `data/state.json` automaticamente (ver [09](09-persistencia-dados.md)) — só o processo em memória reinicia, não o histórico.

## Checklist pós-deploy

- [ ] `systemctl status nautilus-bot` → `active (running)`, sem restart loop
- [ ] `tail logs/systemd-stderr.log` → vazio ou só avisos esperados
- [ ] `python main.py status` → saldo e modo (`paper`/`live`) conferem com o esperado
- [ ] Firewall só com a porta SSH aberta (`ufw status`)
- [ ] `.env` com permissão `600`, nunca commitado
- [ ] Se usar Telegram: `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` preenchidos e um alerta de teste confirmado

## Próximo capítulo

[12 — Desenvolvimento](12-desenvolvimento.md) cobre o fluxo de trabalho pra quem vai alterar o código, não só rodá-lo.
