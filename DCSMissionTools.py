import os
from STMFile import STMFile
from MIZFile import MIZFile
import argparse

parser = argparse.ArgumentParser(description='Assorted mission tools for digital combat simulator.')
parser.add_argument('missionfile', help='mission file to work on', nargs='+')
parser.add_argument('-D', '--dump-mission', help='Dumps the mission LUA of the first missionfile out to the specified '
                                                 'file, or use "-" for STDOUT. This will prevent any other action from '
                                                 'being taken!',
 nargs='?')
parser.add_argument('-M', '--max-ids', help='Displays the current maximum ids for groups and units.',
                    action='store_true', required=False)
parser.add_argument('-F', '--filter-nonclients', help='Filters out non-client units by removing them. Empty groups will '
                                                      'also be removed.',
                    action='store_true', required=False)
parser.add_argument('-C', '--compress-ids', help='Compresses the unit- and groupIds in the mission as to avoid their '
                                                 'values growing too large',
                    action='store_true', required=False)
parser.add_argument('-F1', '--fix-eplrs', help='Fixes incorrect links to groups for EPLRS waypoint settings. Will only '
                                               'work if used together with -C',
                              action='store_true', required=False)

parser.add_argument('-v', '--verbose', help='Give more feedback on what is being worked on',
                    action='store_true', required=False)

args = parser.parse_args()

def printv(obj):
    if args.verbose:
        print(obj)

def printMaxIds(mission):
    maxUnitId = 0
    maxGroupId = 0
    print("beginning analysis")
    for coalition_idx, coalition in mission["coalition"].items():
        printv("analysing coalition: {}".format(coalition_idx))
        for country_idx, country in coalition["country"].items():
            printv("analysing country: {}".format(country["name"]))
            for unittype in ["helicopter", "ship", "plane", "vehicle", "static"]:
                printv("analysing unittype: {}".format(unittype))
                if not unittype in country:
                    printv("unittype-key {} not found".format(unittype))
                    continue
                for group_idx, group in country[unittype]["group"].items():

                    printv("analysing group {}".format(group["groupId"]))
                    if ( group["groupId"] > maxGroupId ):
                        maxGroupId = group["groupId"]
                    for unit_idx, unit in group["units"].items():
                        printv("analysing unit {}".format(unit["unitId"]))
                        if ( unit["unitId"] > maxUnitId ):
                            maxUnitId = unit["unitId"]
    print("the highest group id is {0}, the highest unit id is {1}".format(maxGroupId, maxUnitId))

