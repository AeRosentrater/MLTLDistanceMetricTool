
# MLTL Distance Metric Tool

A small tool for computing the minimum distance between a dissatisfying trace and a satisfying trace for a given MLTL formula

## Setup 

1. Clone this repository
2. Set up the submodule - `cd` there and run `make` to build it
3. Configure and activate a python environment (if needed)

## Example usage

``` 
python3 distance_metric.py "(p0 U[1,2] (p0 & p1))" "[[0,0],[0,1],[0,0]]"
```
Should give the output:
```
Formula:  (p0 U[1,2] (p0 & p1))
Trace:  [[0, 0], [0, 1], [0, 0]]
Minium distance:  1
Regex for minimum distance trace:  ss,11,ss
```