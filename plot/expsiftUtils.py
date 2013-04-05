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
