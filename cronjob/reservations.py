# running on tunneling node, because the authorized_keys file allows only nodes without public ip
import json
from subprocess import check_output
from subprocess import STDOUT
reservation_key = "/home/ubuntu/.ssh/reservation"
reservation_timeout = 3
reservations_json_path = "/mnt/nfs/common/reservations/reservation_csv.json"
systems_json_path = "/mnt/nfs/config/misc/systems.json"
maintenance_json_path = "/mnt/nfs/common/status-messages/maintenance.json"

try:
    with open(reservations_json_path, "r") as f:
        old_reservations = json.load(f)
except:
    old_reservations = {}
with open(systems_json_path, "r") as f:
    systems_json = json.load(f)
with open(maintenance_json_path, "r") as f:
    maintenance_json = json.load(f)

ret = {}

def no_null(x):
    if x == "(null)":
        return ""
    return x

for system, infos in systems_json.get("UNICORE", {}).items():
    if system in maintenance_json or str(infos.get("check_reservations", "false")).lower() not in ["true", "1"]:
        continue
    try:
        fuser = infos["fuser"]
        host = infos["host"]
    except:
        print(f"Couldn't find fuser and/or host for {system}")
        continue
    li = [
        "ssh",
        "-i",
        reservation_key,
        "-oLogLevel=ERROR",
        "-oStrictHostKeyChecking=no",
        "-oUserKnownHostsFile=/dev/null",
        f"{fuser}@{host}",
        "-T",
    ]
    try:
        output = (
            check_output(li, stderr=STDOUT, timeout=reservation_timeout)
            .decode("utf8")
            .rstrip()
        )
        print(output)
    except:
        print("No")
        continue
    if output == "No reservations in the system":
        ret[system] = []
        continue
    split_string = "ReservationName="
    reservation_list = [
        "{}{}".format(split_string, x).split()
        for x in output.strip().split(split_string)
        if x
    ]
    csv = [
        ";".join([no_null(y.split("=", 1)[1]) for y in x if y])
        for x in reservation_list
    ]
    ret[system] = csv
    output = ""
with open(reservations_json_path, "w") as f:
    json.dump(ret, f, indent=4, sort_keys=True)
