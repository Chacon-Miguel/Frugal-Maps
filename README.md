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
