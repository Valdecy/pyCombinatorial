# pyCombinatorial

## Introduction

A library to solve the TSP (Travelling Salesman Problem) using Exact Algorithms, Heuristics and Metaheuristics : **2-opt**; **2.5-opt**; **3-opt**; **4-opt**; **5-opt**; **2-opt Stochastic**; **2.5-opt Stochastic**; **3-opt Stochastic**; **4-opt Stochastic**; **5-opt Stochastic**; **Ant Colony Optimization**; **Bellman-Held-Karp Exact Algorithm**; **Branch & Bound**; **BRKGA** (Biased Random Key Genetic Algorithm); **Brute Force**; **Cheapest Insertion**; **Christofides Algorithm**; **Clarke & Wright**  (Savings Heuristic); **Concave Hull Algorithm**; **Convex Hull Algorithm**; **Elastic Net**; **Extremal Optimization**; **Farthest Insertion**; **Genetic Algorithm**; **GRASP** (Greedy Randomized Adaptive Search Procedure); **Greedy Karp-Steele Patching**; **Guided Search**; **Hopfield Network**; **Iterated Search**; **Karp-Steele Patching**; **Multifragment Heuristic**; **Nearest Insertion**; **Nearest Neighbour**; **Random Insertion**; **Random Tour**; **Scatter Search**; **Simulated Annealing**; **SOM** (Self Organizing Maps); **Space Filling Curve** (Hilbert); **Space Filling Curve** (Morton); **Space Filling Curve** (Sierpinski); **Stochastic Hill Climbing**; **Sweep**; **Tabu Search**; **Truncated Branch & Bound**; **Twice-Around the Tree Algorithm** (Double Tree Algorithm); **Variable Neighborhood Search**.

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

# Loading Coordinates # Berlin 52 (Minimum Distance = 7544.3659)
coordinates = pd.read_csv('https://bit.ly/3Oyn3hN', sep = '\t') 
coordinates = coordinates.values

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

