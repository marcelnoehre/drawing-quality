# Dirichlet random formal context generator
#
# Original code: Copyright (c) 2018 Maximilian Felde
#   https://github.com/maximilian-felde/formal-context-generator
#   Accompanies: M. Felde, T. Hanika, "Formal Context Generation using
#   Dirichlet Distributions", arXiv:1809.11160
#
# Modifications (.cxt export, batch generation): Copyright (c) 2026 Marcel Nöhre,
#   Knowledge & Data Engineering Group, University of Kassel

import numpy as np
import scipy as sci
from pathlib import Path
import scipy.stats as stats

def dirichlet_approach(M=10, b='random'):
    # dirichlet(beta*alpha), beta concentration parameter; alpha base measure
    G = np.random.randint(M, 2*M)
    alpha=[1]*(M+1)
    alpha = list(np.array(alpha)/sum(np.array(alpha))) # normalize initial vector
    if b == 'random':
        # beta >0.001 prevents problems with dirichlet
        beta = 0.001+np.random.random()*(M+1) 
    elif b == 0.1:
        beta = 0.1*(M+1)
    else:
        beta = 1*(M+1)
    #draw probabilities for categorical distribution
    rv = sci.stats.dirichlet(beta*np.array(alpha)) 
    p = rv.rvs()[0]
    categories = np.arange(0,len(alpha))
    # create categorical distribution
    categorical = sci.stats.rv_discrete(name='categorical', values=(categories, p)) 
    # create random context
    context = []
    for i in range(G):    
        # randomly decide how many attributes the object has
        number_of_attributes = categorical.rvs()
        row = [1] * number_of_attributes + [0]*(M - number_of_attributes)
        # randomly decide which attributes specifically
        np.random.shuffle(row)
        context.append(row)
    return context


def context_to_file(context, name='test'):
    '''
    Export a binary context in Burmeister .cxt format.
    '''
    num_objects = len(context)
    num_attributes = len(context[0]) if context else 0
    with open(name + '.cxt', 'w', encoding='utf-8') as file:
        file.write('B\n\n')
        file.write(f'{num_objects}\n')
        file.write(f'{num_attributes}\n\n')
        for index in range(1, num_objects + 1):
            file.write(f'g{index}\n')
        for index in range(1, num_attributes + 1):
            file.write(f'm{index}\n')
        for row in context:
            file.write(''.join('x' if value else '.' for value in row) + '\n')
    return

if __name__ == '__main__':
    # generates 10 random contexts per attribute count M using the dirichlet approach and saves them as cxt
    output_dir = Path(__file__).parent
    for M in range(5, 30, 5):
        for i in range(10):
            context_to_file(dirichlet_approach(M=M), name=str(output_dir / f'random{M}_{i}'))
