import os


# Reads the expsift_tags file for a given experiment directory and searches the
# value for a particular property.
# Returns None if the property could not be found in the tags file.
def readDirTagFileProperty(directory, prop_name):
    res = None
    if (os.path.exists(os.path.join(directory, 'expsift_tags'))):
        tags_file = open(os.path.join(directory, 'expsift_tags'), 'r')
        for line in tags_file:
            # Ignore Comment lines
            if line[0] == '#':
                continue
            prop_val_str = line.strip()
            line = prop_val_str.split('=', 1)
            if not len(line) == 2:
                continue
            if line[0] == prop_name:
                res = line[1]
                tags_file.close()
                return res
        tags_file.close()
    return res


# Reads the expsift_tags file for a given experiment directory and returns a set
# of prop=val strings for the directory.
def readDirTagFile(directory):
    res = set()
    if (os.path.exists(os.path.join(directory, 'expsift_tags'))):
        tags_file = open(os.path.join(directory, 'expsift_tags'), 'r')
        for line in tags_file:
            # Comment lines
            if line[0] == '#':
                continue
            prop_val_str = line.strip()
            line = prop_val_str.split('=', 1)
            if not len(line) == 2:
                continue
            res.add(prop_val_str)
        tags_file.close()
    return res


# Takes a list of directories and returns a dictionary of properties for each
# directory.
# The return dictionary is keyed by directory name and each value is a set of
# prop=val strings for the directory.
def getDir2PropsDict(directories):
    res_props = {}
    for dir in directories:
        props = readDirTagFile(dir)
        res_props[dir] = props
    return res_props


# Returns a (property name, value) tuple from a prop=val string
def propAndVal(prop_val_str):
    line = prop_val_str.split('=', 1)
    assert(len(line) == 2)
    return line


# Returns the property name alone from a prop=val string
def propName(prop_val_str):
    return propAndVal(prop_val_str)[0]


# Takes a set of prop=val strings and returns a dictionary that maps each
# property to its value.
def getPropsDict(prop_vals = set()):
    res = {}
    for prop_val_str in prop_vals:
        prop,val = propAndVal(prop_val_str)
        res[prop] = val
    return res


# Takes a dictionary mapping each directory to a set of prop=val strings and
# returns a 2 level dictionary that maps directory to property name to value,
# ie. dir2prop2val_dict[directory][property] = value
def getDir2Prop2ValDict(dir2props_dict = {}):
    dir2prop2val_dict = {}
    for directory, prop_vals in dir2props_dict.iteritems():
        dir2prop2val_dict[directory] = getPropsDict(prop_vals)
    return dir2prop2val_dict


# Returns a frozen set with only the values corresponding to valid properties
# (those properties in the props2ignore list are ignored)
def removeIgnoredProps(dir_props, props2ignore):
    return frozenset(prop_val_str for prop_val_str in dir_props
                     if propName(prop_val_str) not in props2ignore)


# Returns a frozen set with only the values corresponding to property names
# specified in props2include. All other property values are ignored.
def onlyIncludeProps(dir_props, props2include):
    return frozenset(prop_val_str for prop_val_str in dir_props
                     if propName(prop_val_str) in props2include)


# Parameters:
# - dir2prop_dict: Dictionary that maps directories to the set of all properties
#                  for that directory.
# Returns:
# - common props: The set of common properties for all the directories
# - unique_props: Dictionary that maps directories to the unique properties for
#                 that directory
def getCommonAndUniqueProperties(dir2prop_dict):

    # Find the common and unique properties for all directories
    # If there is only one directory, then all the properties enter the
    # common_props set and the unique_props set becomes empty. So we just add
    # the term 'properties=all_common' to the unique_props set in that case.
    common_props = set.intersection(*(dir2prop_dict.values()))
    unique_props = {}
    for directory, props in dir2prop_dict.iteritems():
        unique = props - common_props
        if not unique:
            dir_shortname = directory[ directory.rfind('/') + 1 : ][ : 30]
            if len(directory) > len(dir_shortname):
                dir_shortname += '...'
            unique = set(['dir='+dir_shortname, 'properties=all_common'])
        unique_props[directory] = unique

    return common_props, unique_props


# This function computes groups of directories.
# If ignore = False:
#     All directories in a group have the same value for any property name
#     included in propnames (all other properties are ignored)
# If ignore = True:
#     All directories in a group have the same value for all properties except
#     for those included in propnames (which are ignored)
#
# The return value is a dictionary from frozensets to lists.
# The key (frozenset) is a set of prop_val strings that are unique to the
# group. It only includes properties included in propnames or ignores all those
# in propnames depending on ignore == True or False.
# Essentially each directory group is identified by a frozenset of prop_val
# strings unique to the group
#
# The value for each frozenset (or directory group) is a list of directories in
# the group
def getDirGroupsByProperty(dir2prop_dict, propnames = [], ignore = False):
    group_props2dir_dict = {} # Map from immutable set of group properties to
                              # the directories in the group

    for dir_current, current_props in dir2prop_dict.iteritems():
        if ignore:
            dir_valid_props = removeIgnoredProps(current_props, propnames)
        else:
            dir_valid_props = onlyIncludeProps(current_props, propnames)

        # Check if there is a group with the exact same set of properties
        if dir_valid_props in group_props2dir_dict:
            group_props2dir_dict[dir_valid_props].append(dir_current)
        else:
            group_props2dir_dict[dir_valid_props] = [dir_current]

    return group_props2dir_dict