- 2-opt ([ Colab Demo ](https://colab.research.google.com/drive/1SLkM8r_VdlFCpNpm-2yTfr_ynSC5WIX9?usp=sharing)) ( [ Paper ](https://www.jstor.org/stable/167074)) 
- 2.5-opt ([ Colab Demo ](https://colab.research.google.com/drive/17bJ-I26prnryAU8p-xf0l7R91cJzb85N?usp=sharing)) ( [ Paper ](https://doi.org/10.1007/s10955-007-9382-1))     
- 3-opt ([ Colab Demo ](https://colab.research.google.com/drive/1iAZLawLBZ-7yaPCyobMtel1SvBamxtjL?usp=sharing)) ( [ Paper ](https://isd.ktu.lt/it2011//material/Proceedings/1_AI_5.pdf)) 
- 4-opt ([ Colab Demo ](https://colab.research.google.com/drive/1N8HKhVY4s20sfqo8IWIaCY-NHVk6gARS?usp=sharing)) ( [ Paper ](https://isd.ktu.lt/it2011//material/Proceedings/1_AI_5.pdf))
- 5-opt ([ Colab Demo ](https://colab.research.google.com/drive/15Qrk-7H4oRaTR77ADvwkiN0sLvycgFDH?usp=sharing)) ( [ Paper ](https://isd.ktu.lt/it2011//material/Proceedings/1_AI_5.pdf))
- 2-opt Stochastic ([ Colab Demo ](https://colab.research.google.com/drive/1xTm__7OwQVC_KX2b-eExLGgG1DgnJ10a?usp=sharing)) ( [ Paper ](https://doi.org/10.1016/j.trpro.2014.10.001)) 
- 2.5-opt Stochastic ([ Colab Demo ](https://colab.research.google.com/drive/16W_QqJ1PebVgqUx8NFOSS5kG3DsJ51UQ?usp=sharing)) ( [ Paper ](https://doi.org/10.1007/s10955-007-9382-1))  
- 3-opt Stochastic ([ Colab Demo ](https://colab.research.google.com/drive/1A5lPW6BSDD2rLNDlnpQo44U8jwKcAGXL?usp=sharing)) ( [ Paper ](https://isd.ktu.lt/it2011//material/Proceedings/1_AI_5.pdf))
- 4-opt Stochastic ([ Colab Demo ](https://colab.research.google.com/drive/1igWrUMVSInzyeOdhPcGuMjyooZ6elvLY?usp=sharing)) ( [ Paper ](https://isd.ktu.lt/it2011//material/Proceedings/1_AI_5.pdf))
- 5-opt Stochastic ([ Colab Demo ](https://colab.research.google.com/drive/13vS5MCeFqb3F4ntxrw3iCsMbJTfEVyeo?usp=sharing)) ( [ Paper ](https://isd.ktu.lt/it2011//material/Proceedings/1_AI_5.pdf))
- Ant Colony Optimization ([ Colab Demo ](https://colab.research.google.com/drive/1O2qogrjE4mZUZX3nsSxw43crumlBnd-D?usp=sharing)) ( [ Paper ](https://doi.org/10.1109/4235.585892)) 
- Bellman-Held-Karp Exact Algorithm ([ Colab Demo ](https://colab.research.google.com/drive/1HSnArk-v8PWY4dlCvT5zcSAnT1FJEDaf?usp=sharing)) ( [ Paper ](https://dl.acm.org/doi/10.1145/321105.321111))
- Branch & Bound ([ Colab Demo ](https://colab.research.google.com/drive/1oDHrECSW3g4vBEsrO8T7qSHID4fxFiqs?usp=sharing)) ( [ Paper ](https://doi.org/10.1016/j.disopt.2016.01.005))
- BRKGA (Biased Random Key Genetic Algorithm) ([ Colab Demo ](https://colab.research.google.com/drive/1lwnpUBl1P1LIvzN1saLgEvnaKZRMWLHn?usp=sharing)) ( [ Paper ](https://doi.org/10.1007/s10732-010-9143-1))
- Brute Force ([ Colab Demo ](https://colab.research.google.com/drive/10vOkBz3Cv9UdHPlcBWkDmJO7EvDg96ar?usp=sharing)) ( [ Paper ](https://swarm.cs.pub.ro/~mbarbulescu/cripto/Understanding%20Cryptography%20by%20Christof%20Paar%20.pdf))
- Cheapest Insertion ([ Colab Demo ](https://colab.research.google.com/drive/1QOg8FDvrFUgojwLXD2BBvEuB9Mu7q88a?usp=sharing)) ( [ Paper ](https://disco.ethz.ch/courses/fs16/podc/readingAssignment/1.pdf))
- Christofides Algorithm ([ Colab Demo ](https://colab.research.google.com/drive/1Wbm-YQ9TeH2OU-IjZzVdDkWGQILv4Pj_?usp=sharing)) ( [ Paper ](https://apps.dtic.mil/dtic/tr/fulltext/u2/a025602.pdf))
- Clarke & Wright  (Savings Heuristic) ([ Colab Demo ](https://colab.research.google.com/drive/1XC2yoVe6wTsjt7u2fBaL3LcKUu42FG8r?usp=sharing)) ( [ Paper ](http://dx.doi.org/10.1287/opre.12.4.568))
- Concave Hull Algorithm ([ Colab Demo ](https://colab.research.google.com/drive/1P96DerRe7CLyC9dQNr96nEkNHnxpGYY4?usp=sharing)) ( [ Paper ](http://repositorium.sdum.uminho.pt/bitstream/1822/6429/1/ConcaveHull_ACM_MYS.pdf))
- Convex Hull Algorithm ([ Colab Demo ](https://colab.research.google.com/drive/1Wn2OWccZukOfMtJuGV9laklLTc8vjOFq?usp=sharing)) ( [ Paper ](https://doi.org/10.1109/TSMC.1974.4309370))
- Elastic Net ([ Colab Demo ](https://colab.research.google.com/drive/1F7IlkKdZ3_zQ_MkhknkIPHvE5RqJG7YC?usp=sharing)) ( [ Paper ](https://doi.org/10.1038/326689a0))
- Extremal Optimization ([ Colab Demo ](https://colab.research.google.com/drive/1Y5YH0eYKjr1nj_IfhJXaILRDIXm-LWLs?usp=sharing)) ( [ Paper ](https://doi.org/10.1109/5992.881710))
- Farthest Insertion ([ Colab Demo ](https://colab.research.google.com/drive/13pWiLL_dO9Y1lvQO0zD50MXk4mD0Tn1W?usp=sharing)) ( [ Paper ](https://disco.ethz.ch/courses/fs16/podc/readingAssignment/1.pdf))
- Genetic Algorithm ([ Colab Demo ](https://colab.research.google.com/drive/1zO9rm-G6HOMeg1Q_ptMHJr48EpHcCAIS?usp=sharing)) ( [ Paper ](https://doi.org/10.1007/BF02125403))  
- GRASP (Greedy Randomized Adaptive Search Procedure) ([ Colab Demo ](https://colab.research.google.com/drive/1OnRyCc6C_QL6wr6-l5RlQI4eGbMdwuhS?usp=sharing)) ( [ Paper ](https://doi.org/10.1007/BF01096763)) 
- Greedy Karp-Steele Patching ([ Colab Demo ](https://colab.research.google.com/drive/1to3u45QWWQK8REj1_YiF5rUqUqNjB18q?usp=sharing)) ( [ Paper ](https://doi.org/10.1016/S0377-2217(99)00468-3))
- Guided Search ([ Colab Demo ](https://colab.research.google.com/drive/1uT9mlDoo37Ni7hqziGNELEGQCGBKQ83o?usp=sharing)) ( [ Paper ](https://doi.org/10.1016/S0377-2217(98)00099-X)) 
- Hopfield Network ([ Colab Demo ](https://colab.research.google.com/drive/1Io20FFsndsRT3Bc1nimLBcpH5WtEt7Pe?usp=sharing)) ( [ Paper ](https://doi.org/10.1515/dema-1996-0126)) 
- Iterated Search ([ Colab Demo ](https://colab.research.google.com/drive/1U3sPpknulwsCUQq9mK7Ywfb8ap2GIXZv?usp=sharing)) ( [ Paper ](https://doi.org/10.1063/1.36219)) 
- Karp-Steele Patching ([ Colab Demo ](https://colab.research.google.com/drive/12xLLDNIk6OOSNQXqYSYtdwhupZ9Kt5xb?usp=sharing)) ( [ Paper ](https://doi.org/10.1137/0208045))
- Multifragment Heuristic ([ Colab Demo ](https://colab.research.google.com/drive/1YNHVjS6P35bAnqGZyP7ERNrTnG9tNuhF?usp=sharing)) ( [ Paper ](https://citeseerx.ist.psu.edu/viewdoc/download;jsessionid=08D176AEFA57EF1941645F2B31DF1686?doi=10.1.1.92.1635&rep=rep1&type=pdf))
- Nearest Insertion ([ Colab Demo ](https://colab.research.google.com/drive/1R4mz604EG-unKktu8ON_Hpoywi3OIRHK?usp=sharing)) ( [ Paper ](https://disco.ethz.ch/courses/fs16/podc/readingAssignment/1.pdf))
- Nearest Neighbour ([ Colab Demo ](https://colab.research.google.com/drive/1aL1kYXgSjUJYPfYSMy_0SWq4hJ3nrueJ?usp=sharing)) ( [ Paper ](https://doi.org/10.1016/S0166-218X(01)00195-0))
- Random Insertion ([ Colab Demo ](https://colab.research.google.com/drive/1RP_grqrTXyDkHOLB_L1H8TkvxdLli5hG?usp=sharing)) ( [ Paper ](https://disco.ethz.ch/courses/fs16/podc/readingAssignment/1.pdf))
- Random Tour ([ Colab Demo ](https://colab.research.google.com/drive/1DPXMJXInkGKTyVFDAQ2bKXjglhy3DaCS?usp=sharing)) ( [ Paper ](https://doi.org/10.1023/A:1011263204536))
- Scatter Search ([ Colab Demo ](https://colab.research.google.com/drive/115Ql6KegvOjlNUUfsbY4fA8Vab-db26N?usp=sharing)) ( [ Paper ](https://doi.org/10.1111/j.1540-5915.1977.tb01074.x)) 
- Simulated Annealing ([ Colab Demo ](https://colab.research.google.com/drive/10Th0yLaAeSqp9FhYB0H00e4sXTbg7Jp2?usp=sharing)) ( [ Paper ](https://www.jstor.org/stable/1690046))
- SOM (Self Organizing Maps) ([ Colab Demo ](https://colab.research.google.com/drive/1-ZwSFnXf1_kCeY_p3SC3N21T8QeSWsg6?usp=sharing)) ( [ Paper ](https://arxiv.org/pdf/2201.07208.pdf))
- Space Filling Curve (Hilbert) ([ Colab Demo ](https://colab.research.google.com/drive/1FXzWrUBjdbJBngRFHv66CZw5pFN3yOs8?usp=sharing)) ( [ Paper ](https://doi.org/10.1016/0960-0779(95)80046-J))
- Space Filling Curve (Morton) ([ Colab Demo ](https://colab.research.google.com/drive/1Z13kXyi7eaNQbBUmhvwuQjY4VaUfGVbs?usp=sharing)) ( [ Paper ](https://dominoweb.draco.res.ibm.com/reports/Morton1966.pdf))
- Space Filling Curve (Sierpinski) ([ Colab Demo ](https://colab.research.google.com/drive/1w-Zptd5kOryCwvQ0qSNBNhPXC61c8QXF?usp=sharing)) ( [ Paper ](https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.67.9061&rep=rep1&type=pdf))
- Stochastic Hill Climbing ([ Colab Demo ](https://colab.research.google.com/drive/1_wP6vg4JoRHGItGxEtXcf9Y9OuuoDlDl?usp=sharing)) ( [ Paper ](http://aima.cs.berkeley.edu/)) 
- Sweep ([ Colab Demo ](https://colab.research.google.com/drive/1AkAn4yeomAp6POBslk3Asd6OrxfBrHT7?usp=sharing)) ( [ Paper ](http://dx.doi.org/10.1287/opre.22.2.340))
- Tabu Search ([ Colab Demo ](https://colab.research.google.com/drive/1SRwQrBaxkKk18SDvQPy--0yNRWdl6Y1G?usp=sharing)) ( [ Paper ](https://doi.org/10.1287/ijoc.1.3.190))
- Truncated Branch & Bound ([ Colab Demo ](https://colab.research.google.com/drive/16m72PrBZN8mWMCer12dgsStcNGs4DVdQ?usp=sharing)) ( [ Paper ](https://research.ijcaonline.org/volume65/number5/pxc3885866.pdf)) 
- Twice-Around the Tree Algorithm ([ Colab Demo ](https://colab.research.google.com/drive/1tf5tc5DxvEUc89JaaFgzmK1TtD1e4fkc?usp=sharing)) ( [ Paper ](https://doi.org/10.1016/0196-6774(84)90029-4)) 
- Variable Neighborhood Search ([ Colab Demo ](https://colab.research.google.com/drive/1yMWjYuurzpcijsCFDTA76fAwJmSaDkZq?usp=sharing)) ( [ Paper ](https://doi.org/10.1016/S0305-0548(97)00031-2)) 

# Single Objective Optimization
For Single Objective Optimization try [pyMetaheuristic](https://github.com/Valdecy/pyMetaheuristic)

# Multiobjective Optimization or Many Objectives Optimization
For Multiobjective Optimization or Many Objectives Optimization try [pyMultiobjective](https://github.com/Valdecy/pyMultiobjective)
