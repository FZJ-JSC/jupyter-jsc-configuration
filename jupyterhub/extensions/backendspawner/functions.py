import copy
import json
import os
import re

from jupyterhub.jupyterjsc.utils.maintenance import get_maintenance_list
from jupyterhub.jupyterjsc.utils.reservations import get_reservations
from jupyterhub.jupyterjsc.utils.resources import get_resources
from jupyterhub.jupyterjsc.utils.services import get_services
from jupyterhub.jupyterjsc.utils.systems import get_systems
from jupyterhub.jupyterjsc.utils.vo import get_vo_config

def get_system_infos(log, user_hpc_accounts, systems_config, reservations_list, resources):
    s = "^([^\,]+),([^\,]+),([^\,]+),([^\,]+)$"
    c = re.compile(s)

    map_systems_path = os.environ.get("MAP_SYSTEMS_PATH")
    map_partitions_path = os.environ.get("MAP_PARTITIONS_PATH")
    with open(map_systems_path, "r") as f:
        map_systems = json.load(f)
    with open(map_partitions_path, "r") as f:
        map_partitions = json.load(f)

    def get_system(full_partition):
        return map_systems.get(full_partition)

    def get_partition(full_partition):
        return map_partitions.get(full_partition)

    def regroup(x):
        groups_ = list(c.match(x).groups())
        sys = get_system(groups_[1])
        if not sys:
            log.error(
                f"No system defined in {map_systems_path} for {groups_[1]}"
            )
        partition = get_partition(groups_[1])
        if not partition:
            log.error(
                f"No system defined in {map_partitions_path} for {groups_[1]}"
            )
        groups = [
            groups_[0],
            get_system(groups_[1]),
            get_partition(groups_[1]),
            groups_[2].lower(),
            groups_[3],
        ]
        return groups

    user_hpc_list = [regroup(x) for x in user_hpc_accounts]

    systems = list(sorted(
        {
            group[1]
            for group in user_hpc_list
        }
    )) + list(systems_config.get("K8s", {}).keys())
    accounts = {
        system: sorted({group[0] for group in user_hpc_list if system == group[1]})
        for system in systems
    }
    projects = {
        system: {
            account: sorted(
                {
                    group[3]
                    for group in user_hpc_list
                    if system == group[1] and account == group[0]
                }
            )
            for account in accounts[system]
        }
        for system in systems
    }

    partitions = {
        system: {
            account: {
                project: systems_config.get("UNICORE", {}).get(system, {}).get("interactive_partitions",[]) + sorted(list(
                    {
                        group[2]
                        for group in user_hpc_list
                        if system == group[1]
                        and account == group[0]
                        and project == group[3]
                        and group[2] in resources.get(system, {}).keys()
                    })
                )
                for project in projects[system][account]
            }
            for account in accounts[system]
        }
        for system in systems
    }
    reservations = {
        system: {
            account: {
                project: {
                    partition: ["None"] + sorted(
                        [
                            x[0]
                            for x in reservations_list.get(system, [])
                            if (
                                (
                                    project in x[12].split(",")
                                    or account in x[11].split(",")
                                )
                                and ((not x[8]) or partition in x[8].split(","))
                            )
                        ]
                    )
                    for partition in partitions[system][account][project]
                }
                for project in projects[system][account]
            }
            for account in accounts[system]
        }
        for system in systems
    }
    return systems, accounts, projects, partitions, reservations

async def options_form(spawner):
    query_options = {}
    for key, byte_list in spawner.handler.request.query_arguments.items():
        query_options[key] = [bs.decode('utf8') for bs in byte_list]
    service = query_options.get("service", "JupyterLab")
    if type(service) == list:
        service = service[0]
    services = get_services()
    if service in services.keys():
        if services[service].get("options_depth", 1) == 1:
            return await options_form_depth_1(spawner, service, services[service].get("options", {}))
    raise NotImplementedError(f"{service} unknown")

