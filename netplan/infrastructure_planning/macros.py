import csv
import geometryIO
import hashlib
import inspect
import json
import shutil
from collections import OrderedDict
from invisibleroads_macros.calculator import divide_safely
from invisibleroads_macros.configuration import TerseArgumentParser
from invisibleroads_macros.disk import (
    make_enumerated_folder_for, make_folder, remove_safely,
    replace_file_extension)
from invisibleroads_macros.iterable import merge_dictionaries, sort_dictionary
from invisibleroads_macros.table import normalize_key
from networkx import Graph
from os.path import isabs, join, splitext
from osgeo.ogr import OFTInteger, OFTReal, OFTString
from pandas import DataFrame, Series, isnull
from shapely import wkt
from shapely.geometry import Point

from .exceptions import (
    ExpectedPositive, InfrastructurePlanningError, ValidationError)
from .parsers import load_files


class BasicArgumentParser(TerseArgumentParser):

    def __init__(self, *args, **kw):
        super(BasicArgumentParser, self).__init__(*args, **kw)
        self.add_argument(
            'configuration_path', metavar='CONFIGURATION_PATH', nargs='?')
        self.add_argument('-w', '--source_folder', metavar='FOLDER')
        self.add_argument('-o', '--target_folder', metavar='FOLDER')


class InfrastructureGraph(Graph):

    def cycle_nodes(self):
        for node_id, node_d in self.nodes(data=True):
            if 'name' not in node_d:
                continue  # We have a fake node
            yield node_id, node_d

    def cycle_edges(self):
        for node1_id, node2_id, edge_d in self.edges_iter(data=True):
            yield node1_id, node2_id, edge_d


def load_and_run(
        normalization_functions, main_functions, arguments, keys):
    g = load_arguments(arguments)
    save_arguments(g, __file__, keys)
    try:
        g = load_files(g)
        g = normalize_arguments(normalization_functions, g)
        run(main_functions, g)
    except InfrastructurePlanningError as e:
        exit(e)


def load_arguments(value_by_key):
    configuration_path = value_by_key.pop('configuration_path')
    source_folder = value_by_key.pop('source_folder')
    g = json.load(open(configuration_path)) if configuration_path else {}
    # Command-line arguments override configuration arguments
    for k, v in value_by_key.items():
        if v is None:
            continue
        g[k] = v
    # Resolve relative paths using source_folder
    if source_folder:
        for k, v in g.items():
            if k.endswith('_path') and v and not isabs(v):
                g[k] = join(source_folder, v)
    return g


def save_arguments(g, script_path, keys):
    d = g.copy()
    target_folder = d.pop('target_folder')
    if not target_folder:
        target_folder = make_enumerated_folder_for(script_path)
    arguments_folder = make_folder(join(target_folder, 'arguments'))
    # Migrate paths
    path_by_key = OrderedDict()
    for k, v in d.items():
        if not k.endswith('_path'):
            continue
        file_name = _get_argument_file_name(k, v)
        # Save a copy of each file
        shutil.copy(v, join(arguments_folder, file_name))
        # Make the reference point to the local copy
        path_by_key[k] = file_name
    d = sort_dictionary(d, keys)
    d.update(path_by_key)
    # Save global arguments as JSON
    target_file = open(join(arguments_folder, 'arguments.json'), 'w')
    json.dump(d, target_file, indent=4, separators=(',', ': '))
    # Save global arguments as CSV
    target_file = open(join(arguments_folder, 'arguments.csv'), 'w')
    csv_writer = csv.writer(target_file)
    for x in d.items():
        csv_writer.writerow(x)


def normalize_arguments(normalization_functions, g):
    errors = []
    # Normalize columns
    for k, v in g.items():
        if not hasattr(v, 'columns'):
            continue
        v.columns = [normalize_key(x, '_') for x in v.columns]
    # Normalize tables
    for normalize_argument in normalization_functions:
        try:
            g.update(compute(normalize_argument, g))
        except ValidationError as e:
            errors.append(e)
    # Make decision
    if errors:
        raise InfrastructurePlanningError('could not normalize arguments')
    return g


def run(main_functions, g):
    g['infrastructure_graph'] = get_graph_from_table(g['demand_point_table'])
    for f in main_functions:
        if '_total_' in f.__name__:
            g.update(compute(f, g))
            continue
        for node_id, node_d in g['infrastructure_graph'].cycle_nodes():
            v = merge_dictionaries(node_d, {
                'node_id': node_id,
                'local_overrides': dict(g['demand_point_table'].loc[node_id])})
            node_d.update(compute(f, v, g))
    return g


