# Frugal-Maps
 My own small version of Google Maps for the Boston Area

## Contents of Each File:
stuff for now. Add later

## Introduction 
We will be working with freely available real-world mapping data to solve the realistic large problem of finding the shortest (or fastest) path between two points on a map. You will implement the backend for a route-finding application, which we will be able to use to plan paths around Cambridge.

All of the software and data we are working with in this lab is freely available, including the mapping data, the images used to render the maps, and the software used to control the map display! In fact, a lot of the world's most widely used software is created in this same spirit of sharing and community. 

### The Data
The data we'll use for this lab comes from OpenStreetMap, and for the bulk to this lab, we are working with data about Cambridge and the surrounding area (about 650 MB of data). While the raw data (downloaded from here) was specified in the OSM XML Format, we have done a little bit of pre-processing to convert the data to a format that is slightly easier to work with.

As in the original format, we have divided the data into two separate pieces: a list of "nodes" (representing individual locations) and a list of "ways" (representing roads or other kinds of connections between nodes). We have stored these data in large files that contain many pickled Python objects, one for each node/way (the function we used to do this is made available to you in the util.py file as osm_to_serial_pickles, in case you want to try it on your own data).

The Cambridge data set stores these in two files, which are available in the code distribution: resources/cambridge.nodes and resources/cambridge.ways.

We have also provided a helper function in util.py called read_osm_data (which has been imported into lab.py for you). Calling read_osm_data with a filename will produce an object over which you can loop to examine each node/way in turn. For example, you could use the following code to print all of the nodes in this database:

```
for node in read_osm_data('resources/cambridge.nodes'):
    print(node)
```

One important thing worth noting is that this object can only be looped over once (looping over the same data again would require calling read_osm_data again).

You can also get a single element out of this object using Python's built-in next function (if you want to grab a single entry rather than looping over the whole structure), for example:
```
data = read_osm_data('resources/cambridge.nodes')
print(next(data))
```

Each node (representing a location) is represented as a dictionary containing the following keys:
* `'id'` maps to an interger ID number for the node.
* `'lat'` maps to the node's latitude and latitude (in degrees)
* `'lon'` maps to the node's longitude (in degrees)
* `'tags` maps to a dictionary containing additional information about the node, including information about the type of object represented by the ndoe (traffic lights, speed limit signs, etc.)

(Note also that is it possible for multiple nodes to have the same location (latitude and longitude).)

Each way (representing an ordered sequence of connected nodes) is represented as a dictionary with the following keys:

* `'id'` maps to an integer ID number for the way.
* `'nodes'` maps to a list of integers representing the nodes that comprise the way (in order).
* `'tags'` maps to a dictionary containing additional information about the way (e.g. is this a one-way street? is it a highway or a pedestrian path? etc.)

## Shortest Paths
Now that we've had a chance to get used to the format of the data set, we'll embark on our first of two tasks for the lab: finding the shortest path between two nodes. Ultimately, we will implement this as a function `find_short_path_nodes`. This function takes three arguments:

* `internal_represenation`: explained in the section below
* `id1`: the ID of our starting node
* `id2`: the ID of our ending node

We are interested in returning the shortest path (in miles) between those two locations.

Ultimately, `find_short_path_nodes` should return a list of IDs (each corresponding to a single node) representing a path between the two given locations, where each pair of adjacent nodes must be connected by a way. If no such path exists, you should return `None`.

## Design Considerations
### Road Types
The datasets we're working with contain information not only about roadways, but also about bicycle paths, pedestrian paths, buildings, etc. Since we are (for now, at least) planning paths for cars only, we will only consider a way to be valid for our purposes if it is a roadway (we're responsible citizens of the world, so we won't drive on a bike path or a pedestrian-only walkway).

Some ways in the dataset have a tag called `'highway'`, indicating that the path represents a path people can use to travel (as opposed to the outline of a building, a river, the outline of a park, etc.). We will use this tag to decide what kinds of ways to include in our results.

In particular, we'll only consider a way as part of our path-planning process if:

* it has a `highway` tag, **and**
* its `'highway'` tag is in the `ALLOWED_HIGHWAY_TYPES` set that has been pre-defined in the file `lab.py`.

### Connectedness
We will assume that we can travel from a node to another node if and only if there is a way that connects them. For example, if we have the following two ways in the database:

```
w1 = {'id': 1, 'nodes': [1, 2, 3], 'tags': {}}
w2 = {'id': 2, 'nodes': [5, 6, 7], 'tags': {'oneway': 'yes'}}
```

