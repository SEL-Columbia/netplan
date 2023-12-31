from invisibleroads_macros.disk import make_folder
from os.path import join
from pandas import DataFrame, Series, concat
from shapely.geometry import LineString, Point

from ..macros import get_table_from_variables, save_shapefile


BASE_KEYS = """\
name
latitude
longitude
population
""".strip().splitlines()


FULL_KEYS = """\
proposed_technology
proposed_cost_per_connection
financing_year
time_horizon_in_years
discount_rate_as_percent_of_cash_flow_per_year
population_year
population_growth_as_percent_of_population_per_year
line_length_adjustment_factor
average_distance_between_buildings_in_meters
peak_hours_of_sun_per_year
number_of_people_per_household
final_population
final_connection_count
consumption_during_peak_hours_as_percent_of_total_consumption
peak_hours_of_consumption_per_year
peak_demand_in_kw
final_consumption_in_kwh_per_year
discounted_consumption_in_kwh
grid_electricity_production_cost_per_kwh
grid_system_loss_as_percent_of_total_production
grid_mv_network_minimum_point_count
grid_mv_network_connection_order
grid_mv_line_raw_cost_per_meter
grid_mv_line_raw_cost
grid_mv_line_installation_cost_as_percent_of_raw_cost
grid_mv_line_installation_cost_per_meter
grid_mv_line_installation_cost
grid_mv_line_maintenance_cost_per_year_as_percent_of_raw_cost
grid_mv_line_maintenance_cost_per_meter_per_year
grid_mv_line_maintenance_cost_per_year
grid_mv_line_lifetime_in_years
grid_mv_line_replacement_cost_per_meter_per_year
grid_mv_line_replacement_cost_per_year
grid_mv_line_final_cost_per_meter_per_year
grid_mv_line_final_cost_per_year
grid_mv_line_discounted_cost_per_meter
grid_mv_line_discounted_cost
grid_mv_line_adjusted_length_in_meters
grid_mv_line_adjusted_budget_in_meters
grid_mv_transformer_load_power_factor
grid_mv_transformer_actual_system_capacity_in_kva
grid_mv_transformer_raw_cost
grid_mv_transformer_installation_cost
grid_mv_transformer_maintenance_cost_per_year
grid_mv_transformer_replacement_cost_per_year
grid_lv_line_raw_cost_per_meter
grid_lv_line_raw_cost
grid_lv_line_installation_cost_as_percent_of_raw_cost
grid_lv_line_installation_cost
grid_lv_line_maintenance_cost_per_year_as_percent_of_raw_cost
grid_lv_line_maintenance_cost_per_year
grid_lv_line_lifetime_in_years
grid_lv_line_replacement_cost_per_year
grid_lv_connection_raw_cost
grid_lv_connection_installation_cost_as_percent_of_raw_cost
grid_lv_connection_installation_cost
grid_lv_connection_maintenance_cost_per_year_as_percent_of_raw_cost
grid_lv_connection_maintenance_cost_per_year
grid_lv_connection_lifetime_in_years
grid_lv_connection_replacement_cost_per_year
grid_final_system_capacity_cost_per_year
grid_final_electricity_production_in_kwh_per_year
grid_final_electricity_production_cost_per_year
grid_final_internal_distribution_cost_per_year
grid_final_external_distribution_cost_per_year
grid_internal_initial_cost
grid_internal_recurring_fixed_cost_per_year
grid_internal_recurring_variable_cost_per_year
grid_internal_discounted_cost
grid_internal_levelized_cost_per_kwh_consumed
grid_external_initial_cost
grid_external_recurring_fixed_cost_per_year
grid_external_recurring_variable_cost_per_year
grid_external_discounted_cost
grid_external_levelized_cost_per_kwh_consumed
grid_local_initial_cost
grid_local_recurring_fixed_cost_per_year
grid_local_recurring_variable_cost_per_year
grid_local_discounted_cost
grid_local_levelized_cost_per_kwh_consumed
diesel_mini_grid_system_loss_as_percent_of_total_production
diesel_mini_grid_fuel_cost_per_liter
diesel_mini_grid_generator_minimum_hours_of_production_per_year
diesel_mini_grid_generator_fuel_liters_consumed_per_kwh
diesel_mini_grid_generator_actual_system_capacity_in_kw
diesel_mini_grid_generator_raw_cost
diesel_mini_grid_generator_installation_cost
diesel_mini_grid_generator_maintenance_cost_per_year
diesel_mini_grid_generator_replacement_cost_per_year
diesel_mini_grid_lv_line_raw_cost_per_meter
diesel_mini_grid_lv_line_raw_cost
diesel_mini_grid_lv_line_installation_cost_as_percent_of_raw_cost
diesel_mini_grid_lv_line_installation_cost
diesel_mini_grid_lv_line_maintenance_cost_per_year_as_percent_of_raw_cost
diesel_mini_grid_lv_line_maintenance_cost_per_year
diesel_mini_grid_lv_line_lifetime_in_years
diesel_mini_grid_lv_line_replacement_cost_per_year
diesel_mini_grid_lv_connection_raw_cost
diesel_mini_grid_lv_connection_installation_cost_as_percent_of_raw_cost
diesel_mini_grid_lv_connection_installation_cost
diesel_mini_grid_lv_connection_maintenance_cost_per_year_as_percent_of_raw_cost
diesel_mini_grid_lv_connection_maintenance_cost_per_year
diesel_mini_grid_lv_connection_lifetime_in_years
diesel_mini_grid_lv_connection_replacement_cost_per_year
diesel_mini_grid_final_system_capacity_cost_per_year
diesel_mini_grid_final_hours_of_production_per_year
diesel_mini_grid_final_fuel_cost_per_year
diesel_mini_grid_final_electricity_production_in_kwh_per_year
diesel_mini_grid_final_electricity_production_cost_per_year
diesel_mini_grid_final_internal_distribution_cost_per_year
diesel_mini_grid_final_external_distribution_cost_per_year
diesel_mini_grid_internal_initial_cost
diesel_mini_grid_internal_recurring_fixed_cost_per_year
diesel_mini_grid_internal_recurring_variable_cost_per_year
diesel_mini_grid_internal_discounted_cost
diesel_mini_grid_internal_levelized_cost_per_kwh_consumed
diesel_mini_grid_external_initial_cost
diesel_mini_grid_external_recurring_fixed_cost_per_year
diesel_mini_grid_external_recurring_variable_cost_per_year
diesel_mini_grid_external_discounted_cost
diesel_mini_grid_external_levelized_cost_per_kwh_consumed
diesel_mini_grid_local_initial_cost
diesel_mini_grid_local_recurring_fixed_cost_per_year
diesel_mini_grid_local_recurring_variable_cost_per_year
diesel_mini_grid_local_discounted_cost
diesel_mini_grid_local_levelized_cost_per_kwh_consumed
solar_home_system_loss_as_percent_of_total_production
solar_home_panel_actual_system_capacity_in_kw
solar_home_panel_raw_cost
solar_home_panel_installation_cost
solar_home_panel_maintenance_cost_per_year
solar_home_panel_replacement_cost_per_year
solar_home_battery_kwh_per_panel_kw
solar_home_battery_storage_in_kwh
solar_home_battery_raw_cost_per_battery_kwh
solar_home_battery_raw_cost
solar_home_battery_installation_cost_as_percent_of_raw_cost
solar_home_battery_installation_cost
solar_home_battery_maintenance_cost_per_year_as_percent_of_raw_cost
solar_home_battery_maintenance_cost_per_year
solar_home_battery_lifetime_in_years
solar_home_battery_replacement_cost_per_year
solar_home_balance_raw_cost_per_panel_kw
solar_home_balance_raw_cost
solar_home_balance_installation_cost_as_percent_of_raw_cost
solar_home_balance_installation_cost
solar_home_balance_maintenance_cost_per_year_as_percent_of_raw_cost
solar_home_balance_maintenance_cost_per_year
solar_home_balance_lifetime_in_years
solar_home_balance_replacement_cost_per_year
solar_home_final_system_capacity_cost_per_year
solar_home_final_electricity_production_in_kwh_per_year
solar_home_final_electricity_production_cost_per_year
solar_home_final_internal_distribution_cost_per_year
solar_home_final_external_distribution_cost_per_year
solar_home_internal_initial_cost
solar_home_internal_recurring_fixed_cost_per_year
solar_home_internal_recurring_variable_cost_per_year
solar_home_internal_discounted_cost
solar_home_internal_levelized_cost_per_kwh_consumed
solar_home_external_initial_cost
solar_home_external_recurring_fixed_cost_per_year
solar_home_external_recurring_variable_cost_per_year
solar_home_external_discounted_cost
solar_home_external_levelized_cost_per_kwh_consumed
solar_home_local_initial_cost
solar_home_local_recurring_fixed_cost_per_year
solar_home_local_recurring_variable_cost_per_year
solar_home_local_discounted_cost
solar_home_local_levelized_cost_per_kwh_consumed
solar_mini_grid_system_loss_as_percent_of_total_production
solar_mini_grid_panel_actual_system_capacity_in_kw
solar_mini_grid_panel_raw_cost
solar_mini_grid_panel_installation_cost
solar_mini_grid_panel_maintenance_cost_per_year
solar_mini_grid_panel_replacement_cost_per_year
solar_mini_grid_battery_kwh_per_panel_kw
solar_mini_grid_battery_storage_in_kwh
solar_mini_grid_battery_raw_cost_per_battery_kwh
solar_mini_grid_battery_raw_cost
solar_mini_grid_battery_installation_cost_as_percent_of_raw_cost
solar_mini_grid_battery_installation_cost
solar_mini_grid_battery_maintenance_cost_per_year_as_percent_of_raw_cost
solar_mini_grid_battery_maintenance_cost_per_year
solar_mini_grid_battery_lifetime_in_years
solar_mini_grid_battery_replacement_cost_per_year
solar_mini_grid_balance_raw_cost_per_panel_kw
solar_mini_grid_balance_raw_cost
solar_mini_grid_balance_installation_cost_as_percent_of_raw_cost
solar_mini_grid_balance_installation_cost
solar_mini_grid_balance_maintenance_cost_per_year_as_percent_of_raw_cost
solar_mini_grid_balance_maintenance_cost_per_year
solar_mini_grid_balance_lifetime_in_years
solar_mini_grid_balance_replacement_cost_per_year
solar_mini_grid_lv_line_raw_cost_per_meter
solar_mini_grid_lv_line_raw_cost
solar_mini_grid_lv_line_installation_cost_as_percent_of_raw_cost
solar_mini_grid_lv_line_installation_cost
solar_mini_grid_lv_line_maintenance_cost_per_year_as_percent_of_raw_cost
solar_mini_grid_lv_line_maintenance_cost_per_year
solar_mini_grid_lv_line_lifetime_in_years
solar_mini_grid_lv_line_replacement_cost_per_year
solar_mini_grid_lv_connection_raw_cost
solar_mini_grid_lv_connection_installation_cost_as_percent_of_raw_cost
solar_mini_grid_lv_connection_installation_cost
solar_mini_grid_lv_connection_maintenance_cost_per_year_as_percent_of_raw_cost
solar_mini_grid_lv_connection_maintenance_cost_per_year
solar_mini_grid_lv_connection_lifetime_in_years
solar_mini_grid_lv_connection_replacement_cost_per_year
solar_mini_grid_final_system_capacity_cost_per_year
solar_mini_grid_final_electricity_production_in_kwh_per_year
solar_mini_grid_final_electricity_production_cost_per_year
solar_mini_grid_final_internal_distribution_cost_per_year
solar_mini_grid_final_external_distribution_cost_per_year
solar_mini_grid_internal_initial_cost
solar_mini_grid_internal_recurring_fixed_cost_per_year
solar_mini_grid_internal_recurring_variable_cost_per_year
solar_mini_grid_internal_discounted_cost
solar_mini_grid_internal_levelized_cost_per_kwh_consumed
solar_mini_grid_external_initial_cost
solar_mini_grid_external_recurring_fixed_cost_per_year
solar_mini_grid_external_recurring_variable_cost_per_year
solar_mini_grid_external_discounted_cost
solar_mini_grid_external_levelized_cost_per_kwh_consumed
solar_mini_grid_local_initial_cost
solar_mini_grid_local_recurring_fixed_cost_per_year
solar_mini_grid_local_recurring_variable_cost_per_year
solar_mini_grid_local_discounted_cost
solar_mini_grid_local_levelized_cost_per_kwh_consumed
""".strip().splitlines()


