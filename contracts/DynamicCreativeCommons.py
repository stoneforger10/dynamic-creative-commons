# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from genlayer import *

ELEMENT_TYPES = ("IMAGE", "AUDIO", "TEXT", "DESIGN", "ANIMATION", "MODEL", "PATTERN")
RELATION_TYPES = ("INSPIRED_BY", "COMBINES_WITH", "EXTENDS", "MODIFIES", "DERIVED_FROM")
OPERATIONS = ("REARRANGE", "CREATE_VARIATION")

def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))

def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def key(space_id: str, item_id: str) -> str:
    return space_id + ":" + item_id

def valid_id(value: str) -> bool:
    return 1 <= len(value) <= 48 and all(c in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in value)

def valid_hash(value: str) -> bool:
    return len(value) == 64 and all(c in "0123456789abcdef" for c in value)

def now() -> int:
    return int(datetime.fromisoformat(gl.message_raw["datetime"]).timestamp())

@allow_storage
@dataclass
class Space:
    owner: Address
    name: str
    status: str
    version: u256
    elements: str
    relations: str
    compositions: str
    root: str

@allow_storage
@dataclass
class Evolution:
    space_id: str
    proposer: Address
    parent_version: u256
    parent_root: str
    operation: str
    composition_id: str
    payload: str
    deadline: u256
    state: str
    result_root: str