def compressIds(mission):
    unitids = dict()
    groupids = dict()
    unitIndex = 10000
    groupIndex = 1000
    print("compressing ids!")
    print("beginning analysis")
    for coalition_idx, coalition in mission["coalition"].items():
        printv("analysing coalition: {}".format(coalition_idx))
        for country_idx, country in coalition["country"].items():
            printv("analysing country: {}".format(country["name"]))
            for unittype in ["helicopter", "ship", "plane", "vehicle", "static"]:
                printv("analysing unittype: {}".format(unittype))
                if not unittype in country:
                    printv("unittype-key {} not found".format(unittype))
                    continue
                for group_idx, group in country[unittype]["group"].items():
                    unitsingroup = []

                    printv("analysing group {}".format(group["groupId"]))
                    groupids[group["groupId"]] = groupIndex
                    groupIndex += 1
                    for unit_idx, unit in group["units"].items():
                        printv("analysing unit {}".format(unit["unitId"]))
                        unitids[unit["unitId"]] = unitIndex
                        unitIndex += 1
                        unitsingroup.append(unit["unitId"])

                    for point_idx, point in group["route"]["points"].items():
                        if "linkUnit" in point:
                            printv("group {0} has a waypoint linked to a unit {1} that needs rewriting".format(
                                group["groupId"],
                                point["linkUnit"]
                            ))
                        if "helipadId" in point:
                            printv("group {0} has a waypoint linked to a helipad unit {1} that needs rewriting".format(
                                group["groupId"],
                                point["helipadId"]
                            ))
                        if not "task" in point:
                            continue
                        for task_idx, task in point["task"]["params"]["tasks"].items():
                            if task["id"] == 'WrappedAction':
                                if "params" in task:
                                    if "action" in task["params"]:
                                        if task["params"]["action"]["id"] == 'ActivateICLS':
                                            if not task["params"]["action"]["params"]["unitId"] in unitsingroup:
                                                print("group {0} has ActivateICLS task for unit {1} not part of group".format(group["groupId"], task["params"]["action"]["params"]["unitId"]))
                                        if task["params"]["action"]["id"] == 'ActivateBeacon':
                                            if not task["params"]["action"]["params"]["unitId"] in unitsingroup:
                                                print("group {0} has ActivateBeacon task for unit {1} not part of group".format(group["groupId"], task["params"]["action"]["params"]["unitId"]))
                                        if task["params"]["action"]["id"] == 'EPLRS':
                                            if not group["groupId"] == task["params"]["action"]["params"]["groupId"]:
                                                print("group {0} has EPLRS task for group {1} which is a foreign group".format(group["groupId"], task["params"]["action"]["params"]["groupId"]))
    print("beginning changes")
    for coalition_idx, coalition in mission["coalition"].items():
        printv("applying changes to coalition: {}".format(coalition_idx))
        for country_idx, country in coalition["country"].items():
            printv("applying changes to country: {}".format(country["name"]))
            for unittype in ["helicopter", "ship", "plane", "vehicle", "static"]:
                printv("applying changes to unittype: {}".format(unittype))
                if not unittype in country:
                    printv("unittype-key {} not found".format(unittype))
                    continue
                for group_idx, group in country[unittype]["group"].items():
                    unitsingroup = []
                    printv("applying changes to group {}".format(group["groupId"]))

                    for unit_idx, unit in group["units"].items():
                        printv("applying changes to unit {}".format(unit["unitId"]))
                        unitsingroup.append(unit["unitId"])

                        if not unit["unitId"] == unitids[unit["unitId"]]:
                            print("unit with id {0} will be rewritten as {1}".format(
                                unit["unitId"],
                                unitids[unit["unitId"]]
                            ))
                            unit["unitId"] = unitids[unit["unitId"]]

                    for point_idx, point in group["route"]["points"].items():
                        if "linkUnit" in point and not unitids[point["linkUnit"]] == point["linkUnit"]:
                            if point["linkUnit"] in unitids:
                                print("group {0} has a waypoint linked to a unit {1} that was rewritten to {2}".format(
                                    group["groupId"],
                                    point["linkUnit"],
                                    unitids[point["linkUnit"]]
                                ))
                                point["linkUnit"] = unitids[point["linkUnit"]]
                            else:
                                print("group {0} has a waypoint linked to a unit {1} that wasn't rewritten, as I the "
                                       "source unit wasn't found. This is most likely going to result in a broken mission!".format(
                                    group["groupId"],
                                    point["linkUnit"]
                                ))
                        if "helipadId" in point and not unitids[point["linkUnit"]] == point["helipadId"]:
                            if point["helipadId"] in unitids:
                                print("group {0} has a waypoint linked to a helipad unit {1} that was rewritten to {2}".format(
                                    group["groupId"],
                                    point["helipadId"],
                                    unitids[point["helipadId"]]
                                ))
                                point["helipadId"] = unitids[point["helipadId"]]
                            else:
                                print("group {0} has a waypoint linked to a helipad unit {1} that wasn't rewritten, as I the "
                                      "source unit wasn't found. This is most likely going to result in a broken mission!".format(
                                    group["groupId"],
                                    point["helipadId"]
                                ))
                        if not "task" in point:
                            continue
                        for task_idx, task in point["task"]["params"]["tasks"].items():
                            if task["id"] == 'WrappedAction':
                                if not "params" in task:
                                    continue
                                if not "action" in task["params"]:
                                    continue
                                if task["params"]["action"]["id"] == 'ActivateICLS':
                                    rewriteTaskUnitId(group, task, unitids, unitsingroup)
                                if task["params"]["action"]["id"] == 'ActivateBeacon':
                                    rewriteTaskUnitId(group, task, unitids, unitsingroup)
                                if task["params"]["action"]["id"] == 'EPLRS':
                                    rewriteTaskGroupId(group, task, groupids)

                    if not group["groupId"] == groupids[group["groupId"]]:
                        print("group with id {0} will be rewritten as {1}".format(
                            group["groupId"],
                            groupids[group["groupId"]]
                        ))
                        group["groupId"] = groupids[group["groupId"]]

def rewriteTaskGroupId(group, task, groupids):
    if not group["groupId"] == task["params"]["action"]["params"]["groupId"]:
        if args.fix_eplrs:
            print("FIXING: group {1} {0} task will be pointed at this groups new id {2}".format(
                task["params"]["action"]["id"],
                group["groupId"],
                groupids[group["groupId"]]
            ))
            task["params"]["action"]["params"]["groupId"] = groupids[group["groupId"]]
        elif task["params"]["action"]["params"]["groupId"] in groupids and not task["params"]["action"]["params"]["groupId"] == groupids[task["params"]["action"]["params"]["groupId"]]:
            print("group {1} has {0} task for group {2} which is a foreign group will be pointed at new id {3}".format(
                task["params"]["action"]["id"],
                group["groupId"],
                task["params"]["action"]["params"]["groupId"],
                groupids[task["params"]["action"]["params"]["groupId"]]
            ))
            task["params"]["action"]["params"]["groupId"] = groupids[task["params"]["action"]["params"]["groupId"]]
        else:
            print("group {1} has {0} task for group {2} which is a foreign group, could not find target to redirect. "
                  "Won't change the value".format(
                task["params"]["action"]["id"],
                group["groupId"],
                task["params"]["action"]["params"]["groupId"]
            ))
    elif not task["params"]["action"]["params"]["groupId"] == groupids[task["params"]["action"]["params"]["groupId"]]:
        print("group {1} {0} task will be pointed to new group id {2} of previously connected group".format(
            task["params"]["action"]["id"],
            group["groupId"],
            groupids[group["groupId"]]
        ))
        task["params"]["action"]["params"]["groupId"] = groupids[task["params"]["action"]["params"]["groupId"]]