async def options_form_depth_1(spawner, service, service_infos):
    user_auth_state = await spawner.user.get_auth_state()
    vo_active = user_auth_state["vo_active"]
    user_hpc_accounts = user_auth_state.get("oauth_user", {}).get(
        "hpc_infos_attribute", []
    )

    resources = get_resources()
    # spawner.log.info(f"Reservations: {reservations_dict}")
    maintenance_list = get_maintenance_list()
    # spawner.log.info(f"Maintenance: {maintenance_list}")
    reservations_dict = get_reservations()
    reservations_list = {
        system: list(x.split(";") for x in reservations_dict.get(system, []))
        for system in reservations_dict.keys()
    }
    systems_config = get_systems()
    vo_config = get_vo_config()

    if ( service not in vo_config.get(vo_active, {}).get("Services", {}).keys()
    or len(vo_config.get(vo_active, {}).get("Services", {}).get(service, {}).keys()) == 0):
        return {
            "options": {},
            "maintenance": maintenance_list,
            "message": f"The {vo_active} group does not support {service} services."
        }

    systems, accounts, projects, partitions, reservations = get_system_infos(spawner.log, user_hpc_accounts, systems_config, reservations_list, resources)

    def in_both_lists(list1, list2):
        return list(set(list1).intersection(set(list2)))

    required_partitions = {}

    options = {}
    for option1, infos in service_infos.items():
        # Check if the specific option1 is part of vo's allowed services
        if option1 not in vo_config.get(vo_active, {}).get("Services", {}).get(service, {}).keys():
            continue

        # HPC systems
        if "systems" in vo_config.get(vo_active, {}).get("Services", {}).get(service, {}).get(option1, {}).get("replace_allowed_lists", {}).keys():
            allowed_lists_systems = vo_config.get(vo_active, {}).get("Services", {}).get(service, {}).get(option1, {}).get("replace_allowed_lists", {})["systems"]
        else:
            allowed_lists_systems = infos.get("allowed_lists", {}).get("systems", systems)
        systems_used = in_both_lists(systems, allowed_lists_systems)
        for system in systems_used:
            # Maintenance -> Not allowed
            if system in maintenance_list:
                continue
            if "accounts" in vo_config.get(vo_active, {}).get("Services", {}).get(service, {}).get(option1, {}).get("replace_allowed_lists", {}).keys():
                allowed_lists_accounts = vo_config.get(vo_active, {}).get("Services", {}).get(service, {}).get(option1, {}).get("replace_allowed_lists", {})["accounts"]
            else:
                allowed_lists_accounts = infos.get("allowed_lists", {}).get("accounts", accounts[system])
            accounts_used = in_both_lists(accounts[system], allowed_lists_accounts)
            for account in accounts_used:
                if "projects" in vo_config.get(vo_active, {}).get("Services", {}).get(service, {}).get(option1, {}).get("replace_allowed_lists", {}).keys():
                    allowed_lists_projects = vo_config.get(vo_active, {}).get("Services", {}).get(service, {}).get(option1, {}).get("replace_allowed_lists", {})["projects"]
                else:
                    allowed_lists_projects = infos.get("allowed_lists", {}).get("projects", projects[system][account])
                projects_used = in_both_lists(projects[system][account], allowed_lists_projects)
                for project in projects_used:
                    if "partitions" in vo_config.get(vo_active, {}).get("Services", {}).get(service, {}).get(option1, {}).get("replace_allowed_lists", {}).keys():
                        allowed_lists_partitions = vo_config.get(vo_active, {}).get("Services", {}).get(service, {}).get(option1, {}).get("replace_allowed_lists", {})["partitions"]
                    else:
                        allowed_lists_partitions = infos.get("allowed_lists", {}).get("partitions", partitions[system][account][project])
                    partitions_used = in_both_lists(partitions[system][account][project], allowed_lists_partitions)
                    for partition in partitions_used:
                        if "reservations" in vo_config.get(vo_active, {}).get("Services", {}).get(service, {}).get(option1, {}).get("replace_allowed_lists", {}).keys():
                            allowed_lists_reservations = vo_config.get(vo_active, {}).get("Services", {}).get(service, {}).get(option1, {}).get("replace_allowed_lists", {})["reservations"]
                        else:
                            allowed_lists_reservations = infos.get("allowed_lists", {}).get("reservations", reservations[system][account][project][partition])
                        reservations_used = in_both_lists(reservations[system][account][project][partition], allowed_lists_reservations)
                        if "reservations" in vo_config.get(vo_active, {}).get("Services", {}).get(service, {}).get(option1, {}).get("replace_allowed_lists", {}).keys() and len(reservations_used) == 0:
                            # Dashboards expects specific reservations which we don't have
                            continue
                        if option1 not in options.keys():
                            options[option1] = {}
                        if system not in options[option1].keys():
                            options[option1][system] = {}
                        if account not in options[option1][system].keys():
                            options[option1][system][account] = {}
                        if project not in options[option1][system][account].keys():
                            options[option1][system][account][project] = {}
                        if system not in required_partitions.keys():
                            required_partitions[system] = []
                        if partition not in required_partitions[system]:
                            required_partitions[system].append(partition)
                        options[option1][system][account][project][partition] = reservations_used
        # Cloud systems
        if "systems" in vo_config.get(vo_active, {}).get("Services", {}).get(service, {}).get(option1, {}).get("replace_allowed_lists", {}).keys():
            allowed_lists_systems = vo_config.get(vo_active, {}).get("Services", {}).get(service, {}).get(option1, {}).get("replace_allowed_lists", {})["systems"]
        else:
            allowed_lists_systems = infos.get("allowed_lists", {}).get("systems", systems_config.get("K8s", {}).keys())
        systems_used = in_both_lists(systems_config.get("K8s", {}).keys(), allowed_lists_systems)
        for system in systems_used:
            if option1 not in options.keys():
                options[option1] = {}
            if system not in options[option1].keys():
                options[option1][system] = {}
        
    if not options:
        return {
            "options": {},
            "maintenance": maintenance_list,
            "message": f"The {vo_active} group does not support {service} services."
        }

    dropdown_lists = {
        "options": options,
        "systems": systems,
        "accounts": accounts,
        "projects": projects,
        "partitions": partitions,
        "reservations": reservations,
    }

    def replace_resource(option1, system, partition, resource, key):
        value = resources[system][partition][resource][key]
        if type(value) is int or type(value) is list:
            if resource in vo_config.get(vo_active, {}).get("Services", {}).get(service, {}).get(option1, {}).get("replace_resources", {}).get(system, {}).get(partition, {}).keys():
                if key == "MINMAX":
                    value = vo_config.get(vo_active, {}).get("Services", {}).get(service, {}).get(option1, {}).get("replace_resources", {}).get(system, {}).get(partition, {})[resource]
                    if type(value) == list and len(value) > 0 and type(value[0]) == list:
                        value = value[0]
                elif key == "DEFAULT":
                    value = vo_config.get(vo_active, {}).get("Services", {}).get(service, {}).get(option1, {}).get("replace_resources", {}).get(system, {}).get(partition, {})[resource]
                    if type(value) == list and len(value) > 0 and type(value[0]) == list:
                        value = value[1]
                    else:
                        value = value[0]
            return value
        else:
            if resource in vo_config.get(vo_active, {}).get("Services", {}).get(service, {}).get(option1, {}).get("replace_resources", {}).get(system, {}).get(partition, {}).keys():
                minmax = vo_config.get(vo_active, {}).get("Services", {}).get(service, {}).get(option1, {}).get("replace_resources", {}).get(system, {}).get(partition, {})[resource]
                if type(minmax) == list and len(minmax) > 0 and type(minmax[0]) == list:
                    minmax = minmax[0]
            else:
                minmax = resources[system][partition][resource]["MINMAX"]
            return value.replace("_min_", str(minmax[0])).replace("_max_", str(minmax[1]))

    resources_replaced = {
        option1: {
            system: {
                partition: {
                    resource: {
                        key: replace_resource(option1, system, partition, resource, key)
                        for key in resources[system][partition][resource].keys()
                    }
                    for resource in resources[system][partition].keys()
                }
                for partition in required_partitions.get(system, [])
            }
            for system, _partitions in _systems.items()
        }
        for option1, _systems in options.items()
    }
    return {
        "dropdown_lists": dropdown_lists,
        "reservations": reservations_list,
        "resources": resources_replaced,
        "maintenance": maintenance_list
    }


