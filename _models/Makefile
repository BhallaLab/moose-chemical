all : simulate plot
	echo "done"

simulate : ./camkii.py ./CaMKII/camkii.ymcl
	python camkii.py 

plot : simulate 
	~/Scripts/plot_csv.py -i CaMKII/camkii.ymcl.dat -y 1 2 3 -s
