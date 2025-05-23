#!/bin/sh
 
#SBATCH --job-name="geos"
#SBATCH --ntasks=8
#SBATCH --nodes=1
#SBATCH --time=3:00:00
#SBATCH --partition=p4_general
##SBATCH --exclusive
#SBATCH --output=job_GEOS_P4_%j.out
#SBATCH --error=job_GEOS_P4_%j.err
##SBATCH --mem=734GB
 
# do not change
ulimit -s unlimited
ulimit -c unlimited
 
# loading of the module 
module purge
module use /workrd/SCR/NUM/GEOS_environment/p4/modulefiles/app
module load geos/develop_3bf12d2/pangea4-gcc12.1-hpcxompi2.17.1-onemkl2023.2.0-Release-2024-06-20-10-05
 
export HDF5_USE_FILE_LOCKING=FALSE
export OMP_NUM_THREADS=1
 
#----- Set standard Output and standrard error base file name. -----
OUT_NAME=job_GEOS_P4_${SLURM_JOBID}
 
srun --mpi=pmix_v3 --hint=nomultithread \
    -n ${SLURM_NTASKS} geos \
    -o modelA \
    -i simulationA.xml