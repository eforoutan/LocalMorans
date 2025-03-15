cwlVersion: v1.2
class: CommandLineTool

hints:
  DockerRequirement:
    dockerPull: "eforoutan/calc_local_morans:latest"
  NetworkAccess:
    networkAccess: true 

inputs:
  input_shapefile:
    type: Directory
    inputBinding:
      position: 1

  field_name:
    type: string
    inputBinding:
      position: 2

  weight_type:
    type:
      type: enum  
      symbols:
        - "queen"
        - "rook"
    default: "queen"
    inputBinding:
      position: 3

outputs:
  local_morans_output_geojson:
    type: File
    outputBinding:
      glob: local_morans_results.geojson

  local_morans_output_csv:
    type: File
    outputBinding:
      glob: local_morans_results.csv

