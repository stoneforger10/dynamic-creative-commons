import time

def test_composition_variation_and_member_guard(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/DynamicCreativeCommons.py")
    direct_vm.sender = direct_alice
    contract.create_space("studio", "Demo Studio")
    contract.register_element("studio", "character", "IMAGE", "a" * 64)
    contract.register_element("studio", "background", "DESIGN", "b" * 64)
    contract.create_composition("studio", "scene", "character,background")
    deadline = int(time.time()) + 3600
    contract.propose_evolution("studio", "variation-1", 0, "CREATE_VARIATION", "scene", "scene-v2", deadline)
    with direct_vm.expect_revert("active space and unique evolution required"):
        contract.propose_evolution("studio", "variation-1", 0, "CREATE_VARIATION", "scene", "scene-v3", deadline)
    assert contract.get_space("studio")["version"] == 0
