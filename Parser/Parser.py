# -*- coding: UTF-8 -*-
import sys
import logging
import xml.etree.ElementTree as ET
from opcua import ua, Server
from opcua.ua.object_ids import ObjectIds
from opcua.common.xmlexporter import XmlExporter
from opcua.common.xmlimporter import XmlImporter


class Parser:
    def __init__(self, nullable=True):
        logging.info("Start.")
        self.nullable = nullable

    def parse(self, aml_file, namespace):
        self.server = Server()
        self.server.import_xml("Opc.Ua.AMLBaseTypes.NodeSet2.xml")
        self.ns = self.server.register_namespace(namespace)
        objects = self.server.get_objects_node()
        tree = ET.parse(aml_file)
        root = tree.getroot()
        assert root.tag == 'CAEXFile'
        aml_node = objects.add_folder(
            ua.NodeId(aml_file, self.ns), ua.QualifiedName(aml_file, self.ns))
        InstanceHierarchies = aml_node.add_folder(ua.NodeId(
            "InstanceHierarchies", self.ns), ua.QualifiedName("InstanceHierarchies", self.ns))
        SystemUnitClassLibs = aml_node.add_folder(ua.NodeId(
            "SystemUnitClassLibs", self.ns), ua.QualifiedName("SystemUnitClassLibs", self.ns))
        RoleClassLibs = aml_node.add_folder(ua.NodeId(
            "RoleClassLibs", self.ns), ua.QualifiedName("RoleClassLibs", self.ns))
        InterfaceClassLibs = aml_node.add_folder(ua.NodeId(
            "InterfaceClassLibs", self.ns), ua.QualifiedName("InterfaceClassLibs", self.ns))

        for node in root.iter('RoleClassLib'):
            UAChild = self.RoleClassLib(RoleClassLibs, node)
            if UAChild is not None:
                self._DFS(node, UAChild)

        for node in root.iter('SystemUnitClassLib'):
            UAChild = self.SystemUnitClassLib(SystemUnitClassLibs, node)
            if UAChild is not None:
                self._DFS(node, UAChild)

        for node in root.iter('InterfaceClassLib'):
            UAChild = self.InterfaceClassLib(InterfaceClassLibs, node)
            if UAChild is not None:
                self._DFS(node, UAChild)

        for node in root.iter('InstanceHierarchy'):
            UAChild = self.InstanceHierarchy(InstanceHierarchies, node)
            if UAChild is not None:
                self._DFS(node, UAChild)

    def export(self, xml_path, ns_only=False):
        self.server.export_xml_by_ns(xml_path, self.ns if ns_only else None)

    # %%
    def _DFS(self, parent, UAParent):
        for child in parent:
            UAChild = getattr(self, child.tag, self.Default)(UAParent, child)
            if UAChild is not None:
                # print("UAChild",UAChild.nodeid.Identifier)
                self._DFS(child, UAChild)

    _Type2Type = {
        "xs:string": "String",
        "xs:decimal": "Float",
        "xs:integer": "Int64",
        "xs:boolean": "Boolean",
        "xs:date": "DateTime",
        "xs:time": "DateTime",
    },

    def _byName(self, child):
        return ua.NodeId(child.get('ID') or child.get('Name'), self.ns)

    def _byPathName(self, UAParent, connector, child):
        return ua.NodeId(str(UAParent.nodeid.Identifier) + connector + child.get('Name'), self.ns)

    def _byID(self, UAParent, child):
        if child.get('ID'):
            return ua.NodeId(child.get('ID'), self.ns)
        else:
            return self._byPathName(UAParent, ":", child)

    def _bname(self, child):
        return ua.QualifiedName(child.attrib['Name'], self.ns)

    # TODO 暂时不考虑 RefBaseClassPath 和 RefBaseSystemUnitPath

    def InstanceHierarchy(self, UAParent, child):
        # name
        return UAParent.add_folder(self._byName(child), self._bname(child))

    def InternalElement(self, UAParent, child):
        # id
        UAChild = UAParent.add_object(
            self._byID(UAParent, child), self._bname(child))

        if child.attrib.get('RefBaseClassPath'):
            dst = ua.NodeId(self.ns, child.attrib['RefBaseClassPath'])
            dst_node = self.server.get_node(dst)
            try:
                UAChild.add_reference(dst_node, ObjectIds.HasTypeDefinition)
            except BaseException as e:
                logging.warn("In InternalElement: %s, with dst %s", e, dst)

        return UAChild

    def InterfaceClassLib(self, UAParent, child):
        # name
        return UAParent.add_folder(self._byName(child), self._bname(child))

    def InterfaceClass(self, UAParent, child):
        # path/name
        UAChild = UAParent.add_object_type(
            self._byPathName(UAParent, "/", child), self._bname(child))

        if child.attrib.get('SupportedRoleClass'):
            logging.error(
                "InterfaceClass shouldn't have attr SupportedRoleClass: %s", self._bname(child))

        if child.attrib.get('RoleRequirement'):
            logging.error(
                "InterfaceClass shouldn't have attr RoleRequirement: %s", self._bname(child))

        if child.attrib.get('RefBaseClassPath'):
            dst = ua.NodeId(self.ns, child.attrib['RefBaseClassPath'])
            dst_node = self.server.get_node(dst)
            try:
                UAChild.add_reference(dst_node, ObjectIds.HasSubtype)
            except BaseException as e:
                logging.warn("In InterfaceClass: %s, with dst %s", e, dst)

        return UAChild

    def ExternalInterface(self, UAParent, child):
        # path:name
        UAChild = UAParent.add_object(self._byPathName(
            UAParent, ":", child), self._bname(child))
        UAChild.add_variable(self.ns, "ID", child.attrib['ID'])

        if child.attrib.get('RefBaseClassPath'):
            dst = ua.NodeId(self.ns, child.attrib['RefBaseClassPath'])
            dst_node = self.server.get_node(dst)
            try:
                UAChild.add_reference(dst_node, ObjectIds.HasTypeDefinition)
            except BaseException as e:
                logging.warn("In ExternalInterface: %s, with dst %s", e, dst)

        return UAChild

    def RoleClassLib(self, UAParent, child):
        # name
        return UAParent.add_folder(self._byName(child), self._bname(child))

    def RoleClass(self, UAParent, child):
        # path/name
        return UAParent.add_object_type(self._byPathName(UAParent, "/", child), self._bname(child))

    def SystemUnitClassLib(self, UAParent, child):
        # name
        node_id = self._byName(child)
        bname = self._bname(child)
        return UAParent.add_folder(node_id, bname)

    def SystemUnitClass(self, UAParent, child):
        # path/name
        UAChild = UAParent.add_object_type(
            self._byPathName(UAParent, "/", child), self._bname(child))

        if child.attrib.get('SupportedRoleClass'):
            dst = ua.NodeId(self.ns, child.attrib['SupportedRoleClass'])
            dst_node = self.server.get_node(dst)
            try:
                UAChild.add_reference(dst_node, "ns=1;i=4001")
            except BaseException as e:
                logging.warn("In SystemUnitClass: %s, with dst %s", e, dst)

        if child.attrib.get('RefBaseClassPath'):
            dst = ua.NodeId(self.ns, child.attrib['RefBaseClassPath'])
            dst_node = self.server.get_node(dst)
            try:
                UAChild.add_reference(dst_node, ObjectIds.HasSubtype)
            except BaseException as e:
                logging.warn("In SystemUnitClass: %s, with dst %s", e, dst)

        return UAChild

    def Version(self, UAParent, child):
        # path:name
        nodeid = ua.NodeId(str(UAParent.nodeid.Identifier) +
                           "@Version", self.ns)
        bname = ua.QualifiedName("Version", self.ns)
        UAChild = UAParent.add_variable(nodeid, bname, child.text)
        return UAChild

    def Attribute(self, UAParent, child):
        # path:name
        UAChild = UAParent.add_object(
            self._byPathName(UAParent, ":", child), self._bname(child))

        Value = None if self.nullable else ""
        if list(child) and child[0].tag == "Value":
            Value = child[0].text

        def getNodeId(s): return ua.NodeId(
            str(UAChild.nodeid.Identifier) + "@" + s, self.ns)

        def getBName(s): return ua.QualifiedName(s, self.ns)

        UAChild.add_variable(getNodeId("Value"), getBName("Value"), Value)
        UAChild.add_variable(getNodeId("DefaultValue"),
                             getBName("DefaultValue"), Value)
        DataType = child.attrib.get("AttributeDataType", "xs:string")
        UAChild.add_variable(getNodeId("DataType"),
                             getBName("DataType"), DataType)
        UAChild.add_variable(getNodeId("Unit"), getBName("Unit"), "")

        return UAChild

    def InternalLink(self, UAParent, child):
        src = ua.NodeId(child.attrib['RefPartnerSideA'], self.ns)
        src_node = self.server.get_node(src)
        dst = ua.NodeId(child.attrib['RefPartnerSideB'], self.ns)
        dst_node = self.server.get_node(dst)
        try:
            src_node.add_reference(
                dst_node, "ns=1;i=4002")
        except BaseException as e:
            logging.warn("In InternalLink: %s, with dst %s", e, dst)

    def SupportedRoleClass(self, UAParent, child):
        path = child.attrib.get('RefRoleClassPath')
        if not path:
            logging.warn("SupportedRoleClass without RefRoleClassPath")
            return
        dst = ua.NodeId(path, self.ns)
        dst_node = self.server.get_node(dst)
        try:
            UAParent.add_reference(
                dst_node, "ns=1;i=4001")
        except BaseException as e:
            logging.warn("In SupportedRoleClass: %s, with dst %s", e, dst)

    def RoleRequirements(self, UAParent, child):
        path = child.attrib.get('RefBaseRoleClassPath')
        if not path:
            logging.warn("RoleRequirements without RefBaseRoleClassPath")
            return
        dst = ua.NodeId(path, self.ns)
        dst_node = self.server.get_node(dst)
        try:
            UAParent.add_reference(
                dst_node, "ns=1;i=4001")
        except BaseException as e:
            logging.warn("In RoleRequirements: %s, with dst %s", e, dst)

    def Default(self, UAParent, child):
        logging.debug("Unfound Tag: %s", child.tag, )
        return None


