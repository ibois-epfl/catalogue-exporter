


def recurDictConstruct(children, items):
    if (len(items) > 0):
        children.append({
            "name": items.pop(0),
            "children": []
        })
        recurDictConstruct(children[0]["children"], items)
    return children

## recurDictConstruct example
#db = {
#    "name": "root",
#    "children": []
#}
#db["children"] = recurDictConstruct([], itemList)
#print db


def nestedDictGetItem(dict, path):
    def getDictChild(dict, i):
        return dict["children"][i]
    item = dict
    for i in path:
        item = getDictChild(item, i)
    return item

### nestedDictGetItem example
#db = {
#    "name": "root",
#    "children": [
#        {
#            "name": "0",
#            "children": [
#                {
#                    "name": "0.0",
#                    "children": []
#                },
#                {
#                    "name": "0.1",
#                    "children": []
#                }
#            ]
#        },
#        {
#            "name": "1",
#            "children": [
#                {
#                    "name": "1.0",
#                    "children": []
#                },
#                {
#                    "name": "1.1",
#                    "children": []
#                }
#            ]
#        }
#    ]
#}
#
#print nestedDictGetItem(db, [1,1])