async def options_from_form(formdata):
    service = formdata.get("service_input", [""])[0]
    services = get_services()
    if service in services.keys():
        if services[service].get("options_depth", 1) == 1:
            return await options_from_form_depth_1(formdata)
    raise NotImplementedError("{} unknown".format(formdata.get("service_input"))) 
    

async def options_from_form_depth_1(formdata):
    resources = get_resources()

    resourcemapping = {"nodes": "Nodes", "runtime": "Runtime", "gpus": "GPUS"}
    systems_config = get_systems()

    def skip_resources(key, value):
        if key.startswith("resource_"):
            if formdata.get("system_input")[0] not in systems_config.get("UNICORE", {}).keys():
                return True
            elif formdata.get("partition_input")[0] in systems_config.get("UNICORE", {}).get(formdata.get("system_input")[0], {}).get("interactive_partitions", []):
                return True
            else:
                resource_name = key[len("resource_") :]
                if (
                    resourcemapping.get(resource_name, resource_name)
                    not in resources.get(formdata.get("system_input")[0].upper())
                    .get(formdata.get("partition_input")[0])
                    .keys()
                ):
                    return True
        else:
            if value in ["undefined", "None"]:
                return True
        return False

    def runtime_update(key, value_list):
        if key == "resource_Runtime":
            return int(value_list[0]) * 60
        return value_list[0]

    ret = {
        key: runtime_update(key, value)
        for key, value in formdata.items()
        if not skip_resources(key, value[0])
    }
    ret["options_input"] = ret.pop("options1_input")

    return ret

def options_from_query(query_options):
    ret = {key: value[0] for key, value in query_options.items() if key != "display"}
    # ret = insert_display(ret)
    return ret


"""
def insert_display(ret):
    ret["display"] = {}

    if ret["system_input"] == "hdfcloud":
        hdf_cloud = get_hdfcloud()
        _display_image = ret["account_input"]
        _image = hdf_cloud.get(_display_image, {}).get("internal_name", _display_image)
        ret["account_input"] = _image
        ret["display"]["system"] = "HDF-Cloud"
        ret["display"]["account"] = _display_image
        if _display_image == _image:
            for key, value in hdf_cloud.items():
                if type(value) == dict and value.get("internal_name", "") == _image:
                    ret["display"]["account"] = key
                    break
    return ret
"""
