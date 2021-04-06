import copy
import json
import os
import re

from .input_files import get_reservations
from .input_files import get_resources
from jupyterhub.jupyterjsc.utils.hdfcloud import get_hdfcloud
from jupyterhub.jupyterjsc.utils.maintenance import get_maintenance_list
from jupyterhub.jupyterjsc.utils.unicore import get_unicore_config


async def options_form(spawner):
    user_auth_state = await spawner.user.get_auth_state()
    vo_active = user_auth_state["vo_active"]
    user_hpc_accounts = user_auth_state.get("oauth_user", {}).get(
        "hpc_infos_attribute", []
    )

    resources = get_resources()
    reservations_dict = get_reservations()
    spawner.log.info(f"Reservations: {reservations_dict}")
    maintenance_list = get_maintenance_list()
    spawner.log.info(f"Maintenance: {maintenance_list}")
    hdf_cloud = get_hdfcloud()
    unicore_config = get_unicore_config()

    if "HDF-Cloud" in maintenance_list:
        hdf_cloud = {}
    else:
        # Remove all Images that are not allowed for active VO
        hdf_to_remove = [
            k
            for k, v in hdf_cloud.items()
            if "vos" in v.keys() and vo_active not in v["vos"]
        ]
        for name in hdf_to_remove:
            del hdf_cloud[name]

    # s = "^([^\,]+),([^\,\_]+)[_]?([^\,]*),([^\,]*),([^\,]*)$"
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
            spawner.log.error(
                f"No system defined in {map_systems_path} for {groups_[1]}"
            )
        partition = get_partition(groups_[1])
        if not partition:
            spawner.log.error(
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

    add_deep_ml_gpu_list = []
    add_deep_ml_gpu_projects = []
    for group in user_hpc_list:
        if group[1] == "DEEP" and group[3] not in add_deep_ml_gpu_projects:
            add_deep_ml_gpu_list.append(
                [group[0], group[1], "ml-gpu", group[3], group[4]]
            )
            add_deep_ml_gpu_projects.append(group[3])

    user_hpc_list.extend(add_deep_ml_gpu_list)

    systems = sorted(
        {
            group[1]
            for group in user_hpc_list
            if group[1] not in maintenance_list
            and (
                "vos" not in unicore_config.get(group[1].upper(), {}).keys()
                or vo_active in unicore_config.get(group[1].upper())["vos"]
            )
        }
    )

    def add_default_if(groups):
        if groups[2] == "gpus":
            return True
        return False

    def add_default(groups):
        ret = copy.deepcopy(groups)
        if ret[2] == "gpus":
            ret[2] = "develgpus"
        elif ret[2] == "batch":
            ret[2] = "devel"
        return ret

    add_defaults = [add_default(x) for x in user_hpc_list if add_default_if(x)]
    user_hpc_list.extend(add_defaults)

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
                project: sorted(
                    {
                        group[2]
                        for group in user_hpc_list
                        if system == group[1]
                        and account == group[0]
                        and project == group[3]
                        and group[2] in resources.get(system, {}).keys()
                    }
                )
                for project in projects[system][account]
            }
            for account in accounts[system]
        }
        for system in systems
    }
    reservations_list = {
        system: list(x.split(";") for x in reservations_dict.get(system, []))
        for system in reservations_dict.keys()
    }
    reservations = {
        system: {
            account: {
                project: {
                    partition: sorted(
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
    dropdown_lists = {
        "systems": systems,
        "accounts": accounts,
        "projects": projects,
        "partitions": partitions,
        "reservations": reservations,
    }

    def replace_resource(key, resource):
        value = resource[key]
        if type(value) is int or type(value) is list:
            return value
        else:
            return value.replace("_min_", str(resource["MINMAX"][0])).replace(
                "_max_", str(resource["MINMAX"][1])
            )

    resources_replaced = {
        system: {
            partition: {
                resource: {
                    key: replace_resource(key, resources[system][partition][resource])
                    for key in resources[system][partition][resource].keys()
                }
                for resource in resources[system][partition].keys()
            }
            for partition in resources[system].keys()
        }
        for system in resources.keys()
    }
    unicore_vo = {
        system.upper(): {
            "vos": unicore_config.get(system.upper(), {}).get("vos", []),
            "vo_exclude_partition": unicore_config.get(system.upper(), {}).get(
                "vo_exclude_partition", {}
            ),
        }
        for system in resources.keys()
    }
    return {
        "dropdown_lists": dropdown_lists,
        "reservations": reservations_list,
        "resources": resources_replaced,
        "hdfcloud": hdf_cloud,
        "maintenance": maintenance_list,
        "unicore_vo": unicore_vo,
    }


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


def runtime_update(key, value_list):
    if key == "resource_Runtime":
        return int(value_list[0]) * 60
    return value_list[0]


async def options_from_form(formdata):
    resources = get_resources()

    resourcemapping = {"nodes": "Nodes", "runtime": "Runtime", "gpus": "GPUS"}

    def skip_resources(key, value):
        if key.startswith("resource_"):
            if formdata.get("system_input")[0] == "hdfcloud":
                return True
            elif formdata.get("partition_input")[0] in [
                "LoginNode",
                "LoginNodeVis",
                "LoginBooster",
            ]:
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

    ret = {
        key: runtime_update(key, value)
        for key, value in formdata.items()
        if not skip_resources(key, value[0])
    }

    ret = insert_display(ret)

    return ret


def options_from_query(query_options):
    ret = {key: value[0] for key, value in query_options.items() if key != "display"}
    ret = insert_display(ret)
    return ret
