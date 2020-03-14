echo "Running jupyter"

jupyter notebook --ip=0.0.0.0 --port=8888 --allow-root --no-browser --NotebookApp.token='password' --notebook-dir=/plugins/son-mano-traffic-forecast/notebooks &