SOME_KEYS = """\
final_population
final_connection_count
final_consumption_in_kwh_per_year
peak_demand_in_kw
proposed_technology
proposed_cost_per_connection
grid_mv_network_connection_order

grid_local_levelized_cost_per_kwh_consumed
diesel_mini_grid_local_levelized_cost_per_kwh_consumed
solar_home_local_levelized_cost_per_kwh_consumed
solar_mini_grid_local_levelized_cost_per_kwh_consumed

grid_local_initial_cost
diesel_mini_grid_local_initial_cost
solar_home_local_initial_cost
solar_mini_grid_local_initial_cost

grid_local_recurring_fixed_cost_per_year
diesel_mini_grid_local_recurring_fixed_cost_per_year
solar_home_local_recurring_fixed_cost_per_year
solar_mini_grid_local_recurring_fixed_cost_per_year

grid_local_recurring_variable_cost_per_year
diesel_mini_grid_local_recurring_variable_cost_per_year
solar_home_local_recurring_variable_cost_per_year
solar_mini_grid_local_recurring_variable_cost_per_year

grid_local_discounted_cost
diesel_mini_grid_local_discounted_cost
solar_home_local_discounted_cost
solar_mini_grid_local_discounted_cost

grid_external_discounted_cost
grid_mv_line_adjusted_budget_in_meters
grid_mv_line_adjusted_length_in_meters
grid_internal_discounted_cost
grid_mv_transformer_actual_system_capacity_in_kva
grid_mv_transformer_raw_cost
grid_mv_transformer_installation_cost
grid_mv_transformer_maintenance_cost_per_year
grid_mv_transformer_replacement_cost_per_year
grid_lv_connection_raw_cost
grid_lv_connection_installation_cost
grid_lv_connection_maintenance_cost_per_year
grid_lv_connection_replacement_cost_per_year
grid_lv_line_raw_cost
grid_lv_line_installation_cost
grid_lv_line_maintenance_cost_per_year
grid_lv_line_replacement_cost_per_year

diesel_mini_grid_external_discounted_cost
diesel_mini_grid_internal_discounted_cost
diesel_mini_grid_generator_actual_system_capacity_in_kw
diesel_mini_grid_lv_connection_raw_cost
diesel_mini_grid_lv_connection_installation_cost
diesel_mini_grid_lv_connection_maintenance_cost_per_year
diesel_mini_grid_lv_connection_replacement_cost_per_year
diesel_mini_grid_lv_line_raw_cost
diesel_mini_grid_lv_line_installation_cost
diesel_mini_grid_lv_line_maintenance_cost_per_year
diesel_mini_grid_lv_line_replacement_cost_per_year

solar_home_external_discounted_cost
solar_home_internal_discounted_cost
solar_home_panel_actual_system_capacity_in_kw
solar_home_panel_raw_cost
solar_home_panel_installation_cost
solar_home_panel_maintenance_cost_per_year
solar_home_panel_replacement_cost_per_year
solar_home_balance_raw_cost
solar_home_balance_installation_cost
solar_home_balance_maintenance_cost_per_year
solar_home_balance_replacement_cost_per_year
solar_home_battery_raw_cost
solar_home_battery_installation_cost
solar_home_battery_maintenance_cost_per_year
solar_home_battery_replacement_cost_per_year

solar_mini_grid_external_discounted_cost
solar_mini_grid_internal_discounted_cost
solar_mini_grid_panel_actual_system_capacity_in_kw
solar_mini_grid_panel_raw_cost
solar_mini_grid_panel_installation_cost
solar_mini_grid_panel_maintenance_cost_per_year
solar_mini_grid_panel_replacement_cost_per_year
solar_mini_grid_balance_raw_cost
solar_mini_grid_balance_installation_cost
solar_mini_grid_balance_maintenance_cost_per_year
solar_mini_grid_balance_replacement_cost_per_year
solar_mini_grid_battery_raw_cost
solar_mini_grid_battery_installation_cost
solar_mini_grid_battery_maintenance_cost_per_year
solar_mini_grid_battery_replacement_cost_per_year
solar_mini_grid_lv_connection_raw_cost
solar_mini_grid_lv_connection_installation_cost
solar_mini_grid_lv_connection_maintenance_cost_per_year
solar_mini_grid_lv_connection_replacement_cost_per_year
solar_mini_grid_lv_line_raw_cost
solar_mini_grid_lv_line_installation_cost
solar_mini_grid_lv_line_maintenance_cost_per_year
solar_mini_grid_lv_line_replacement_cost_per_year
""".strip().splitlines()