def rewriteTaskUnitId(group, task, unitids, unitsingroup):
    if not task["params"]["action"]["params"]["unitId"] in unitsingroup:
        if args.fix_eplrs:
            print("group {1} {0} task for unit {2} will be pointed at first unit in group".format(
                task["params"]["action"]["id"],
                group["groupId"],
                task["params"]["action"]["params"]["unitId"]
            ))
            task["params"]["action"]["params"]["unitId"] = unitids[group["units"][0]["unitId"]]
        elif task["params"]["action"]["params"]["unitId"] in unitids and not task["params"]["action"]["params"]["unitId"] == unitids[task["params"]["action"]["params"]["unitId"]]:
            print("group {1} {0} task for unit {2} will be pointed at new id {3} for that foreign unit".format(
                task["params"]["action"]["id"],
                group["groupId"],
                task["params"]["action"]["params"]["unitId"],
                unitids[task["params"]["action"]["params"]["unitId"]]
           ))
            task["params"]["action"]["params"]["unitId"] = unitids[task["params"]["action"]["params"]["unitId"]]
        else:
            print("group {1} {0} task for unit {2} could not find target to redirect. Won't change the value".format(
                task["params"]["action"]["id"],
                group["groupId"],
                task["params"]["action"]["params"]["unitId"]
            ))
    elif not task["params"]["action"]["params"]["unitId"] == unitids[task["params"]["action"]["params"]["unitId"]]:
        print("group {1} {0} task for unit {2} will be pointed to new unit id {3} of previously connected unit".format(
            task["params"]["action"]["id"],
            group["groupId"],
            task["params"]["action"]["params"]["unitId"],
            unitids[task["params"]["action"]["params"]["unitId"]]
        ))
        task["params"]["action"]["params"]["unitId"] = unitids[task["params"]["action"]["params"]["unitId"]]

def removeNonClientUnits(mission):
    print("removing non-client units!")
    print("beginning analysis")
    for coalition_idx, coalition in mission["coalition"].items():
        printv("analysing coalition: {}".format(coalition_idx))
        for country_idx, country in coalition["country"].items():
            printv("analysing country: {}".format(country["name"]))
            for unittype in ["helicopter", "ship", "plane", "vehicle", "static"]:
                printv("analysing unittype: {}".format(unittype))
                if not unittype in country:
                    printv("unittype-key {} not found".format(unittype))
                    continue

                groupsToBeRemoved = []
                for group_idx, group in country[unittype]["group"].items():
                    printv("analysing group {}".format(group["groupId"]))

                    numClientUnits = 0
                    clientsToBeRemoved = []
                    for unit_idx, unit in group["units"].items():
                        printv("analysing unit {}".format(unit["unitId"]))
                        if not 'skill' in unit or not unit["skill"] == "Client":
                            print("flagging unit {} to be removed as it's not a client".format(unit["unitId"]))
                            clientsToBeRemoved.append(unit_idx)
                        else:
                            print("found client {}".format(unit["unitId"]))
                            numClientUnits += 1

                    for unit_idx in reversed(clientsToBeRemoved):
                        print("removing unit with technical index {}.".format(unit_idx))
                        del group["units"][unit_idx]

                    if numClientUnits == 0:
                        printv("flagging group {} to be removed as it has no client-units (anymore)".format(group["groupId"]))
                        groupsToBeRemoved.append(group_idx)

                for group_idx in reversed(groupsToBeRemoved):
                    printv("removing group with technical index {}.".format(group_idx))
                    del country[unittype]["group"][group_idx]

if __name__ == '__main__':
    muteOutput = not (args.dump_mission is None and not args.dump_mission == '-')

    for missionfile in args.missionfile:
        extension = os.path.splitext(missionfile)[1].lower()
        if extension == '.stm':
            if not muteOutput:
                print("Opening template {}".format(missionfile))
            MIZ = STMFile(missionfile, False)
        elif extension == '.miz':
            if not muteOutput:
                print("Opening mission {}".format(missionfile))
            MIZ = MIZFile(missionfile, False)
        else:
            if not muteOutput:
                print("Skipped input missionfile {} because it's extension doesn't match STM or MIZ".format(missionfile))
            continue

        mission_changed = False

        mission = MIZ.getMission()

        if not args.dump_mission is None:
            if args.dump_mission == '-':
                print(MIZ.getMissionLUA())
            else:
                print("Saving mission (LUA) to file {0}".format(args.dump_mission))
                output = open(args.dump_mission, "wb")
                output.write(MIZ.getMissionLUA())
                output.close()
            break
        if args.max_ids:
            printMaxIds(mission)
        if args.filter_nonclients:
            removeNonClientUnits(mission)
            mission_changed = True
        if args.compress_ids:
            compressIds(mission)
            mission_changed = True

        if mission_changed:
            print("Committing changes to mission {}".format(missionfile))
            MIZ.setMission(mission)
            MIZ.commit()
            if args.max_ids:
                print("max-ids after changes")
                printMaxIds(mission)

    if not muteOutput:
        print("done")