# pyCombinatorial

## Introduction

A python library to solve TSP problems using the following Metaheuristics: **2-opt**; **3-opt**; **4-opt**; **2-opt Stochastic**; **3-opt Stochastic**; **4-opt Stochastic**; **5-opt Stochastic**; **Ant Colony Optimization**; **BRKGA** (Biased Random Key Genetic Algorithm); **Clarke & Wright**  (Savings Heuristic); **Convex Hull Algorithm**; **Extremal Optimization**; **Genetic Algorithm**; **GRASP** (Greedy Randomized Adaptive Search Procedure); **Guided Search**; **Iterated Search**; **Scatter Search**; **Stochastic Hill Climbing**; **Tabu Search**; **Variable Neighborhood Search**.

## Usage

1. Install

```bash
pip install pyCombinatorial
```

2. Import

```py3


# Required Libraries
import pandas as pd

# GA
from pyCombinatorial.algorithm import genetic_algorithm
from pyCombinatorial.utils import graphs, util

# Obtaining the Distance Matrix
distance_matrix = util.build_distance_matrix(coordinates)

# GA - Parameters
parameters = {
            'population_size': 15,
            'elite': 1,
            'mutation_rate': 0.1,
            'mutation_search': 8,
            'generations': 1000,
            'verbose': True
             }

# GA - Algorithm
route, distance = genetic_algorithm(distance_matrix, **parameters)

# Plot Locations and Tour
graphs.plot_tour(coordinates, city_tour = route, view = 'browser', size = 10)
print('Total Distance: ', round(distance, 2))

```

3. Try it in **Colab**

- 2-opt([ Colab Demo ](https://colab.research.google.com/drive/1SLkM8r_VdlFCpNpm-2yTfr_ynSC5WIX9?usp=sharing)) ( [ Paper ](https://www.jstor.org/stable/167074))     
- 3-opt([ Colab Demo ](https://colab.research.google.com/drive/1iAZLawLBZ-7yaPCyobMtel1SvBamxtjL?usp=sharing)) ( [ Paper ](https://isd.ktu.lt/it2011//material/Proceedings/1_AI_5.pdf)) 
- 4-opt([ Colab Demo ](https://colab.research.google.com/drive/1N8HKhVY4s20sfqo8IWIaCY-NHVk6gARS?usp=sharing)) ( [ Paper ](https://isd.ktu.lt/it2011//material/Proceedings/1_AI_5.pdf))
- 2-opt Stochastic ([ Colab Demo ](https://colab.research.google.com/drive/1xTm__7OwQVC_KX2b-eExLGgG1DgnJ10a?usp=sharing)) ( [ Paper ](https://doi.org/10.1016/j.trpro.2014.10.001)) 
- 3-opt Stochastic ([ Colab Demo ](https://colab.research.google.com/drive/1A5lPW6BSDD2rLNDlnpQo44U8jwKcAGXL?usp=sharing)) ( [ Paper ](https://isd.ktu.lt/it2011//material/Proceedings/1_AI_5.pdf))
- 4-opt Stochastic ([ Colab Demo ](https://colab.research.google.com/drive/1igWrUMVSInzyeOdhPcGuMjyooZ6elvLY?usp=sharing)) ( [ Paper ](https://isd.ktu.lt/it2011//material/Proceedings/1_AI_5.pdf))
- 5-opt Stochastic ([ Colab Demo ](https://colab.research.google.com/drive/13vS5MCeFqb3F4ntxrw3iCsMbJTfEVyeo?usp=sharing)) ( [ Paper ](https://isd.ktu.lt/it2011//material/Proceedings/1_AI_5.pdf))
- Ant Colony Optimization ([ Colab Demo ](https://colab.research.google.com/drive/1O2qogrjE4mZUZX3nsSxw43crumlBnd-D?usp=sharing)) ( [ Paper ](https://doi.org/10.1109/4235.585892)) 
- Biased Random Key Genetic Algorithm ([ Colab Demo ](https://colab.research.google.com/drive/1lwnpUBl1P1LIvzN1saLgEvnaKZRMWLHn?usp=sharing)) ( [ Paper ](https://doi.org/10.1007/s10732-010-9143-1))
- Clarke & Wright  (Savings Heuristic) ([ Colab Demo ](https://colab.research.google.com/drive/1XC2yoVe6wTsjt7u2fBaL3LcKUu42FG8r?usp=sharing)) ( [ Paper ](http://dx.doi.org/10.1287/opre.12.4.568))
- Convex Hull Algorithm ([ Colab Demo ](https://colab.research.google.com/drive/1Wn2OWccZukOfMtJuGV9laklLTc8vjOFq?usp=sharing)) ( [ Paper ](https://doi.org/10.1109/TSMC.1974.4309370))
- Extremal Optimization ([ Colab Demo ](https://colab.research.google.com/drive/1Y5YH0eYKjr1nj_IfhJXaILRDIXm-LWLs?usp=sharing)) ( [ Paper ](https://doi.org/10.1109/5992.881710))
- Genetic Algorithm ([ Colab Demo ](https://colab.research.google.com/drive/1zO9rm-G6HOMeg1Q_ptMHJr48EpHcCAIS?usp=sharing)) ( [ Paper ](https://doi.org/10.1007/BF02125403))  
- GRASP ([ Colab Demo ](https://colab.research.google.com/drive/1OnRyCc6C_QL6wr6-l5RlQI4eGbMdwuhS?usp=sharing)) ( [ Paper ](https://doi.org/10.1007/BF01096763)) 
- Guided Search ([ Colab Demo ](https://colab.research.google.com/drive/1uT9mlDoo37Ni7hqziGNELEGQCGBKQ83o?usp=sharing)) ( [ Paper ](https://doi.org/10.1016/S0377-2217(98)00099-X)) 
- Iterated Search ([ Colab Demo ](https://colab.research.google.com/drive/1U3sPpknulwsCUQq9mK7Ywfb8ap2GIXZv?usp=sharing)) ( [ Paper ](https://doi.org/10.1063/1.36219)) 
- Scatter Search ([ Colab Demo ](https://colab.research.google.com/drive/115Ql6KegvOjlNUUfsbY4fA8Vab-db26N?usp=sharing)) ( [ Paper ](https://doi.org/10.1111/j.1540-5915.1977.tb01074.x)) 
- Stochastic Hill Climbing ([ Colab Demo ](https://colab.research.google.com/drive/1_wP6vg4JoRHGItGxEtXcf9Y9OuuoDlDl?usp=sharing)) ( [ Paper ](http://aima.cs.berkeley.edu/)) 
- Tabu Search ([ Colab Demo ](https://colab.research.google.com/drive/1SRwQrBaxkKk18SDvQPy--0yNRWdl6Y1G?usp=sharing)) ( [ Paper ](https://doi.org/10.1287/ijoc.1.3.190)) 
- Variable Neighborhood Search ([ Colab Demo ](https://colab.research.google.com/drive/1yMWjYuurzpcijsCFDTA76fAwJmSaDkZq?usp=sharing)) ( [ Paper ](https://doi.org/10.1016/S0305-0548(97)00031-2)) 
