#!/data/data/com.termux/files/usr/bin/bash
# zanaX — setup en Termux (Android). Uso:
#   pkg install git && git clone https://github.com/riquelmechile/zanaX.git
#   cd zanaX && bash termux-setup.sh
set -e

echo "==> Paquetes de sistema"
pkg update -y
pkg install -y python python-pip git clang make rust binutils

echo "==> Dependencias Python"
pip install --upgrade pip
# pydantic-core necesita compilar en Android (bionic); rust/clang ya están
pip install -r requirements.txt

echo "==> Config"
[ -f .env ] || cp .env.example .env
mkdir -p data

echo
echo "Listo. Ahora:"
echo "  1. nano .env   # rellena GOOGLE_API_KEY, claves de X y Telegram"
echo "  2. termux-wake-lock   # evita que Android mate el proceso"
echo "  3. python -m src.main"
echo
echo "Para que sobreviva al cerrar Termux: instala Termux:Boot y crea"
echo "  ~/.termux/boot/start-zanax.sh con:"
echo "    #!/data/data/com.termux/files/usr/bin/sh"
echo "    termux-wake-lock"
echo "    cd \$HOME/zanaX && python -m src.main"