def save_total_points(
        target_folder, infrastructure_graph, demand_point_table, **keywords):
    ls = [node_d for node_id, node_d in infrastructure_graph.cycle_nodes()]
    g = keywords
    properties_folder = make_folder(join(target_folder, 'properties'))
    reports_folder = make_folder(join(target_folder, 'reports'))

    # Preserve columns and column order from demand_point_table
    keys = BASE_KEYS + [
        x for x in demand_point_table.columns if x not in BASE_KEYS + FULL_KEYS
    ] + FULL_KEYS
    # Include miscellaneous variables
    miscellaneous_keys = _get_miscellaneous_keys(ls, g, keys)
    # Save properties/points.csv
    t = get_table_from_variables(ls, g, keys=keys + miscellaneous_keys)
    t_path = join(properties_folder, 'points.csv')
    t.to_csv(t_path)
    # Save properties/points.shp.zip
    save_shapefile(join(properties_folder, 'points.shp.zip'), t)
    # Save reports/examples-by-technology.csv
    table = t.reset_index().groupby(
        'proposed_technology').first().reset_index()
    table.columns = [format_column_name(x) for x in table.columns]
    table_path = join(reports_folder, 'example-by-technology.csv')
    table.transpose().to_csv(table_path, header=False)


def save_total_lines(
        target_folder, infrastructure_graph, grid_mv_line_geotable):
    rows = []
    for node1_id, node2_id, edge_d in infrastructure_graph.cycle_edges():
        node1_d = infrastructure_graph.node[node1_id]
        node2_d = infrastructure_graph.node[node2_id]
        edge_order = edge_d['grid_mv_network_connection_order']
        line_length = edge_d['grid_mv_line_adjusted_length_in_meters']
        discounted_cost = edge_d['grid_mv_line_discounted_cost']

        node1_d, node2_d = order_nodes(node1_d, node2_d, edge_order)
        wkt = LineString([(
            node1_d['longitude'], node1_d['latitude'],
        ), (
            node2_d['longitude'], node2_d['latitude'],
        )]).wkt
        rows.append([line_length, discounted_cost, edge_order, wkt])
    properties_folder = make_folder(join(target_folder, 'properties'))
    # Save CSV
    t = DataFrame(rows, columns=[
        'grid_mv_line_adjusted_length_in_meters',
        'grid_mv_line_discounted_cost',
        'grid_mv_network_connection_order',
        'wkt',
    ]).sort_values('grid_mv_network_connection_order')
    t_path = join(properties_folder, 'lines.csv')
    t.to_csv(t_path, index=False)
    # Save SHP
    save_shapefile(join(
        properties_folder, 'lines-proposed.shp.zip'), t)
    save_shapefile(join(
        properties_folder, 'lines-existing.shp.zip'), grid_mv_line_geotable)


