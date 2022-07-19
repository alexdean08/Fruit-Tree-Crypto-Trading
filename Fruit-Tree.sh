##
## Fruit-Tree.sh
## This is the startup file that installs the necessary packages
## and starts the main python script.
##

sudo echo ""
echo "----------------------------------
|   Fruit Tree Crypto Trading   |
----------------------------------"
echo "Installing packages"
echo "-------------------"

echo -n "Installing pip3..."
sudo apt-get -qq install python3-pip
echo "Done"

echo -n "Installing requests package..."
pip3 install requests
echo "Done"

echo -n "Installing cbpro package..."
pip3 install -q cbpro
echo "Done"

echo -n "Installing robin_stocks package..."
pip3 install -q robin_stocks
echo "Done"

echo "All packages installed!"
echo "-------------------"
echo "Configuring the auto-trader"
echo "-------------------"

python3 auto-trader.py