class DynamicCreativeCommons(gl.Contract):
    spaces: TreeMap[str, Space]
    evolutions: TreeMap[str, Evolution]
    records: TreeMap[str, str]
    snapshots: TreeMap[str, str]

    def __init__(self) -> None:
        pass

    def _owned(self, space_id: str) -> Space:
        if space_id not in self.spaces:
            raise gl.vm.UserError("[EXPECTED] unknown creative space")
        space = self.spaces[space_id]
        if space.owner != gl.message.sender_address:
            raise gl.vm.UserError("[EXPECTED] space owner required")
        return space

    def _element_ids(self, raw: str) -> list:
        if not 1 <= len(raw) <= 1200:
            raise gl.vm.UserError("[EXPECTED] bounded element list required")
        ids = [x for x in raw.split(",") if x]
        if not 1 <= len(ids) <= 32 or len(set(ids)) != len(ids):
            raise gl.vm.UserError("[EXPECTED] unique element list required")
        if not all(valid_id(x) for x in ids):
            raise gl.vm.UserError("[EXPECTED] valid element IDs required")
        return ids

    def _simulate(self, space: Space, evolution: Evolution) -> dict:
        compositions = json.loads(space.compositions)
        elements = json.loads(space.elements)
        if evolution.composition_id not in compositions:
            return {"valid": False, "reason": "unknown_composition", "compositions": compositions}
        current = compositions[evolution.composition_id]["elements"]
        if evolution.operation == "REARRANGE":
            ids = self._element_ids(evolution.payload)
            if sorted(ids) != sorted(current):
                return {"valid": False, "reason": "composition_membership_changed", "compositions": compositions}
            compositions[evolution.composition_id]["elements"] = ids
        elif evolution.operation == "CREATE_VARIATION":
            if not valid_id(evolution.payload) or evolution.payload in compositions:
                return {"valid": False, "reason": "variation_id", "compositions": compositions}
            compositions[evolution.payload] = {"elements": list(current), "parent": evolution.composition_id}
        else:
            return {"valid": False, "reason": "operation", "compositions": compositions}
        if any(x not in elements for c in compositions.values() for x in c["elements"]):
            return {"valid": False, "reason": "missing_element", "compositions": compositions}
        return {"valid": True, "reason": "", "compositions": compositions}

    def _report(self, space_id: str, evolution_id: str, space: Space, evolution: Evolution) -> dict:
        simulated = self._simulate(space, evolution)
        packet = {"protocol": "dynamic-creative-commons-v1", "space": space_id,
                  "evolution": evolution_id, "parent_version": int(evolution.parent_version),
                  "parent_root": evolution.parent_root, "operation": evolution.operation,
                  "composition_id": evolution.composition_id, "payload": evolution.payload,
                  "valid": simulated["valid"], "reason": simulated["reason"],
                  "compositions": simulated["compositions"]}
        packet["result_root"] = digest(canonical(packet))
        return packet

    def _finish(self, space_id: str, evolution_id: str, space: Space, evolution: Evolution,
                state: str, report: dict) -> None:
        packet = {"state": state, "space": space_id, "evolution": evolution_id, "report": report}
        evolution.state = state
        evolution.result_root = digest(canonical(packet))
        self.records[key(space_id, evolution_id)] = canonical(packet)
        if state == "APPLIED":
            space.compositions = canonical(report["compositions"])
            space.version += 1
            space.status = "EVOLVING"
            space.root = digest(canonical({"space": space_id, "version": int(space.version),
                "elements": json.loads(space.elements), "relations": json.loads(space.relations),
                "compositions": json.loads(space.compositions), "parent_root": evolution.parent_root,
                "evolution_root": evolution.result_root}))
            self.snapshots[key(space_id, str(int(space.version)))] = canonical({
                "version": int(space.version), "root": space.root,
                "compositions": json.loads(space.compositions), "evolution": evolution_id})
            self.spaces[space_id] = space
        self.evolutions[key(space_id, evolution_id)] = evolution

    @gl.public.write
    def create_space(self, space_id: str, name: str) -> None:
        if not valid_id(space_id) or space_id in self.spaces:
            raise gl.vm.UserError("[EXPECTED] unique space ID required")
        if not 1 <= len(name) <= 120:
            raise gl.vm.UserError("[EXPECTED] bounded space name required")
        self.spaces[space_id] = Space(gl.message.sender_address, name, "CREATED", 0, "{}", "{}", "{}",
            digest(canonical({"space": space_id, "version": 0, "elements": {}, "relations": {}, "compositions": {}})))

    @gl.public.write
    def register_element(self, space_id: str, element_id: str, element_type: str, reference_hash: str) -> None:
        space = self._owned(space_id)
        elements = json.loads(space.elements)
        if len(elements) >= 256 or not valid_id(element_id) or element_id in elements:
            raise gl.vm.UserError("[EXPECTED] unique bounded element required")
        if element_type not in ELEMENT_TYPES or not valid_hash(reference_hash):
            raise gl.vm.UserError("[EXPECTED] element type and SHA-256 reference required")
        elements[element_id] = {"type": element_type, "reference_hash": reference_hash,
                                "creator": gl.message.sender_address.as_hex, "version": 0}
        space.elements = canonical(elements)
        space.status = "ACTIVE"
        space.root = digest(canonical({"space": space_id, "version": int(space.version),
            "elements": elements, "relations": json.loads(space.relations),
            "compositions": json.loads(space.compositions)}))
        self.spaces[space_id] = space

    @gl.public.write
    def connect_elements(self, space_id: str, relation_id: str, source: str, target: str, relation_type: str) -> None:
        space = self._owned(space_id)
        elements = json.loads(space.elements)
        relations = json.loads(space.relations)
        if not valid_id(relation_id) or relation_id in relations:
            raise gl.vm.UserError("[EXPECTED] unique relation required")
        if source not in elements or target not in elements or source == target or relation_type not in RELATION_TYPES:
            raise gl.vm.UserError("[EXPECTED] valid distinct elements and relation required")
        relations[relation_id] = {"source": source, "target": target, "type": relation_type}
        space.relations = canonical(relations)
        self.spaces[space_id] = space

    @gl.public.write
    def create_composition(self, space_id: str, composition_id: str, element_ids: str) -> None:
        space = self._owned(space_id)
        compositions = json.loads(space.compositions)
        elements = json.loads(space.elements)
        ids = self._element_ids(element_ids)
        if composition_id in compositions or any(x not in elements for x in ids):
            raise gl.vm.UserError("[EXPECTED] unique composition with existing elements required")
        compositions[composition_id] = {"elements": ids, "parent": ""}
        space.compositions = canonical(compositions)
        space.status = "ACTIVE"
        self.spaces[space_id] = space

    @gl.public.write
    def propose_evolution(self, space_id: str, evolution_id: str, parent_version: int,
                          operation: str, composition_id: str, payload: str, deadline: int) -> None:
        space = self._owned(space_id)
        evolution_key = key(space_id, evolution_id)
        if space.status not in ("ACTIVE", "EVOLVING") or not valid_id(evolution_id) or evolution_key in self.evolutions:
            raise gl.vm.UserError("[EXPECTED] active space and unique evolution required")
        if parent_version != int(space.version) or not now() < deadline <= now() + 86400:
            raise gl.vm.UserError("[EXPECTED] current version and deadline within one day required")
        if operation not in OPERATIONS or not valid_id(composition_id):
            raise gl.vm.UserError("[EXPECTED] valid operation and composition required")
        evolution = Evolution(space_id, gl.message.sender_address, parent_version, space.root,
                              operation, composition_id, payload, deadline, "PROPOSED", "")
        if not self._simulate(space, evolution)["valid"]:
            raise gl.vm.UserError("[EXPECTED] evolution violates composition rules")
        self.evolutions[evolution_key] = evolution

    @gl.public.write
    def apply_evolution(self, space_id: str, evolution_id: str) -> None:
        space = self._owned(space_id)
        evolution_key = key(space_id, evolution_id)
        if evolution_key not in self.evolutions:
            raise gl.vm.UserError("[EXPECTED] evolution not found")
        evolution = self.evolutions[evolution_key]
        if evolution.space_id != space_id or evolution.state != "PROPOSED":
            raise gl.vm.UserError("[EXPECTED] terminal or cross-space evolution")
        if now() >= int(evolution.deadline):
            self._finish(space_id, evolution_id, space, evolution, "EXPIRED", {"reason": "deadline"})
            return
        if int(evolution.parent_version) != int(space.version) or evolution.parent_root != space.root:
            self._finish(space_id, evolution_id, space, evolution, "STALE", {"reason": "parent_head"})
            return
        def observe() -> dict:
            return self._report(space_id, evolution_id, space, evolution)
        def validate(leader: gl.vm.Result) -> bool:
            return isinstance(leader, gl.vm.Return) and leader.calldata == self._report(space_id, evolution_id, space, evolution)
        report = gl.vm.run_nondet_unsafe(observe, validate)
        self._finish(space_id, evolution_id, space, evolution,
                     "APPLIED" if report["valid"] else "REJECTED", report)

    @gl.public.view
    def get_space(self, space_id: str) -> dict:
        space = self.spaces[space_id]
        return {"owner": space.owner, "name": space.name, "status": space.status,
                "version": space.version, "root": space.root, "elements": json.loads(space.elements),
                "relations": json.loads(space.relations), "compositions": json.loads(space.compositions)}

    @gl.public.view
    def get_evolution(self, space_id: str, evolution_id: str) -> dict:
        evolution = self.evolutions[key(space_id, evolution_id)]
        return {"space": evolution.space_id, "proposer": evolution.proposer,
                "parent_version": evolution.parent_version, "parent_root": evolution.parent_root,
                "operation": evolution.operation, "composition": evolution.composition_id,
                "payload": evolution.payload, "deadline": evolution.deadline,
                "state": evolution.state, "result_root": evolution.result_root}

    @gl.public.view
    def get_record(self, space_id: str, evolution_id: str) -> str:
        return self.records[key(space_id, evolution_id)]

    @gl.public.view
    def get_snapshot(self, space_id: str, version: int) -> str:
        return self.snapshots[key(space_id, str(version))]
