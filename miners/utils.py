def addProposalType(string, types):
    result = string
    for p_type in types:
        result = result + "&siglaTipo={}".format(p_type)
    return result


def addProposalYear(string, types):
    result = string
    for p_year in types:
        result = result + "&ano={}".format(p_year)
    return result


def addProposalSituation(string, types):
    result = string
    for p_situation in types:
        result = result + "&idSituacao={}".format(p_situation)
    return result


def addLegislature(string, types):
    result = string
    for p_legislature_id in types:
        result = result + "&idLegislatura={}".format(p_legislature_id)
    return result


def addStatus(string, status):
    if(status):
        return string + "&idLegislatura={}".format("true")
    else:
        return string + "&idLegislatura={}".format("false")


# Print iterations progress
def printProgressBar(iteration, total, prefix="", suffix="", decimals=1, length=50, fill="█", printEnd="\r"):
    """
    Call in a loop to create terminal progress bar.
    Safe for total == 0.
    """
    if total is None or total == 0:
        percent = ("{0:." + str(decimals) + "f}").format(0)
        filledLength = 0
        bar = fill * filledLength + "-" * (length - filledLength)
        print(f"\r{prefix} |{bar}| {percent}% {suffix}", end=printEnd)
        # não dá flush final aqui, para manter compatível com o seu fluxo
        return

    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + "-" * (length - filledLength)
    print(f"\r{prefix} |{bar}| {percent}% {suffix}", end=printEnd)

    if iteration == total:
        print()
