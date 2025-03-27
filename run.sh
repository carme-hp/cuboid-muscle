cd build_release
rm -r precice-run
echo "Launching left-muscle"
mpirun -n 1 ./muscle_contraction ../settings_left_muscle.py left_muscle.py &> left_muscle.log &
echo "Launching Tendon"
mpirun -n 1 ./tendon ../settings_tendon.py tendon.py &> tendon.log &
echo "Launching right-muscle"
mpirun -n 1 ./muscle_mechanics ../settings_right_mechanics.py right_muscle.py &> right_muscle.log &
echo "Simulation completed."
cd ..
