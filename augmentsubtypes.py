import json

from ifcopenshell.ifcopenshell_wrapper import schema_names, schema_by_name

icons = json.load(open("ifc-icons.json"))
icons_incl_subtypes = {}

def traverse(decl, icon=None):
    icon = icons.get(decl.name()) or icon
    icons_incl_subtypes[decl.name()] = icon
    for subtype in decl.subtypes():
        traverse(subtype, icon)

for nm in schema_names():
    schema = schema_by_name(nm)
    decl = schema.declaration_by_name("IfcProduct")
    traverse(decl)
    
json.dump(icons_incl_subtypes, open("ifc-full-icons.json", "w"))
