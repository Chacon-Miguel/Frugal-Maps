#!/usr/bin/env python3

import typing
from util import read_osm_data, great_circle_distance, to_local_kml_url

# NO ADDITIONAL IMPORTS!


ALLOWED_HIGHWAY_TYPES = {
    'motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified',
    'residential', 'living_street', 'motorway_link', 'trunk_link',
    'primary_link', 'secondary_link', 'tertiary_link',
}


DEFAULT_SPEED_LIMIT_MPH = {
    'motorway': 60,
    'trunk': 45,
    'primary': 35,
    'secondary': 30,
    'residential': 25,
    'tertiary': 25,
    'unclassified': 25,
    'living_street': 10,
    'motorway_link': 30,
    'trunk_link': 30,
    'primary_link': 30,
    'secondary_link': 30,
    'tertiary_link': 25,
}


def build_internal_representation(nodes_filename, ways_filename):
    """
    Create any internal representation you you want for the specified map, by
    reading the data from the given filenames (using read_osm_data)
    """
    # will hold final map representation
    map_rep = {}
    # will temporarily hold node info
    nodes = {}
    # set of all nodes needed
    needed_nodes = set()
    # for every way...
    for way in read_osm_data(ways_filename):
        # check if the way is valid, i.e. it's a highway and it's in the 
        # allowed highway types
        if way['tags'].get('highway', 0) in ALLOWED_HIGHWAY_TYPES:
            # get the way's speed limit
            speed_limit = way['tags'].get('maxspeed_mph', DEFAULT_SPEED_LIMIT_MPH[way['tags']['highway']])
            # for every node in this way except the last one...
            for i in range(len(way['nodes']) - 1):
                # make the key for the nodes dict the node's ID that maps to 
                # another dict whose keys are the ID of the connecting nodes
                # and the values are the speed limit of the way
                # Example: nodes[3] would hold the dict below
                # {3: {4: 25mph, 11: 60mpn}, 5: {3:30mph, 8:30mph, 9: 35mph}}
                nodes[ way['nodes'][i] ] = nodes.get(way['nodes'][i], {}) 
                nodes[ way['nodes'][i] ][way['nodes'][i+1]] = speed_limit
                # add the current node to needed nodes
                needed_nodes.add(way['nodes'][i])
            # make sure to get the last node too
            needed_nodes.add(way['nodes'][len(way['nodes']) -1] )
            # check if the raod is a not a one-way
            if way['tags'].get('oneway', 'no') == 'no':
                # if it's not, then do the same as above, but backwards
                for i in range(1, len(way['nodes'])):
                    nodes[ way['nodes'][i] ] = nodes.get(way['nodes'][i], {})
                    nodes[ way['nodes'][i] ][way['nodes'][i-1]] = speed_limit

    # for every node available in the data...
    for node in read_osm_data(nodes_filename):
        # if the node is valid...
        if node['id'] in needed_nodes:
            # add it to the map rep
            map_rep[node['id']] = {
                'lon': node['lon'],
                'lat': node['lat'],
                'connecting nodes': {},
            }
    # for every node and its list of connecting nodes...
    for node, c_nodes in nodes.items():        
        # for every connecting node...
        for c_node, speed_lim in c_nodes.items():
            # get the current nodes latitude and longitude
            loc1 = ( map_rep[node]['lat'], map_rep[node]['lon'] )
            # get the connecting nodes latitude and longitude
            loc2 = ( map_rep[c_node]['lat'], map_rep[c_node]['lon'] )
            dist = great_circle_distance(loc1, loc2)
            # make the keys of the connecting nodes dict the connecting nodes id
            # and then value would be the distance between the node and connecting
            # node
            map_rep[node]['connecting nodes'][c_node] = {'distance':dist, 'time':dist/speed_lim}
    # final view of map_rep is below
    # map_rep[10] = {'lon':41, 'lat':-89, 'connecting nodes': {4: {'distance: 4, 'time': 0.005}}}
    return map_rep
    

