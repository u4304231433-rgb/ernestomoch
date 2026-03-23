mkdir ./BOcal/numeros/$1
curl --output ./BOcal/numeros/$1/$1.pdf $2
pdftoppm -jpeg -r 300 ./BOcal/numeros/$1/$1.pdf ./BOcal/numeros/$1/$1