#!/bin/bash


#$ -V
#$ -j y
#$ -o logs
#$ -r yes
#$ -cwd
#$ -S /bin/bash
#$ -P control

export TMPDIR=/fast/users/${USER}/scratch/tmp
export LOGDIR=logs/${JOB_ID}
mkdir -p $LOGDIR

set -x

snakemake \
    -j 2 \
    -k \
    -p \
    -s /fast/users/kwreczy_m/projects/makeWGBSnake/Snakemake.py \
    --configfile /fast/users/kwreczy_m/projects/makeWGBSnake/Config_files/wgbs.json