def save_total_report_by_location(
        target_folder, infrastructure_graph, demand_point_table, **keywords):
    ls = [node_d for node_id, node_d in infrastructure_graph.cycle_nodes()]
    g = keywords
    reports_folder = make_folder(join(target_folder, 'reports'))

    t = get_table_from_variables(ls, g, keys=BASE_KEYS + [
        x for x in demand_point_table.columns if x not in BASE_KEYS + SOME_KEYS
    ] + SOME_KEYS)
    t.columns = [format_column_name(x) for x in t.columns]
    t_path = join(reports_folder, 'report-by-location.csv')
    t.to_csv(t_path)


def save_total_summary_by_technology(
        target_folder, discounted_cost_by_technology,
        levelized_cost_by_technology, count_by_technology):
    t = concat([
        Series(discounted_cost_by_technology),
        Series(levelized_cost_by_technology),
        Series(count_by_technology),
    ], sort=True, axis=1)
    t.index.name = 'Technology'
    t.index = [format_technology(x) for x in t.index]
    t.columns = [
        'Discounted Cost',
        'Levelized Cost Per kWh Consumed',
        'Count',
    ]

    reports_folder = make_folder(join(target_folder, 'reports'))
    t_path = join(reports_folder, 'summary-by-technology.csv')
    t.to_csv(t_path)
    print('summary_by_technology_table_path = %s' % t_path)


