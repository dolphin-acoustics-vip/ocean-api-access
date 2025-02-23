SELECTION_DIR="./downloads"
echo $SELECTION_DIR

cd $SELECTION_DIR

# create directories
mkdir --parents Training/
mkdir --parents Testing/

COUNT=0
SPECIES=()
for file in `ls -d *.wav`; do

    # find species and create folder
    species=$(echo ${file} | cut -d '_' -f 1)
    echo $species
    if [[ ! " ${SPECIES[@]} " =~ " ${species} " ]]; then
        SPECIES+=($species)
        mkdir --parents Training/$species
        mkdir --parents Testing/$species
    fi

    # split testing training data
    if [[ $COUNT%10 -gt 1 ]]; then
        mv $file Training/$species/
        echo $file,$species >> labels_train.csv
    fi
    if [[ $COUNT%10 -lt 2 ]]; then
        mv $file Testing/$species/
        echo $file,$species >> labels_test.csv
    fi
    COUNT=$(( $COUNT + 1 ))
done

echo $COUNT