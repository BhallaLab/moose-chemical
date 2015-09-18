all : simulate plot
	echo "done"

simulate : ./camkii.py ./CaMKII/camkii.yacml
	rm -f CaMKII/camkii.yacml.dat
	python camkii.py 

plot : simulate 
	~/Scripts/plot_csv.py -i CaMKII/camkii.yacml.dat -y 1-6 -s -o CaMKII/camkii.yacml.png
