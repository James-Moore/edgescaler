pings=10 
machines=20 
tpings=$(echo "${pings}*${machines}"| bc -l)
avg=0
num=0
mapfile -t < <(python3 -m tools.hosts -l 2 -m 0 --timeout 15 pushcommand -f config/config.json.${machines} "for i in {0..$pings}; do ping -qc1 8.8.8.8 | grep mdev | sed 's|/| |g' | cut -d ' ' -f 7 & done" |& xargs -I {} echo {})
max=$(echo "${MAPFILE[@]}" | sort -n | cut -d" " -f1)
min=$(echo "${MAPFILE[@]}" | sort -n | cut -d" " -f${#MAPFILE[@]})
for i in "${MAPFILE[@]}"; 
do 
	avg=$(echo $avg+$i | bc )
	num=$(echo $num+1 | bc )
done
avg=$(echo $avg/${#MAPFILE[@]} | bc -l)

echo "PING TEST"
echo "Virtual Macines: ${machines}, PingsPerVM ${pings}, Total Parallel Pings: ${tpings}"
echo "MAX: ${max}"
echo "MIN: ${min}"
echo "Average: ${avg}"

