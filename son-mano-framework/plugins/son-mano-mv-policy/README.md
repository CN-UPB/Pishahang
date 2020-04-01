# Policy Plugin

## Flow

![policy-flowchart](policy-flowchart.jpg)

----
## Decision Matrix    

|                    	| Weights 	| Version1 	| Version2 	| Version3 	| Score 	|
|--------------------	|:-------:	|:--------:	|:--------:	|:--------:	|:--------:	|
| Cost (-)           	|    -4    	|     x1   	|    x2    	|    x3    	|    s    	|
| Over Provision (-) 	|    -3   	|     x1   	|    x2    	|    x3    	|    s    	|
| Overhead (-)       	|    -4   	|     x1   	|    x2    	|    x3    	|    s    	|
| Support deviation (+) |    3    	|     x1   	|    x2    	|    x3    	|    s    	|
| Same Version (+)   	|    3    	|     x1   	|    x2    	|    x3    	|    s    	|