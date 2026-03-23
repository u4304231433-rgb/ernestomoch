mkdir ./BOcal/numeros/$1
curl --output ./BOcal/numeros/$1/$1.pdf "https://bocal.cof.ens.fr/bocal_www/2025-2026/$1.pdf"
pdftoppm -jpeg -r 300 ./BOcal/numeros/$1/$1.pdf ./BOcal/numeros/$1/$1