def save_total_summary_by_location(
        target_folder, infrastructure_graph, selected_technologies):
    rows = []
    for node_id, node_d in infrastructure_graph.cycle_nodes():
        xs = [
            node_d['name'],
            node_d.get('grid_mv_network_connection_order', '')]
        xs.extend(node_d[
            x + '_local_levelized_cost_per_kwh_consumed'
        ] for x in selected_technologies)
        xs.append(format_technology(node_d['proposed_technology']))
        rows.append(xs)
    t = DataFrame(rows, columns=[
        'Name',
        'Proposed MV Network Connection Order',
    ] + [format_technology(x) for x in selected_technologies] + [
        'Proposed Technology',
    ]).sort_values('Proposed MV Network Connection Order')

    reports_folder = make_folder(join(target_folder, 'reports'))
    t_path = join(reports_folder, 'summary-by-location.csv')
    t.to_csv(t_path, index=False)
    print('summary_by_location_table_path = %s' % t_path)


def save_total_summary_by_grid_mv_line(target_folder, infrastructure_graph):
    rows = []
    for node1_id, node2_id, edge_d in infrastructure_graph.cycle_edges():
        node1_d = infrastructure_graph.node[node1_id]
        node2_d = infrastructure_graph.node[node2_id]
        edge_order = edge_d['grid_mv_network_connection_order']
        line_length = edge_d['grid_mv_line_adjusted_length_in_meters']
        discounted_cost = edge_d['grid_mv_line_discounted_cost']

        node1_d, node2_d = order_nodes(node1_d, node2_d, edge_order)
        name = 'From %s to %s' % (
            node1_d.get('name', 'the grid'),
            node2_d.get('name', 'the grid'))
        rows.append([name, line_length, discounted_cost, edge_order])
    t = DataFrame(rows, columns=[
        'Name',
        'Length (m)',
        'Discounted Cost',
        'Proposed MV Network Connection Order',
    ]).sort_values('Proposed MV Network Connection Order')

    reports_folder = make_folder(join(target_folder, 'reports'))
    t_path = join(reports_folder, 'summary-by-grid-mv-line.csv')
    t.to_csv(t_path, index=False)
    print('summary_by_grid_mv_line_table_path = %s' % t_path)


