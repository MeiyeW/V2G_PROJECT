year="2025" 
for renewable in {0.4,0.44,0.48}; do
    for batteryCost in {10,12,14} ; do
        echo "Running:$year $batteryCost $renewable "
        python main.py $year $renewable $batteryCost  
    done
done

year="2030"
for renewable in {0.56,0.60,0.64}; do
    for batteryCost in {6,8,10} ; do

        echo "Running: $year $batteryCost $renewable"
        python main.py $year $renewable $batteryCost 
    done
done