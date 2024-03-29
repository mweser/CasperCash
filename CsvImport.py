class CsvImport:
    def __init__(self):
        pass

    @staticmethod
    def to_dict(fullpath):
        with open(fullpath, "r") as f:
            return CsvImport.csv_to_dict(f.readlines())

    @staticmethod
    def csv_to_dict(source_data):
        new_list = []
        for i, line in enumerate(source_data):
            if i == 0:
                headers = line.strip().replace("\"", "").split(",")
            elif "Zelle" in line:
                pass
            elif "IMAD" in line:
                pass
            elif "OVERSEA CHINESE BANKING CORP" in line:
                pass
            else:
                dictionary = {}
                for j, item in enumerate(line.strip().replace(", ", "").replace(",,", ",").replace("\"", "").split(",")):
                    if j < len(headers):
                        if "Zelle" in item:
                            dictionary[headers[j]] = "Zelle Quickpay"
                        else:
                            dictionary[headers[j]] = item
                new_list.append(dictionary)
        return new_list
