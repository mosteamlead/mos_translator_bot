# Деплой бота

## 1. На своём компьютере (Windows)

```powershell
cd C:\Users\julia\mos_translator_bot
git status
git add .
git commit -m "описание изменения"
git push
```

## 2. На сервере

```bash
ssh root@88.216.70.147
cd /opt/mos_translator_bot
git pull
systemctl restart mosgpt_translator_bot
systemctl status mosgpt_translator_bot
```

Готово. После `git push` заходишь по SSH и выполняешь команды из блока «На сервере».