def save_shapefile(target_path, geotable):
    if 'wkt' in geotable:
        # Shapefiles expect (x, y) or (longitude, latitude) coordinate order
        geometries = [wkt.loads(x) for x in geotable['wkt']]
    else:
        xys = geotable[['longitude', 'latitude']].values
        geometries = [Point(xy) for xy in xys]
    # Collect name_packs
    name_packs = []
    for index, row in geotable.iterrows():
        for column_name, column_value in row.iteritems():
            if column_name in ('wkt', 'longitude', 'latitude'):
                continue
            if isinstance(column_value, float):
                column_type = OFTReal
            elif isinstance(column_value, int):
                column_type = OFTInteger
            elif hasattr(column_value, 'strip'):
                column_type = OFTString
            else:
                continue
            name_packs.append((column_name, column_type))
        break
    # Collect field_packs
    field_packs = []
    for index, row in geotable.iterrows():
        field_packs.append(tuple(row[x] for x, _ in name_packs))
    # Set field_definitions
    field_definitions, field_name_by_column_name = [], {}
    for column_name, column_type in name_packs:
        field_name = get_field_name(column_name)
        field_name_by_column_name[column_name] = field_name
        field_definitions.append((field_name, column_type))
    # Save
    geometryIO.save(
        target_path, geometryIO.proj4LL, geometries, field_packs,
        field_definitions)
    if field_name_by_column_name:
        Series(field_name_by_column_name).to_csv(
            replace_file_extension(target_path, '-thesaurus.csv'))
    return target_path


def compute(f, l, g=None, prefix=''):
    'Compute the function using local arguments if possible'
    value_by_key = rename_keys(compute_raw(f, l, g) or {}, prefix=prefix)
    local_overrides = l.get('local_overrides', {})
    for key in local_overrides:
        local_value = local_overrides[key]
        if isnull(local_value):
            continue
        if key in value_by_key:
            value_by_key[key] = local_value
    return value_by_key


def compute_raw(f, l, g=None):
    if not g:
        g = {}
    # If the function wants every argument, provide every argument
    argument_specification = inspect.getfullargspec(f)
    if argument_specification.varkw:
        return f(**merge_dictionaries(g, l))
    # Otherwise, provide only requested arguments
    keywords = {}
    for argument_name in argument_specification.args:
        argument_value = l.get(argument_name, g.get(argument_name))
        if argument_value is None:
            raise ValidationError(argument_name, 'required')
        keywords[argument_name] = argument_value
    return f(**keywords)


def sum_by_suffix(value_by_key, suffix):
    x = 0
    for k, v in value_by_key.items():
        if k.endswith(suffix):
            x += v
    return x


def get_by_prefix(value_by_key, prefix):
    for key in value_by_key:
        if key.startswith(prefix):
            return value_by_key[key]


def get_first_value(value_by_year):
    return value_by_year.loc[sorted(value_by_year.index)[0]]


def get_final_value(value_by_year):
    return value_by_year.loc[sorted(value_by_year.index)[-1]]


def make_zero_by_year(value_by_year):
    return Series(0, index=value_by_year.index)


def get_graph_from_table(table):
    graph = InfrastructureGraph()
    for index, row in table.iterrows():
        graph.add_node(index, **dict(row))
    return graph


def get_table_from_graph(graph, keys=None):
    index, rows = zip(*graph.cycle_nodes())
    if keys:
        rows = ({k: d[k] for k in keys} for d in rows)
    return DataFrame(rows, index=index)


def get_table_from_variables(ls, g, keys):
    rows = [[l.get(x, g.get(x, '')) for x in keys] for l in ls]
    return DataFrame(rows, columns=keys).set_index('name')


def interpolate_values(source_table, source_column, target_value):
    t = source_table
    source_values = t[source_column]
    minimum_source_value = source_values.min()
    maximum_source_value = source_values.max()
    message_template = 'source_column (%s) values must be %%s' % source_column
    assert len(t) > 0, 'table must have at least one row'
    assert len(t) == len(set(source_values)), message_template % 'unique'
    assert minimum_source_value >= 0, message_template % 'positive'
    if len(t) == 1:
        return t.loc[t.index[0]]
    if target_value <= minimum_source_value:
        return t.loc[source_values.idxmin()]
    if target_value >= maximum_source_value:
        return t.loc[source_values.idxmax()]
    # Get two rows nearest to target value
    sorted_indices = (source_values - target_value).abs().argsort()
    row0 = t.loc[sorted_indices[0]]
    row1 = t.loc[sorted_indices[1]]
    # Compute fraction of interpolation
    fraction = divide_safely(
        target_value - row0[source_column],
        row1[source_column] - row0[source_column],
        ExpectedPositive(message_template % 'unique and positive'))
    # Interpolate
    return row0 + (row1 - row0) * fraction


def rename_keys(value_by_key, prefix='', suffix=''):
    d = {}
    for key, value in value_by_key.items():
        if prefix and not key.startswith(prefix):
            key = prefix + key
        if suffix and not key.endswith(suffix):
            key = key + suffix
        d[key] = value
    return d


def get_field_name(column_name):
    abbreviation = ''.join(x[0] for x in column_name.split('_'))[:5]
    column_name_hash = hashlib.md5(column_name).hexdigest()
    return '%s%s' % (abbreviation, column_name_hash[:10 - len(abbreviation)])


def wash_total_folder(target_folder):
    drafts_folder = join(target_folder, 'drafts')
    remove_safely(drafts_folder)
    remove_safely(drafts_folder + '.prj')


def save_total_graph(target_folder, infrastructure_graph):
    write_gpickle(infrastructure_graph, join(
        target_folder, 'infrastructure-graph.pkl'))


def _get_argument_file_name(k, v):
    file_base = k
    file_base = file_base.replace('_path', '')
    file_extension = splitext(v)[1]
    return file_base.replace('_', '-') + file_extension