def save_total_map(
        target_folder, infrastructure_graph, selected_technologies,
        grid_mv_line_geotable):
    graph = infrastructure_graph
    colors = 'bgrcmykw'
    color_by_technology = {x: colors[i] for i, x in enumerate([
        'unelectrified'] + selected_technologies)}
    columns = [
        'Name',
        'Peak Demand (kW)',
        'Proposed Technology',
        'Proposed MV Network Connection Order',
        'Proposed MV Line Length (m)',
        'Levelized Cost Per kWh Consumed',
        'WKT',
        'FillColor',
        'RadiusInPixelsRange5-10',
    ]
    rows = []
    for node_id, node_d in graph.cycle_nodes():
        longitude, latitude = node_d['longitude'], node_d['latitude']
        technology = node_d['proposed_technology']
        levelized_cost = node_d.get(
            technology + '_local_levelized_cost_per_kwh_consumed', 0)
        rows.append({
            'Name': node_d['name'],
            'Peak Demand (kW)': node_d['peak_demand_in_kw'],
            'Proposed Technology': format_technology(technology),
            'Proposed MV Network Connection Order':
                node_d.get('grid_mv_network_connection_order', ''),
            'Proposed MV Line Length (m)': node_d.get(
                'grid_mv_line_adjusted_length_in_meters'),
            'Levelized Cost Per kWh Consumed': levelized_cost,
            'WKT': Point(longitude, latitude).wkt,
            'FillColor': color_by_technology[technology],
            'RadiusInPixelsRange5-10': node_d['peak_demand_in_kw'],
        })
    for node1_id, node2_id, edge_d in graph.edges_iter(data=True):
        node1_d, node2_d = graph.node[node1_id], graph.node[node2_id]
        edge_order = edge_d['grid_mv_network_connection_order']

        node1_d, node2_d = order_nodes(node1_d, node2_d, edge_order)
        name = 'From %s to %s' % (
            node1_d.get('name', 'the grid'),
            node2_d.get('name', 'the grid'))
        peak_demand = max(
            node1_d['peak_demand_in_kw'],
            node2_d['peak_demand_in_kw'])
        line_length = edge_d['grid_mv_line_adjusted_length_in_meters']
        geometry_wkt = LineString([
            (node1_d['longitude'], node1_d['latitude']),
            (node2_d['longitude'], node2_d['latitude'])]).wkt
        rows.append({
            'Name': name,
            'Peak Demand (kW)': peak_demand,
            'Proposed Technology': 'Grid',
            'Proposed MV Network Connection Order': edge_order,
            'Proposed MV Line Length (m)': line_length,
            'WKT': geometry_wkt,
            'FillColor': color_by_technology['grid'],
        })
    for geometry_wkt in grid_mv_line_geotable['wkt']:
        rows.append({
            'Name': '(Existing MV Line)',
            'Proposed Technology': 'grid',
            'WKT': geometry_wkt,
            'FillColor': color_by_technology['grid'],
        })
    target_path = join(target_folder, 'infrastructure-map.csv')
    DataFrame(rows)[columns].to_csv(target_path, index=False)
    print('infrastructure_streets_satellite_geotable_path = %s' % target_path)


def format_column_name(x):
    x = x.replace('_', ' ')
    # Encourage spreadsheet programs to include empty columns when sorting rows
    return x or '-'


def format_technology(x):
    x = x.replace('_', ' ')
    return x.title()


def order_nodes(node1_d, node2_d, edge_order):
    if node2_d.get('grid_mv_network_connection_order') == edge_order:
        return node2_d, node1_d
    return node1_d, node2_d


def _get_miscellaneous_keys(ls, g, keys):
    miscellaneous_keys = []
    d = {}
    d.update(g)
    for l in ls:
        d.update(l)
    for k, v in d.items():
        if k in keys:
            continue
        if k in miscellaneous_keys:
            continue
        if k.endswith('_path'):
            continue
        if isinstance(v, Series) or isinstance(v, DataFrame):
            continue
        if isinstance(v, list) or isinstance(v, dict):
            continue
        miscellaneous_keys.append(k)
    return sorted(miscellaneous_keys)
