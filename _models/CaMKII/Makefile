all : simulate plot
	echo "done"

simulate : ./camkii.py ./camkii.yacml
	rm -f camkii.yacml.dat
	python camkii.py   | tee __log__.txt

plot : simulate 
	~/Scripts/plot_csv.py -i camkii.yacml.dat -y 1-7 -s -o camkii.yacml.png
