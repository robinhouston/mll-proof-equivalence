#!/usr/bin/python

"""Compute the maximal diameter of a subset sum reconfiguration
graph with n elements.

The algorithm is naivety itself: enumerate all possible such
graphs and compute all-pairs shortest paths for each.

(In fact our enumeration method may also produce some unrealisable
graphs: I am not certain that it does, but have no good reason
to think it does not. But we are searching for upper bounds on
the diameter, so this is harmless.)
"""

import re, sys

def each_subset(xs):
    if not xs:
        yield frozenset()
        return
    
    xs_copy = { x for x in xs }
    x = xs_copy.pop()
    for ys in each_subset(xs_copy):
        yield ys
        yield ys | {x}

debug_indent = ""
def debug_enter(fmt, *args):
    debug_print(fmt, *args)
    global debug_indent
    debug_indent += "  "

def debug_print(fmt, *args):
    formatted = fmt % args
    #print debug_indent + re.sub(r"frozenset\(\[([^\]]*)\]\)", lambda mo: "{"+mo.group(1)+"}", formatted)

def debug_leave(fn):
    global debug_indent
    debug_indent = debug_indent[:-2]
    debug_print("/" + fn)

def each_ordering(n):
    debug_enter("each_ordering(%d)", n)
    if n == 0:
        yield (frozenset(),)
        debug_leave("each_ordering")
        return
    for prev in each_ordering(n-1):
        for ordering in each_merge(prev, n):
            yield ordering
    debug_leave("each_ordering")

def each_merge(prev, n):
    elements = prev[-1] # The last element is always the whole set
    other = tuple( s|{n} for s in prev )
    debug_enter("each_merge(%r, %r)", prev, other)
    
    def each_partial_merge(comp, i, j, partial):
        debug_enter("each_partial_merge(%d, %d, %r)", i, j, partial)
        if i == len(prev):
            yield partial + other[j:]
            debug_leave("each_partial_merge")
            return
        if j == len(prev):
            yield partial + prev[i:]
            debug_leave("each_partial_merge")
            return
        
        pair = (prev[i], other[j])
        if pair in comp:
            new_i, new_j, new_partial = i, j, partial
            debug_print("[%d, %d] %r in comp", i, j, pair)
            if comp[pair] >= 0:
                new_partial += (prev[i],)
                new_i = i + 1
            else:
                new_partial += (other[j],)
                new_j = j + 1
            
            for merge in each_partial_merge(comp, new_i, new_j, new_partial):
                yield merge
            debug_leave("each_partial_merge")
            return
        
        debug_print("[%d, %d] %r not in comp", i, j, pair)
        
        # If the elements are currently incomparable, try it both ways
        for chosen_order in (-1, +1):
            new_comp = {}
            new_comp.update(comp)
            new_partial, new_i, new_j = partial, i, j
            
            # Add this choice to the comp table
            for subset in each_subset(elements - pair[0] - pair[1]):
                comp[(pair[0] | subset, pair[1] | subset)] = chosen_order
            
            # Make the appropriate recursive call
            if comp[pair] > 0:
                new_partial += (prev[i],)
                new_i = i + 1
            else:
                new_partial += (other[j],)
                new_j = j + 1
        
            for merge in each_partial_merge(comp, new_i, new_j, new_partial):
                yield merge
        
        debug_leave("each_partial_merge")
    
    # Record some of the order relations between prev and other that
    # are implied by the chosen order of prev.
    init_comp = {}
    for i in range(len(prev)):
        for j in range(i, len(other)):
            init_comp[(prev[i], other[j])] = +1
            if (n-1) in prev[j]:
                init_comp[(prev[i], (prev[j] - {n-1}) | {n})] = +1
    
    for merge in each_partial_merge(init_comp, i, 0, prev[:i]):
        yield merge
    
    debug_leave("each_merge")

def each_graph(n):
    graphs = set()
    for ordering in each_ordering(n):
        for i in range(len(ordering)):
            for j in range(i+1, len(ordering)+1):
                graph = frozenset(ordering[i:j])
                if graph not in graphs:
                    yield ordering[i:j]
                    graphs.add(graph)

def graph_diameter(graph):
    entries = tuple(graph)
    index_of_entry = dict( (entry, index) for index, entry in enumerate(entries) )
    elements = frozenset.union(*entries)
    
    t = [ [ float("inf") for i in range(len(graph)) ] for j in range(len(graph)) ]
    for i in range(len(graph)):
        t[i][i] = 0
        entry = entries[i]
        for element in elements:
            if element in entry:
                if entry - {element} in graph:
                    t[index_of_entry[entry - {element}]][i] = t[i][index_of_entry[entry - {element}]] = 1
            else:
                if entry | {element} in graph:
                    t[index_of_entry[entry | {element}]][i] = t[i][index_of_entry[entry | {element}]] = 1
    
    for k in range(len(graph)):
        for i in range(len(graph)):
            for j in range(len(graph)):
                if t[i][k] + t[k][j] < t[i][j]:
                    t[i][j] = t[i][k] + t[k][j]
    
    diameter = 0
    for i in range(len(graph)):
        for j in range(i, len(graph)):
            if t[i][j] < float("inf"):
                diameter = max(diameter, t[i][j])
    return diameter

def maxd(n):
    max_diameter = 0
    size_of_best_solution = 0
    for graph in each_graph(n):
        d = graph_diameter(graph)
        if d > max_diameter:
            print "New record diameter = %d" % (d,)
            max_diameter = d
            size_of_best_solution = len(graph)
            print ", ".join([ "{" + ", ".join(map(str, xs)) + "}" for xs in graph ])
            print
        elif d == max_diameter and len(graph) < size_of_best_solution:
            print "Shorter solution found for diameter %d" % (d,)
            size_of_best_solution = len(graph)
            print ", ".join([ "{" + ", ".join(map(str, xs)) + "}" for xs in graph ])
            print

if __name__ == "__main__":
    maxd(int(sys.argv[1]))
    sys.exit(0)

# The code below is dead unless you comment out the three lines
# above. It may be used to verify that our algorithm produces
# valid orderings.

def precedes(x, y):
    intersection = x & y
    x -= intersection
    y -= intersection
    if not x and y:
        return True
    if len(x) < len(y):
        for a, b in zip(sorted(x), sorted(y)[-len(x):]):
            if a >= b:
                return False
        return True
    return False

def order_is_okay(graph):
    for i, x in enumerate(graph):
        for y in graph[i:]:
            if precedes(y, x):
                return False
    return True

for graph in each_ordering(int(sys.argv[1])):
    print ", ".join([ "{" + ", ".join(map(str, xs)) + "}" for xs in graph ])
    if not order_is_okay(graph):
        raise Exception("sequence is out of order!")
