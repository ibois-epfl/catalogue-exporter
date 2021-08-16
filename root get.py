import json

itemList = "Stones.Basalt.Batch42".split(".")

db = {
    "name": "root",
    "children": []
}

def recurDictConstruct(children, items):
    if (len(items) > 0):
        children.append({
            "name": items.pop(0),
            "children": []
        })
        recurDictConstruct(children[0]["children"], items)
    return children
    
db["children"] = recurDictConstruct([], itemList)
print db

print json.dumps(db)


db = {
    "name": "root",
    "children": [
        {
            "name": "0",
            "children": [
                {
                    "name": "0.0",
                    "children": []
                },
                {
                    "name": "0.1",
                    "children": []
                }
            ]
        },
        {
            "name": "1",
            "children": [
                {
                    "name": "1.0",
                    "children": []
                },
                {
                    "name": "1.1",
                    "children": []
                }
            ]
        }
    ]
}

print db

def nestedDictGetItem(dict, path):
    def getDictChild(dict, i):
        return dict["children"][i]
    item = dict
    for i in path:
        item = getDictChild(item, i)
    return item

print nestedDictGetItem(db, [1,1])

itemList = "Stones.Basalt.Batch34".split(".")

db = {
    "name": "root",
    "children": []
}

