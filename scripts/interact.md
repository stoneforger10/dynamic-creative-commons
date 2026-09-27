# Interaction sketch

```powershell
genlayer write ADDRESS create_space --args studio 'Demo Studio'
genlayer write ADDRESS register_element --args studio character IMAGE HASH64
genlayer write ADDRESS register_element --args studio background DESIGN HASH64
genlayer write ADDRESS create_composition --args studio scene 'character,background'
genlayer write ADDRESS propose_evolution --args studio variation-1 0 CREATE_VARIATION scene scene-v2 DEADLINE
genlayer write ADDRESS apply_evolution --args studio variation-1
```
