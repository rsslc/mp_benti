#!/usr/bin/env bash
set -euo pipefail
mkdir -p static/images/products
# Cheeses
wget -O static/images/products/cheese1.jpg "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55"
wget -O static/images/products/cheese2.jpg "https://images.unsplash.com/photo-1604909052743-86ad1c0d1b7c"
# Smallgoods
wget -O static/images/products/smallgoods1.jpg "https://images.unsplash.com/photo-1617191519400-2f2f49bfae78"
wget -O static/images/products/smallgoods2.jpg "https://images.unsplash.com/photo-1551218808-94e220e084d2"
# Flour / Pantry
wget -O static/images/products/flour1.jpg "https://images.unsplash.com/photo-1519681393784-d120267933ba"
wget -O static/images/products/flour2.jpg "https://images.unsplash.com/photo-1526318472351-c75fcf070305"
# Vegetables (marinated)
wget -O static/images/products/veg1.jpg "https://images.unsplash.com/photo-1568605114967-8130f3a36994"
# Oils
wget -O static/images/products/oil1.jpg "https://images.unsplash.com/photo-1510626176961-4b57d4fbad03"
echo "Images downloaded into static/images/products/"