def a_star(map_rep, node1, node2, key):
    """
    Uses the great circle distance between nodes as a heuristic. Returns the optimal path based on the key given.
    If the key is distance, the cost function is based on distance, and a heuristic is used. If the key is time,
    the cost function just uses uniform-cost search to get the optimal path
    """
    # if start and end nodes are the same, return 0
    if node1 == node2:
        return [node1]

    queue = []
    visited = set()
    # initially set all nodes as infinitely far away
    cost = {node:{'g': float('inf'), 'f': float('inf')} for node in map_rep.keys()}
    # keeps track of nodes we traverse through to rebuild path at the end
    predecessor = {node:None for node in map_rep.keys()}
    # add starting node and heuristic value to queue
    queue.append((0, node1))

    # get lon and lat of boths initial nodes in a tuple
    loc1 = (map_rep[node1]['lat'], map_rep[node1]['lon'])
    loc2 = (map_rep[node2]['lat'], map_rep[node2]['lon'])

    # set the cost to get to this node, g, to 0 for starting node
    # make heuristic fucntion for starting node to 0
    cost[node1]['g'] = 0
    cost[node1]['f'] = 0

    while len(queue) != 0:
        # get the node id from the queue
        curr_node = queue.pop(0)[1]
        visited.add(curr_node)

        # if we've reached the end node, return the path taken
        if curr_node == node2:
            break
        # for every connecting node...
        for node, costs in map_rep[curr_node]['connecting nodes'].items():  
            # if not already seen...
            if node not in visited:
                # check if the cost of visiting this node is less than known path
                new_cost = cost[curr_node]['g'] + costs[key] 
                if new_cost < cost[node]['g']:
                    # if it is, set the current nodes cost value to the new one
                    cost[node]['g'] = new_cost
                    # update heuristic
                    if key == 'distance':
                        cost[node]['f'] = new_cost + great_circle_distance((map_rep[node]['lat'], map_rep[node]['lon']), loc2)
                    else:
                        cost[node]['f'] = new_cost
                    # update the optimal path
                    predecessor[node] = curr_node
                    queue.append((cost[node]['g'], node))
        # sort to make the first in queue the node with lowest cost
        queue.sort(key = lambda x: x[0])
    
    # reconstruct path
    path = []
    curr_node = node2
    while predecessor[curr_node]!= None:
        path.insert(0, curr_node)
        curr_node = predecessor[curr_node]
    if path != []:
        path.insert(0, curr_node)
        return path
    return None

def find_short_path_nodes(map_rep, node1, node2):
    """
    Return the shortest path between the two nodes

    Parameters:
        map_rep: the result of calling build_internal_representation
        node1: node representing the start location
        node2: node representing the end location

    Returns:
        a list of node IDs representing the shortest path (in terms of
        distance) from node1 to node2
    """
    return a_star(map_rep, node1, node2, 'distance')

def find_closest_node(map_rep, loc):
    """
    Return the closest node in map_rep to the given location
    """
    diff = float('inf')
    closest_node_id = 0
    # go through all nodes
    for k, v in map_rep.items():
        # get distance between current node and the given location
        distance = great_circle_distance(loc, ( v['lat'], v['lon'] ) )
        # if the distance between them is smaller than the curret known min,
        # update the min
        if diff > distance:
            diff = distance
            closest_node_id = k
    return closest_node_id 


def find_short_path(map_rep, loc1, loc2):
    """
    Return the shortest path between the two locations

    Parameters:
        map_rep: the result of calling build_internal_representation
        loc1: tuple of 2 floats: (latitude, longitude), representing the start
              location
        loc2: tuple of 2 floats: (latitude, longitude), representing the end
              location

    Returns:
        a list of (latitude, longitude) tuples representing the shortest path
        (in terms of distance) from loc1 to loc2.
    """
    # get nodes closest to given locations
    node1 = find_closest_node(map_rep, loc1)
    node2 = find_closest_node(map_rep, loc2)
    # get id's of all nodes in the optimal path
    node_path = find_short_path_nodes(map_rep, node1, node2)

    if node_path == None:
        return None
    # return lat on lon of each node in the optimal path
    return [(map_rep[ID]['lat'], map_rep[ID]['lon']) for ID in node_path]



def find_fast_path(map_rep, loc1, loc2):
    """
    Return the shortest path between the two locations, in terms of expected
    time (taking into account speed limits).

    Parameters:
        map_rep: the result of calling build_internal_representation
        loc1: tuple of 2 floats: (latitude, longitude), representing the start
              location
        loc2: tuple of 2 floats: (latitude, longitude), representing the end
              location

    Returns:
        a list of (latitude, longitude) tuples representing the shortest path
        (in terms of time) from loc1 to loc2.
    """
    # find closest nodes to given locations
    node1 = find_closest_node(map_rep, loc1)
    node2 = find_closest_node(map_rep, loc2)
    # get id's of nodes in optimal path and use time as cost instead of distance
    node_path = a_star(map_rep, node1, node2, 'time')

    if node_path == None:
        return None
    # return lat on lon of each node in the optimal path
    return [(map_rep[ID]['lat'], map_rep[ID]['lon']) for ID in node_path]



if __name__ == '__main__':
    # additional code here will be run only when lab.py is invoked directly
    # (not when imported from test.py), so this is a good place to put code
    # used, for example, to generate the results for the online questions.
    map_rep = build_internal_representation('resources/mit.nodes', 'resources/mit.ways')
    # loc1, loc2 = ((41.505515, -89.463392), (41.43567, -89.394277))
    loc1 = (42.355, -71.1009) # New House
    loc2 = (42.3612, -71.092) # 34-501
    # dist = great_circle_distance(loc2, (0,0))
    file = open('testing.txt', 'w')
    for k, v in map_rep.items():
        file.write(str(k) + " " + str(v['lat']) + " " +str(v['connecting nodes']))
        file.write('\n')
    file.close()

    # print(find_fast_path(map_rep, loc1, loc2))
    print(find_short_path_nodes(map_rep, 2, 8))

    # with heuristic: 50180 additions to the queue
    # without heuristic: 412275 additions to the queue
    # major difference! so cool!