then moving from node `1` to node `2`, from `2` to `3`, from `3` to `2`, or from `2` to `1` are all OK because `w1` represents a bidirectional street. But, while moving from `5` to `6` or from `6` to `7` are OK, moving from `7` to `6` or from `6` to `5` are not OK because `w2` represents a one-way street (we're responsible citizens of the world, so we respect one-way restrictions).

Note that moving directly from node `1` to node `3` is not possible given the above, unless there is another way that directly connects those two nodes.

As we're planning paths between nodes, we'll want to make sure that we only consider a node as a possibility if it exists as part of a way (we can ignore all other nodes in the database).

### Distance Measure
We will use an approximation for distance (in miles) that takes into account the approximate curvature of the earth

### Auxiliary Data Structures
The chosen data structure was an adjancency set, which in Python is essentially a dictionary that maps every nodes ID to another dictionary that contains the following keys:
* `'lon'`: a float representing the nodes longitude
* `'lat'`: a float representing the nodes latitude
* `'connecting nodes'`: a dictionary that maps the ID's of nodes that are connected to the current node to another dictionary that contains the distance between the two nodes and the time to get from one node to another

The following is an example of node's entry with an ID of 10:
```
map_rep[10] = {
    'lon':41, 
    'lat':-89, 
    'connecting nodes': {
        4: {
            'distance: 4, 
            'time': 0.005
            }
        }
    }
```

## Starting and Ending Points
Often, when we are interested in path planning in real geographical contexts, our given starting point might not actually be a known point of interest (for example, it might be a location specified by GPS).

To this end, we augmented our system so that it can accept arbitrary locations for the starting and ending points, specified as (latitude, longitude) tuples.

We will do this by implementing a new function `find_short_path` in `lab.py`. This function takes in three arguments:
* `map_rep`: the internal representation of the map
* `loc1`: a tuple of (latitude, longitude) of our starting location
* `loc2`: a tuple of (latitude, longitude) of our ending location

The function then returns a list of (latitude, longitude) tuples connecting the start and end location.

It is entirely possible that the locations passed to find_short_path will not correspond exactly to nodes in the dataset. As such, we will instead plan our shortest paths as follows, where a "relevant" way refers to any way that we will actually consider in our path planning:
* finding the nearest node to `loc1` that is part of a relevant way (call this node $n_{1}$)
* finding the nearest node to `loc2` that is part of a relevant way (call this node $n_{2}$)
* finding the shortest path from $n_{1}$ to $n_{2}$ (in terms of miles)
* convert the resulting path into (latitude, longitude) tuples.

## Visualization
As with the last lab, we have provided a web-based interface that acts as a visualization for your code.

Here, we use leaflet to display map data from the Wikimedia foundation.

You can start the server by running server.py but providing the filename of one of the datasets as an argument, for example:
```
python3 server.py midwest
```
or 
```
python3 server.py cambridge
```

This process will first build up the necessary internal representation for pathfinding by calling your `build_internal_representation` function, and then it will start a server. After the server has successfully started, you can interact with this application by navigating to `http://localhost:6009/` in your web browser. In that view, you can double-click on two locations to find and display a path between them.

Alternatively, you can manually call your path-finding procedure to generate a path and then pass its path to the provided `to_local_kml_url` function to receive a URL that will initialize to display the resulting path.

## Improving Runtime with Heuristics
A reasonable heuristic in this domain is the distance directly from the given node to the goal node:
$$
h(n) = great_circle_distance(n, goal)
$$

This function provides a decent estimate of our overall cost, it is admissible and consistent, and it is pretty fast to compute.

## Need for Speed (Limits)
So far, our planning has been based purely on distance, but oftentimes, when planning a route between two locations, we are actually interested in the amount of time it will take to move from one location to another.

For the last part of this lab, you should implement `find_fast_path`, which, unlike `find_short_path`, should take into account speed limits (we're responsible citizens of the world, so we won't drive over the speed limit).

Some ways in the dataset store information about the speed limit along that way. That said, unfortunately, speed-limit information is somewhat sparse in OSM data (at least in these datasets), and so we'll have to guess a little bit for some of the roads. We have done a little bit of preprocessing of the data for you, to make extracting this information a little bit easier than it would otherwise be.

For each way, we'll determine the speed limit as follows:
* if the way has the `'maxspeed_mph'` tag, the corresponding value (an integer) represents the speed limit in miles per hour
* if that tag does not exist, look up the way's `'highway'` type in the `DEFAULT_SPEED_LIMIT_MPH` dictionary and use the corresponding value.

If the two nodes are connected by more than one way with distinct speed limits, you should always prefer higher of the two speed limits.

