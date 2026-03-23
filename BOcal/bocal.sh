mkdir ./BOcal/numeros/1288
curl --output ./BOcal/numeros/1288/1288.pdf "https://bocal.cof.ens.fr/bocal_www/2025-2026/1288.pdf"
pdftoppm -jpeg -r 300 ./BOcal/numeros/1288/1288.pdf ./BOcal/numeros/1288/1288